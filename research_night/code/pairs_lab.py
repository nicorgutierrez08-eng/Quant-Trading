"""Pairs lab: the one market-neutral strategy that pays in every sub-period, tuned honestly.

``strategies.pairs_strategy`` (classic pairs trading inside the k-means peer
clusters, pairs re-formed yearly on the past year's correlations) has Sharpe
0.85 / 0.71 / 0.76 in 2006-14 / 2015-20 / 2021-26 with correlation 0.22 to the
market, and it is the only strategy besides the regime switch that earns in
the stressed regime. Its parameters (5 pairs per cluster, enter at |z| > 2, exit
at |z| < 0.5, hold at most 21 days, 60-day z-score) were never varied.

This sweeps them, scores every configuration net of measured costs on 2006-14
(choose) and 2015-26 (check), and reports the chosen configuration's sub-period
Sharpes, turnover proxy, and how many pairs it trades - all walk-forward (the
pairs and the z-score only use past data).

    python -m qtrade.research.pairs_lab --lab data/lab --out reports/pairs_lab
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, setup_logging
from .edge import cost_panel

SPLIT = "2015-01-01"
HALF = "2021-01-01"

G: dict = {}


def pairs_pnl(top_pairs: int, entry: float, exit_: float, max_hold: int, window: int, min_corr: float = 0.6) -> dict:
    """Daily net P&L of the pairs book (unit capital, equal weight per pair) and trade statistics."""
    lp, ret, cost, fm, dates = G["lp"], G["ret"], G["cost"], G["fm"], G["dates"]
    pnl = pd.Series(0.0, index=dates)
    n_pairs, n_trades, days_held = [], 0, 0
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
            pairs += [(mem[iu[0][b]], mem[iu[1][b]]) for b in best if cm[iu][b] > min_corr]
        if not pairs:
            continue
        n_pairs.append(len(pairs))
        days = dates[dates.year == yr]
        w_pair = 1.0 / len(pairs)
        for a, b in pairs:
            spread = lp[a] - lp[b]
            z = (spread - spread.rolling(window).mean()) / spread.rolling(window).std()
            zt = z.loc[days].to_numpy()
            ra, rb = ret[a].loc[days].fillna(0).to_numpy(), ret[b].loc[days].fillna(0).to_numpy()
            ca, cb = cost[a].loc[days].to_numpy(), cost[b].loc[days].to_numpy()
            pos, held = 0, 0
            out = np.zeros(len(days))
            for i in range(1, len(days)):
                out[i] = pos * (ra[i] - rb[i]) * w_pair / 2
                new = pos
                if pos == 0 and np.isfinite(zt[i]) and abs(zt[i]) > entry:
                    new = -int(np.sign(zt[i]))
                elif pos != 0 and (abs(zt[i]) < exit_ or held >= max_hold or not np.isfinite(zt[i])):
                    new = 0
                if new != pos:
                    out[i] -= abs(new - pos) * w_pair / 2 * (ca[i] + cb[i])
                    held = 0
                    n_trades += 1
                held += 1 if new != 0 else 0
                days_held += 1 if new != 0 else 0
                pos = new
            pnl.loc[days] += out
    return {"pnl": pnl, "avg_pairs": float(np.mean(n_pairs)) if n_pairs else 0.0, "trades": n_trades,
            "avg_hold_days": days_held / max(n_trades, 1) * 2}


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 20 and x.std() > 0 else np.nan


def run_config(cfg: tuple) -> dict:
    t0 = time.time()
    top, entry, exit_, hold, window = cfg
    r = pairs_pnl(top, entry, exit_, hold, window)
    p = r["pnl"]
    res = {"top_pairs": top, "entry": entry, "exit": exit_, "max_hold": hold, "window": window,
           "avg_pairs": r["avg_pairs"], "trades": r["trades"], "avg_hold_days": r["avg_hold_days"],
           "sharpe_2006_14": _sharpe(p["2006":"2014"]), "sharpe_2015_20": _sharpe(p["2015":"2020"]),
           "sharpe_2021_26": _sharpe(p["2021":]), "sharpe_2015_26": _sharpe(p["2015":]),
           "ann_return_2015_26": float(p["2015":].mean() * 252), "ann_vol_2015_26": float(p["2015":].std() * np.sqrt(252)),
           "corr_market_2015_26": float(p["2015":].corr(G["mkt"]["2015":])), "seconds": time.time() - t0}
    LOG.info("pairs top=%d entry=%.1f exit=%.1f hold=%d window=%d: Sharpe %.2f / %.2f (%.0fs)", top, entry, exit_, hold,
             window, res["sharpe_2006_14"], res["sharpe_2015_26"], res["seconds"])
    res["_pnl"] = p
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--out", default="reports/pairs_lab")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    md, ctx, X, names = load(args.lab)
    del X
    G.update({"lp": np.log(md.close), "ret": ctx.ret, "cost": cost_panel(ctx), "fm": ctx.factor_model,
              "dates": md.dates, "mkt": ctx.market_ret})
    grid = {"top_pairs": (5, 10, 25), "entry": (1.5, 2.0, 2.5), "exit": (0.0, 0.5), "max_hold": (21, 63),
            "window": (60, 120)}
    if args.quick:
        grid = {"top_pairs": (5, 25), "entry": (2.0,), "exit": (0.5,), "max_hold": (21,), "window": (60, 120)}
    configs = list(itertools.product(*grid.values()))
    LOG.info("pairs lab: %d configurations", len(configs))
    with Pool(args.workers) as pool:
        rows = pool.map(run_config, configs, chunksize=1)
    pnls = {tuple(r[k] for k in ("top_pairs", "entry", "exit", "max_hold", "window")): r.pop("_pnl") for r in rows}
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "pairs_lab.csv", index=False)
    base = tab[(tab.top_pairs == 5) & (tab.entry == 2.0) & (tab.exit == 0.5) & (tab.max_hold == 21) & (tab.window == 60)]
    pick = tab.sort_values("sharpe_2006_14", ascending=False).iloc[0]
    key = tuple(pick[k] for k in ("top_pairs", "entry", "exit", "max_hold", "window"))
    pd.DataFrame({"picked": pnls[key], "baseline": pnls[(5, 2.0, 0.5, 21, 60)]}).to_csv(out / "pairs_daily.csv")
    cols = ["top_pairs", "entry", "exit", "max_hold", "window", "avg_pairs", "avg_hold_days", "sharpe_2006_14",
            "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ann_return_2015_26", "ann_vol_2015_26",
            "corr_market_2015_26"]
    by = {k: tab.groupby(k)[["sharpe_2006_14", "sharpe_2015_26"]].median().round(2) for k in grid}
    lines = ["# Pairs lab", "",
             "Classic pairs trading inside the k-means peer clusters, pairs re-formed every January on the past "
             "year's correlations (> 0.6), z-score of the log-price spread over `window` days, enter when |z| > "
             "`entry`, exit when |z| < `exit` or after `max_hold` days. Unit capital split equally across pairs; net "
             "of measured spreads + 1 bp on every leg. Sharpe is of the raw (unlevered) book; vol is ~1-2%, so it "
             "would be levered in a real book.", "",
             f"Arjun's configuration (5, 2.0, 0.5, 21, 60): Sharpe {base['sharpe_2006_14'].iloc[0]:.2f} (2006-14) / "
             f"{base['sharpe_2015_26'].iloc[0]:.2f} (2015-26).", "",
             f"**Picked on 2006-14:** top_pairs={key[0]}, entry={key[1]}, exit={key[2]}, max_hold={key[3]}, "
             f"window={key[4]}: Sharpe {pick['sharpe_2006_14']:.2f} -> **{pick['sharpe_2015_26']:.2f}** "
             f"(2015-20 {pick['sharpe_2015_20']:.2f}, 2021-26 {pick['sharpe_2021_26']:.2f}).", "",
             "## Every configuration (sorted by 2006-14)", "",
             tab.sort_values("sharpe_2006_14", ascending=False)[cols].round(3).to_markdown(index=False), "",
             "## Median Sharpe by each parameter", ""]
    for k, v in by.items():
        lines += [f"### {k}", "", v.to_markdown(), ""]
    lines += [f"Rank correlation of Sharpe between periods across configurations: "
              f"{tab['sharpe_2006_14'].corr(tab['sharpe_2015_26'], method='spearman'):.2f}", ""]
    (out / "pairs_lab.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps({"picked": [float(k) for k in key], "configs": len(tab)}, indent=2))
    print(tab.sort_values("sharpe_2006_14", ascending=False)[cols[:5] + cols[7:11]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
