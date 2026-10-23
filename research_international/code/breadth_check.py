"""Is the new-exchange result about breadth? The flat-in-stress book on each new exchange's 30 largest
names (an index-like universe, like the original 21) vs all 120.

The original 21 used index members (20-60 large caps in most of Europe); the
new exchanges use the 120 largest companies. If momentum is stronger in mid
caps, restricting the new exchanges to their 30 largest names should pull
their Sharpe down towards the original 21's level.

    python research_international/code/breadth_check.py --prices data2/prices_new --universe data2/universe_new_markets.csv --out reports/new_exchanges
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from intl_more import equal_risk
from new_exchanges import load
from new_exchanges_robust import NO_BORROW

TOP = 30


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--out", default="reports/new_exchanges")
    args = ap.parse_args(argv)
    u = pd.read_csv(args.universe)
    vix = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    markets = load(Path(args.prices), u, vix, dict.fromkeys(u["market"]))
    per = {}
    for name, m in markets.items():
        uu = u[u["market"] == name].copy()
        if uu["market_cap"].notna().sum() >= TOP:
            big = set(uu.sort_values("market_cap", ascending=False)["ticker"].head(TOP))
        else:                              # hand lists (Vietnam, Austria, Pakistan): use today's traded value instead
            big = set(m.adv.iloc[-250:].median().sort_values(ascending=False).index[:TOP])
        in_big = pd.DataFrame(np.repeat(m.tickers.isin(list(big))[None, :], len(m.dates), 0), index=m.dates, columns=m.tickers)
        sigs = m.signals()
        flat = pd.Series(np.where(m.vix > 20, 0.0, 1.0), index=m.dates)
        mask = m.tradable & in_big
        z = sum(L.zscore(sigs[s], mask) for s in L.MOM) / len(L.MOM)      # re-standardise within the 30
        comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
        per[name] = {"all 120": L.pnl(L.staggered(m, comp, m.tradable, flat), m)["net"],
                     f"largest {TOP}": L.pnl(L.staggered(m, z, mask, flat), m)["net"]}
    rows = []
    for sname, members in (("all 20", tuple(per)), ("14 borrowable", tuple(k for k in per if k not in NO_BORROW))):
        for k in ("all 120", f"largest {TOP}"):
            rows.append(L.period_stats(equal_risk(pd.DataFrame({mk: per[mk][k] for mk in members})), f"{sname}: flat in stress, {k}"))
    pm = pd.DataFrame([{"market": k, "all_120_2015_26": L._sharpe(v["all 120"]["2015":]),
                        f"largest_{TOP}_2015_26": L._sharpe(v[f"largest {TOP}"]["2015":])} for k, v in per.items()])
    t = pd.DataFrame(rows)
    t.to_csv(Path(args.out) / "breadth_check.csv", index=False)
    pm.to_csv(Path(args.out) / "breadth_check_per_market.csv", index=False)
    pd.set_option("display.width", 250)
    print(pm.round(2).to_string(index=False))
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "maxdd_2015_26"]
    print(t[cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
