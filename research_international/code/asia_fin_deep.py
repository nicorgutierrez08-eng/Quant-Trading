"""Every listed Asia-Pacific financial (~1,340 names, 12 markets): what is predictable?

Builds on asia_financials.py (index members only, ~210 names) with the deep
screener universe from deep_universe.py, which carries each company's
industry. Industries are grouped into banks, insurance, capital markets
(brokers, asset managers, exchanges) and credit (consumer finance, leasing,
mortgage, conglomerates).

1. Stock selection, pooled across markets: rank ICs of every lab signal,
   z-scored within market (country-neutral) and within market x industry
   group (industry-neutral), for all names and for the liquid half only.
2. The strategy's momentum books on the deep universe: plain, flat in stress,
   flip, and long-only flat-in-stress hedged with the equal-weighted
   financials of the same markets. Liquid half only (the illiquid half is
   where survivor bias and cost errors are largest).
3. Industry momentum: market x industry-group baskets ranked on 12-1 month
   momentum (Moskowitz-Grinblatt), long the top third, short the bottom third.
4. Lead-lag (Hou 2007): do the large financials of a market's industry group
   lead its small ones? Signal for each non-large name = past 1- and 5-day
   return of its group's large-cap basket.
5. Rates: each group's return relative to its market's index members, next
   21 days, on local 10y yield changes, the local curve slope, US 10y
   changes, VIX and the group's own trend. Fit 2004-14, scored 2015-26.
   Also the contemporaneous rate betas by period: are they stable?

    python research_international/code/asia_fin_deep.py --fin-prices data2/prices_fin --fin-universe data2/universe_asia_financials.csv \
        --mkt-prices data/prices --mkt-universe data/universe.csv --macro data2/macro.parquet --out reports/asia_fin_deep
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L

MARKETS = ("Japan", "Korea", "Taiwan", "Hong Kong", "China", "India", "Indonesia", "Singapore", "Malaysia", "Thailand",
           "Australia", "New Zealand")
GROUP = {"Banks—Regional": "banks", "Banks—Diversified": "banks", "Insurance—Life": "insurance",
         "Insurance—Property & Casualty": "insurance", "Insurance—Diversified": "insurance", "Insurance—Reinsurance": "insurance",
         "Insurance—Specialty": "insurance", "Insurance Brokers": "insurance", "Capital Markets": "capital_markets",
         "Asset Management": "capital_markets", "Financial Data & Stock Exchanges": "capital_markets",
         "Credit Services": "credit", "Mortgage Finance": "credit", "Financial Conglomerates": "credit"}
# rate series per market; USD-pegged or missing-rate markets use US yields only
RATES = {"Japan": "JP", "Korea": "KR", "Australia": "AU", "New Zealand": "NZ", "India": "IN", "Indonesia": "ID", "China": "CN"}
SPLIT = "2015-01-01"


class Panel:
    """Market-like object over pooled columns (enough for L.staggered / L.pnl)."""

    def __init__(self, r1, cost):
        self.r1, self.cost = r1, cost


def zscore_within(z: pd.DataFrame, mask: pd.DataFrame, keys: pd.Series) -> pd.DataFrame:
    parts = []
    for _, cols in keys.groupby(keys).groups.items():
        x = z[list(cols)].where(mask[list(cols)])
        parts.append(x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1) + 1e-12, axis=0))
    return pd.concat(parts, axis=1)[z.columns]


def build(markets: dict[str, L.Market], groups: pd.Series):
    """Pooled panels: signals (country- and industry-neutral), forward returns relative to the market's financials,
    masks for all and for the liquid half (top half by 21-day median traded value within the market)."""
    sig_c, sig_i, r1, cost, trad, liquid, f5, f21, keys_c, keys_i = {}, {}, [], [], [], [], [], [], {}, {}
    for mk, m in markets.items():
        tr = m.tradable
        liq = tr & (m.adv.where(tr).rank(axis=1, pct=True) > 0.5)
        sigs = m.signals()
        g = groups.reindex(m.tickers).fillna("credit")
        # small groups (median < 4 tradable names) fold into the market's financials as a whole
        sizes = {k: int(tr[list(c)].sum(axis=1)["2010":].median()) for k, c in g.groupby(g).groups.items()}
        gi = g.map(lambda x: x if sizes.get(x, 0) >= 4 else "other")
        for k, z in sigs.items():
            sig_c.setdefault(k, []).append(z)                                  # lab z-scores are already within-market
            sig_i.setdefault(k, []).append(zscore_within(z, tr, gi))
        o = m.open
        a5 = (o.shift(-6) / o.shift(-1) - 1).where(tr)
        a21 = (o.shift(-22) / o.shift(-1) - 1).where(tr)
        f5.append(a5.sub(a5.mean(axis=1), axis=0))
        f21.append(a21.sub(a21.mean(axis=1), axis=0))
        r1.append(m.r1), cost.append(m.cost), trad.append(tr), liquid.append(liq)
        for t in m.tickers:
            keys_c[t], keys_i[t] = mk, f"{mk}|{gi[t]}"
    cat = lambda parts: pd.concat(parts, axis=1, sort=True)
    return {"sig_c": {k: cat(v) for k, v in sig_c.items()}, "sig_i": {k: cat(v) for k, v in sig_i.items()},
            "r1": cat(r1).clip(-0.5, 0.5), "cost": cat(cost), "tradable": cat(trad).fillna(False).astype(bool),
            "liquid": cat(liquid).fillna(False).astype(bool), "fwd5": cat(f5), "fwd21": cat(f21),
            "key_c": pd.Series(keys_c), "key_i": pd.Series(keys_i)}


def ics(P: dict, sigs: dict, mask: pd.DataFrame, vix: pd.Series, label: str) -> pd.DataFrame:
    stress = vix.reindex(P["r1"].index, method="ffill") > 20
    rows = []
    for k, z in sigs.items():
        for h, fwd in ((5, P["fwd5"]), (21, P["fwd21"])):
            ic = L.rank_ic(z.where(mask), fwd, min_names=50)
            row = {"universe": label, "signal": k, "horizon": h, "ic_all": ic.mean(),
                   "t_all": ic.mean() / ic.std() * np.sqrt(ic.notna().sum() / h)}
            for tag, a, b in L.IC_PERIODS:
                row[f"ic_{tag}"] = ic[a:b].mean()
            per = [row[f"ic_{t}"] for t, _, _ in L.IC_PERIODS]
            row["same_sign_all_4"] = bool(np.all(np.sign(per) == np.sign(per[0]))) and not np.any(np.isnan(per))
            row["ic_calm"], row["ic_stressed"] = ic[~stress].mean(), ic[stress].mean()
            rows.append(row)
    return pd.DataFrame(rows)


def momentum_books(P: dict, vix: pd.Series) -> pd.DataFrame:
    dates = P["r1"].index
    v = vix.reindex(dates, method="ffill")
    m = Panel(P["r1"], P["cost"])
    flat = pd.Series(np.where(v > 20, 0.0, 1.0), index=dates)
    flip = pd.Series(np.where(v > 20, -1.0, 1.0), index=dates)
    rows = []
    for nlabel, sigs in (("country-neutral", P["sig_c"]), ("industry-neutral", P["sig_i"])):
        comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
        for ulabel, mask in (("all names", P["tradable"]), ("liquid half", P["liquid"])):
            for rlabel, sign in (("plain", None), ("flat in stress", flat), ("flip", flip)):
                W = L.staggered(m, comp, mask, sign)
                rows.append(L.period_stats(L.pnl(W, m)["net"]["2004":], f"deep Asian financials, {nlabel}, {ulabel}: momentum {rlabel}"))
            # long-only flat in stress, minus the equal-weighted financials of the same mask (both legs survivors)
            lo = L.long_only_flip(m, comp, mask, flat)
            held = sum(L.held_sign(flat, k) for k in L.COHORTS) / len(L.COHORTS)
            ew = P["r1"].where(mask).mean(axis=1)
            s = L.pnl(lo, m)["net"] - ew * held
            rows.append(L.period_stats(s["2004":], f"deep Asian financials, {nlabel}, {ulabel}: long-only flat in stress, EW-hedged"))
        for k in ("rev_5d", "rev_21d", "low_vol", "low_beta", "size_proxy", "amihud", "max_effect"):
            W = L.staggered(m, sigs[k], P["liquid"], None)
            rows.append(L.period_stats(L.pnl(W, m)["net"]["2004":], f"deep Asian financials, {nlabel}, liquid half: {k}"))
    return pd.DataFrame(rows)


def group_returns(P: dict, mask: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Equal-weighted market x group baskets: held return (r1), cost, past daily return, member count."""
    r1, cost, n = {}, {}, {}
    for key, cols in P["key_i"].groupby(P["key_i"]).groups.items():
        if key.endswith("|other"):
            continue
        cols = list(cols)
        mk = mask[cols]
        r1[key] = P["r1"][cols].where(mk).mean(axis=1)
        cost[key] = P["cost"][cols].where(mk).mean(axis=1)
        n[key] = mk.sum(axis=1)
    return pd.DataFrame(r1), pd.DataFrame(cost), pd.DataFrame(n)


