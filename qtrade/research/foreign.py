"""Trading on foreign stock exchanges, as the $10,000 sheet book would: fills at the official
open / close auction prices, 0 bp fees (the sheet's rules - real taxes and commissions are shown too).

``python -m qtrade.research.foreign --out reports/foreign`` (Yahoo daily data since 2005):

1. **Strategies inside each market** (Asia: Japan, Hong Kong, Korea, Taiwan, Australia, India;
   Europe: UK, Germany, France), long the top fifth / short the bottom fifth of 30-40 large caps:
   overnight persistence (close in, open out), the end-of-day fade, 1- and 5-day reversal.
   Direction fixed on 2006-2014, judged on 2015-2026.
2. **Is the overnight edge real or a data artefact?** Yahoo's daily *open* for foreign stocks is
   sometimes stale (a copy of the previous close, or a late first trade). Two checks:
   * the same signal lagged a day (a stale open's error reverses the next day; a real
     persistence effect survives a one-day lag);
   * the last 60 days with the open taken from the first 5-minute bar instead of the daily bar:
     how often the two differ, and whether the strategy's daily P&L agrees.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, setup_logging
from .asia import COSTS, P1, P2, STOCKS, _sharpe, _xs_weights

EUROPE = {
    "UK": ["SHEL.L", "AZN.L", "HSBA.L", "ULVR.L", "BP.L", "GSK.L", "RIO.L", "BATS.L", "DGE.L", "REL.L", "LSEG.L",
           "NG.L", "BARC.L", "LLOY.L", "GLEN.L", "VOD.L", "PRU.L", "TSCO.L", "BA.L", "CPG.L", "AAL.L", "NWG.L",
           "IMB.L", "EXPN.L", "RKT.L", "SSE.L", "LGEN.L", "AV.L", "STAN.L", "III.L"],
    "Germany": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MUV2.DE", "AIR.DE", "MBG.DE", "BMW.DE", "BAS.DE",
                "IFX.DE", "DHL.DE", "BAYN.DE", "DB1.DE", "ADS.DE", "VOW3.DE", "RWE.DE", "EOAN.DE", "DBK.DE",
                "HEN3.DE", "MRK.DE", "BEI.DE", "CON.DE", "FRE.DE", "HEI.DE", "MTX.DE", "SY1.DE", "VNA.DE",
                "CBK.DE", "PAH3.DE", "RHM.DE"],
    "France": ["MC.PA", "OR.PA", "TTE.PA", "SAN.PA", "AIR.PA", "SU.PA", "AI.PA", "BNP.PA", "RMS.PA", "EL.PA",
               "CS.PA", "DG.PA", "SAF.PA", "KER.PA", "RI.PA", "BN.PA", "ACA.PA", "GLE.PA", "CAP.PA", "ENGI.PA",
               "ORA.PA", "VIE.PA", "SGO.PA", "ML.PA", "HO.PA", "DSY.PA", "STLAP.PA", "PUB.PA", "LR.PA", "EN.PA"],
}
EUROPE_COSTS = {
    "UK": (55.0, True, "0.05% commission each side + 0.5% stamp duty on purchases"),
    "Germany": (10.0, True, "0.05% commission each side, no transaction tax"),
    "France": (30.0, True, "0.05% commission each side + 0.3% financial transaction tax on purchases (large caps)"),
}
MARKETS = {**STOCKS, **EUROPE}
ALL_COSTS = {**COSTS, **EUROPE_COSTS}


def panels(md, tickers: list[str]):
    c = md.close[[t for t in tickers if t in md.close.columns]]
    live = c.notna().sum(axis=1) >= max(10, c.shape[1] // 3)
    c = c[live]
    o = md.open[c.columns].reindex(c.index)
    prev = c.shift(1)
    bad = (o == prev) | (o == c)
    on = np.log(o / prev).mask(bad)
    intra = np.log(c / o).mask(bad)
    cc = np.log(c / prev).clip(-0.5, 0.5)
    return c, o, on, intra, cc, bad


def book_pnl(sig: pd.DataFrame, ret: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    sig = sig.sub(sig.mean(axis=1), axis=0)
    w = _xs_weights(sig)
    g = (w * ret.clip(-0.5, 0.5)).sum(axis=1, min_count=1).fillna(0.0)
    return g.where(w.abs().sum(axis=1) > 0), w


def strategies(md) -> pd.DataFrame:
    rows = []
    for mkt, tickers in MARKETS.items():
        c, o, on, intra, cc, bad = panels(md, tickers)
        if c.shape[1] < 10:
            continue
        nxt_on, nxt_cc = on.shift(-1), cc.shift(-1)
        on21 = on.rolling(21, min_periods=15).sum()
        sigs = {
            "overnight persistence (close in, open out)": (on21, nxt_on),
            "overnight persistence, signal lagged a day (stale-open check)": (on21.shift(1), nxt_on),
            "overnight persistence, 21 days ending a week ago (stale-open check)": (on21.shift(5), nxt_on),
            "end-of-day fade (close in, open out)": (-intra, nxt_on),
            "1-day reversal (close to close)": (-cc, nxt_cc),
            "5-day reversal (close to close)": (-cc.rolling(5).sum(), nxt_cc),
        }
        cost, broker, note = ALL_COSTS.get(mkt, (20.0, False, ""))
        for name, (sig, ret) in sigs.items():
            g, w = book_pnl(sig, ret)
            s1 = g[P1[0]:P1[1]]
            d = np.sign(s1.mean()) if s1.notna().sum() > 120 else np.sign(g.mean())
            d = d if np.isfinite(d) and d != 0 else 1.0
            pnl = d * g
            turn = (w.diff().abs().sum(axis=1) / 2) if "close to close" in name else w.abs().sum(axis=1)
            net = pnl - turn * cost / 1e4
            p2 = pnl[P2[0]:P2[1]]
            rows.append({"market": mkt, "strategy": name, "direction": "+" if d > 0 else "-", "stocks": c.shape[1],
                         "sharpe_2006_14": _sharpe(pnl[P1[0]:P1[1]]), "sharpe_2015_26": _sharpe(p2),
                         "annual_return_2015_26": float(p2.mean() * 252),
                         "sharpe_2021_26": _sharpe(pnl["2021":]), "worst_year_2015_26": float(
                             p2.groupby(p2.index.year).sum().min()) if len(p2.dropna()) else np.nan,
                         "net_sharpe_2015_26": _sharpe(net[P2[0]:P2[1]]), "round_trip_cost_bp": cost,
                         "bad_open_share": float(bad.where(c.notna()).mean().mean())})
    return pd.DataFrame(rows)


def intraday_open_check(md) -> pd.DataFrame:
    """Last ~60 days: the daily bar's open vs the first 5-minute bar's open, and the overnight
    persistence book's daily P&L computed both ways."""
    rows = []
    for mkt, tickers in MARKETS.items():
        try:
            rows.append(_open_check_market(md, mkt, tickers))
        except Exception as exc:                          # one market's data problem shouldn't sink the study
            LOG.warning("%s: open check failed (%s)", mkt, exc)
    return pd.DataFrame([r for r in rows if r])


