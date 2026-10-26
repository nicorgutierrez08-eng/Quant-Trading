"""The intraday strategy as an Interactive Brokers account would have traded it.

Same forecasts and portfolio rule as the intraday backtest (walk-forward, out
of sample), but every order is simulated as a whole-share fill and charged what
IBKR Pro would charge, so the result is a trade-by-trade ledger and an account
value you could reconcile against real statements:

* commission, IBKR Pro Tiered: $0.0035 per share (<= 300k shares a month),
  at least $0.35 and at most 1% of the trade value per order;
* exchange fee for orders that take liquidity, clearing (NSCC/DTC) and the
  FINRA pass-through on the commission;
* on sales, the SEC fee and the FINRA trading activity fee;
* the half-spread and slippage paid by a marketable order (the bid-ask spread
  measured on Alpaca quotes, by liquidity tier), shown separately.

Two workbooks are written: ``ibkr_intraday.xlsx`` with the fill ledger, and
``ibkr_intraday_no_trades.xlsx`` without it. Fill prices come from licensed
market data, so only the second one is published openly.

The fee rates are in ``IBKR`` below and in the workbook's Assumptions sheet;
check them against interactivebrokers.com before relying on them, because
regulators change the SEC fee rate every year.

    python -m qtrade.intraday.ibkr_sim --store data/intraday/5min --symbols 500 --capital 100000
    python -m qtrade.intraday.ibkr_sim --synthetic
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG
from .bars import DayBars
from .features import exec_prices
from .strategy import ic_for_sizing, prepare, target_weights, unit_cost

IBKR = {
    "commission_per_share": 0.0035,      # IBKR Pro Tiered, <= 300,000 shares a month
    "commission_min": 0.35,              # per order
    "commission_max_pct": 0.01,          # of trade value
    "exchange_fee_per_share": 0.0030,    # removing liquidity (marketable orders), typical NYSE/Nasdaq
    "clearing_fee_per_share": 0.00020,   # NSCC / DTC
    "finra_passthrough_pct": 0.000175,   # of the commission
    "sec_fee_per_dollar_sold": 27.80e-6, # SEC Section 31 fee on sales
    "finra_taf_per_share_sold": 0.000166,
    "finra_taf_max": 8.30,               # per trade
}
FIXED = {"per_share": 0.005, "min": 1.00, "max_pct": 0.01}   # IBKR Pro Fixed, for comparison


def order_fees(shares: np.ndarray, price: np.ndarray, sell: np.ndarray, fees: dict = IBKR) -> dict:
    """Fee components for a batch of orders (absolute share counts)."""
    value = shares * price
    commission = np.clip(shares * fees["commission_per_share"], fees["commission_min"],
                         np.maximum(value * fees["commission_max_pct"], fees["commission_min"]))
    exchange = shares * fees["exchange_fee_per_share"]
    clearing = shares * fees["clearing_fee_per_share"]
    passthrough = commission * fees["finra_passthrough_pct"]
    sec = np.where(sell, value * fees["sec_fee_per_dollar_sold"], 0.0)
    taf = np.where(sell, np.minimum(shares * fees["finra_taf_per_share_sold"], fees["finra_taf_max"]), 0.0)
    fixed = np.clip(shares * FIXED["per_share"], FIXED["min"], np.maximum(value * FIXED["max_pct"], FIXED["min"]))
    return {"commission": commission, "exchange_fee": exchange, "clearing_fee": clearing,
            "finra_passthrough": passthrough, "sec_fee": sec, "finra_taf": taf, "fixed_commission": fixed}


def simulate(bars: DayBars, hist, pred: np.ndarray, icfg, ic_by_day: np.ndarray, capital: float,
             trade_log_from: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily account values for every day, and a fill-by-fill ledger from ``trade_log_from`` on."""
    D, B, N = bars.close.shape
    icfg = copy.deepcopy(icfg)
    icfg.aum = capital
    equity = capital
    days, fills = [], []
    log_from = pd.Timestamp(trade_log_from) if trade_log_from else None
    tick = np.array(bars.tickers)
    for d in range(D):
        if not np.isfinite(pred[d]).any():
            continue
        Qf, can = exec_prices(bars.open[d], bars.close[d])
        sigma, adv = hist.sigma[d], hist.adv[d]
        q = np.zeros(N)                         # shares held
        start_equity = equity
        pnl = spread_cost = 0.0
        fee_tot = {k: 0.0 for k in ("commission", "exchange_fee", "clearing_fee", "finra_passthrough",
                                    "sec_fee", "finra_taf", "fixed_commission")}
        n_orders = shares_traded = value_traded = 0.0
        keep_log = log_from is not None and bars.days[d] >= log_from
        for k in range(1, B + 1):              # decision k: open of bar k (k = B: the close)
            P0, P1 = np.nan_to_num(Qf[k - 1]), np.nan_to_num(Qf[k])
            pnl += float(q @ (P1 - P0))
            b = k - 1
            e_now = start_equity + pnl - spread_cost - sum(v for kk, v in fee_tot.items() if kk != "fixed_commission")
            if k > icfg.flat_bar or k == B:
                w_t = np.zeros(N)
            elif b >= icfg.start_bar and (b - icfg.start_bar) % icfg.rebalance_every == 0:
                h_dollars = q * P1
                w_t = target_weights(pred[d, b], sigma, adv, h_dollars / e_now, icfg, ic_by_day[d], B)
            else:
                continue
            with np.errstate(invalid="ignore", divide="ignore"):
                tgt = np.where(can[k] & (P1 > 0), np.trunc(w_t * e_now / np.where(P1 > 0, P1, np.nan)), q)
            tgt = np.nan_to_num(tgt, nan=0.0)
            if k == B:
                tgt[:] = 0.0                   # flat at the close
            dq = tgt - q
            small = (np.abs(dq) * P1 < icfg.min_order_value) & (tgt != 0)
            dq[small] = 0.0
            idx = np.flatnonzero(dq != 0)
            if len(idx) == 0:
                continue
            sh, px, sell = np.abs(dq[idx]), P1[idx], dq[idx] < 0
            f = order_fees(sh, px, sell)
            half = unit_cost(adv[idx], sigma[idx], icfg, dq[idx] * px, B)     # spread + slippage + impact per $
            sc = sh * px * half
            spread_cost += float(sc.sum())
            for kk in fee_tot:
                fee_tot[kk] += float(f[kk].sum())
            n_orders += len(idx)
            shares_traded += float(sh.sum())
            value_traded += float((sh * px).sum())
            if keep_log:
                t = bars.days[d] + pd.Timedelta(minutes=9 * 60 + 30 + k * bars.bar_minutes)
                for j, i in enumerate(idx):
                    fills.append({"time": t, "ticker": tick[i], "side": "SELL" if sell[j] else "BUY",
                                  "shares": int(sh[j]), "price": round(float(px[j]), 4),
                                  "value": round(float(sh[j] * px[j]), 2),
                                  "position_after": int(q[i] + dq[i]),
                                  "commission": round(float(f["commission"][j]), 4),
                                  "exchange_fee": round(float(f["exchange_fee"][j]), 4),
                                  "clearing_fee": round(float(f["clearing_fee"][j]), 4),
                                  "regulatory_fees": round(float(f["sec_fee"][j] + f["finra_taf"][j]
                                                                 + f["finra_passthrough"][j]), 4),
                                  "spread_slippage_est": round(float(sc[j]), 4)})
            q = q + dq
        fees = sum(v for kk, v in fee_tot.items() if kk != "fixed_commission")
        equity = start_equity + pnl - spread_cost - fees
        days.append({"date": bars.days[d], "start_value": start_equity, "trading_pnl": pnl,
                     "commissions": fee_tot["commission"],
                     "exchange_clearing_fees": fee_tot["exchange_fee"] + fee_tot["clearing_fee"],
                     "regulatory_fees": fee_tot["sec_fee"] + fee_tot["finra_taf"] + fee_tot["finra_passthrough"],
                     "spread_slippage_est": spread_cost, "net_pnl": equity - start_equity, "end_value": equity,
                     "orders": int(n_orders), "shares_traded": shares_traded, "value_traded": value_traded,
                     "commission_if_fixed_plan": fee_tot["fixed_commission"]})
    return pd.DataFrame(days), pd.DataFrame(fills)


