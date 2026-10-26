"""Intraday paper trading on Alpaca: rebalance every bar, flat before the close.

Each cycle, a few seconds after a bar closes:

1. fetch today's bars for the model's stocks (real-time IEX feed on the free
   plan) and recompute the same features the backtest uses;
2. forecast with the latest model: the production ridge (``model.json``) or
   the intraday zoo's winner (``model_zoo.joblib``);
3. read the account's positions, build target weights with the backtest's own
   ``target_weights`` and send whole-share market orders for the difference;
4. from ``flat_bar`` on (15:45, or 15 minutes before an early close) close
   everything, so nothing is held overnight.

This mode owns the whole paper account: don't run it alongside the daily
strategy (the TRADING_MODE variable picks one: auction (default), intraday or daily).
A GitHub job can run for at most 6 hours, so the loop stops at ``deadline``
and reports that a follow-up run is needed; positions live at Alpaca, so the
next run carries on where this one stopped.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.intraday import AlpacaBars, bars_to_frame
from ..live.alpaca_trader import _account_state, _client, _submit, plan_orders
from ..utils import LOG
from .bars import from_frames
from .features import FEATURES, day_features, history
from .strategy import target_weights

NY = "America/New_York"


def load_model(path: str | Path) -> dict:
    """model.json (production ridge, from intraday-backtest) or model_zoo.joblib (the
    intraday zoo's best model, from intraday-train)."""
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"No intraday model at {path}. Run the intraday-backtest workflow first.")
    if path.suffix == ".joblib":
        from .zoo_model import load

        bundle = load(path)
        bundle["kind"] = "zoo"
        return bundle
    model = json.loads(path.read_text())
    if model.get("features") != FEATURES:
        raise SystemExit("model.json was trained on different features; re-run the intraday backtest.")
    model["kind"] = "ridge"
    return model


def _fetch(data: AlpacaBars, symbols, timeframe, start, end, feed) -> dict[str, pd.DataFrame]:
    old = data.feed
    data.feed = feed
    try:
        out = {}
        for i in range(0, len(symbols), 200):
            got = data.bars(symbols[i:i + 200], timeframe, start.isoformat(), end.isoformat())
            out.update({s: bars_to_frame(rows) for s, rows in got.items() if rows})
        return out
    finally:
        data.feed = old


class LiveState:
    """History-based baselines, fetched once per run."""

    def __init__(self, data: AlpacaBars, tickers: list[str], icfg, today: pd.Timestamp):
        self.tickers = tickers
        start = (today - pd.Timedelta(days=int(icfg.vol_days * 1.6) + 10)).tz_localize(NY)
        midnight = today.tz_localize(NY)
        # same feed as today's bars, so volume baselines are comparable
        self.hist_frames = _fetch(data, tickers, f"{icfg.bar_minutes}Min", start, midnight, icfg.feed)
        # liquidity for the cost model from the consolidated daily tape (allowed when >15 min old)
        daily = _fetch(data, tickers, "1Day", start, midnight, "sip")
        dv = {t: float((f["close"] * f["volume"]).tail(icfg.vol_days).median()) for t, f in daily.items()
              if len(f)}
        self.adv = np.array([dv.get(t, np.nan) for t in tickers])
        LOG.info("history: %d/%d symbols with %s bars, %d with daily volume", len(self.hist_frames),
                 len(tickers), icfg.feed.upper(), len(dv))


