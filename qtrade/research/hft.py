"""High-frequency trading on tick data: what predicts the next seconds, and can it pay?

Alpaca's consolidated (SIP) quotes and trades, tick by tick, for liquid stocks on
sampled days and windows. On a one-second grid:

  quote_imbalance   (bid size - ask size) / (bid size + ask size)
  microprice        size-weighted price vs the midquote (bp)
  ofi_1s / ofi_5s   order-flow imbalance (Cont, Kukanov and Stoikov 2014): the net change
                    of size at the best bid minus the best ask, over 1 / 5 seconds,
                    relative to the window's average depth
  flow_1s/5s/30s    signed trade volume (trade above the mid = buy), relative to the
                    window's average volume per second
  ret_1s/5s/30s     the midquote's last move (momentum or reversal)
  spread_bp         the quoted spread

against the midquote's move over the next 1, 5, 30 and 60 seconds. The first half of
the sampled days fits a linear model; the second half tests it. Then two ways to trade:

* **taker** - cross the spread when the predicted move beats the half-spread, get out
  h seconds later crossing it again (non-overlapping trades);
* **maker** - rest at the best bid and ask; a fill happens when a trade prints through
  the quote (pessimistic: strictly through, so the queue ahead must be gone) or at it
  (optimistic: as if first in the queue); P&L = the spread earned minus the adverse
  move of the midquote 30 s after the fill. With the signal, only quote the side it
  favours. A 0.2 bp maker rebate (direct exchange membership) shown separately.

What this cannot capture: queue position, latency (a colocated firm sees and acts in
microseconds; Alpaca's API is ~100 ms+ away and the paper simulator fills at will) and
hidden liquidity. It measures whether the signals exist and how large they are against
the spread, not a live strategy.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

QUOTES_URL = "https://data.alpaca.markets/v2/stocks/quotes"
TRADES_URL = "https://data.alpaca.markets/v2/stocks/trades"
NY = "America/New_York"
SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "META", "AMD", "JPM", "XOM", "BAC"]
WINDOWS = ["10:00", "12:30", "15:15"]            # 15-minute windows (avoid the open and the close auction)
WINDOW_MIN = 15
HORIZONS = [1, 5, 30, 60]
FEATURES = ["quote_imbalance", "microprice", "ofi_1s", "ofi_5s", "flow_1s", "flow_5s", "flow_30s",
            "ret_1s", "ret_5s", "ret_30s", "spread_bp"]
MAKER_REBATE_BP = 0.2


def _ticks(client, url: str, key: str, symbol: str, start: pd.Timestamp, end: pd.Timestamp,
           max_pages: int = 60) -> list[dict]:
    params = {"symbols": symbol, "start": start.isoformat(), "end": end.isoformat(), "limit": 10000,
              "feed": "sip", "sort": "asc"}
    out = []
    for _ in range(max_pages):
        data = client._get(params, url)
        out += (data.get(key) or {}).get(symbol, [])
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return out


def quotes_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["bid", "ask", "bsize", "asize"])
    q = pd.DataFrame(rows)
    df = pd.DataFrame({"bid": q["bp"].astype(float), "ask": q["ap"].astype(float),
                       "bsize": q["bs"].astype(float), "asize": q["as"].astype(float)},
                      index=pd.to_datetime(q["t"], utc=True, format="ISO8601"))
    df = df[(df["bid"] > 0) & (df["ask"] > df["bid"]) & (df["bsize"] > 0) & (df["asize"] > 0)]
    return df.sort_index()


def trades_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["price", "size"])
    t = pd.DataFrame(rows)
    df = pd.DataFrame({"price": t["p"].astype(float), "size": t["s"].astype(float)},
                      index=pd.to_datetime(t["t"], utc=True, format="ISO8601"))
    return df[(df["price"] > 0) & (df["size"] > 0)].sort_index()


def ofi_events(q: pd.DataFrame) -> pd.Series:
    """Order-flow imbalance contribution of each quote update (Cont, Kukanov and Stoikov)."""
    b, a, bs, as_ = q["bid"], q["ask"], q["bsize"], q["asize"]
    pb, pa, pbs, pas = b.shift(1), a.shift(1), bs.shift(1), as_.shift(1)
    e = (np.where(b >= pb, bs, 0) - np.where(b <= pb, pbs, 0)
         - np.where(a <= pa, as_, 0) + np.where(a >= pa, pas, 0))
    return pd.Series(np.nan_to_num(e), index=q.index)


def window_features(q: pd.DataFrame, t: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """One row per second: features known at that second and the midquote's future moves."""
    grid = pd.date_range(start, end, freq="1s", tz="UTC")
    if len(q) < 50:
        return pd.DataFrame()
    last = q.groupby(level=0).last()
    g = last.reindex(last.index.union(grid)).ffill().reindex(grid)
    mid = (g["bid"] + g["ask"]) / 2
    out = pd.DataFrame(index=grid)
    out["mid"] = mid
    out["bid"], out["ask"] = g["bid"], g["ask"]
    out["spread_bp"] = (g["ask"] - g["bid"]) / mid * 1e4
    out["quote_imbalance"] = (g["bsize"] - g["asize"]) / (g["bsize"] + g["asize"])
    micro = (g["bid"] * g["asize"] + g["ask"] * g["bsize"]) / (g["bsize"] + g["asize"])
    out["microprice"] = (micro / mid - 1) * 1e4
    depth = float((q["bsize"] + q["asize"]).mean() / 2)
    cum_ofi = ofi_events(q).cumsum().groupby(level=0).last()
    cum_ofi = cum_ofi.reindex(cum_ofi.index.union(grid)).ffill().reindex(grid).fillna(0)
    for k in (1, 5):
        out[f"ofi_{k}s"] = cum_ofi.diff(k) / max(depth, 1e-9)
    if len(t):
        tt = t.copy()
        mq = ((last["bid"] + last["ask"]) / 2).rename("m")
        tt["m"] = mq.reindex(mq.index.union(tt.index)).ffill().reindex(tt.index).to_numpy()
        signed = np.sign(tt["price"] - tt["m"]).fillna(0) * tt["size"]
        cum = signed.cumsum().groupby(level=0).last()
        cum = cum.reindex(cum.index.union(grid)).ffill().reindex(grid).fillna(0)
        vol_per_s = float(t["size"].sum() / max((end - start).total_seconds(), 1))
        for k in (1, 5, 30):
            out[f"flow_{k}s"] = cum.diff(k) / max(vol_per_s * k, 1e-9)
    else:
        for k in (1, 5, 30):
            out[f"flow_{k}s"] = np.nan
    lm = np.log(mid)
    for k in (1, 5, 30):
        out[f"ret_{k}s"] = (lm - lm.shift(k)) * 1e4
    for h in HORIZONS:
        out[f"fwd_{h}s"] = (lm.shift(-h) - lm) * 1e4
    return out.iloc[30:]                           # need 30 s of history


