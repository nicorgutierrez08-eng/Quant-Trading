"""Does the US pairs sleeve survive realistic execution?

Arjun's `strategies.pairs_strategy` decides the position from the z-score at
the close of day i-1 and earns day i's close-to-close return, i.e. it trades
at the same close that produced the signal. That is only achievable with
market-on-close orders sent before the close is known. This reruns the
identical rule (same k-means peer clusters, same yearly formation, same
thresholds, same cost panel) with:

* same close (the original; checked against strategy_returns.csv),
* next open: signal at the close of i, trade at the open of i+1, earn
  open i+1 -> open i+2,
* one day late: signal at the close of i, trade at the close of i+1.

and then rebuilds the combined book with the next-open pairs.

    python research_international/code/us_pairs_execution.py --keen <Arjun's repo> --out reports/us_pairs_execution \
        --vix-from data/prices/_series/adj_close.parquet --intl-sleeves reports/conservative/sleeves_daily.csv
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from new_exchanges import blend


def run(md, ctx, cost_panel, top_pairs=5, entry=2.0, exit_=0.5, max_hold=21) -> dict[str, pd.Series]:
    lp = np.log(md.close)
    ret = ctx.ret
    r1 = (md.open.shift(-2) / md.open.shift(-1) - 1).clip(-0.5, 0.5)
    cost = cost_panel(ctx)
    fm = ctx.factor_model
    dates = md.dates
    out = {k: pd.Series(0.0, index=dates) for k in ("same close", "next open", "one day late")}
    for yr in sorted(set(dates.year))[2:]:
        start = dates[dates.year == yr][0]
        snap = fm.snapshot_at(start)
        if snap is None:
            continue
        form = ret.loc[:start].iloc[-252:]
        pairs = []
        for k in np.unique(snap.clusters):
            mem = [t for t, c in zip(snap.tickers, snap.clusters) if c == k and t in form.columns]
            if len(mem) < 2:
                continue
            cm = form[mem].corr().to_numpy()
            iu = np.triu_indices(len(mem), 1)
            best = np.argsort(-np.nan_to_num(cm[iu]))[:top_pairs]
            pairs += [(mem[iu[0][b]], mem[iu[1][b]]) for b in best if cm[iu][b] > 0.6]
        if not pairs:
            continue
        days = dates[dates.year == yr]
        w = 1.0 / len(pairs)
        for a, b in pairs:
            spread = lp[a] - lp[b]
            z = ((spread - spread.rolling(60).mean()) / spread.rolling(60).std()).loc[days].to_numpy()
            ra, rb = ret[a].loc[days].fillna(0).to_numpy(), ret[b].loc[days].fillna(0).to_numpy()
            oa, ob = r1[a].loc[days].fillna(0).to_numpy(), r1[b].loc[days].fillna(0).to_numpy()
            ca, cb = cost[a].loc[days].to_numpy(), cost[b].loc[days].to_numpy()
            # the position path is the same in all variants: pos[i] is decided from z[i] at the close of i
            pos = np.zeros(len(days))
            p, held = 0, 0
            for i in range(1, len(days)):
                new = p
                if p == 0 and np.isfinite(z[i]) and abs(z[i]) > entry:
                    new = -int(np.sign(z[i]))
                elif p != 0 and (abs(z[i]) < exit_ or held >= max_hold or not np.isfinite(z[i])):
                    new = 0
                if new != p:
                    held = 0
                held += 1 if new != 0 else 0
                p = new
                pos[i] = p
            dpos = np.abs(np.diff(np.r_[0.0, pos]))
            tc = dpos * w / 2 * (ca + cb)
            # same close: pos decided at close i earns day i+1 (original code books the cost on day i)
            s = np.zeros(len(days))
            s[1:] = pos[:-1] * (ra[1:] - rb[1:]) * w / 2
            s -= np.nan_to_num(tc)
            # next open: pos decided at close i earns open i+1 -> open i+2 (r1[i]); cost at the open of i+1
            n = pos * (oa - ob) * w / 2 - np.nan_to_num(tc)
            # one day late: pos decided at close i, traded at close i+1, earns day i+2
            d = np.zeros(len(days))
            d[2:] = pos[:-2] * (ra[2:] - rb[2:]) * w / 2
            d[1:] -= np.nan_to_num(tc[:-1])
            out["same close"].loc[days] += s
            out["next open"].loc[days] += n
            out["one day late"].loc[days] += d
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--keen", required=True, help="path of Arjun's repo (for qtrade.research and data/lab)")
    ap.add_argument("--out", default="reports/us_pairs_execution")
    ap.add_argument("--intl-sleeves", help="sleeves_daily.csv from conservative_combo.py")
    ap.add_argument("--vix-from", required=True, help="_series/adj_close.parquet with the vol:US column")
    args = ap.parse_args(argv)
    sys.path.insert(0, args.keen)
    from qtrade.research.edge import cost_panel          # noqa: E402
    keen = Path(args.keen)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(keen / "data/lab/md.pkl", "rb") as fh:
        md = pickle.load(fh)
    with open(keen / "data/lab/ctx.pkl", "rb") as fh:
        ctx = pickle.load(fh)
    res = run(md, ctx, cost_panel)
    orig = pd.read_csv(keen / "research_data/studies/strategy_returns.csv", index_col=0, parse_dates=True)["pairs"]
    check = pd.concat([orig, res["same close"]], axis=1).dropna().corr().iloc[0, 1]
    print(f"same-close rerun vs strategy_returns.csv['pairs']: correlation {check:.4f}")
    vix = pd.read_csv(keen / "reports/momentum_flip/momentum_flip_staggered_daily.csv", index_col=0, parse_dates=True)
    rows = []
    etf = pd.read_csv(keen / "research_data/studies/multi_daily.csv", index_col=0, parse_dates=True)["all 8 sleeves"]
    vv = pd.read_parquet(args.vix_from)["vol:US"].dropna().reindex(etf.index, method="ffill")
    for k, s in res.items():
        rows.append(L.period_stats(s["2004":], f"US pairs, {k}"))
        s2 = s.reindex(etf.index).fillna(0) * (1 + (vv.shift(2) > 20).astype(float))
        rows.append(L.period_stats(s2["2004":], f"US pairs x2 when VIX > 20, {k}"))
    us_flip = vix.iloc[:, 0]
    B = pd.DataFrame({"etf": etf, "us_flip": us_flip.reindex(etf.index).fillna(0)})
    for k, s in res.items():
        B[f"pairs2 {k}"] = s.reindex(etf.index).fillna(0) * (1 + (vv.shift(2) > 20).astype(float))
    if args.intl_sleeves:
        sl = pd.read_csv(args.intl_sleeves, index_col=0, parse_dates=True)
        for c in ("orig21_costs_x2", "new14_costs_x2"):
            B[c] = sl[c].reindex(etf.index).fillna(0)
    for k in res:
        rows.append(L.period_stats(blend(B, ["etf", f"pairs2 {k}", "us_flip"]), f"US book, pairs {k}"))
        if args.intl_sleeves:
            rows.append(L.period_stats(blend(B, ["etf", f"pairs2 {k}", "us_flip", "orig21_costs_x2", "new14_costs_x2"]),
                                       f"US book + original 21 + 14 new (costs x2), pairs {k}"))
    t = pd.DataFrame(rows)
    t.to_csv(out / "us_pairs_execution.csv", index=False)
    pd.DataFrame(res).to_csv(out / "us_pairs_daily.csv")
    pd.set_option("display.width", 250)
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26"]
    print(t[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
