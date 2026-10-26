"""Intraday strategies with an edge, traded through IBKR Lite or IBKR Pro.

Four strategies from the intraday strategy study (``qtrade.research.intraday_strats``)
earned money before costs in both 2016-2020 and 2021-2026. Each trades one
slice of the day, so it needs only two orders per stock per day:

  gap_reversal          short stocks that gapped up, buy those that gapped down,
                        9:35 -> close (marketable order in, market-on-close out)
  opening_fade          against the 9:30-10:00 move, 10:00 -> close
                        (marketable order in, market-on-close out)
  overnight_persistence past month's overnight return, close -> next open
                        (market-on-close in, market-on-open out)
  last30_fade           against the 15:15-15:45 move, close -> next open

Every signal uses only prices printed before its order is sent. (The research
version of the gap trade entered at the official open, which already defines
the gap, so it overstated the edge.)

The direction of each comes from 2016-2020 only. Books are long the top fifth
and short the bottom fifth (equal weight, whole shares, gross ``gross`` x
capital), and the blend gives each strategy an equal share of the capital.

Costs: auction orders (market-on-open / market-on-close) fill at the auction
price, so they pay ``auction_slippage_bp`` but no spread; the 10:00 entry pays
the half-spread by liquidity tier plus slippage. Fees per order follow IBKR
Lite (no commission, no exchange or clearing fees, regulatory fees on sales)
or IBKR Pro Tiered (``ibkr_sim.IBKR``).

    python -m qtrade.intraday.slice_sim --store data/intraday/5min --symbols 500
    python -m qtrade.intraday.slice_sim --synthetic
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG
from .bars import DayBars
from .features import _ffill_bars, history
from .ibkr_sim import IBKR, order_fees

SPLIT = "2021-01-01"
IBKR_LITE = dict(IBKR, commission_per_share=0.0, commission_min=0.0, exchange_fee_per_share=0.0,
                 clearing_fee_per_share=0.0, finra_passthrough_pct=0.0)
PLANS = {"IBKR Lite": IBKR_LITE, "IBKR Pro Tiered": IBKR}
HALF_SPREAD_TIERS = [(1e9, 1.0), (2e8, 2.0), (5e7, 4.0), (0.0, 8.0)]   # bp, as in the intraday config
STRATEGIES = ["gap_reversal", "opening_fade", "overnight_persistence", "last30_fade"]


def _half_spread(adv: np.ndarray) -> np.ndarray:
    adv = np.nan_to_num(adv)
    hs = np.full(adv.shape, HALF_SPREAD_TIERS[-1][1])
    for thr, bp in sorted(HALF_SPREAD_TIERS):
        hs = np.where(adv >= thr, bp, hs)
    return hs / 1e4


def _bar_open(bars: DayBars, px: np.ndarray, b: int) -> np.ndarray:
    """Open of bar b (the trade price for an order sent after bar b-1 closed)."""
    return np.where(np.isfinite(bars.open[:, b, :]), bars.open[:, b, :], px[:, b - 1, :])


def day_prices(bars: DayBars):
    """Per day and stock: official open, 9:35, 10:00 and close prices."""
    Q0 = bars.open[:, 0, :]
    px = _ffill_bars(bars.close)
    return Q0, _bar_open(bars, px, 1), _bar_open(bars, px, 6), px[:, -1, :]


def signals(bars: DayBars):
    """Each signal uses only prices printed before its order goes in (D x N, positive = buy,
    before the sign flip):

    * gap: previous close -> today's open, traded at 9:35 (the open defines the gap, so an
      order sent before the open could not know it);
    * first half hour: open -> close of the 9:55 bar, traded at the 10:00 open;
    * last half hour: 15:15 -> 15:45, so a market-on-close order makes the 15:50 cutoff;
    * overnight: the past 21 sessions' close -> open returns, traded at today's close.
    """
    Q0, q935, q10, qc = day_prices(bars)
    px = _ffill_bars(bars.close)
    prev_c = np.vstack([np.full((1, Q0.shape[1]), np.nan), qc[:-1]])
    with np.errstate(invalid="ignore", divide="ignore"):
        gap = Q0 / prev_c - 1
        first30 = px[:, 5, :] / Q0 - 1
        on = np.log(Q0 / prev_c)
    on21 = pd.DataFrame(on).rolling(21, min_periods=15).sum().to_numpy()
    dm = lambda x: x - np.nanmean(x, axis=1, keepdims=True)  # noqa: E731
    return {"gap_reversal": -dm(gap), "opening_fade": -dm(first30),
            "overnight_persistence": dm(on21), "last30_fade": last30_signal(px[:, 68, :], px[:, 74, :])}


def last30_signal(p_1515: np.ndarray, p_1545: np.ndarray) -> np.ndarray:
    """Against the 15:15 -> 15:45 move, relative to the cross-section (last axis = stocks).
    Shared with the live auction trader."""
    with np.errstate(invalid="ignore", divide="ignore"):
        r = p_1545 / p_1515 - 1
    return -(r - np.nanmean(r, axis=-1, keepdims=True))


def overnight_signal(opens: np.ndarray, prev_closes: np.ndarray, min_days: int = 15) -> np.ndarray:
    """Sum of the last 21 sessions' close -> open log returns (rows = sessions, oldest
    first, the last row = today), relative to the cross-section. Shared with the live trader."""
    with np.errstate(invalid="ignore", divide="ignore"):
        lr = np.log(opens[-21:] / prev_closes[-21:])
    s = np.where(np.isfinite(lr).sum(axis=0) >= min_days, np.nansum(lr, axis=0), np.nan)
    return s - np.nanmean(s)


def legs(bars: DayBars):
    """(entry price, exit price, entry is an auction, exit is an auction) per strategy, D x N."""
    Q0, q935, q10, qc = day_prices(bars)
    nxt_open = np.vstack([Q0[1:], np.full((1, Q0.shape[1]), np.nan)])
    return {"gap_reversal": (q935, qc, False, True), "opening_fade": (q10, qc, False, True),
            "overnight_persistence": (qc, nxt_open, True, True), "last30_fade": (qc, nxt_open, True, True)}


def _weights(sig: np.ndarray, ok: np.ndarray, frac: float = 0.2) -> np.ndarray:
    s = np.where(ok, sig, np.nan)
    n = np.isfinite(s).sum()
    w = np.zeros_like(sig)
    if n < 20:
        return w
    k = max(int(n * frac), 1)
    order = np.argsort(np.where(np.isfinite(s), s, np.inf))[:n]
    w[order[-k:]] = 1.0 / k
    w[order[:k]] = -1.0 / k
    return w / 2                                   # gross 1 per unit of capital


def simulate(bars: DayBars, capital: float = 100_000, gross: float = 2.0, auction_slippage_bp: float = 1.0,
             cont_slippage_bp: float = 0.5, trade_log_from: str | None = None):
    """Daily results for each strategy x plan, the blend, the signs used, and a fill ledger (blend, Lite)."""
    hist = history(bars)
    sig = signals(bars)
    lg = legs(bars)
    days = bars.days
    first = np.asarray(days < SPLIT)
    # direction from 2016-2020 gross returns only (frictionless, equal weight)
    signs = {}
    for name in STRATEGIES:
        e, x, *_ = lg[name]
        g = []
        for d in np.flatnonzero(first):
            ok = np.isfinite(e[d]) & np.isfinite(x[d]) & (e[d] > 0) & np.isfinite(hist.adv[d])
            w = _weights(sig[name][d], ok)
            with np.errstate(invalid="ignore", divide="ignore"):
                g.append(np.nansum(w * (x[d] / e[d] - 1)))
        signs[name] = 1.0 if np.nansum(g) >= 0 else -1.0
    rows, fills = [], []
    log_from = pd.Timestamp(trade_log_from) if trade_log_from else None
    tick = np.array(bars.tickers)
    for plan, fees in PLANS.items():
        for name in STRATEGIES + ["blend"]:
            members = STRATEGIES if name == "blend" else [name]
            eq = capital
            for d in range(len(days)):
                start = eq
                pnl = spread = fee = 0.0
                n_orders = 0
                for m in members:
                    e, x, e_auc, x_auc = lg[m]
                    ok = np.isfinite(e[d]) & np.isfinite(x[d]) & (e[d] > 0) & np.isfinite(hist.adv[d])
                    if ok.sum() < 20 or not np.isfinite(sig[m][d]).any():
                        continue
                    w = _weights(signs[m] * sig[m][d], ok) * gross / len(members)
                    with np.errstate(invalid="ignore", divide="ignore"):
                        sh = np.where(ok, np.trunc(w * start / e[d]), 0.0)
                    idx = np.flatnonzero(sh != 0)
                    if len(idx) == 0:
                        continue
                    q, pe, px = sh[idx], e[d][idx], x[d][idx]
                    pnl += float((q * (px - pe)).sum())
                    hs = _half_spread(hist.adv[d][idx])
                    c_in = (auction_slippage_bp / 1e4) if e_auc else hs + cont_slippage_bp / 1e4
                    c_out = (auction_slippage_bp / 1e4) if x_auc else hs + cont_slippage_bp / 1e4
                    spread += float((np.abs(q) * pe * c_in + np.abs(q) * px * c_out).sum())
                    f_in = order_fees(np.abs(q), pe, q < 0, fees)       # opening: shorts sell
                    f_out = order_fees(np.abs(q), px, q > 0, fees)      # closing: longs sell
                    fee += sum(float(f_in[k].sum() + f_out[k].sum()) for k in
                               ("commission", "exchange_fee", "clearing_fee", "finra_passthrough", "sec_fee",
                                "finra_taf"))
                    n_orders += 2 * len(idx)
                    if (name == "blend" and plan == "IBKR Lite" and log_from is not None
                            and days[d] >= log_from):
                        for j, i in enumerate(idx):
                            for leg, p, side in (("open", pe[j], "BUY" if q[j] > 0 else "SELL"),
                                                 ("close", px[j], "SELL" if q[j] > 0 else "BUY")):
                                fills.append({"date": days[d].date(), "strategy": m, "leg": leg,
                                              "ticker": tick[i], "side": side, "shares": int(abs(q[j])),
                                              "price": round(float(p), 4),
                                              "value": round(float(abs(q[j]) * p), 2)})
                net = pnl - spread - fee
                eq = start + net
                rows.append({"plan": plan, "strategy": name, "date": days[d], "start_value": start,
                             "trading_pnl": pnl, "spread_slippage_est": spread, "fees": fee, "net_pnl": net,
                             "end_value": eq, "orders": n_orders})
    return pd.DataFrame(rows), signs, pd.DataFrame(fills)


def summarize(daily: pd.DataFrame, capital: float) -> pd.DataFrame:
    out = []
    for (plan, name), g in daily.groupby(["plan", "strategy"], sort=False):
        r = g["net_pnl"] / g["start_value"]
        row = {"plan": plan, "strategy": name, "ending_value": g["end_value"].iloc[-1],
               "total_return": g["end_value"].iloc[-1] / capital - 1,
               "max_drawdown": (g["end_value"] / g["end_value"].cummax() - 1).min(),
               "trading_pnl": g["trading_pnl"].sum(), "spread_slippage_est": g["spread_slippage_est"].sum(),
               "fees": g["fees"].sum(), "orders_per_day": g["orders"].mean()}
        for tag, m in (("2016_20", g["date"] < SPLIT), ("2021_26", g["date"] >= SPLIT)):
            x = r[m.to_numpy()]
            row[f"sharpe_{tag}"] = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
            row[f"annual_return_{tag}"] = x.mean() * 252
        out.append(row)
    return pd.DataFrame(out)


def write(out: Path, daily, signs, fills, capital, include_trades: bool, scenarios: pd.DataFrame | None = None) -> None:
    summ = summarize(daily, capital) if scenarios is None else scenarios
    blend = daily[(daily["plan"] == "IBKR Lite") & (daily["strategy"] == "blend")].drop(columns=["plan", "strategy"])
    monthly = blend.assign(month=blend["date"].dt.to_period("M").astype(str)).groupby("month").agg(
        start_value=("start_value", "first"), end_value=("end_value", "last"), trading_pnl=("trading_pnl", "sum"),
        spread_slippage_est=("spread_slippage_est", "sum"), fees=("fees", "sum"), net_pnl=("net_pnl", "sum"))
    monthly["return"] = monthly["end_value"] / monthly["start_value"] - 1
    assum = pd.DataFrame([{"item": "direction (from 2016-2020 only)", "value": str(signs)},
                          {"item": "book", "value": "top / bottom fifth of 500 most liquid stocks, equal weight, "
                                                    "whole shares, gross 2x, blend = equal capital per strategy"},
                          {"item": "auction orders (MOO / MOC)", "value": "auction price + 1 bp slippage, no spread (Summary "
                           "also shows 0 and 0.5 bp; other sheets use 1 bp)"},
                          {"item": "9:35 / 10:00 entries", "value": "half-spread by liquidity tier + 0.5 bp slippage"},
                          {"item": "IBKR Lite", "value": "no commission, exchange or clearing fees; SEC fee and "
                                                         "FINRA TAF on sales; orders routed to market makers"},
                          {"item": "IBKR Pro Tiered", "value": str(IBKR)},
                          {"item": "note", "value": "check current fees at interactivebrokers.com"}])
    path = out / ("intraday_edge_ibkr.xlsx" if include_trades else "intraday_edge_ibkr_no_trades.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        summ.to_excel(xw, sheet_name="Summary", index=False)
        blend.to_excel(xw, sheet_name="Daily value (blend, Lite)", index=False)
        monthly.to_excel(xw, sheet_name="Monthly (blend, Lite)")
        if include_trades:
            fills.to_excel(xw, sheet_name="Trades (blend, Lite)", index=False)
        assum.to_excel(xw, sheet_name="Assumptions", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "B2"
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 50)
    LOG.info("wrote %s", path)


def main(argv=None):
    from ..utils import setup_logging

    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="data/intraday/5min")
    ap.add_argument("--symbols", type=int, default=500)
    ap.add_argument("--capital", type=float, default=100_000)
    ap.add_argument("--trade-months", type=int, default=3)
    ap.add_argument("--out", default="reports/intraday_edge")
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    if args.synthetic:
        from .synthetic import make_intraday

        bars = make_intraday(n_stocks=60, n_days=400, seed=4)
        bars.days = pd.bdate_range("2019-09-02", periods=len(bars.days))
    else:
        from .bars import load_store

        bars = load_store(args.store, args.symbols)
    log_from = str((bars.days[-1] - pd.DateOffset(months=args.trade_months)).date())
    daily, signs, fills = simulate(bars, args.capital, trade_log_from=log_from)
    # sensitivity: what an auction fill costs beyond the official open / close price
    scen = [summarize(daily, args.capital).assign(auction_slippage_bp=1.0)]
    for slip in (0.0, 0.5):
        d2, _, _ = simulate(bars, args.capital, auction_slippage_bp=slip)
        scen.append(summarize(d2, args.capital).assign(auction_slippage_bp=slip))
    summ = pd.concat(scen, ignore_index=True)
    summ = summ[["auction_slippage_bp"] + [c for c in summ.columns if c != "auction_slippage_bp"]]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write(out, daily, signs, fills, args.capital, include_trades=True, scenarios=summ)
    write(out, daily, signs, fills, args.capital, include_trades=False, scenarios=summ)
    summ.to_csv(out / "summary.csv", index=False)
    (out / "signs.json").write_text(json.dumps(signs, indent=2))   # read by the live auction trader
    print(summ.round(3).to_string())


if __name__ == "__main__":
    main()