def maker_fills(q_grid: pd.DataFrame, t: pd.DataFrame, step: int = 10, wait: int = 10, hold: int = 30,
                strict: bool = True) -> pd.DataFrame:
    """Rest one unit at the best bid and ask every ``step`` seconds for ``wait`` seconds. A bid fills when a
    trade prints below it (strict) or at/below it; P&L marked at the mid ``hold`` s after the fill (bp)."""
    rows = []
    if t.empty or q_grid.empty:
        return pd.DataFrame()
    px = t["price"]
    mids = q_grid["mid"]
    for ts in q_grid.index[::step]:
        bid, ask = q_grid.at[ts, "bid"], q_grid.at[ts, "ask"]
        if not (np.isfinite(bid) and np.isfinite(ask)):
            continue
        w = px[(px.index > ts) & (px.index <= ts + pd.Timedelta(seconds=wait))]
        if w.empty:
            continue
        for side, hit in (("bid", w[(w < bid) if strict else (w <= bid)]),
                          ("ask", w[(w > ask) if strict else (w >= ask)])):
            if hit.empty:
                continue
            ft = hit.index[0]
            later = mids[mids.index >= ft + pd.Timedelta(seconds=hold)]
            if later.empty:
                continue
            m_after = float(later.iloc[0])
            price = bid if side == "bid" else ask
            pnl = (m_after / price - 1) * 1e4 if side == "bid" else (price / m_after - 1) * 1e4
            m_at = (bid + ask) / 2
            rows.append({"time": ts, "side": side, "pnl_bp": pnl,
                         "half_spread_bp": abs(m_at / price - 1) * 1e4})
    return pd.DataFrame(rows)