def decide(state: LiveState, today_frames: dict[str, pd.DataFrame], model: dict, icfg,
           today: pd.Timestamp):
    """Forecast for every completed bar of today: (B x N predictions, bars, sigma)."""
    frames = {}
    for t in state.tickers:
        parts = [f for f in (state.hist_frames.get(t), today_frames.get(t)) if f is not None and len(f)]
        if parts:
            frames[t] = pd.concat(parts)
    frames = {t: frames.get(t, pd.DataFrame(columns=["open", "close", "volume", "vwap"],
                                            index=pd.DatetimeIndex([], tz=NY))) for t in state.tickers}
    bars = from_frames(frames, icfg.bar_minutes)
    d = bars.days.get_loc(today) if today in bars.days else None
    if d is None:
        return None, None, None
    hist = history(bars, icfg.vol_days)
    if model["kind"] == "zoo":
        from .zoo_model import day_signals, predict_day, tod_grid

        X = day_signals(bars, hist, d)
        pred = predict_day(model["model"], X, tod_grid(*X.shape[:2]))
    else:
        X = day_features(bars.open[d], bars.close[d], bars.volume[d], bars.vwap[d], hist.prev_close[d],
                         hist.sigma[d], hist.vol_base[d])
        pred = np.einsum("bnf,f->bn", np.nan_to_num(X), np.asarray(model["coef"]))
    pred[~np.isfinite(X[..., 0])] = np.nan
    return pred, bars.close[d], hist.sigma[d]


def last_completed_bar(now: pd.Timestamp, bar_minutes: int) -> int:
    mins = (now.hour * 60 + now.minute) - (9 * 60 + 30)
    return mins // bar_minutes - 1


