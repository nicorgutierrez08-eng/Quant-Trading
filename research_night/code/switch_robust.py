"""Due diligence on the regime switch before anyone believes a 0.6 Sharpe.

Varies everything that was a choice in ``switch_lab`` and reports the signed
regime switch (reversal vs momentum, capital by regime-conditional IC) under
each: rebalance interval (10 / 21 / 42 days), book composition (composites vs
single signals), regime proxy (trailing-vol terciles, VIX terciles, HMM
probabilities), and the universe. Then, for the headline configuration:

* net return by calendar year, Sharpe in 2015-20 and 2021-26 separately;
* correlation with the market and with the plain monthly reversal book;
* a 21-day block bootstrap (2,000 draws) of the 2015-2026 Sharpe and of the
  Sharpe *difference* against plain monthly reversal, so the result comes with
  an interval, not a point.

    python -m qtrade.research.switch_robust --lab data/lab --probs <hmm probs parquet> --out reports/switch_robust
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, rank_ic, setup_logging
from .book_lab import tercile_probs
from .edge import SPLIT, cost_panel, portfolio_stats, summarize
from .switch_lab import MOM, REV, composite, monthly_weights, regime_split

HALF = "2021-01-01"


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 20 and x.std() > 0 else np.nan


def block_bootstrap(x: np.ndarray, y: np.ndarray | None = None, block: int = 21, n: int = 2000, seed: int = 0):
    """Sharpe of x (and of x - y paired, if y is given) under a moving-block bootstrap."""
    rng = np.random.default_rng(seed)
    T = len(x)
    nb = int(np.ceil(T / block))
    starts = rng.integers(0, T - block, size=(n, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, :T]
    xs = x[idx]
    sr = xs.mean(1) / xs.std(1) * np.sqrt(252)
    out = {"sharpe_p5": float(np.percentile(sr, 5)), "sharpe_p50": float(np.percentile(sr, 50)),
           "sharpe_p95": float(np.percentile(sr, 95)), "p_sharpe_below_0": float((sr < 0).mean())}
    if y is not None:
        ys = y[idx]
        d = xs.mean(1) / xs.std(1) * np.sqrt(252) - ys.mean(1) / ys.std(1) * np.sqrt(252)
        out |= {"diff_p5": float(np.percentile(d, 5)), "diff_p50": float(np.percentile(d, 50)),
                "diff_p95": float(np.percentile(d, 95)), "p_diff_below_0": float((d < 0).mean())}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--probs", nargs="*", default=[])
    ap.add_argument("--out", default="reports/switch_robust")
    args = ap.parse_args(argv)
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    md, ctx, X, names = load(args.lab)
    dates, tickers = md.dates, md.tickers
    tr = ctx.tradable
    liquid = tr & (ctx.adv.where(tr).rank(axis=1, ascending=False) <= 300)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5)
    cost = cost_panel(ctx)
    mkt = ctx.market_ret
    regimes = {"vol_tercile": tercile_probs(mkt.rolling(21).std())}
    fp = Path(args.lab) / "fred.parquet"
    if fp.exists():
        fred = pd.read_parquet(fp)
        if "vix" in fred:
            regimes["vix_tercile"] = tercile_probs(fred["vix"].reindex(dates).ffill())
    for f in args.probs:
        regimes[Path(f).stem] = pd.read_parquet(f).reindex(dates)

    books = {"composites": (REV, MOM), "rev_21d vs mom_12_1": (["rev_21d"], ["mom_12_1"]),
             "rev_5d+bollinger vs resid_mom+high_52w": (["rev_5d", "bollinger_z"], ["resid_mom", "high_52w"])}
    rows, series = [], {}
    for uni_name, mask in (("all", tr), ("top300", liquid)):
        for bname, (rev_m, mom_m) in books.items():
            z_rev = composite(X, names, rev_m, dates, tickers, mask)
            z_mom = composite(X, names, mom_m, dates, tickers, mask)
            for h in (10, 21, 42):
                fwd = (o.shift(-(1 + h)) / o.shift(-1) - 1).where(tr).to_numpy()
                ic_rev = pd.Series(rank_ic(z_rev.to_numpy(), fwd), index=dates)
                ic_mom = pd.Series(rank_ic(z_mom.to_numpy(), fwd), index=dates)
                reb = np.zeros(len(dates), bool)
                reb[::h] = True
                w_rev, w_mom = monthly_weights(z_rev, mask, reb), monthly_weights(z_mom, mask, reb)
                plain = portfolio_stats(w_rev, r1, cost)["net"]
                base = {"universe": uni_name, "books": bname, "rebalance_days": h}
                st = summarize(portfolio_stats(w_rev, r1, cost))
                rows.append({**base, "regime": "(plain reversal)", "net_sharpe_1st": st["net_sharpe_1st"],
                             "net_sharpe_2nd": st["net_sharpe_2nd"], "breakeven_bp_2nd": st["breakeven_bp_2nd"]})
                for rname, P in regimes.items():
                    import qtrade.research.switch_lab as SL

                    SL.HORIZON = h                      # the IC lag used when learning per-regime ICs
                    s = regime_split(P, ic_rev, ic_mom, reb, signed=True)
                    w = w_rev.mul(s["rev"].fillna(0.5), axis=0) + w_mom.mul(s["mom"].fillna(0.5), axis=0)
                    ps = portfolio_stats(w, r1, cost)
                    st = summarize(ps)
                    rows.append({**base, "regime": rname, "net_sharpe_1st": st["net_sharpe_1st"],
                                 "net_sharpe_2nd": st["net_sharpe_2nd"], "breakeven_bp_2nd": st["breakeven_bp_2nd"],
                                 "turnover": st["turnover_1st"]})
                    series[(uni_name, bname, h, rname)] = (ps["net"], plain)
                LOG.info("robust: %s %s h=%d done", uni_name, bname, h)
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "switch_robust.csv", index=False)

    # headline: composites, 21 days, all names, first HMM given (else vol terciles)
    head_regime = Path(args.probs[0]).stem if args.probs else "vol_tercile"
    net, plain = series[("all", "composites", 21, head_regime)]
    both = pd.DataFrame({"switch": net, "plain_reversal": plain, "market": mkt}).dropna()
    yearly = both.groupby(both.index.year).agg(lambda s: s.mean() * 252).rename(columns=lambda c: f"{c}_return")
    yearly["switch_sharpe"] = both["switch"].groupby(both.index.year).apply(_sharpe)
    yearly = yearly[yearly.index >= 2004]
    sub = {}
    for tag, m in (("2004_14", (both.index >= "2004-01-01") & (both.index < SPLIT)),
                   ("2015_20", (both.index >= SPLIT) & (both.index < HALF)), ("2021_26", both.index >= HALF)):
        sub[tag] = {"switch": _sharpe(both["switch"][m]), "plain_reversal": _sharpe(both["plain_reversal"][m]),
                    "corr_market": float(both["switch"][m].corr(both["market"][m])),
                    "corr_plain_reversal": float(both["switch"][m].corr(both["plain_reversal"][m]))}
    second = both[both.index >= SPLIT]
    boot = block_bootstrap(second["switch"].to_numpy(), second["plain_reversal"].to_numpy())
    boot_first = block_bootstrap(both[(both.index >= "2004-01-01") & (both.index < SPLIT)]["switch"].to_numpy())
    summary = {"headline": {"universe": "all", "books": "composites", "rebalance_days": 21, "regime": head_regime},
               "subperiods": sub, "bootstrap_2015_26": boot, "bootstrap_2004_14": boot_first}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    piv = tab.pivot_table(index=["universe", "books", "rebalance_days"], columns="regime",
                          values=["net_sharpe_1st", "net_sharpe_2nd"])
    lines = ["# Switch robustness", "",
             "Signed regime switch between a reversal and a momentum book (capital by regime-conditional IC learned "
             "walk-forward), net of measured costs, under every variation of the design choices. '(plain reversal)' "
             "is the reversal book alone at the same rebalance interval.", "",
             piv.round(2).to_markdown(), "",
             f"## Headline configuration: {head_regime}, composites, 21-day rebalance, all names", "",
             pd.DataFrame(sub).T.round(3).to_markdown(), "",
             "### Net return by year", "", yearly.round(3).to_markdown(), "",
             "### 21-day block bootstrap of the 2015-2026 Sharpe (2,000 draws)", "",
             pd.Series(boot).round(3).to_frame("value").to_markdown(), "",
             "### Same for 2004-2014", "", pd.Series(boot_first).round(3).to_frame("value").to_markdown(), ""]
    (out / "switch_robust.md").write_text("\n".join(lines) + "\n")
    print(piv.round(2).to_string())
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