def taker_trades(df: pd.DataFrame, pred: pd.Series, h: int, edge_bp: float = 0.0) -> pd.DataFrame:
    """Cross the spread when |prediction| > half-spread + ``edge_bp``; exit h s later crossing again."""
    rows = []
    for _, g in df.groupby(["symbol", "day", "window"]):
        p = pred.loc[g.index]
        i = 0
        idx = g.index
        while i < len(idx):
            r = g.loc[idx[i]]
            hs = r["spread_bp"] / 2
            if np.isfinite(p.iloc[i]) and abs(p.iloc[i]) > hs + edge_bp and np.isfinite(r[f"fwd_{h}s"]):
                j = min(i + h, len(idx) - 1)
                hs_exit = g.loc[idx[j], "spread_bp"] / 2
                d = np.sign(p.iloc[i])
                rows.append({"gross_bp": d * r[f"fwd_{h}s"], "cost_bp": hs + hs_exit,
                             "net_bp": d * r[f"fwd_{h}s"] - hs - hs_exit})
                i += h
            else:
                i += 1
    return pd.DataFrame(rows)


def sample_days(n: int, end: pd.Timestamp | None = None, seed: int = 0) -> list[pd.Timestamp]:
    end = end or pd.Timestamp.today().normalize() - pd.Timedelta(days=3)
    days = pd.bdate_range(end - pd.Timedelta(days=730), end)
    rng = np.random.default_rng(seed)
    return sorted(pd.DatetimeIndex(rng.choice(days, size=min(n, len(days)), replace=False)))


def collect(symbols: list[str], days: list[pd.Timestamp]) -> pd.DataFrame:
    from ..data.intraday import AlpacaBars

    client = AlpacaBars(feed="sip")
    frames, maker = [], []
    for day in days:
        for w in WINDOWS:
            start = pd.Timestamp(f"{day.date()} {w}", tz=NY).tz_convert("UTC")
            end = start + pd.Timedelta(minutes=WINDOW_MIN)
            for sym in symbols:
                try:
                    q = quotes_frame(_ticks(client, QUOTES_URL, "quotes", sym, start, end))
                    t = trades_frame(_ticks(client, TRADES_URL, "trades", sym, start, end))
                except Exception as exc:
                    LOG.warning("ticks %s %s %s: %s", sym, day.date(), w, exc)
                    continue
                f = window_features(q, t, start, end)
                if f.empty:
                    continue
                f = f.assign(symbol=sym, day=day, window=w)
                frames.append(f)
                for strict in (True, False):
                    m = maker_fills(f, t, strict=strict)
                    if len(m):
                        maker.append(m.assign(symbol=sym, day=day, window=w, strict=strict))
        LOG.info("hft: %s collected (%d windows so far)", day.date(), len(frames))
    feats = pd.concat(frames).reset_index(names="time") if frames else pd.DataFrame()
    mk = pd.concat(maker, ignore_index=True) if maker else pd.DataFrame()
    return feats, mk


