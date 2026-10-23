"""Asian financials: what is predictable about banks, insurers and brokers in Asia-Pacific?

Per-market financials universes are small (10-50 names), so this pools them:
every signal is z-scored *within each market's financials* (country-neutral),
and ICs are computed on the pooled cross-section of ~220 Asia-Pacific
financials each day. Three questions:

1. Stock selection within financials: rank IC of each signal (momentum,
   reversal, low vol, size, illiquidity...) at 5 and 21 days, by sub-period
   and in calm vs. stressed markets.
2. Sector timing: the equal-weighted financials of each market minus that
   market's equal-weighted universe, next 21 days, regressed on what is known
   today: VIX level and 1-month change, US 10y-3m term spread and its
   1-month change, the sector's own 12-month relative return. Fitted on
   2004-2014, scored on 2015-2026 (IC of predicted vs. realised relative
   return across markets and through time).
3. Books: the momentum flat-in-stress rule on pooled financials (country
   neutral), and a sector-timing book (long financials vs. market when the
   2004-14 model predicts outperformance) - net of local costs.

    python research_international/code/asia_financials.py --prices data/prices --universe data/universe.csv --out reports/asia_fin
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L

ASIA = ("Japan", "Hong Kong", "Hong Kong (H-shares)", "China", "Korea", "Taiwan", "Singapore", "Australia", "India",
        "Malaysia", "Thailand", "New Zealand")
SPLIT = "2015-01-01"


def pooled_panel(markets: dict[str, L.Market]) -> dict:
    """Stack each market's financials into one wide panel (union of dates, tickers are unique per market)."""
    sig_parts, r1_parts, fwd5, fwd21, trad, cost = {}, [], [], [], [], []
    names = None
    for mk, m in markets.items():
        fin_cols = m.tickers[m.financial.reindex(m.tickers).to_numpy()]
        if len(fin_cols) < 5:
            continue
        mask = m.tradable[fin_cols]
        sigs = m.signals()
        # re-z-score within the market's financials (country-neutral)
        for k, z in sigs.items():
            x = z[fin_cols].where(mask)
            x = x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1) + 1e-12, axis=0)
            sig_parts.setdefault(k, []).append(x)
        r1_parts.append(m.r1[fin_cols])
        o = m.open[fin_cols]
        f5 = (o.shift(-6) / o.shift(-1) - 1).where(mask)
        f21 = (o.shift(-22) / o.shift(-1) - 1).where(mask)
        # forward returns relative to the market's own financials average, so pooling compares like with like
        fwd5.append(f5.sub(f5.mean(axis=1), axis=0))
        fwd21.append(f21.sub(f21.mean(axis=1), axis=0))
        trad.append(mask)
        cost.append(m.cost[fin_cols])
        names = list(sigs)
    cat = lambda parts: pd.concat(parts, axis=1).sort_index()
    return {"sigs": {k: cat(v) for k, v in sig_parts.items()}, "r1": cat(r1_parts), "fwd5": cat(fwd5), "fwd21": cat(fwd21),
            "tradable": cat(trad).fillna(False).astype(bool), "cost": cat(cost), "names": names}


def selection_ics(P: dict, vix: pd.Series) -> pd.DataFrame:
    stress = vix.reindex(P["r1"].index, method="ffill") > 20
    rows = []
    for k, z in P["sigs"].items():
        for h, fwd in ((5, P["fwd5"]), (21, P["fwd21"])):
            ic = L.rank_ic(z, fwd, min_names=40)
            row = {"signal": k, "horizon": h, "ic_all": ic.mean(),
                   "t_all": ic.mean() / ic.std() * np.sqrt(ic.notna().sum() / h)}
            for tag, a, b in L.IC_PERIODS:
                row[f"ic_{tag}"] = ic[a:b].mean()
            row["ic_calm"], row["ic_stressed"] = ic[~stress].mean(), ic[stress].mean()
            rows.append(row)
    return pd.DataFrame(rows)