def _open_check_market(md, mkt: str, tickers: list[str]) -> dict | None:
    import yfinance as yf

    try:
        raw = yf.download(tickers, period="60d", interval="5m", group_by="ticker", progress=False,
                          auto_adjust=False, threads=True)
    except Exception as exc:
        LOG.warning("%s: 5-minute data failed (%s)", mkt, exc)
        return None
    first = {}
    for t in tickers:
        if raw is None or raw.empty or t not in raw.columns.get_level_values(0):
            continue
        f = raw[t].dropna(how="all")
        if f.empty:
            continue
        idx = f.index.tz_convert(f.index.tz) if f.index.tz is not None else f.index
        day = pd.DatetimeIndex(idx.date)
        first[t] = f["Open"].groupby(day).first()
    if len(first) < 10:
        return None
    o5 = pd.DataFrame(first)
    c, o, on, intra, cc, bad = panels(md, tickers)
    o5 = o5[[t for t in o5.columns if t in c.columns]]
    days = o5.index.intersection(o.index)
    if len(days) < 20:
        return None
    # the daily panels are dividend-adjusted; the 5-minute bars are not: compare in raw prices
    raw_c = getattr(md, "raw_close", None)
    factor = (raw_c[c.columns].reindex(c.index) / c) if raw_c is not None else 1.0
    o_raw = o * factor
    od, o5d = o_raw.loc[days, o5.columns], o5.loc[days]
    diff = (np.log(od / o5d)).abs() * 1e4
    prev = (c * factor).shift(1)[o5.columns]
    on5 = np.log(o5.reindex(c.index) / prev)
    on_d = on[o5.columns]
    # the book decided at each close from the daily-bar history, filled at either open
    sig = on_d.rolling(21, min_periods=15).sum()
    g_daily, _ = book_pnl(sig, on_d.shift(-1))
    g_5m, _ = book_pnl(sig, on5.shift(-1))
    dd = g_daily.reindex(days[:-1]).dropna()
    d5 = g_5m.reindex(days[:-1]).dropna()
    common = dd.index.intersection(d5.index)
    return {"market": mkt, "days": len(days), "stocks": o5.shape[1],
                 "median_open_gap_bp": float(np.nanmedian(diff.values)),
                 "share_open_differs_over_10bp": float((diff > 10).mean().mean()),
                 "book_bp_per_day_daily_open": float(dd.loc[common].mean() * 1e4) if len(common) else np.nan,
                 "book_bp_per_day_5min_open": float(d5.loc[common].mean() * 1e4) if len(common) else np.nan,
                 "corr_daily_vs_5min": float(dd.loc[common].corr(d5.loc[common])) if len(common) > 5 else np.nan}


