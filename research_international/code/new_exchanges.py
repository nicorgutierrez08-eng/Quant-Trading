"""Out-of-sample test of the international rule on 20 exchanges it was not built on.

The rule (momentum composite, 21-day rebalance, staggered cohorts, next-open
execution, local costs, no position while the US VIX is above 20) was chosen
on 21 markets. This script applies it unchanged to 20 new exchanges and
checks the three predictions written into LOG.md before it was run:

1. momentum's IC is lower in stress than in calm in at least 14 of 20;
2. the equal-risk flat-in-stress book over the 20 is positive in 2015-20 and
   in 2021-26;
3. it beats the never-flipped book over 2015-26.

It then pools old and new markets (41) and blends that with the US book
exactly as intl_more.py does.

    python research_international/code/new_exchanges.py --prices data2/prices_new --universe data2/universe_new_markets.csv \
        --old-prices data/prices --old-universe data/universe.csv --out reports/new_exchanges \
        --us-flip <US flip daily> --us-etf <multi_daily.csv> --us-strategies <strategy_returns.csv>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from intl_more import ASIA, WEST, block_bootstrap, equal_risk, market_books, stats_table

NEW_EM = ("Indonesia", "Vietnam", "Pakistan", "Brazil", "Mexico", "Chile", "South Africa", "Turkey", "Saudi Arabia",
          "Kuwait", "Qatar", "Poland", "Greece")
NEW_DEV = ("Israel", "Norway", "Denmark", "Finland", "Belgium", "Austria", "Portugal")
RULES = ("plain", "flip", "flat_in_stress", "plain_costs_x2", "flip_costs_x2", "flat_in_stress_costs_x2",
         "long_only_flip_ew_hedge", "long_only_flat_ew_hedge")


def load(prices: Path, universe: pd.DataFrame, vix: pd.Series, names) -> dict[str, L.Market]:
    out = {}
    for name in names:
        p = prices / name.replace(" ", "_").replace("(", "").replace(")", "")
        if not (p / "adj_close.parquet").exists():
            print(f"{name}: no prices")
            continue
        try:
            out[name] = L.Market(name, p, universe[universe["market"] == name], vix)
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: FAILED {type(exc).__name__}: {exc}")
    return out


def momentum_ic_by_regime(m: L.Market, sigs: dict) -> dict:
    t = L.ic_table(m, {k: sigs[k] for k in L.MOM}, 21)
    return {"market": m.name, "ic_calm": float(t["ic_calm"].mean()), "ic_stressed": float(t["ic_stressed"].mean()),
            "ic_all": float(t["ic_all"].mean())}


def threshold_books(m: L.Market, comp: pd.DataFrame, level: float) -> pd.Series:
    """Robustness only (not pre-registered): flat-in-stress with a different VIX trigger."""
    flat = pd.Series(np.where(m.vix > level, 0.0, 1.0), index=m.dates)
    return L.pnl(L.staggered(m, comp, m.tradable, flat), m)["net"]


def blend(B: pd.DataFrame, cols: list[str], cap: float = 0.25) -> pd.Series:
    """Same construction as intl_more: inverse-vol sleeves, 25% cap, 10% vol target, 2-day lags."""
    X = B[cols]
    vol = X.rolling(756, min_periods=126).std()
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
    for _ in range(5):
        w = w.clip(upper=cap)
        w = w.div(w.sum(axis=1), axis=0)
    bl = (w.shift(2) * X).sum(axis=1)
    real = bl.rolling(252, min_periods=126).std() * np.sqrt(252)
    return (bl * (0.10 / real).clip(0, 3).shift(2)).dropna()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--old-prices")
    ap.add_argument("--old-universe")
    ap.add_argument("--out", default="reports/new_exchanges")
    ap.add_argument("--us-flip")
    ap.add_argument("--us-etf")
    ap.add_argument("--us-strategies")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    u = pd.read_csv(args.universe)
    vix = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    markets = load(Path(args.prices), u, vix, dict.fromkeys(u["market"]))

    per, rows, ics, thresh = {}, [], [], []
    for name, m in markets.items():
        sigs = m.signals()
        comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
        books = market_books(m, None)
        per[name] = books
        t = stats_table(books)
        t.insert(0, "market", name)
        t["median_names"] = int(m.tradable.sum(axis=1)["2015":].median())
        t["first_year"] = int(m.tradable.any(axis=1).idxmax().year)
        rows.append(t)
        ics.append(momentum_ic_by_regime(m, sigs))
        for lvl in (17.5, 25, 30):
            thresh.append({"market": name, "vix_level": lvl, "series": threshold_books(m, comp, lvl)})
        print(f"{name:14s} names {t['median_names'].iloc[0]:4d} from {t['first_year'].iloc[0]}  "
              f"plain {L._sharpe(books['plain']['2015':]):5.2f}  flip {L._sharpe(books['flip']['2015':]):5.2f}  "
              f"flat {L._sharpe(books['flat_in_stress']['2015':]):5.2f}  (2015-26)")
    per_t = pd.concat(rows)
    per_t.to_csv(out / "per_market.csv", index=False)
    ic = pd.DataFrame(ics).set_index("market")
    ic["weaker_in_stress"] = ic["ic_stressed"] < ic["ic_calm"]
    ic["negative_in_stress"] = ic["ic_stressed"] < 0
    ic.to_csv(out / "momentum_ic_by_regime.csv")

    agg_rows, daily = [], {}

    def agg(label, R):
        s = equal_risk(R)
        daily[label] = s
        agg_rows.append(L.period_stats(s, label, {"markets": R.shape[1]}))

    groups = (("20 new exchanges", tuple(markets)), ("new emerging", NEW_EM), ("new developed", NEW_DEV))
    for g, members in groups:
        for rule in RULES:
            R = pd.DataFrame({k: per[k][rule] for k in members if k in per})
            agg(f"{g}: {rule}", R)
    for lvl in (17.5, 25, 30):
        R = pd.DataFrame({x["market"]: x["series"] for x in thresh if x["vix_level"] == lvl})
        agg(f"20 new exchanges: flat when VIX > {lvl} (robustness, not pre-registered)", R)

    # the 41-market book: old markets rebuilt with the same code
    if args.old_prices and args.old_universe:
        uo = pd.read_csv(args.old_universe)
        old = load(Path(args.old_prices), uo, vix, ASIA + WEST)
        old_per = {k: market_books(m, None) for k, m in old.items()}
        for rule in ("flat_in_stress", "flat_in_stress_costs_x2", "long_only_flat_ew_hedge"):
            agg(f"original 21: {rule}", pd.DataFrame({k: v[rule] for k, v in old_per.items()}))
            agg(f"all 41: {rule}", pd.DataFrame({**{k: v[rule] for k, v in old_per.items()}, **{k: v[rule] for k, v in per.items()}}))
        asia_new = ("Indonesia", "Vietnam", "Pakistan")
        agg("Asia-Pacific incl. Indonesia, Vietnam, Pakistan: flat_in_stress",
            pd.DataFrame({**{k: old_per[k]["flat_in_stress"] for k in ASIA if k in old_per},
                          **{k: per[k]["flat_in_stress"] for k in asia_new if k in per}}))
        corr = pd.DataFrame({k: v["flat_in_stress"] for k, v in per.items()})["2015":].corr()
        cross = pd.concat([pd.DataFrame({k: v["flat_in_stress"] for k, v in old_per.items()}).pipe(equal_risk).rename("old"),
                           daily["20 new exchanges: flat_in_stress"].rename("new")], axis=1)["2015":].corr().iloc[0, 1]
        print(f"\ncorrelation of the old-21 and new-20 flat books (2015-26): {cross:.2f}; "
              f"average pairwise among the 20 new: {corr.where(~np.eye(len(corr), dtype=bool)).stack().mean():.2f}")

    aggt = pd.DataFrame(agg_rows)
    aggt.to_csv(out / "cross_market.csv", index=False)
    pd.DataFrame(daily).to_csv(out / "cross_market_daily.csv")

    pers = (("2006-14", "2006", "2014"), ("2015-20", "2015", "2020"), ("2021-26", "2021", "2026"), ("2015-26", "2015", "2026"))
    boot = {}
    for label in ("20 new exchanges: flat_in_stress", "new emerging: flat_in_stress", "new developed: flat_in_stress",
                  "all 41: flat_in_stress"):
        if label in daily:
            for p, a, b in pers:
                x = daily[label][a:b].dropna().to_numpy()
                if len(x) > 250:
                    boot[(label, p)] = block_bootstrap(x)
    boot = pd.DataFrame(boot).T
    boot.to_csv(out / "bootstrap.csv")

    loo = []
    for drop in per:
        s = equal_risk(pd.DataFrame({k: v["flat_in_stress"] for k, v in per.items() if k != drop}))
        loo.append({"dropped": drop, "flat_2015_26": L._sharpe(s["2015":]), "flat_2021_26": L._sharpe(s["2021":])})
    loo = pd.DataFrame(loo).sort_values("flat_2015_26")
    loo.to_csv(out / "leave_one_out.csv", index=False)

    combo = None
    if args.us_flip and args.us_etf and args.us_strategies and "all 41: flat_in_stress" in daily:
        us_flip = pd.read_csv(args.us_flip, index_col=0, parse_dates=True).iloc[:, 0]
        etf = pd.read_csv(args.us_etf, index_col=0, parse_dates=True)["all 8 sleeves"]
        strat = pd.read_csv(args.us_strategies, index_col=0, parse_dates=True)
        v = vix.reindex(etf.index, method="ffill")
        B = pd.DataFrame({"etf": etf,
                          "pairs2": strat["pairs"].reindex(etf.index).fillna(0) * (1 + (v.shift(2) > 20).astype(float)),
                          "us_flip": us_flip.reindex(etf.index).fillna(0),
                          "intl21": daily["original 21: flat_in_stress"].reindex(etf.index).fillna(0),
                          "new20": daily["20 new exchanges: flat_in_stress"].reindex(etf.index).fillna(0),
                          "intl41": daily["all 41: flat_in_stress"].reindex(etf.index).fillna(0)})
        rows = []
        for label, cols in (("US book", ["etf", "pairs2", "us_flip"]),
                            ("US book + original 21 (flat)", ["etf", "pairs2", "us_flip", "intl21"]),
                            ("US book + original 21 + new 20 as separate sleeves", ["etf", "pairs2", "us_flip", "intl21", "new20"]),
                            ("US book + all 41 as one sleeve", ["etf", "pairs2", "us_flip", "intl41"])):
            s = blend(B, cols)
            rows.append(L.period_stats(s, label, {"worst_month": float(s["2015":].resample("ME").sum().min())}))
        combo = pd.DataFrame(rows)
        combo.to_csv(out / "combined_with_us.csv", index=False)
        B["2015":].corr().round(2).to_csv(out / "combined_correlations.csv")

    pd.set_option("display.width", 250)
    print("\n== momentum IC by regime, new exchanges ==")
    print(ic.round(4).to_string())
    print(f"weaker in stress: {int(ic['weaker_in_stress'].sum())}/{len(ic)}; negative in stress: {int(ic['negative_in_stress'].sum())}/{len(ic)}")
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26", "markets"]
    print("\n== cross-market books ==")
    print(aggt[cols].round(2).to_string(index=False))
    print("\n== bootstrap ==")
    print(boot.round(3).to_string())
    print("\n== leave one out ==")
    print(loo.round(2).to_string(index=False))
    if combo is not None:
        print("\n== combined with the US book ==")
        print(combo.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