def analyse(feats: pd.DataFrame, mk: pd.DataFrame) -> dict[str, pd.DataFrame]:
    days = sorted(feats["day"].unique())
    train_days = set(days[: len(days) // 2])
    tr = feats["day"].isin(train_days)
    # 1. rank correlation of each feature with each future move (test days)
    ic_rows = []
    for f in FEATURES:
        for h in HORIZONS:
            row = {"feature": f, "horizon_s": h}
            for tag, m in (("train", tr), ("test", ~tr)):
                x, y = feats.loc[m, f], feats.loc[m, f"fwd_{h}s"]
                ok = x.notna() & y.notna()
                row[f"ic_{tag}"] = float(x[ok].rank().corr(y[ok].rank())) if ok.sum() > 100 else np.nan
                row[f"n_{tag}"] = int(ok.sum())
            ic_rows.append(row)
    ic = pd.DataFrame(ic_rows)
    # 2. linear model per horizon, fitted on the train days, judged on the test days
    X = feats[FEATURES].fillna(0.0).clip(-50, 50)
    model_rows, taker_rows = [], []
    for h in HORIZONS:
        y = feats[f"fwd_{h}s"]
        ok = y.notna()
        A = np.c_[np.ones(int((ok & tr).sum())), X[ok & tr].to_numpy()]
        beta, *_ = np.linalg.lstsq(A, y[ok & tr].to_numpy(), rcond=None)
        pred = pd.Series(np.c_[np.ones(len(X)), X.to_numpy()] @ beta, index=feats.index)
        te = ok & ~tr
        r2 = 1 - ((y[te] - pred[te]) ** 2).sum() / ((y[te] - y[te].mean()) ** 2).sum()
        corr = float(np.corrcoef(pred[te], y[te])[0, 1])
        model_rows.append({"horizon_s": h, "test_r2": float(r2), "test_corr": corr,
                           "pred_sd_bp": float(pred[te].std()), "move_sd_bp": float(y[te].std()),
                           "median_half_spread_bp": float(feats.loc[te, "spread_bp"].median() / 2)})
        test = feats[~tr]
        for edge in (0.0, 0.5, 1.0):
            tt = taker_trades(test, pred[~tr], h, edge)
            taker_rows.append({"horizon_s": h, "extra_edge_bp": edge, "trades": len(tt),
                               "gross_bp": float(tt["gross_bp"].mean()) if len(tt) else np.nan,
                               "cost_bp": float(tt["cost_bp"].mean()) if len(tt) else np.nan,
                               "net_bp": float(tt["net_bp"].mean()) if len(tt) else np.nan,
                               "hit_rate": float((tt["net_bp"] > 0).mean()) if len(tt) else np.nan})
        model_rows[-1]["beta"] = [float(v) for v in beta]
        if h == 30:
            feats = feats.assign(pred30=pred)
    # 3. market making: spread earned minus adverse selection, with and without the 30 s signal
    mm_rows = []
    if len(mk):
        p30 = feats.set_index(["symbol", "day", "window", "time"])["pred30"]
        key = pd.MultiIndex.from_frame(mk[["symbol", "day", "window", "time"]])
        mk = mk.assign(pred=p30.reindex(key).to_numpy())
        for strict, g in mk.groupby("strict"):
            for label, sel in (("both sides", np.ones(len(g), bool)),
                               ("signal side only", ((g["side"] == "bid") & (g["pred"] > 0))
                                | ((g["side"] == "ask") & (g["pred"] < 0)))):
                gg = g[sel]
                mm_rows.append({"fill_rule": "trade through the quote (pessimistic)" if strict
                                else "trade at the quote (optimistic)", "quotes": label, "fills": len(gg),
                                "spread_earned_bp": float(gg["half_spread_bp"].mean()) if len(gg) else np.nan,
                                "pnl_bp_per_fill": float(gg["pnl_bp"].mean()) if len(gg) else np.nan,
                                "with_rebate_bp": float(gg["pnl_bp"].mean() + MAKER_REBATE_BP) if len(gg) else np.nan})
    return {"ic": ic, "model": pd.DataFrame(model_rows), "taker": pd.DataFrame(taker_rows),
            "maker": pd.DataFrame(mm_rows)}


def run(md, ctx, out: Path, cfg) -> dict:
    n_days = int(os.environ.get("HFT_DAYS", "10"))
    symbols = os.environ.get("HFT_SYMBOLS", ",".join(SYMBOLS)).split(",")
    feats, mk = collect(symbols, sample_days(n_days))
    if feats.empty:
        (out / "hft.md").write_text("## High-frequency (tick) study\n\n(no tick data)\n")
        return {"error": "no ticks"}
    res = analyse(feats, mk)
    import json

    for k, v in res.items():
        v.drop(columns=["beta"], errors="ignore").to_csv(out / f"hft_{k}.csv", index=False)
    coefs = {"features": FEATURES, "horizons": {str(r["horizon_s"]): r["beta"] for _, r in res["model"].iterrows()},
             "fitted_on_days": sorted(str(d.date()) for d in feats["day"].unique())[: feats["day"].nunique() // 2]}
    (out / "hft_model.json").write_text(json.dumps(coefs, indent=1))
    ic = res["ic"].sort_values("ic_test", key=lambda s: -s.abs())
    lines = ["## High-frequency trading on tick data", "",
             f"{len(symbols)} liquid stocks, {feats['day'].nunique()} sampled days in the last two years, "
             f"windows {', '.join(WINDOWS)} New York ({WINDOW_MIN} min each), consolidated quotes and trades on a "
             "one-second grid. First half of the days fits, second half tests.", "",
             "### What predicts the next seconds (rank correlation, test days)", "",
             ic.head(20).round(4).to_markdown(index=False), "",
             "### Linear model of all the features (test days)", "",
             res["model"].drop(columns=["beta"]).round(3).to_markdown(index=False), "",
             "### Taking liquidity: cross the spread when the forecast beats it", "",
             res["taker"].round(3).to_markdown(index=False), "",
             "### Making markets: earn the spread, lose to adverse selection", "",
             res["maker"].round(3).to_markdown(index=False), "",
             "Not modelled: queue position, latency (a colocated firm acts in microseconds; Alpaca's API is "
             "~100 ms+ away and its paper simulator fills at will) and hidden liquidity.", ""]
    (out / "hft.md").write_text("\n".join(lines) + "\n")
    return {"rows": int(len(feats)), "model": res["model"].drop(columns=["beta"]).round(3).to_dict(orient="records"),
            "maker": res["maker"].round(3).to_dict(orient="records")}