def run(out: Path) -> dict:
    from ..data.loader import download_prices

    out.mkdir(parents=True, exist_ok=True)
    tickers = [t for v in MARKETS.values() for t in v]
    md = download_prices(tickers, start="2005-01-01")
    LOG.info("foreign: %d of %d tickers", md.close.shape[1], len(tickers))
    st = strategies(md)
    st.to_csv(out / "foreign_strategies.csv", index=False)
    chk = intraday_open_check(md)
    chk.to_csv(out / "foreign_open_check.csv", index=False)
    costs = pd.DataFrame([{"market": k, "round_trip_cost_bp": v[0], "on_ibkr": v[1], "what": v[2]}
                          for k, v in ALL_COSTS.items() if k in MARKETS])
    lines = ["## Foreign exchanges: auction strategies at 0 bp (the sheet's rules) and with real costs", "",
             "Daily Yahoo data since 2005, 30-40 large caps per market (today's large caps: survivorship). "
             "Long top fifth / short bottom fifth, gross 1. Direction fixed on 2006-14, judged on 2015-26. "
             "`sharpe_*` = 0 bp (fills at the official open / close); `net_sharpe` = after commission and "
             "stamp / transaction taxes.", "",
             st.round(3).to_markdown(index=False), "",
             "### Stale-open check: daily-bar open vs the first 5-minute bar (last ~60 days)", "",
             chk.round(3).to_markdown(index=False) if len(chk) else "(no 5-minute data)", "",
             "### Costs", "", costs.to_markdown(index=False), ""]
    (out / "foreign.md").write_text("\n".join(lines) + "\n")
    return {"strategies": len(st), "open_check": chk.round(3).to_dict(orient="records")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/foreign")
    args = ap.parse_args(argv)
    setup_logging()
    print(json.dumps(run(Path(args.out)), indent=1, default=str))


if __name__ == "__main__":
    main()
