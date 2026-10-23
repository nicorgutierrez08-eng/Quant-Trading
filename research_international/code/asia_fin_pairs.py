"""Pairs trading inside Asia-Pacific financials (pre-registered in LOG.md).

The US pairs sleeve's rule, unchanged, applied within each market x
industry group of the deep financials universe (liquid half at formation):
each year the 5 most correlated pairs (past 252 days, corr > 0.6), trade the
log-price spread on a 60-day z-score, enter |z| > 2, exit |z| < 0.5 or after
21 days. Main version executes at the next open (signal at the close of t,
earns open t+1 -> t+2, costs charged on each change); the same-close version
(the US convention, position from the close of t-1 earns day t's return) is
for comparison only. Also: the same rule scaled x2 when the VIX is above 20,
as in the US book.

    python research_international/code/asia_fin_pairs.py --fin-prices data2/prices_fin --fin-universe data2/universe_asia_financials.csv --out reports/asia_fin_pairs
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from asia_fin_deep import GROUP, MARKETS
from intl_more import block_bootstrap, equal_risk

TOP, ENTRY, EXIT, MAX_HOLD, WIN, MIN_CORR = 5, 2.0, 0.5, 21, 60, 0.6


def market_pairs(m: L.Market, groups: pd.Series) -> tuple[pd.Series, pd.Series, list]:
    lp = np.log(m.adj)
    ret = m.ret.fillna(0)
    r1 = m.r1.fillna(0)
    z_all = (lp - lp.rolling(WIN).mean()) * 0          # placeholder for alignment
    nxt, same = pd.Series(0.0, index=m.dates), pd.Series(0.0, index=m.dates)
    log = []
    g = groups.reindex(m.tickers).fillna("credit")
    for yr in sorted(set(m.dates.year))[2:]:
        days = m.dates[m.dates.year == yr]
        start = days[0]
        hist = m.ret.loc[:start].iloc[-253:-1]
        tr = m.tradable.loc[start]
        adv = m.adv.loc[start].where(tr)
        liquid = adv > adv.median()
        pairs = []
        for grp in ("banks", "insurance", "capital_markets", "credit"):
            mem = [t for t in m.tickers if g[t] == grp and liquid.get(t, False) and hist[t].notna().sum() >= 240]
            if len(mem) < 2:
                continue
            cm = hist[mem].corr().to_numpy()
            iu = np.triu_indices(len(mem), 1)
            vals = np.nan_to_num(cm[iu], nan=-1)
            for b in np.argsort(-vals)[:TOP]:
                if vals[b] > MIN_CORR:
                    pairs.append((mem[iu[0][b]], mem[iu[1][b]], grp, float(vals[b])))
        if not pairs:
            continue
        w = 1.0 / len(pairs)
        for a, b, grp, c in pairs:
            spread = lp[a] - lp[b]
            z = ((spread - spread.rolling(WIN).mean()) / spread.rolling(WIN).std()).loc[days].to_numpy()
            ca, cb = m.cost[a].loc[days].to_numpy(), m.cost[b].loc[days].to_numpy()
            ra1, rb1 = r1[a].loc[days].to_numpy(), r1[b].loc[days].to_numpy()
            ra, rb = ret[a].loc[days].to_numpy(), ret[b].loc[days].to_numpy()
            # next-open: position chosen at the close of i from z_i, earns r1[i]
            o_next, o_same = np.zeros(len(days)), np.zeros(len(days))
            pos, held, trades = 0, 0, 0
            for i in range(len(days)):
                new = pos
                if pos == 0 and np.isfinite(z[i]) and abs(z[i]) > ENTRY:
                    new = -int(np.sign(z[i]))
                elif pos != 0 and (abs(z[i]) < EXIT or held >= MAX_HOLD or not np.isfinite(z[i])):
                    new = 0
                if i == len(days) - 1:
                    new = 0                                    # pairs are re-formed every year: close out
                if new != pos:
                    o_next[i] -= abs(new - pos) * w / 2 * (ca[i] + cb[i])
                    if i + 1 < len(days):
                        o_same[i + 1] -= abs(new - pos) * w / 2 * (ca[i] + cb[i])
                    held, trades = 0, trades + (new != 0)
                pos = new
                held += 1 if pos != 0 else 0
                o_next[i] += pos * (ra1[i] - rb1[i]) * w / 2
                if i + 1 < len(days):
                    o_same[i + 1] += pos * (ra[i + 1] - rb[i + 1]) * w / 2
            nxt.loc[days] += np.nan_to_num(o_next)
            same.loc[days] += np.nan_to_num(o_same)
            log.append({"market": m.name, "year": yr, "a": a, "b": b, "group": grp, "corr": c, "trades": trades})
    return nxt, same, log


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin-prices", required=True)
    ap.add_argument("--fin-universe", required=True)
    ap.add_argument("--out", default="reports/asia_fin_pairs")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fu = pd.read_csv(args.fin_universe)
    groups = fu.set_index("ticker")["industry"].map(GROUP)
    vix = pd.read_parquet(Path(args.fin_prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    nxt, same, logs, rows = {}, {}, [], []
    for mk in MARKETS:
        if (fu["market"] == mk).sum() < 15:
            continue
        m = L.Market(mk, Path(args.fin_prices) / mk.replace(" ", "_"), fu[fu["market"] == mk], vix)
        a, b, lg = market_pairs(m, groups)
        nxt[mk], same[mk] = a, b
        logs += lg
        rows.append(L.period_stats(a["2004":], f"{mk}: pairs, next open", {"pairs_per_year": len(lg) / max(1, len({x['year'] for x in lg}))}))
        print(f"{mk:10s} next-open {L._sharpe(a['2006':'2014']):5.2f} / {L._sharpe(a['2015':'2020']):5.2f} / {L._sharpe(a['2021':]):5.2f}"
              f"   same-close {L._sharpe(b['2015':]):5.2f} (2015-26)")
    agg = {}
    N, S = pd.DataFrame(nxt), pd.DataFrame(same)
    agg["Asia-Pacific financials: pairs, next open"] = equal_risk(N.where(N != 0))
    agg["Asia-Pacific financials: pairs, same close (US convention)"] = equal_risk(S.where(S != 0))
    v = vix.reindex(agg["Asia-Pacific financials: pairs, next open"].index, method="ffill")
    agg["Asia-Pacific financials: pairs, next open, x2 when VIX > 20"] = agg["Asia-Pacific financials: pairs, next open"] * (1 + (v.shift(2) > 20).astype(float))
    for k, s in agg.items():
        rows.append(L.period_stats(s.fillna(0)["2004":], k))
    t = pd.DataFrame(rows)
    t.to_csv(out / "pairs.csv", index=False)
    pd.DataFrame(logs).to_csv(out / "pairs_formed.csv", index=False)
    pd.DataFrame(agg).to_csv(out / "pairs_daily.csv")
    boot = {p: block_bootstrap(agg["Asia-Pacific financials: pairs, next open"].fillna(0)[a:b].to_numpy())
            for p, a, b in (("2006-14", "2006", "2014"), ("2015-20", "2015", "2020"), ("2021-26", "2021", "2026"))}
    pd.DataFrame(boot).T.to_csv(out / "pairs_bootstrap.csv")
    pd.set_option("display.width", 250)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26"]
    print(t[cols].round(2).to_string(index=False))
    print(pd.DataFrame(boot).T.round(3).to_string())


if __name__ == "__main__":
    main()
