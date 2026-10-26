"""Pre-registered: the flat-in-stress momentum book on the 400 largest companies of each Asia-Pacific exchange,
against the same book on the original index universes (LOG.md).

    python research_international/code/broad_asia.py --prices data2/prices_broad --universe data2/universe_asia_broad.csv \
        --old-prices data/prices --old-universe data/universe.csv --out reports/broad_asia
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from intl_more import block_bootstrap, equal_risk, market_books
from new_exchanges import load

SAME = ("Japan", "Korea", "Taiwan", "Hong Kong", "China", "India", "Australia", "Singapore", "Malaysia", "Thailand")


def liquid_flat(m: L.Market, mult: float = 1.0) -> pd.Series:
    sigs = m.signals()
    comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
    flat = pd.Series(np.where(m.vix > 20, 0.0, 1.0), index=m.dates)
    liq = m.tradable & (m.adv.where(m.tradable).rank(axis=1, pct=True) > 0.5)
    saved = m.cost
    m.cost = saved * mult
    s = L.pnl(L.staggered(m, comp, liq, flat), m)["net"]
    m.cost = saved
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--old-prices", required=True)
    ap.add_argument("--old-universe", required=True)
    ap.add_argument("--out", default="reports/broad_asia")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vix = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    u, uo = pd.read_csv(args.universe), pd.read_csv(args.old_universe)
    broad = load(Path(args.prices), u, vix, SAME)
    old = load(Path(args.old_prices), uo, vix, SAME)
    per, rows, pm = {}, [], []
    for label, mk in (("broad top 400", broad), ("index members", old)):
        per[label] = {}
        for name, m in mk.items():
            b = market_books(m, None)
            b["flat_liquid_half"] = liquid_flat(m)
            b["flat_liquid_half_costs_x2"] = liquid_flat(m, 2.0)
            per[label][name] = b
            pm.append({"universe": label, "market": name, "median_names_2015_26": int(m.tradable.sum(axis=1)["2015":].median()),
                       **{f"{k}_2015_26": L._sharpe(b[k]["2015":]) for k in ("plain", "flip", "flat_in_stress", "flat_in_stress_costs_x2", "flat_liquid_half")}})
        for rule in ("plain", "flip", "flat_in_stress", "flat_in_stress_costs_x2", "long_only_flat_ew_hedge", "flat_liquid_half",
                     "flat_liquid_half_costs_x2"):
            s = equal_risk(pd.DataFrame({k: v[rule] for k, v in per[label].items()}))
            rows.append(L.period_stats(s, f"{label} ({len(mk)} markets): {rule}"))
            if label == "broad top 400" and rule == "flat_in_stress":
                boot = {p: block_bootstrap(s[a:b_].dropna().to_numpy()) for p, a, b_ in
                        (("2006-14", "2006", "2014"), ("2015-20", "2015", "2020"), ("2021-26", "2021", "2026"))}
    t = pd.DataFrame(rows)
    t.to_csv(out / "broad_asia.csv", index=False)
    pd.DataFrame(pm).to_csv(out / "broad_asia_per_market.csv", index=False)
    pd.DataFrame(boot).T.to_csv(out / "broad_asia_bootstrap.csv")
    pd.set_option("display.width", 250)
    print(pd.DataFrame(pm).round(2).to_string(index=False))
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26"]
    print(t[cols].round(2).to_string(index=False))
    print(pd.DataFrame(boot).T.round(3).to_string())


if __name__ == "__main__":
    main()
