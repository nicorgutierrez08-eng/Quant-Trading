"""Paper trading on Alpaca, using exactly the backtest's decision logic.

Daily cycle (meant to run before the US open, e.g. ~8:45am New York time):

1. Load the universe and refresh prices through the last completed session.
2. Rebuild the research pipeline with a final walk-forward refit on the
   latest data, so the newest model makes today's forecast.
3. Ask the same ``Decider`` the backtest uses for target weights, starting
   from the account's real positions.
4. Remove shorts in names Alpaca cannot borrow, convert weights to whole
   shares, and diff against current holdings.
5. Cancel stale open orders and submit market-on-open (OPG) orders - or
   regular market orders if the session is already open.

Safety: the client is hard-wired to Alpaca's *paper* endpoint. ``dry_run``
(the default) prints the plan without sending anything.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data import get_market_data, load_universe, to_alpaca, to_yahoo
from ..data.loader import last_completed_session
from ..pipeline import build_research
from ..portfolio.decider import Decider
from ..utils import LOG


@dataclass
class PlannedOrder:
    symbol: str
    side: str        # "buy" | "sell"
    qty: int
    price: float
    reason: str

    @property
    def notional(self) -> float:
        return self.qty * self.price


def plan_orders(
    target_weights: dict[str, float],
    prices: dict[str, float],
    equity: float,
    positions: dict[str, int],
    shortable: set[str] | None = None,
    min_order_value: float = 50.0,
) -> tuple[list[PlannedOrder], dict[str, int]]:
    """Convert target weights to whole-share orders (pure function, unit tested).

    * shorts are dropped for names not in ``shortable`` (when given);
    * a position that would flip from long to short (or back) is only closed
      today - brokers reject single orders that cross zero - and the new side
      is opened on the next run;
    * orders smaller than ``min_order_value`` are skipped.
    """
    targets: dict[str, int] = {}
    for sym, w in target_weights.items():
        px = prices.get(sym)
        if px is None or not np.isfinite(px) or px <= 0:
            continue
        if w < 0 and shortable is not None and sym not in shortable:
            continue
        shares = int(math.trunc(w * equity / px))
        if shares != 0:
            targets[sym] = shares

    orders: list[PlannedOrder] = []
    for sym in sorted(set(targets) | set(positions)):
        cur = int(positions.get(sym, 0))
        tgt = int(targets.get(sym, 0))
        px = prices.get(sym, np.nan)
        if not np.isfinite(px):
            if cur != 0 and sym not in target_weights:
                orders.append(PlannedOrder(sym, "sell" if cur > 0 else "buy", abs(cur), float("nan"), "exit (no price)"))
            continue
        if cur != 0 and tgt != 0 and np.sign(cur) != np.sign(tgt):
            tgt, reason = 0, "close before flip"
        elif tgt == 0:
            reason = "exit"
        elif cur == 0:
            reason = "open"
        else:
            reason = "resize"
        delta = tgt - cur
        if delta == 0:
            continue
        if abs(delta) * px < min_order_value and tgt != 0:
            continue
        orders.append(PlannedOrder(sym, "buy" if delta > 0 else "sell", abs(delta), float(px), reason))
    return orders, targets


def _client():
    from alpaca.trading.client import TradingClient

    key = os.environ.get("ALPACA_API_KEY") or os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        return None
    return TradingClient(key, secret, paper=True)  # never a live account


def _account_state(client):
    """(equity, {yahoo_symbol: qty}, {yahoo_symbol: market_value}, shortable set, peak equity)."""
    from alpaca.trading.requests import GetPortfolioHistoryRequest

    acct = client.get_account()
    equity = float(acct.equity)
    pos_qty, pos_val = {}, {}
    # raw JSON for positions and assets: alpaca-py's typed models reject exchange
    # codes it doesn't know yet (e.g. the Texas Stock Exchange, "TXSE")
    for p in client.get("/positions"):
        sym = to_yahoo(p["symbol"])
        pos_qty[sym] = int(float(p["qty"]))
        pos_val[sym] = float(p["market_value"])
    assets = client.get("/assets", {"status": "active", "asset_class": "us_equity"})
    shortable = {to_yahoo(a["symbol"]) for a in assets
                 if a.get("tradable") and a.get("shortable") and a.get("easy_to_borrow")}
    tradable = {to_yahoo(a["symbol"]) for a in assets if a.get("tradable")}
    peak = equity
    try:
        hist = client.get_portfolio_history(GetPortfolioHistoryRequest(period="1A", timeframe="1D"))
        vals = [v for v in (hist.equity or []) if v]
        if vals:
            peak = max(max(vals), equity)
    except Exception as exc:  # history is optional
        LOG.warning("portfolio history unavailable: %s", exc)
    return equity, pos_qty, pos_val, shortable, tradable, peak


def traded_today(client) -> bool:
    """True if the account already has orders submitted since midnight New York time."""
    midnight = pd.Timestamp.now(tz="America/New_York").normalize()
    orders = client.get("/orders", {"status": "all", "after": midnight.isoformat(), "limit": 5})
    return bool(orders)


def run_paper(cfg: Config, dry_run: bool | None = None, out_dir: str | Path | None = None,
              once_per_day: bool = False) -> dict:
    dry_run = cfg.live.dry_run if dry_run is None else dry_run
    out_dir = Path(out_dir or cfg.live.log_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # talk to Alpaca first, so a bad key fails in seconds rather than after the model run
    client = _client()
    if client is None:
        if not dry_run:
            raise SystemExit("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to place paper orders.")
        LOG.info("no Alpaca keys: simulating an empty $100,000 account")
        equity, pos_qty, pos_val, shortable, tradable, peak = 100_000.0, {}, {}, None, None, 100_000.0
    else:
        try:
            equity, pos_qty, pos_val, shortable, tradable, peak = _account_state(client)
        except Exception as exc:
            hint = ""
            if any(code in str(exc) for code in ("401", "403", "unauthorized", "forbidden")):
                hint = (" Check that ALPACA_API_KEY / ALPACA_SECRET_KEY are the PAPER account's keys,"
                        " copied without spaces, and not regenerated since.")
            raise SystemExit(f"Alpaca request failed: {exc}.{hint}") from exc
        LOG.info("Alpaca paper account OK: equity $%.0f, %d open positions, %d shortable names",
                 equity, len(pos_qty), len(shortable))
        if once_per_day and not dry_run and traded_today(client):
            LOG.info("orders were already sent today (earlier scheduled run) - nothing to do")
            return {"skipped": True}

    uni = load_universe(cfg.data.cache_dir)
    if uni is None:
        raise SystemExit("No universe found. Run `python -m qtrade universe` first.")
    tickers = uni["ticker"].tolist()

    # enough history for signal warm-up + walk-forward training + an IC track record
    need_days = cfg.model.min_train + cfg.model.train_window + 2 * 252
    start = (pd.Timestamp.today() - pd.Timedelta(days=int(need_days * 1.5))).strftime("%Y-%m-%d")
    start = max(start, cfg.data.start)
    md = get_market_data(tickers, start, None, cfg.data.cache_dir + "/live", cfg.data.batch_size)
    md = md.subset(end=last_completed_session())   # drop any partial bar for today
    asof = md.dates[-1]
    LOG.info("live data through %s for %d tickers", asof.date(), len(md.tickers))

    trade_model = cfg.model.trade_model
    members = cfg.model.ensemble if trade_model == "ensemble" else [trade_model]
    research = build_research(md, cfg, final_refit=True, models=list(dict.fromkeys(members)))
    pred = research.prediction(trade_model)
    dec = Decider(research.ctx, pred, research.fwd_ret, cfg)

    deploy = equity * cfg.live.capital_fraction
    if cfg.live.max_capital:
        deploy = min(deploy, cfg.live.max_capital)

    # ETF sleeves next to the stock book: each gets its share of the deployed capital
    etf_w, etf_px = {}, {}
    stock_deploy = deploy
    if cfg.multi.enabled:
        from ..portfolio.sleeves import etf_targets

        etf_w, etf_px, etf_asof, sw = etf_targets(cfg, end=last_completed_session())
        if etf_asof != asof:
            LOG.warning("ETF data ends %s but stock data ends %s", etf_asof.date(), asof.date())
        if tradable is not None:
            etf_w = {k: v for k, v in etf_w.items() if k in tradable}
        stock_deploy = deploy * (1 - cfg.multi.etf_fraction)
        LOG.info("ETF sleeves (%.0f%% of capital): %s | sleeve weights %s", 100 * cfg.multi.etf_fraction,
                 ", ".join(f"{k} {v:+.2f}" for k, v in sorted(etf_w.items(), key=lambda x: -abs(x[1]))),
                 sw.iloc[-1].round(2).to_dict())

    cols = md.tickers
    w_cur = (np.array([pos_val.get(t, 0.0) / stock_deploy for t in cols]) if stock_deploy > 0
             else np.zeros(len(cols)))
    allowed = None if tradable is None else np.array([t in tradable for t in cols])
    no_short = None if shortable is None else np.array([t not in shortable for t in cols])
    dd = equity / peak - 1 if peak > 0 else 0.0
    risk_scale = cfg.portfolio.drawdown_scale if dd < -cfg.portfolio.drawdown_limit else 1.0
    t = len(md.dates) - 1
    d = dec.decide(t, w_cur, stock_deploy, risk_scale, allowed=allowed, no_short=no_short)

    prices = {tk: float(px) for tk, px in md.traded_close.iloc[-1].items() if np.isfinite(px)}
    # weights below are fractions of the whole deployed capital
    share = stock_deploy / deploy if deploy > 0 else 0.0
    tw = {tk: float(w) * share for tk, w in zip(cols, d.weights) if abs(w) > 1e-6}
    for tk, w in etf_w.items():
        tw[tk] = tw.get(tk, 0.0) + w * cfg.multi.etf_fraction * risk_scale
        prices.setdefault(tk, etf_px.get(tk, np.nan))
    orders, targets = plan_orders(tw, prices, deploy, pos_qty, shortable, cfg.live.min_order_value)

    stamp = pd.Timestamp.now(tz="America/New_York").strftime("%Y%m%d_%H%M")
    pd.Series(tw, name="weight").sort_values().to_csv(out_dir / f"targets_{stamp}.csv")
    plan = pd.DataFrame([o.__dict__ | {"notional": o.notional} for o in orders])
    plan.to_csv(out_dir / f"orders_{stamp}.csv", index=False)
    LOG.info("as of %s | equity $%.0f | IC estimate %.4f | holding ~%.1f periods | sizing bound by %s",
             asof.date(), equity, d.ic_hat, d.holding_periods, d.info.binding)
    LOG.info("target: %d long, %d short, gross %.2fx, predicted vol %.1f%%",
             sum(v > 0 for v in tw.values()), sum(v < 0 for v in tw.values()), d.info.gross,
             d.info.predicted_vol * 100)
    LOG.info("%d orders, $%.0f to trade", len(orders), float(np.nansum([o.notional for o in orders])))

    submitted = []
    if not dry_run and client is not None and orders:
        submitted = _submit(client, orders, cfg.live.order_type)
    elif dry_run:
        LOG.info("dry run - nothing sent. First orders:\n%s", plan.head(15).to_string(index=False) if len(plan) else "(none)")
    return {"asof": str(asof.date()), "equity": equity, "orders": plan, "targets": tw,
            "submitted": submitted, "ic_hat": d.ic_hat, "gross": d.info.gross}


def _submit(client, orders: list[PlannedOrder], order_type: str) -> list[str]:
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    clock = client.get_clock()
    if order_type == "auto":
        order_type = "market" if clock.is_open else "opg"
    tif = TimeInForce.OPG if order_type == "opg" else TimeInForce.DAY
    client.cancel_orders()  # clear anything left from a previous run
    ids = []
    # sells first so buying power is freed before buys
    for o in sorted(orders, key=lambda o: o.side != "sell"):
        try:
            r = client.submit_order(MarketOrderRequest(
                symbol=to_alpaca(o.symbol), qty=o.qty,
                side=OrderSide.BUY if o.side == "buy" else OrderSide.SELL, time_in_force=tif,
            ))
            ids.append(str(r.id))
        except Exception as exc:  # one bad symbol should not stop the batch
            LOG.warning("order %s %d %s rejected: %s", o.side, o.qty, o.symbol, exc)
    LOG.info("submitted %d/%d %s orders", len(ids), len(orders), order_type.upper())
    return ids
