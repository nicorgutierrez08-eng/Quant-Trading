"""South America: the pre-registered test of the flat-in-stress rule, the New York ADR route, financials,
commodity lead-lag, and the combined book (predictions in LOG.md).

Markets: Brazil (296 largest companies), Chile, Argentina, Colombia (COLCAP), Peru (S&P/BVL Peru General),
and the 58 South American companies listed in New York as one cross-section.

1. Per market: momentum IC calm vs stress; plain / flip / flat books; costs x2 and x3; liquid half; one day
   late; long and short legs; data quality.
2. Equal-risk aggregates: the 5 local markets, the 3 fresh ones (Argentina, Colombia, Peru); Brazil broad vs
   its 120 largest; bootstrap and leave-one-out.
3. The ADR book: pooled and country-neutral, L/S and long-only (EW-hedged).
4. South American financials, pooled and country-neutral: ICs and books (descriptive; no prediction).
5. Commodity lead-lag: does a stock's commodity-implied move predict it? Trailing 252-day betas to copper,
   oil, gold, silver, soybeans, coffee and sugar futures (estimated on data up to the day before), times the
   commodities' 1-day and 5-day returns, with and without the stock's own 5-day return subtracted.
6. Combined with the US book and the international sleeves from conservative_combo.py.

    python research_international/code/south_america.py --prices data_sa/prices --universe data_sa/universe_south_america.csv \
        --adr-prices data_sa/prices_adr --adr-universe data_sa/universe_sa_adrs.csv \
        --fin-prices data_sa/prices_fin --fin-universe data_sa/universe_sa_financials.csv \
        --brazil120-prices data2/prices_new --macro data2/macro.parquet --intl-sleeves reports/conservative/sleeves_daily.csv \
        --us-flip <US flip daily> --us-etf <multi_daily.csv> --us-strategies <strategy_returns.csv> --out reports/south_america
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

import intl_lab as L
from asia_fin_deep import GROUP, Panel, build, zscore_within
from intl_more import block_bootstrap, equal_risk, held_flat, market_books
from new_exchanges import blend, load, momentum_ic_by_regime
from new_exchanges_robust import legs, quality

warnings.filterwarnings("ignore")

LOCAL = ("Brazil", "Chile", "Argentina", "Colombia", "Peru")
FRESH = ("Argentina", "Colombia", "Peru")
COMMODITIES = {"copper": "HG=F", "oil": "CL=F", "gold": "GC=F", "silver": "SI=F", "soybeans": "ZS=F", "coffee": "KC=F", "sugar": "SB=F"}
PERS = (("2006-14", "2006", "2014"), ("2015-20", "2015", "2020"), ("2021-26", "2021", "2026"))


def flat_sign(m) -> pd.Series:
    return pd.Series(np.where(m.vix > 20, 0.0, 1.0), index=m.dates)


def books_for(m: L.Market, comp: pd.DataFrame | None = None, mask: pd.DataFrame | None = None) -> dict[str, pd.Series]:
    """market_books plus the robustness variants used for the new exchanges."""
    sigs = m.signals()
    comp = comp if comp is not None else sum(sigs[s] for s in L.MOM) / len(L.MOM)
    mask = mask if mask is not None else m.tradable
    stress = m.vix > 20
    flat = flat_sign(m)
    flip = pd.Series(np.where(stress, -1.0, 1.0), index=m.dates)
    liquid = mask & (m.adv.where(mask).rank(axis=1, pct=True) > 0.5)
    b = {}
    for name, sign in (("plain", None), ("flip", flip), ("flat", flat)):
        b[name] = L.pnl(L.staggered(m, comp, mask, sign), m)["net"]
    b["flat_liquid_half"] = L.pnl(L.staggered(m, comp, liquid, flat), m)["net"]
    b["flat_one_day_late"] = L.pnl(L.staggered(m, comp.shift(1), mask, flat.shift(1).fillna(1.0)), m)["net"]
    saved = m.cost
    for mult in (2, 3):
        m.cost = saved * mult
        b[f"flat_costs_x{mult}"] = L.pnl(L.staggered(m, comp, mask, flat), m)["net"]
        b[f"plain_costs_x{mult}"] = L.pnl(L.staggered(m, comp, mask, None), m)["net"]
    m.cost = saved
    ew = m.r1.where(mask).mean(axis=1)
    b["long_only_flat_ew_hedge"] = L.pnl(L.long_only_flip(m, comp, mask, flat), m)["net"] - ew * held_flat(flat)
    b.update(legs(m, comp, mask, flat))
    return b


def commodity_lead_lag(markets: dict[str, L.Market], vix: pd.Series) -> pd.DataFrame:
    px = yf.download(list(COMMODITIES.values()), start="2000-01-01", progress=False, auto_adjust=False)["Close"]
    px.index = pd.to_datetime(px.index).tz_localize(None)
    cr = px.rename(columns={v: k for k, v in COMMODITIES.items()}).pct_change(fill_method=None).clip(-0.3, 0.3)
    rows = []
    for mk, m in markets.items():
        c = cr.reindex(m.dates).fillna(0.0)
        r = m.ret
        imp1, imp5 = 0.0, 0.0
        for k in COMMODITIES:
            x = c[k]
            beta = (r.rolling(252, min_periods=150).cov(x).div(x.rolling(252, min_periods=150).var(), axis=0)).shift(1)
            imp1 = imp1 + beta.mul(x, axis=0)
            imp5 = imp5 + beta.mul(x.rolling(5).sum(), axis=0)
        own5 = np.log1p(r).rolling(5).sum()
        sigs = {"commodity_implied_1d": imp1, "commodity_implied_5d": imp5, "commodity_implied_5d_minus_own_5d": imp5 - own5,
                "own_reversal_5d (control)": -own5}
        o = m.open
        stress = m.vix > 20
        for h in (1, 5, 21):
            fwd = (o.shift(-(1 + h)) / o.shift(-1) - 1).where(m.tradable)
            for name, s in sigs.items():
                ic = L.rank_ic(L.zscore(s, m.tradable), fwd, min_names=12)
                row = {"market": mk, "signal": name, "horizon": h, "ic_all": ic.mean(),
                       "t_all": ic.mean() / ic.std() * np.sqrt(ic.notna().sum() / h) if ic.notna().sum() > 50 else np.nan,
                       "ic_2004_14": ic[:"2014"].mean(), "ic_2015_26": ic["2015":].mean(),
                       "ic_calm": ic[~stress].mean(), "ic_stressed": ic[stress].mean()}
                rows.append(row)
    return pd.DataFrame(rows)


def financials(fin_prices: Path, fu: pd.DataFrame, vix: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = fu.set_index("ticker")["industry"].map(GROUP)
    fm = {}
    for mk in LOCAL:
        p = fin_prices / mk
        if (p / "adj_close.parquet").exists() and (fu["market"] == mk).sum() >= 7:
            try:
                m = L.Market(mk, p, fu[fu["market"] == mk], vix)
            except Exception as exc:  # noqa: BLE001
                print(f"financials {mk}: skipped ({exc})")
                continue
            # the lab drops days with fewer than 10 prices, which empties markets with only 7-10 financials
            if len(m.dates) < 1000 or int(m.tradable.sum(axis=1).median()) < 5:
                print(f"financials {mk}: skipped (too few names: {len(m.tickers)})")
                continue
            fm[mk] = m
    P = build(fm, groups)
    stress = vix.reindex(P["r1"].index, method="ffill") > 20
    rows = []
    for k in ("mom_12_1", "resid_mom", "high_52w", "rev_5d", "rev_21d", "low_vol", "max_effect", "size_proxy", "amihud"):
        ic = L.rank_ic(P["sig_c"][k].where(P["tradable"]), P["fwd21"], min_names=20)
        rows.append({"signal": k, "ic_all": ic.mean(), "t_all": ic.mean() / ic.std() * np.sqrt(ic.notna().sum() / 21),
                     **{f"ic_{t}": ic[a:b].mean() for t, a, b in L.IC_PERIODS}, "ic_calm": ic[~stress].mean(), "ic_stressed": ic[stress].mean()})
    m = Panel(P["r1"], P["cost"])
    v = vix.reindex(P["r1"].index, method="ffill")
    flat = pd.Series(np.where(v > 20, 0.0, 1.0), index=P["r1"].index)
    comp = sum(P["sig_c"][s] for s in L.MOM) / len(L.MOM)
    b = []
    for label, sign in (("plain", None), ("flat in stress", flat)):
        b.append(L.period_stats(L.pnl(L.staggered(m, comp, P["tradable"], sign), m)["net"]["2004":], f"South American financials ({len(fm)} markets): momentum {label}",
                                {"median_names_2015_26": int(P["tradable"].sum(axis=1)["2015":].median())}))
    return pd.DataFrame(rows), pd.DataFrame(b)


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("prices", "universe", "adr-prices", "adr-universe", "fin-prices", "fin-universe", "brazil120-prices", "macro", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--intl-sleeves")
    ap.add_argument("--us-flip")
    ap.add_argument("--us-etf")
    ap.add_argument("--us-strategies")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vix = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    u = pd.read_csv(args.universe)
    markets = load(Path(args.prices), u, vix, LOCAL)
    pd.set_option("display.width", 250)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26"]

    # 1. per market
    per, ics, qual, rows = {}, [], [], []
    for name, m in markets.items():
        sigs = m.signals()
        ics.append(momentum_ic_by_regime(m, sigs))
        qual.append(quality(m))
        per[name] = books_for(m)
        for k, s in per[name].items():
            rows.append(L.period_stats(s, f"{name}: {k}", {"median_names_2015_26": int(m.tradable.sum(axis=1)["2015":].median())}))
    ic = pd.DataFrame(ics).set_index("market")
    ic["weaker_in_stress"] = ic["ic_stressed"] < ic["ic_calm"]
    ic.to_csv(out / "momentum_ic_by_regime.csv")
    pd.DataFrame(qual).to_csv(out / "data_quality.csv", index=False)
    pm = pd.DataFrame(rows)
    pm.to_csv(out / "per_market.csv", index=False)
    print("== momentum IC by regime ==")
    print(ic.round(4).to_string())
    print(pd.DataFrame(qual).round(3).to_string(index=False))
    print(pm[pm["book"].str.contains(": (plain|flip|flat)$")][cols + ["median_names_2015_26"]].round(2).to_string(index=False))

    # 2. aggregates
    agg_rows, daily = [], {}
    keys = ("plain", "flip", "flat", "flat_costs_x2", "flat_costs_x3", "plain_costs_x2", "flat_liquid_half", "flat_one_day_late",
            "long_only_flat_ew_hedge", "long_leg_vs_ew", "short_leg_vs_ew")
    for g, members in (("5 South American markets", LOCAL), ("3 fresh (Argentina, Colombia, Peru)", FRESH), ("Brazil + Chile", ("Brazil", "Chile"))):
        for k in keys:
            s = equal_risk(pd.DataFrame({mk: per[mk][k] for mk in members if mk in per}))
            daily[f"{g}: {k}"] = s
            agg_rows.append(L.period_stats(s, f"{g}: {k}"))
    # Brazil: the 120 largest from the earlier new-exchange run, and the 120 largest within the broad set
    un = pd.read_csv(Path(args.brazil120_prices).parent / "universe_new_markets.csv")
    b120 = load(Path(args.brazil120_prices), un, vix, ["Brazil"])["Brazil"]
    s120 = books_for(b120)["flat"]
    mb = markets["Brazil"]
    big = set(u[u["market"] == "Brazil"].sort_values("market_cap", ascending=False)["ticker"].head(120))
    in_big = pd.DataFrame(np.repeat(mb.tickers.isin(list(big))[None, :], len(mb.dates), 0), index=mb.dates, columns=mb.tickers)
    sig_b = mb.signals()
    mask_b = mb.tradable & in_big
    comp_b = sum(L.zscore(sig_b[s], mask_b) for s in L.MOM) / len(L.MOM)
    s_b120 = L.pnl(L.staggered(mb, comp_b, mask_b, flat_sign(mb)), mb)["net"]
    for label, s in (("Brazil, 120 largest (earlier new-exchange universe): flat", s120),
                     ("Brazil, 120 largest within the broad set: flat", s_b120),
                     ("Brazil, broad (296): flat", per["Brazil"]["flat"]),
                     ("Brazil, broad, liquid half: flat", per["Brazil"]["flat_liquid_half"])):
        agg_rows.append(L.period_stats(s, label))
    aggt = pd.DataFrame(agg_rows)
    aggt.to_csv(out / "cross_market.csv", index=False)
    print("\n== aggregates ==")
    print(aggt[cols].round(2).to_string(index=False))
    boot = {}
    for label in ("5 South American markets: flat", "3 fresh (Argentina, Colombia, Peru): flat"):
        for p, a, b in PERS:
            x = daily[label][a:b].dropna().to_numpy()
            if len(x) > 250:
                boot[(label, p)] = block_bootstrap(x)
    loo = [{"dropped": d, "flat_2015_26": L._sharpe(equal_risk(pd.DataFrame({k: per[k]["flat"] for k in per if k != d}))["2015":])} for d in per]

    # 3. ADRs
    ua = pd.read_csv(args.adr_universe)
    adr = L.Market("South America ADRs", Path(args.adr_prices) / "South_America_ADRs", ua, vix)
    sig_a = adr.signals()
    comp_a = sum(sig_a[s] for s in L.MOM) / len(L.MOM)
    country = ua.set_index("ticker")["industry"].reindex(adr.tickers)
    comp_cn = sum(zscore_within(sig_a[s], adr.tradable, country) for s in L.MOM) / len(L.MOM)
    adr_rows = []
    adr_b = books_for(adr, comp_a)
    adr_bc = books_for(adr, comp_cn)
    for label, b in (("pooled", adr_b), ("country-neutral", adr_bc)):
        for k in ("plain", "flip", "flat", "flat_costs_x2", "flat_costs_x3", "flat_one_day_late", "long_only_flat_ew_hedge", "long_leg_vs_ew", "short_leg_vs_ew"):
            adr_rows.append(L.period_stats(b[k], f"South American ADRs, {label}: {k}", {"median_names_2015_26": int(adr.tradable.sum(axis=1)["2015":].median())}))
    for p, a, b in PERS:
        boot[("ADRs pooled: flat", p)] = block_bootstrap(adr_b["flat"][a:b].dropna().to_numpy())
    adr_ic = momentum_ic_by_regime(adr, sig_a)
    adrt = pd.DataFrame(adr_rows)
    adrt.to_csv(out / "adr_books.csv", index=False)
    print("\n== ADRs ==", {k: round(v, 4) if isinstance(v, float) else v for k, v in adr_ic.items()})
    print(adrt[cols + ["median_names_2015_26"]].round(2).to_string(index=False))
    bt = pd.DataFrame(boot).T
    bt.to_csv(out / "bootstrap.csv")
    pd.DataFrame(loo).to_csv(out / "leave_one_out.csv", index=False)
    print(bt.round(3).to_string())
    print(pd.DataFrame(loo).round(2).to_string(index=False))

    # 4. financials
    fic, fb = financials(Path(args.fin_prices), pd.read_csv(args.fin_universe), vix)
    fic.to_csv(out / "financials_ic.csv", index=False)
    fb.to_csv(out / "financials_books.csv", index=False)
    print("\n== South American financials ==")
    print(fic.round(4).to_string(index=False))
    print(fb[cols + ["median_names_2015_26"]].round(2).to_string(index=False))

    # 5. commodity lead-lag
    cl = commodity_lead_lag(markets, vix)
    cl.to_csv(out / "commodity_lead_lag.csv", index=False)
    piv = cl.pivot_table(index=["signal", "horizon"], values=["ic_all", "ic_2004_14", "ic_2015_26"], aggfunc="mean")
    print("\n== commodity lead-lag, IC averaged over the 5 markets ==")
    print(piv.round(4).to_string())
    print(cl[cl["horizon"] == 5].round(4).to_string(index=False))

    # 6. combined book
    if args.intl_sleeves and args.us_flip and args.us_etf and args.us_strategies:
        us_flip = pd.read_csv(args.us_flip, index_col=0, parse_dates=True).iloc[:, 0]
        etf = pd.read_csv(args.us_etf, index_col=0, parse_dates=True)["all 8 sleeves"]
        strat = pd.read_csv(args.us_strategies, index_col=0, parse_dates=True)
        sl = pd.read_csv(args.intl_sleeves, index_col=0, parse_dates=True)
        vv = vix.reindex(etf.index, method="ffill")
        B = pd.DataFrame({"etf": etf,
                          "pairs2": strat["pairs"].reindex(etf.index).fillna(0) * (1 + (vv.shift(2) > 20).astype(float)),
                          "us_flip": us_flip.reindex(etf.index).fillna(0),
                          "orig21": sl["orig21_costs_x2"].reindex(etf.index).fillna(0),
                          "new14": sl["new14_costs_x2"].reindex(etf.index).fillna(0),
                          "sa_adr": adr_b["flat_costs_x2"].reindex(etf.index).fillna(0),
                          "sa_local_bc": daily["Brazil + Chile: flat_costs_x2"].reindex(etf.index).fillna(0)})
        crow = []
        for label, c in (("US + original 21 + 14 new (costs x2)", ["etf", "pairs2", "us_flip", "orig21", "new14"]),
                         ("  + South American ADR sleeve (costs x2)", ["etf", "pairs2", "us_flip", "orig21", "new14", "sa_adr"])):
            s = blend(B, c)
            crow.append(L.period_stats(s, label, {"worst_month": float(s["2015":].resample("ME").sum().min())}))
        combo = pd.DataFrame(crow)
        combo.to_csv(out / "combined.csv", index=False)
        corr = B["2015":].corr().round(2)
        corr.to_csv(out / "combined_correlations.csv")
        print("\n== combined ==")
        print(combo[cols + ["worst_month"]].round(3).to_string(index=False))
        print(corr.loc[["sa_adr", "sa_local_bc"]].to_string())


if __name__ == "__main__":
    main()
