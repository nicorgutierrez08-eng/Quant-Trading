"""The number to plan with: the combined book under conservative assumptions.

* International sleeve = flat-in-stress momentum on the original 21 markets plus only the 14 new exchanges
  where single stocks can be borrowed, every market at double its estimated costs, equal-risk across markets.
* Blended with the US book exactly as intl_more / new_exchanges do (inverse vol, 25% cap, 10% vol target).

    python research_international/code/conservative_combo.py --old-prices data/prices --old-universe data/universe.csv \
        --new-prices data2/prices_new --new-universe data2/universe_new_markets.csv --out reports/conservative \
        --us-flip <US flip daily> --us-etf <multi_daily.csv> --us-strategies <strategy_returns.csv>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from intl_more import ASIA, WEST, equal_risk
from new_exchanges import blend, load
from new_exchanges_robust import NO_BORROW


def flat_series(m: L.Market, cost_mult: float) -> pd.Series:
    sigs = m.signals()
    comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
    flat = pd.Series(np.where(m.vix > 20, 0.0, 1.0), index=m.dates)
    saved = m.cost
    m.cost = saved * cost_mult
    s = L.pnl(L.staggered(m, comp, m.tradable, flat), m)["net"]
    m.cost = saved
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("old", "new"):
        ap.add_argument(f"--{k}-prices", required=True)
        ap.add_argument(f"--{k}-universe", required=True)
    ap.add_argument("--out", default="reports/conservative")
    ap.add_argument("--us-flip", required=True)
    ap.add_argument("--us-etf", required=True)
    ap.add_argument("--us-strategies", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vix = pd.read_parquet(Path(args.new_prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    uo, un = pd.read_csv(args.old_universe), pd.read_csv(args.new_universe)
    old = load(Path(args.old_prices), uo, vix, ASIA + WEST)
    new = load(Path(args.new_prices), un, vix, [k for k in dict.fromkeys(un["market"]) if k not in NO_BORROW])
    sleeves = {}
    for mult in (1.0, 2.0):
        o = {k: flat_series(m, mult) for k, m in old.items()}
        n = {k: flat_series(m, mult) for k, m in new.items()}
        sleeves[f"intl35_costs_x{mult:g}"] = equal_risk(pd.DataFrame({**o, **n}))
        sleeves[f"orig21_costs_x{mult:g}"] = equal_risk(pd.DataFrame(o))
        sleeves[f"new14_costs_x{mult:g}"] = equal_risk(pd.DataFrame(n))
    us_flip = pd.read_csv(args.us_flip, index_col=0, parse_dates=True).iloc[:, 0]
    etf = pd.read_csv(args.us_etf, index_col=0, parse_dates=True)["all 8 sleeves"]
    strat = pd.read_csv(args.us_strategies, index_col=0, parse_dates=True)
    v = vix.reindex(etf.index, method="ffill")
    B = pd.DataFrame({"etf": etf,
                      "pairs2": strat["pairs"].reindex(etf.index).fillna(0) * (1 + (v.shift(2) > 20).astype(float)),
                      "us_flip": us_flip.reindex(etf.index).fillna(0),
                      **{k: s.reindex(etf.index).fillna(0) for k, s in sleeves.items()}})
    rows = [L.period_stats(s, f"sleeve alone: {k}") for k, s in sleeves.items()]
    for label, cols in (("US book", ["etf", "pairs2", "us_flip"]),
                        ("US + original 21 (costs x2)", ["etf", "pairs2", "us_flip", "orig21_costs_x2"]),
                        ("US + original 21 + 14 borrowable new, separate sleeves (costs x1)", ["etf", "pairs2", "us_flip", "orig21_costs_x1", "new14_costs_x1"]),
                        ("US + original 21 + 14 borrowable new, separate sleeves (costs x2)", ["etf", "pairs2", "us_flip", "orig21_costs_x2", "new14_costs_x2"]),
                        ("US + 35 markets as one sleeve (costs x2)", ["etf", "pairs2", "us_flip", "intl35_costs_x2"])):
        s = blend(B, cols)
        rows.append(L.period_stats(s, label, {"worst_month": float(s["2015":].resample("ME").sum().min())}))
    t = pd.DataFrame(rows)
    t.to_csv(out / "conservative_combo.csv", index=False)
    pd.DataFrame(sleeves).to_csv(out / "sleeves_daily.csv")
    pd.set_option("display.width", 250)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26", "worst_month"]
    print(t[[c for c in cols if c in t]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