def _summary(daily: pd.DataFrame, capital: float) -> dict:
    r = daily["net_pnl"] / daily["start_value"]
    yrs = len(daily) / 252
    return {"start": str(daily["date"].iloc[0].date()), "end": str(daily["date"].iloc[-1].date()),
            "starting_capital": capital, "ending_value": float(daily["end_value"].iloc[-1]),
            "total_return": float(daily["end_value"].iloc[-1] / capital - 1),
            "annual_return": float((daily["end_value"].iloc[-1] / capital) ** (1 / max(yrs, 1e-9)) - 1),
            "sharpe": float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan,
            "max_drawdown": float((daily["end_value"] / daily["end_value"].cummax() - 1).min()),
            "trading_pnl_before_costs": float(daily["trading_pnl"].sum()),
            "commissions": float(daily["commissions"].sum()),
            "exchange_and_clearing_fees": float(daily["exchange_clearing_fees"].sum()),
            "regulatory_fees": float(daily["regulatory_fees"].sum()),
            "spread_and_slippage_est": float(daily["spread_slippage_est"].sum()),
            "orders": int(daily["orders"].sum()), "orders_per_day": float(daily["orders"].mean()),
            "value_traded": float(daily["value_traded"].sum()),
            "commission_if_fixed_plan": float(daily["commission_if_fixed_plan"].sum())}