def run_intraday_paper(cfg, model_path: str | Path, dry_run: bool = True, minutes: float | None = None,
                       out_dir: str | Path = "logs") -> dict:
    icfg = cfg.intraday
    model = load_model(model_path)
    tickers = model["tickers"]
    if model["kind"] == "zoo":
        # sizing uses the zoo's out-of-sample IC; the no-trade band uses the model's horizon
        ic = max(float(model.get("ic") or 0.02), 0.005)
        icfg.horizon_bars = int(min(model["horizon"], 24))
        LOG.info("intraday zoo model %s, horizon %d bars, trained through %s, IC %.4f",
                 model["model_name"], model["horizon"], model["trained_through"], ic)
    else:
        ic = max(0.5 * float(model.get("ic_in_sample", 0.02)), 0.005)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_end = time.time() + minutes * 60 if minutes else None

    client = _client()
    if client is None and not dry_run:
        raise SystemExit("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to place paper orders.")
    data = AlpacaBars(feed=icfg.feed)
    clock = client.get_clock() if client else None
    now = pd.Timestamp.now(tz=NY)
    if clock is not None and not clock.is_open:
        if not dry_run:
            LOG.info("market is closed (next open %s) - nothing to do", clock.next_open)
            return {"status": "closed"}
        LOG.info("market is closed: dry run on the most recent session instead")
    today = now.tz_localize(None).normalize()
    close_time = pd.Timestamp(clock.next_close).tz_convert(NY) if clock is not None and clock.is_open \
        else now.normalize() + pd.Timedelta(hours=16)
    session_bars = int(((close_time.hour * 60 + close_time.minute) - (9 * 60 + 30)) // icfg.bar_minutes)
    flat_bar = min(icfg.flat_bar, session_bars - 15 // icfg.bar_minutes - 1)
    live = clock is not None and clock.is_open

    if not live:   # dry run outside market hours: replay the last full session
        probe = _fetch(data, tickers[:5], "1Day", now - pd.Timedelta(days=10), now - pd.Timedelta(minutes=20), "sip")
        last = max(f.index.max() for f in probe.values())
        today = last.tz_convert(NY).tz_localize(None).normalize()
    state = LiveState(data, tickers, icfg, today)
    log_rows, result = [], {"status": "done"}
    done_bars: set[int] = set()

    while True:
        now = pd.Timestamp.now(tz=NY)
        b = last_completed_bar(now, icfg.bar_minutes) if live else flat_bar - 1
        if live and now >= close_time - pd.Timedelta(minutes=2):
            break
        if t_end and time.time() > t_end and live:
            result["status"] = "continue"
            LOG.info("time budget used - a follow-up run should continue the session")
            break
        if b in done_bars or b < 0:
            nxt = now.normalize() + pd.Timedelta(minutes=9 * 60 + 30 + (b + 2) * icfg.bar_minutes, seconds=20)
            time.sleep(max(5.0, min(60.0, (nxt - now).total_seconds())))
            continue
        done_bars.add(b)
        try:
            row = _cycle(client, data, state, model, icfg, today, b, flat_bar, ic, cfg, dry_run, live)
            log_rows.append(row)
            pd.DataFrame(log_rows).to_csv(out_dir / f"intraday_{today.date()}.csv", index=False)
        except Exception as exc:          # keep trading through one bad cycle
            LOG.warning("cycle for bar %d failed: %s", b, exc)
        if not live:
            break
    if live and not dry_run and result["status"] == "done":
        client.close_all_positions(cancel_orders=True)    # belt and braces: never hold overnight
    result["cycles"] = log_rows
    return result


def _cycle(client, data, state, model, icfg, today, b, flat_bar, ic, cfg, dry_run, live) -> dict:
    when = pd.Timestamp.now(tz=NY)
    if b + 1 > flat_bar:
        if live and not dry_run:
            client.close_all_positions(cancel_orders=True)
        LOG.info("bar %d: going flat for the close", b)
        return {"time": str(when), "bar": b, "action": "flatten"}
    if b < icfg.start_bar or (b - icfg.start_bar) % icfg.rebalance_every:
        return {"time": str(when), "bar": b, "action": "hold"}
    start = today.tz_localize(NY) + pd.Timedelta(hours=9, minutes=30)
    end = min(pd.Timestamp.now(tz=NY), start + pd.Timedelta(hours=6, minutes=30))
    today_frames = _fetch(data, state.tickers, f"{icfg.bar_minutes}Min", start, end, icfg.feed)
    pred, close, sigma = decide(state, today_frames, model, icfg, today)
    if pred is None:
        return {"time": str(when), "bar": b, "action": "no data"}
    if client is not None:
        equity, pos_qty, pos_val, shortable, tradable, _ = _account_state(client)
    else:
        equity, pos_qty, pos_val, shortable, tradable = 100_000.0, {}, {}, None, None
    deploy = equity * cfg.live.capital_fraction
    deploy = min(deploy, cfg.live.max_capital or icfg.aum)
    tk = state.tickers
    score = pred[b].copy()
    if tradable is not None:
        score[~np.array([t in tradable for t in tk])] = np.nan
    if shortable is not None:      # unshortable names may only be bought
        mu = np.nanmean(score)
        score[np.array([t not in shortable for t in tk]) & (score < mu)] = np.nan
    w_cur = np.array([pos_val.get(t, 0.0) / deploy for t in tk])
    w = target_weights(score, sigma, state.adv, w_cur, icfg, ic)
    prices = {t: float(p) for t, p in zip(tk, pd.DataFrame(close).ffill().iloc[b]) if np.isfinite(p)}
    tw = {t: float(x) for t, x in zip(tk, w) if abs(x) > 1e-6}
    # positions outside the model's universe are not ours to manage, except at the close
    pos = {t: q for t, q in pos_qty.items() if t in set(tk)}
    orders, _ = plan_orders(tw, prices, deploy, pos, shortable, icfg.min_order_value)
    LOG.info("bar %d (%s): %d long, %d short, gross %.2fx -> %d orders", b, when.strftime("%H:%M"),
             sum(v > 0 for v in tw.values()), sum(v < 0 for v in tw.values()),
             sum(abs(v) for v in tw.values()), len(orders))
    if orders and live and not dry_run:
        _submit(client, orders, "market")
    elif dry_run and orders:
        LOG.info("dry run - first orders:\n%s",
                 pd.DataFrame([o.__dict__ for o in orders]).head(10).to_string(index=False))
    return {"time": str(when), "bar": b, "action": "trade", "orders": len(orders),
            "long": sum(v > 0 for v in tw.values()), "short": sum(v < 0 for v in tw.values()),
            "gross": sum(abs(v) for v in tw.values()), "equity": equity}