def industry_momentum(P: dict, vix: pd.Series) -> pd.DataFrame:
    r1, cost, n = group_returns(P, P["liquid"])
    # past daily basket return realised by close t: r1 at t-2 covers open t-1 -> open t, close enough for a 12-1 month signal
    past = r1.shift(2)
    mom = np.log1p(past.fillna(0)).rolling(231, min_periods=200).sum().shift(21).where(n >= 3)
    z = mom.sub(mom.mean(axis=1), axis=0).div(mom.std(axis=1) + 1e-12, axis=0)
    mask = (n >= 3) & z.notna()
    # cost of rebalancing a basket ~ its members' average one-way cost
    m = Panel(r1.fillna(0), cost.fillna(cost.stack().median()))
    v = vix.reindex(r1.index, method="ffill")
    flat = pd.Series(np.where(v > 20, 0.0, 1.0), index=r1.index)
    rows = []
    for label, sign, frac in (("industry momentum (market x group), all baskets", None, None),
                              ("industry momentum, top vs bottom third", None, 1 / 3),
                              ("industry momentum, top vs bottom third, flat in stress", flat, 1 / 3)):
        W = L.staggered(m, z, mask, sign, frac)
        rows.append(L.period_stats(L.pnl(W, m)["net"]["2004":], label, {"median_baskets": int(mask.sum(axis=1)["2010":].median())}))
    return pd.DataFrame(rows)


