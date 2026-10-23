"""Pre-registered test: does avoiding lottery stocks improve the long-only flat-in-stress momentum book?

Before picking the top momentum quintile, drop every name in its market's
top 30% by 63-day volatility or by 21-day maximum daily return (the names the
low-vol and MAX signals penalise, which cannot be shorted in most of Asia).
The hedge is unchanged (equal-weighted universe). Three universes: the
original 21 markets, the 20 new exchanges, and pooled Asia-Pacific financials
(liquid half). The prediction (LOG.md): higher 2015-26 Sharpe in all three,
no worse drawdown.

    python research_international/code/lottery_filter.py --old-prices data/prices --old-universe data/universe.csv \
        --new-prices data2/prices_new --new-universe data2/universe_new_markets.csv \
        --fin-prices data2/prices_fin --fin-universe data2/universe_asia_financials.csv --out reports/lottery
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from asia_fin_deep import GROUP, MARKETS as FIN_MARKETS, Panel, build
from intl_more import ASIA, WEST, equal_risk, held_flat
from new_exchanges import load

CUT = 0.30


def not_lottery(sigs: dict, mask: pd.DataFrame) -> pd.DataFrame:
    """True unless the name is in the market's most volatile 30% or highest-MAX 30% (z-scores are within-market)."""
    lv = sigs["low_vol"].where(mask).rank(axis=1, pct=True)          # low_vol = -vol: low percentile = most volatile
    mx = sigs["max_effect"].where(mask).rank(axis=1, pct=True)
    return mask & (lv > CUT) & (mx > CUT)


def beta_hedged(long_net: pd.Series, ew: pd.Series, exposure: pd.Series) -> pd.Series:
    """Post-hoc diagnostic: hedge with the trailing beta of the long book to the EW market (lagged 3 days, as in
    intl_more), estimated on invested days only and applied only while the book is invested."""
    inv = exposure > 0
    x, y = long_net.where(inv), ew.where(inv)
    b = (x.rolling(252, min_periods=126).cov(y) / y.rolling(252, min_periods=126).var()).ffill().shift(3).clip(0, 2)
    return (long_net - b * ew * exposure).where(b.notna())


def books(m, comp, mask, keep, flat) -> dict[str, pd.Series]:
    ew_raw = m.r1.where(mask).mean(axis=1)
    ew = ew_raw * held_flat(flat)
    lo_base = L.pnl(L.long_only_flip(m, comp, mask, flat), m)["net"]
    lo_filt = L.pnl(L.long_only_flip(m, comp, keep, flat), m)["net"]
    return {"unfiltered": lo_base - ew, "lottery filter": lo_filt - ew,
            "unfiltered, beta hedge (post hoc)": beta_hedged(lo_base, ew_raw, held_flat(flat)),
            "lottery filter, beta hedge (post hoc)": beta_hedged(lo_filt, ew_raw, held_flat(flat))}


def per_market(markets: dict) -> dict[str, dict[str, pd.Series]]:
    out = {}
    for name, m in markets.items():
        sigs = m.signals()
        comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
        flat = pd.Series(np.where(m.vix > 20, 0.0, 1.0), index=m.dates)
        out[name] = books(m, comp, m.tradable, not_lottery(sigs, m.tradable), flat)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("old", "new", "fin"):
        ap.add_argument(f"--{k}-prices", required=True)
        ap.add_argument(f"--{k}-universe", required=True)
    ap.add_argument("--out", default="reports/lottery")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vix = pd.read_parquet(Path(args.new_prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    rows = []
    for label, prices, universe, names in (("original 21", args.old_prices, args.old_universe, ASIA + WEST),
                                           ("20 new exchanges", args.new_prices, args.new_universe, None)):
        u = pd.read_csv(universe)
        mk = load(Path(prices), u, vix, names or dict.fromkeys(u["market"]))
        pm = per_market(mk)
        for b in ("unfiltered", "lottery filter", "unfiltered, beta hedge (post hoc)", "lottery filter, beta hedge (post hoc)"):
            s = equal_risk(pd.DataFrame({k: v[b] for k, v in pm.items()}))
            rows.append(L.period_stats(s, f"{label}: long-only flat in stress, {b}", {"markets": len(pm)}))
        wins = sum(L._sharpe(v["lottery filter"]["2015":]) > L._sharpe(v["unfiltered"]["2015":]) for v in pm.values())
        print(f"{label}: filter better in {wins}/{len(pm)} markets (2015-26)")
    fu = pd.read_csv(args.fin_universe)
    groups = fu.set_index("ticker")["industry"].map(GROUP)
    fin = {k: L.Market(k, Path(args.fin_prices) / k.replace(" ", "_"), fu[fu["market"] == k], vix)
           for k in FIN_MARKETS if (fu["market"] == k).sum() >= 15}
    P = build(fin, groups)
    m = Panel(P["r1"], P["cost"])
    v = vix.reindex(P["r1"].index, method="ffill")
    flat = pd.Series(np.where(v > 20, 0.0, 1.0), index=P["r1"].index)
    comp = sum(P["sig_c"][s] for s in L.MOM) / len(L.MOM)
    # within-market percentiles for the pooled panel
    keep = []
    for mk_, cols in P["key_c"].groupby(P["key_c"]).groups.items():
        cols = list(cols)
        keep.append(not_lottery({k: P["sig_c"][k][cols] for k in ("low_vol", "max_effect")}, P["liquid"][cols]))
    keep = pd.concat(keep, axis=1, sort=True).reindex(columns=P["liquid"].columns).fillna(False).astype(bool)
    for b, s in books(m, comp, P["liquid"], keep, flat).items():
        rows.append(L.period_stats(s["2004":].dropna(), f"Asia-Pacific financials (liquid half): long-only flat in stress, {b}"))
    t = pd.DataFrame(rows)
    t.to_csv(out / "lottery_filter.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26"]
    print(t[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