def write_workbook(path: Path, runs: dict[float, tuple[pd.DataFrame, pd.DataFrame]], main_capital: float,
                   model_note: str, include_trades: bool = True) -> None:
    """``include_trades=False`` leaves out the fill ledger, whose prices come from licensed
    market data (that version is safe to publish)."""
    daily, fills = runs[main_capital]
    summ = pd.DataFrame({f"${c:,.0f} account": _summary(d, c) for c, (d, _) in runs.items()}).T
    monthly = daily.assign(month=daily["date"].dt.to_period("M").astype(str)).groupby("month").agg(
        start_value=("start_value", "first"), end_value=("end_value", "last"),
        trading_pnl=("trading_pnl", "sum"), commissions=("commissions", "sum"),
        exchange_clearing_fees=("exchange_clearing_fees", "sum"), regulatory_fees=("regulatory_fees", "sum"),
        spread_slippage_est=("spread_slippage_est", "sum"), net_pnl=("net_pnl", "sum"), orders=("orders", "sum"))
    monthly["return"] = monthly["end_value"] / monthly["start_value"] - 1
    assumptions = pd.DataFrame([{"item": k, "value": v} for k, v in IBKR.items()]
                               + [{"item": f"fixed_plan_{k}", "value": v} for k, v in FIXED.items()]
                               + [{"item": "model", "value": model_note},
                                  {"item": "fills", "value": "whole shares at the open of the bar after each "
                                                              "decision (5-minute bars), marketable orders"},
                                  {"item": "spread_slippage_est", "value": "half-spread by liquidity tier "
                                   "(measured on Alpaca quotes) + 0.5 bp slippage + square-root impact"},
                                  {"item": "pattern day trader rule", "value": "US margin accounts need "
                                   ">= $25,000 equity to day trade freely"},
                                  {"item": "note", "value": "check fee rates at interactivebrokers.com; "
                                   "the SEC fee rate changes each year"}])
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        summ.to_excel(xw, sheet_name="Summary")
        daily.to_excel(xw, sheet_name=f"Daily value ${main_capital/1e3:,.0f}k", index=False)
        monthly.to_excel(xw, sheet_name="Monthly")
        if include_trades:
            fills.to_excel(xw, sheet_name="Trades", index=False)
        assumptions.to_excel(xw, sheet_name="Assumptions", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "B2"
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 45)
    LOG.info("workbook %s: %d daily rows, %d fills", path, len(daily), len(fills))


def main(argv=None):
    from ..config import Config
    from ..utils import setup_logging

    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="data/intraday/5min")
    ap.add_argument("--symbols", type=int, default=500)
    ap.add_argument("--start")
    ap.add_argument("--capital", type=float, default=100_000)
    ap.add_argument("--also", default="25000,1000000", help="other account sizes for the summary")
    ap.add_argument("--trade-months", type=int, default=3, help="months of fills in the Trades sheet")
    ap.add_argument("--out", default="reports/ibkr")
    ap.add_argument("--config")
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    cfg = Config.load(args.config)
    icfg = cfg.intraday
    if args.synthetic:
        from .synthetic import make_intraday

        bars = make_intraday(n_stocks=60, n_days=260, seed=2)
        icfg.min_train_months = 2
    else:
        from .bars import load_store

        bars = load_store(args.store, args.symbols, args.start)
    hist, pred, _, _, daily_ic = prepare(bars, icfg)
    ic_size = ic_for_sizing(daily_ic)
    log_from = str((bars.days[-1] - pd.DateOffset(months=args.trade_months)).date())
    caps = [args.capital] + [float(x) for x in args.also.split(",") if x]
    runs = {}
    for c in dict.fromkeys(caps):
        runs[c] = simulate(bars, hist, pred, icfg, ic_size, c, log_from if c == args.capital else None)
        LOG.info("$%.0f account: ending value $%.0f", c, runs[c][0]["end_value"].iloc[-1])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    note = (f"production intraday ridge, walk-forward out of sample, {len(bars.tickers)} stocks, "
            f"rebalanced every {icfg.rebalance_every * bars.bar_minutes} min, top/bottom {icfg.n_side} names, "
            f"gross {icfg.gross}x")
    write_workbook(out / "ibkr_intraday.xlsx", runs, args.capital, note)
    write_workbook(out / "ibkr_intraday_no_trades.xlsx", runs, args.capital, note, include_trades=False)
    runs[args.capital][0].to_csv(out / "ibkr_daily.csv", index=False)
    pd.DataFrame({f"{c:.0f}": _summary(d, c) for c, (d, _) in runs.items()}).to_json(out / "summary.json", indent=2)
    s = _summary(runs[args.capital][0], args.capital)
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()})


if __name__ == "__main__":
    main()