def lead_lag(P: dict, vix: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Big financials lead small ones? Signal for non-large names = large-cap basket's past return (same market x group)."""
    tr = P["tradable"]
    big_parts, small_mask_parts = [], []
    sig1, sig5 = {}, {}
    adv_rank = {}
    for key, cols in P["key_i"].groupby(P["key_i"]).groups.items():
        cols = list(cols)
        if len(cols) < 6:
            continue
        # size by traded value: the lab's size_proxy z is -log(adv); larger adv -> more negative size_proxy
        size = -P["sig_c"]["size_proxy"][cols].where(tr[cols])
        pct = size.rank(axis=1, pct=True)
        big = pct > 2 / 3
        r = P["r1"][cols].shift(2)                        # realised by the open of t, known at t
        big_r = r.where(big.shift(2, fill_value=False)).mean(axis=1)
        b5 = np.log1p(big_r).rolling(5).sum()
        own5 = np.log1p(r).rolling(5).sum()
        small = (pct <= 2 / 3) & tr[cols]
        sig1[key] = pd.DataFrame(np.repeat(big_r.to_numpy()[:, None], len(cols), 1), index=r.index, columns=cols).where(small)
        sig5[key] = (pd.DataFrame(np.repeat(b5.to_numpy()[:, None], len(cols), 1), index=r.index, columns=cols) - own5).where(small)
    s1 = pd.concat(sig1.values(), axis=1, sort=True)
    s5 = pd.concat(sig5.values(), axis=1, sort=True)
    mask = s5.notna()
    # z-score within market (country-neutral) before pooling
    def zc(x):
        k = P["key_c"].reindex(x.columns)
        return zscore_within(x, x.notna(), k)
    sigs = {"lead_big_1d": zc(s1), "lead_big_minus_own_5d": zc(s5)}
    fwd = {"fwd5": P["fwd5"].reindex(columns=s5.columns), "fwd21": P["fwd21"].reindex(columns=s5.columns)}
    Q = {**P, **fwd, "r1": P["r1"].reindex(columns=s5.columns)}
    ic = ics(Q, sigs, mask, vix, "non-large financials")
    m = Panel(P["r1"].reindex(columns=s5.columns), P["cost"].reindex(columns=s5.columns))
    rows = []
    for k, z in sigs.items():
        W = L.staggered(m, z, mask, None)
        rows.append(L.period_stats(L.pnl(W, m)["net"]["2004":], f"lead-lag book (21-day hold): {k}"))
    return ic, pd.DataFrame(rows)


def rates(markets: dict[str, L.Market], broad: dict[str, L.Market], groups: pd.Series, macro: pd.DataFrame,
          vix: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    recs, betas = [], []
    us10 = macro["us10y"]
    for mk, m in markets.items():
        if mk not in broad:
            continue
        b = broad[mk]
        mkt_r1 = b.r1.where(b.tradable).mean(axis=1).reindex(m.dates)
        mkt_ret = b.ret.where(b.tradable).mean(axis=1).reindex(m.dates)
        liq = m.tradable & (m.adv.where(m.tradable).rank(axis=1, pct=True) > 0.5)
        g = groups.reindex(m.tickers).fillna("credit")
        cc = RATES.get(mk)
        lt = macro.get(f"lt:{cc}") if cc else None
        st = macro.get(f"st:{cc}") if cc else None
        d = m.dates
        u10 = us10.reindex(d, method="ffill")
        for grp in ("banks", "insurance", "capital_markets"):
            cols = list(g.index[g == grp])
            if len(cols) < 4 or int(liq[cols].sum(axis=1)["2010":].median()) < 3:
                continue
            rel_r1 = m.r1[cols].where(liq[cols]).mean(axis=1) - mkt_r1
            rel_ret = m.ret[cols].where(liq[cols]).mean(axis=1) - mkt_ret
            y = rel_r1[::-1].rolling(21).sum()[::-1]
            x = pd.DataFrame({
                "us10y_chg_21d": u10.diff(21), "us10y_chg_63d": u10.diff(63),
                "local10y_chg_63d": lt.reindex(d, method="ffill").diff(63) if lt is not None else np.nan,
                "local_slope": (lt - st).reindex(d, method="ffill") if (lt is not None and st is not None) else np.nan,
                "log_vix": np.log(vix.reindex(d, method="ffill")),
                "rel_12m": rel_ret.rolling(252, min_periods=200).sum(), "rel_1m": rel_ret.rolling(21).sum(),
            }, index=d)
            x["y"], x["market"], x["group"] = y, mk, grp
            recs.append(x.iloc[::21])
            # contemporaneous sensitivity of the group's relative return to US 10y moves (21-day, non-overlapping)
            dy = u10.diff(21).iloc[::21]
            rr = rel_ret.rolling(21).sum().iloc[::21]
            for tag, a, bb in L.IC_PERIODS:
                xx, yy = dy[a:bb], rr[a:bb]
                ok = xx.notna() & yy.notna()
                if ok.sum() > 20:
                    betas.append({"market": mk, "group": grp, "period": tag,
                                  "rel_return_per_100bp_us10y": float(np.polyfit(xx[ok], yy[ok], 1)[0])})
    D = pd.concat(recs)
    feats = ["us10y_chg_21d", "us10y_chg_63d", "local10y_chg_63d", "local_slope", "log_vix", "rel_12m", "rel_1m"]
    uni, model_rows, books = [], [], {}
    for grp, G in D.groupby("group"):
        G = G.dropna(subset=["y"])
        for f in feats:
            a = G[G.index < SPLIT][[f, "y"]].dropna()
            b_ = G[G.index >= SPLIT][[f, "y"]].dropna()
            uni.append({"group": grp, "feature": f, "corr_2004_14": a.corr().iloc[0, 1] if len(a) > 30 else np.nan,
                        "corr_2015_26": b_.corr().iloc[0, 1] if len(b_) > 30 else np.nan, "n_fit": len(a), "n_test": len(b_)})
        # pooled linear model on features available everywhere (local-rate features are missing for USD-linked markets)
        fs = ["us10y_chg_21d", "us10y_chg_63d", "log_vix", "rel_12m", "rel_1m"]
        H = G.dropna(subset=fs)
        tr, te = H[H.index < SPLIT], H[H.index >= SPLIT]
        mu, sd = tr[fs].mean(), tr[fs].std()
        X = np.column_stack([np.ones(len(tr)), (tr[fs] - mu) / sd])
        beta, *_ = np.linalg.lstsq(X, tr["y"], rcond=None)
        pred = beta[0] + ((te[fs] - mu) / sd).to_numpy() @ beta[1:]
        yc = te["y"] - te["y"].mean()                   # remove the period's average (survivor drift) to judge timing alone
        model_rows.append({"group": grp, "n_test": len(te), "corr_pred_realised": float(np.corrcoef(pred, te["y"])[0, 1]),
                           "corr_pred_demeaned": float(np.corrcoef(pred - pred.mean(), yc)[0, 1]),
                           "hit_rate_vs_median": float(((pred > np.median(pred)) == (te["y"] > te["y"].median())).mean()),
                           **{f"coef_{f}": round(float(c) * 1e4, 1) for f, c in zip(fs, beta[1:])}})
        books[grp] = pd.Series(np.sign(pred - np.median(pred)) * te["y"].to_numpy(), index=te.index)
    timing = pd.DataFrame([{"group": g, "mean_monthly_bp": float(s.mean() * 1e4),
                            "sharpe_monthly_annualised": float(s.mean() / s.std() * np.sqrt(12)) if s.std() > 0 else np.nan,
                            "months": len(s)} for g, s in books.items()])
    return pd.DataFrame(uni), pd.DataFrame(model_rows), pd.DataFrame(betas), timing


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin-prices", required=True)
    ap.add_argument("--fin-universe", required=True)
    ap.add_argument("--mkt-prices", required=True)
    ap.add_argument("--mkt-universe", required=True)
    ap.add_argument("--macro", required=True)
    ap.add_argument("--out", default="reports/asia_fin_deep")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fu = pd.read_csv(args.fin_universe)
    groups = fu.set_index("ticker")["industry"].map(GROUP)
    vix = pd.read_parquet(Path(args.fin_prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    macro = pd.read_parquet(args.macro)
    fin, broad = {}, {}
    mu = pd.read_csv(args.mkt_universe)
    for mk in MARKETS:
        p = Path(args.fin_prices) / mk.replace(" ", "_")
        if (p / "adj_close.parquet").exists() and (fu["market"] == mk).sum() >= 15:     # New Zealand (9 names) is too small
            fin[mk] = L.Market(mk, p, fu[fu["market"] == mk], vix)
        q = Path(args.mkt_prices) / mk.replace(" ", "_")
        if (q / "adj_close.parquet").exists():
            broad[mk] = L.Market(mk, q, mu[mu["market"] == mk], vix)
    cover = pd.DataFrame([{"market": k, "names_with_prices": len(m.tickers),
                           "median_tradable_2015_26": int(m.tradable.sum(axis=1)["2015":].median()),
                           "median_tradable_2006_14": int(m.tradable.sum(axis=1)["2006":"2014"].median())} for k, m in fin.items()])
    cover.to_csv(out / "coverage.csv", index=False)
    pd.set_option("display.width", 250)
    print(cover.to_string(index=False))

    P = build(fin, groups)
    ic = pd.concat([ics(P, P["sig_c"], P["tradable"], vix, "all, country-neutral"),
                    ics(P, P["sig_i"], P["tradable"], vix, "all, industry-neutral"),
                    ics(P, P["sig_i"], P["liquid"], vix, "liquid half, industry-neutral")])
    ic.to_csv(out / "selection_ic.csv", index=False)
    print("\n== stock selection ICs (21-day) ==")
    print(ic[ic["horizon"] == 21].drop(columns="horizon").round(4).to_string(index=False))

    mb = momentum_books(P, vix)
    mb.to_csv(out / "books.csv", index=False)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "maxdd_2015_26"]
    print("\n== books =="); print(mb[cols].round(2).to_string(index=False))

    im = industry_momentum(P, vix)
    im.to_csv(out / "industry_momentum.csv", index=False)
    print("\n== industry momentum =="); print(im[cols + ["median_baskets"]].round(2).to_string(index=False))

    ll_ic, ll_b = lead_lag(P, vix)
    ll_ic.to_csv(out / "lead_lag_ic.csv", index=False)
    ll_b.to_csv(out / "lead_lag_books.csv", index=False)
    print("\n== lead-lag =="); print(ll_ic.round(4).to_string(index=False)); print(ll_b[cols].round(2).to_string(index=False))

    uni, model, betas, timing = rates(fin, broad, groups, macro, vix)
    uni.to_csv(out / "rates_univariate.csv", index=False)
    model.to_csv(out / "rates_model.csv", index=False)
    betas.to_csv(out / "rate_betas.csv", index=False)
    timing.to_csv(out / "rates_timing.csv", index=False)
    print("\n== rates: univariate correlation with next-21-day group-minus-market return =="); print(uni.round(3).to_string(index=False))
    print("\n== rates: pooled model, out of sample =="); print(model.round(3).to_string(index=False))
    print(timing.round(2).to_string(index=False))
    bt = betas.pivot_table(index=["group", "market"], columns="period", values="rel_return_per_100bp_us10y")
    print("\n== relative return per +100bp in the US 10y (21-day windows), by period =="); print(bt.round(3).to_string())
    bt.to_csv(out / "rate_betas_wide.csv")


if __name__ == "__main__":
    main()
