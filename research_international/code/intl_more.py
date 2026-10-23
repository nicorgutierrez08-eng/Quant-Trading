"""Second-layer international tests, on top of intl_lab.

* Universal rules that need no per-market choice: plain momentum, flip short
  in stress, and *flat* in stress (momentum weakens in stress in all 21
  markets, so stepping aside may be the robust version).
* Long-only versions hedged with the actual (cap-weighted) local index with a
  trailing beta, as an index future would hedge them, not with an
  equal-weighted basket.
* Costs doubled.
* Cross-market books (equal risk across markets): every rule, Asia-Pacific and
  Europe+Canada separately; the per-market choice made on 2006-14; block
  bootstrap and leave-one-market-out for the chosen book.
* Combination with the US book from research_night (ETF sleeves + pairs +
  US momentum flip).

    python research_international/code/intl_more.py --prices data/prices --universe data/universe.csv --out reports/intl_more \
        --us-flip <US staggered flip daily csv> --us-etf <multi_daily.csv> --us-strategies <strategy_returns.csv>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L

ASIA = ("Japan", "Hong Kong", "Hong Kong (H-shares)", "China", "Korea", "Taiwan", "Singapore", "Australia", "India",
        "Malaysia", "Thailand", "New Zealand")
WEST = ("UK", "Germany", "France", "Switzerland", "Netherlands", "Spain", "Italy", "Sweden", "Canada")


def equal_risk(R: pd.DataFrame) -> pd.Series:
    R = R.sort_index()
    R = R.groupby(R.index).last()
    vol = R.rolling(252, min_periods=126).std().shift(1)
    w = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
    return (w * R).sum(axis=1).where(w.notna().any(axis=1)).dropna()


def block_bootstrap(x: np.ndarray, block: int = 21, n: int = 4000, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    T = len(x)
    nb = int(np.ceil(T / block))
    starts = rng.integers(0, T - block, size=(n, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, :T]
    xs = x[idx]
    sr = xs.mean(1) / xs.std(1) * np.sqrt(252)
    return {"p5": float(np.percentile(sr, 5)), "p50": float(np.percentile(sr, 50)), "p95": float(np.percentile(sr, 95)),
            "p_below_0": float((sr < 0).mean())}


def market_books(m: L.Market, idx: pd.Series | None) -> dict[str, pd.Series]:
    sigs = m.signals()
    comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
    tr = m.tradable
    stress = m.vix > 20
    flip = pd.Series(np.where(stress, -1.0, 1.0), index=m.dates)
    flat = pd.Series(np.where(stress, 0.0, 1.0), index=m.dates)
    out = {}
    W_plain = L.staggered(m, comp, tr, None)
    W_flip = L.staggered(m, comp, tr, flip)
    W_flat = L.staggered(m, comp, tr, flat)
    for name, W in (("plain", W_plain), ("flip", W_flip), ("flat_in_stress", W_flat)):
        out[name] = L.pnl(W, m)["net"]
    cost_saved = m.cost
    m.cost = cost_saved * 2
    out["flip_costs_x2"] = L.pnl(W_flip, m)["net"]
    out["plain_costs_x2"] = L.pnl(W_plain, m)["net"]
    m.cost = cost_saved
    lo = L.long_only_flip(m, comp, tr, flip)
    lo_gross = L.pnl(lo, m)["net"]
    out["long_only_flip_ew_hedge"] = lo_gross - m.r1.where(tr).mean(axis=1)
    if idx is not None:
        ir = idx.reindex(m.dates).ffill().pct_change(fill_method=None).shift(-2)      # close t+1 -> t+2 ~ open-to-open window
        beta = (lo_gross.rolling(252, min_periods=126).cov(ir) / ir.rolling(252, min_periods=126).var()).shift(1).clip(0, 2)
        out["long_only_flip_index_hedge"] = (lo_gross - beta * ir).where(beta.notna())
        out["long_only_flip_unhedged"] = lo_gross
        out["index_buy_hold"] = ir
    return out


def stats_table(series: dict[str, pd.Series], label_prefix: str = "") -> pd.DataFrame:
    return pd.DataFrame([L.period_stats(s.dropna(), f"{label_prefix}{k}") for k, s in series.items()])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices")
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--out", default="reports/intl_more")
    ap.add_argument("--choice", default="reports/intl/market_choice.csv")
    ap.add_argument("--us-flip")
    ap.add_argument("--us-etf")
    ap.add_argument("--us-strategies")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    u = pd.read_csv(args.universe)
    series = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")
    vix = series["vol:US"].dropna()
    per_market, rows = {}, []
    for name in dict.fromkeys(u["market"]):
        p = Path(args.prices) / name.replace(" ", "_").replace("(", "").replace(")", "")
        m = L.Market(name, p, u[u["market"] == name], vix)
        idx = series.get(f"idx:{name}")
        books = market_books(m, idx.dropna() if idx is not None else None)
        per_market[name] = books
        t = stats_table(books)
        t.insert(0, "market", name)
        rows.append(t)
        print(f"{name:22s} plain {L._sharpe(books['plain']['2015':]):5.2f}  flip {L._sharpe(books['flip']['2015':]):5.2f}  "
              f"flat {L._sharpe(books['flat_in_stress']['2015':]):5.2f}  LO idx-hedged "
              f"{L._sharpe(books.get('long_only_flip_index_hedge', pd.Series(dtype=float))['2015':]) if 'long_only_flip_index_hedge' in books else float('nan'):5.2f}  (2015-26)")
    per = pd.concat(rows)
    per.to_csv(out / "per_market.csv", index=False)

    choice = pd.read_csv(args.choice, index_col=0)["chosen"]
    chosen = {k: ("flip" if "flip" in v else "plain") for k, v in choice.items()}
    agg_rows, agg_daily = [], {}

    def agg(label, R):
        s = equal_risk(R)
        agg_daily[label] = s
        agg_rows.append(L.period_stats(s, label, {"markets": R.shape[1]}))

    for region, members in (("all 21", ASIA + WEST), ("Asia-Pacific", ASIA), ("Europe + Canada", WEST)):
        for rule in ("plain", "flip", "flat_in_stress", "flip_costs_x2", "long_only_flip_index_hedge"):
            R = pd.DataFrame({mk: per_market[mk][rule] for mk in members if rule in per_market[mk]})
            agg(f"{region}: {rule}", R)
        R = pd.DataFrame({mk: per_market[mk][chosen[mk]] for mk in members if mk in chosen})
        agg(f"{region}: chosen per market on 2006-14", R)
        R2 = pd.DataFrame({mk: per_market[mk][chosen[mk] + "_costs_x2"] for mk in members if mk in chosen})
        agg(f"{region}: chosen on 2006-14, costs x2", R2)
    aggt = pd.DataFrame(agg_rows)
    aggt.to_csv(out / "cross_market.csv", index=False)
    pd.DataFrame(agg_daily).to_csv(out / "cross_market_daily.csv")

    # robustness of the chosen all-21 book
    sel = agg_daily["all 21: chosen per market on 2006-14"]
    boot = {per: block_bootstrap(sel[a:b].dropna().to_numpy()) for per, a, b in (("2006-14", "2006", "2014"), ("2015-26", "2015", "2026"),
                                                                                    ("2015-20", "2015", "2020"), ("2021-26", "2021", "2026"))}
    loo = []
    for drop in chosen:
        R = pd.DataFrame({mk: per_market[mk][chosen[mk]] for mk in chosen if mk != drop})
        s = equal_risk(R)
        loo.append({"dropped": drop, "sharpe_2015_26": L._sharpe(s["2015":]), "sharpe_2021_26": L._sharpe(s["2021":])})
    loo = pd.DataFrame(loo).sort_values("sharpe_2015_26")
    corr = pd.DataFrame({mk: per_market[mk][chosen[mk]] for mk in chosen})["2015":].corr()
    avg_corr = float(corr.where(~np.eye(len(corr), dtype=bool)).stack().mean())

    # combination with the US book
    combo_rows = []
    if args.us_flip and args.us_etf and args.us_strategies:
        us_flip = pd.read_csv(args.us_flip, index_col=0, parse_dates=True).iloc[:, 0]
        etf = pd.read_csv(args.us_etf, index_col=0, parse_dates=True)["all 8 sleeves"]
        strat = pd.read_csv(args.us_strategies, index_col=0, parse_dates=True)
        v = vix.reindex(etf.index, method="ffill")
        pairs2 = strat["pairs"].reindex(etf.index).fillna(0) * (1 + (v.shift(2) > 20).astype(float))
        intl = sel.reindex(etf.index).fillna(0)
        B = pd.DataFrame({"etf": etf, "pairs2": pairs2, "us_flip": us_flip.reindex(etf.index).fillna(0), "intl": intl})
        cmat = B["2015":].corr().round(2)

        def blend(cols, cap=0.25):
            X = B[cols]
            vol = X.rolling(756, min_periods=126).std()
            w = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
            for _ in range(5):
                w = w.clip(upper=cap)
                w = w.div(w.sum(axis=1), axis=0)
            bl = (w.shift(2) * X).sum(axis=1)
            real = bl.rolling(252, min_periods=126).std() * np.sqrt(252)
            return (bl * (0.10 / real).clip(0, 3).shift(2)).dropna()

        for label, cols in (("ETF sleeves alone", ["etf"]), ("US book: ETF + pairs x2 + US flip", ["etf", "pairs2", "us_flip"]),
                            ("US book + international momentum", ["etf", "pairs2", "us_flip", "intl"])):
            s = blend(cols)
            combo_rows.append(L.period_stats(s, label, {"worst_month": float(s["2015":].resample("ME").sum().min())}))
        combo = pd.DataFrame(combo_rows)
        combo.to_csv(out / "combined_with_us.csv", index=False)
        cmat.to_csv(out / "combined_correlations.csv")
    pd.set_option("display.width", 250)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26", "markets"]
    print("\n== cross-market books =="); print(aggt[cols].round(2).to_string(index=False))
    print("\n== bootstrap, chosen all-21 book =="); print(pd.DataFrame(boot).T.round(3).to_string())
    print(f"\naverage pairwise correlation of the 21 chosen market books (2015-26): {avg_corr:.3f}")
    print("\n== leave one market out (chosen book) =="); print(loo.round(2).to_string(index=False))
    if combo_rows:
        print("\n== combined with the US book =="); print(combo.round(3).to_string(index=False)); print(cmat.to_string())
    pd.DataFrame(boot).T.to_csv(out / "bootstrap_chosen.csv")
    loo.to_csv(out / "leave_one_out.csv", index=False)


if __name__ == "__main__":
    main()