def pooled_books(P: dict, vix: pd.Series) -> pd.DataFrame:
    dates = P["r1"].index
    v = vix.reindex(dates, method="ffill")
    comp = sum(P["sigs"][s] for s in L.MOM) / len(L.MOM)

    class _M:  # minimal Market-like object for L.pnl
        pass

    m = _M()
    m.r1, m.cost = P["r1"].clip(-0.5, 0.5), P["cost"]
    rows = []
    for label, sign in (("pooled Asian financials: momentum, plain", None),
                        ("pooled Asian financials: momentum, flat in stress", pd.Series(np.where(v > 20, 0.0, 1.0), index=dates)),
                        ("pooled Asian financials: momentum, flip", pd.Series(np.where(v > 20, -1.0, 1.0), index=dates))):
        W = L.staggered(m, comp, P["tradable"], sign)
        rows.append(L.period_stats(L.pnl(W, m)["net"]["2004":], label))
    for k in ("rev_5d", "rev_21d", "low_vol", "size_proxy", "amihud"):
        W = L.staggered(m, P["sigs"][k], P["tradable"], None)
        rows.append(L.period_stats(L.pnl(W, m)["net"]["2004":], f"pooled Asian financials: {k}, plain"))
    return pd.DataFrame(rows)


def sector_timing(markets: dict[str, L.Market], macro: pd.DataFrame, vix: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Financials minus market, per Asia-Pacific market, on macro state known today."""
    recs = []
    daily = {}
    for mk, m in markets.items():
        fin = m.tradable & pd.DataFrame(np.repeat(m.financial.reindex(m.tickers).to_numpy()[None, :], len(m.dates), 0),
                                        index=m.dates, columns=m.tickers)
        if int(fin.sum(axis=1).median()) < 5:
            continue
        rel_daily = m.r1.where(fin).mean(axis=1) - m.r1.where(m.tradable).mean(axis=1)       # held over t+1 -> t+2
        rel_fwd21 = rel_daily[::-1].rolling(21).sum()[::-1]
        past = (m.ret.where(fin).mean(axis=1) - m.ret.where(m.tradable).mean(axis=1))
        x = pd.DataFrame({
            "vix": np.log(vix.reindex(m.dates, method="ffill")),
            "vix_chg_21d": np.log(vix.reindex(m.dates, method="ffill")).diff(21),
            "term": macro["term"].reindex(m.dates, method="ffill"),
            "term_chg_21d": macro["term"].reindex(m.dates, method="ffill").diff(21),
            "rate10y_chg_21d": macro["rate10y"].reindex(m.dates, method="ffill").diff(21),
            "sector_rel_12m": past.rolling(252, min_periods=200).sum(),
            "sector_rel_1m": past.rolling(21).sum(),
        })
        x["y"] = rel_fwd21
        x["market"] = mk
        recs.append(x.iloc[::21])                                   # non-overlapping monthly samples
        daily[mk] = (rel_daily, x.drop(columns=["y", "market"]))
    D = pd.concat(recs).dropna()
    feats = [c for c in D.columns if c not in ("y", "market")]
    tr = D[D.index < SPLIT]
    mu, sd = tr[feats].mean(), tr[feats].std()
    Z = (D[feats] - mu) / sd
    beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(int((D.index < SPLIT).sum())), Z[D.index < SPLIT]]), tr["y"], rcond=None)
    D["pred"] = beta[0] + Z.to_numpy() @ beta[1:]
    coef = pd.DataFrame({"feature": ["const"] + feats, "coef_per_sd_bp_per_month": np.round(beta * 1e4, 1)})
    rows = []
    for per, m_ in (("2004-14 (fit)", D.index < SPLIT), ("2015-26 (out of sample)", D.index >= SPLIT)):
        d = D[m_]
        rows.append({"period": per, "samples": len(d), "corr(pred, realised)": float(np.corrcoef(d["pred"], d["y"])[0, 1]),
                     "hit_rate": float((np.sign(d["pred"]) == np.sign(d["y"])).mean()),
                     "mean_rel_return_bp": float(d["y"].mean() * 1e4)})
    # univariate: does each feature alone predict the sector's relative return out of sample?
    uni = []
    for f in feats:
        for per, m_ in (("1st", D.index < SPLIT), ("2nd", D.index >= SPLIT)):
            d = D[m_]
            uni.append({"feature": f, "period": per, "corr": float(np.corrcoef(d[f], d["y"])[0, 1])})
    uni = pd.DataFrame(uni).pivot(index="feature", columns="period", values="corr")
    # timing book: in each market, long financials / short market when the model (2004-14 fit) predicts > 0
    books = {}
    for mk, (rel, x) in daily.items():
        z = (x[feats] - mu) / sd
        pred = beta[0] + z.to_numpy() @ beta[1:]
        pos = pd.Series(np.sign(pred), index=x.index).where(z.notna().all(axis=1))
        reb = np.zeros(len(pos), bool)
        reb[::21] = True
        pos = pos.where(pd.Series(reb, index=pos.index), np.nan).ffill()
        books[mk] = (pos * rel - pos.diff().abs().fillna(0) * 2 * 15e-4).dropna()        # ~15 bp a side on both legs
    R = pd.DataFrame(books)
    port = R.mean(axis=1).dropna()
    rows_b = [L.period_stats(port["2006":], "sector timing: long/short Asian financials vs their market (2004-14 model)")]
    always_long = pd.DataFrame({mk: rel for mk, (rel, _) in daily.items()}).mean(axis=1)
    rows_b.append(L.period_stats(always_long["2006":], "always long financials vs market (no timing)"))
    stress_only = pd.DataFrame({mk: rel * (vix.reindex(rel.index, method='ffill') > 20).astype(float).shift(0)
                                for mk, (rel, _) in daily.items()}).mean(axis=1)
    rows_b.append(L.period_stats(stress_only["2006":], "long financials vs market only when VIX > 20"))
    return pd.DataFrame(rows), coef, uni, pd.DataFrame(rows_b)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices")
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--macro", default=None, help="parquet with term and rate10y columns (Yahoo stand-ins from the US lab)")
    ap.add_argument("--out", default="reports/asia_fin")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    u = pd.read_csv(args.universe)
    series = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")
    vix = series["vol:US"].dropna()
    markets = {}
    for mk in ASIA:
        p = Path(args.prices) / mk.replace(" ", "_").replace("(", "").replace(")", "")
        markets[mk] = L.Market(mk, p, u[u["market"] == mk], vix)
    P = pooled_panel(markets)
    print(f"pooled Asian financials: {P['tradable'].shape[1]} names, median tradable 2015+ {int(P['tradable'].sum(axis=1)['2015':].median())}")
    ics = selection_ics(P, vix)
    books = pooled_books(P, vix)
    macro = pd.read_parquet(args.macro) if args.macro else None
    if macro is not None:
        macro = macro.rename(columns={"term_spread_10y3m": "term"})
        if "rate10y" not in macro:
            tnx = pd.read_parquet(Path(args.prices) / "_series" / "close.parquet").get("idx:US10Y")
            macro["rate10y"] = macro["term"] if tnx is None else tnx
        st, coef, uni, sbooks = sector_timing(markets, macro, vix)
    else:
        st = coef = uni = sbooks = None
    pd.set_option("display.width", 250)
    ics.to_csv(out / "financials_signal_ic.csv", index=False)
    books.to_csv(out / "financials_books.csv", index=False)
    print("\n== stock selection within Asian financials (pooled, country-neutral IC) ==")
    print(ics[["signal", "horizon", "ic_all", "t_all", "ic_2004_09", "ic_2010_14", "ic_2015_20", "ic_2021_26", "ic_calm", "ic_stressed"]].round(4).to_string(index=False))
    print("\n== books on pooled Asian financials =="); print(books[["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "maxdd_2015_26"]].round(2).to_string(index=False))
    if st is not None:
        st.to_csv(out / "sector_timing_fit.csv", index=False)
        coef.to_csv(out / "sector_timing_coef.csv", index=False)
        uni.to_csv(out / "sector_timing_univariate.csv")
        sbooks.to_csv(out / "sector_timing_books.csv", index=False)
        print("\n== sector timing: financials minus market, next 21 days =="); print(st.round(3).to_string(index=False))
        print(coef.to_string(index=False)); print(uni.round(3).to_string())
        print(sbooks[["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
