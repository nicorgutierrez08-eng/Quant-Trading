"""Switch lab: a slow momentum / reversal book that follows the regime.

The invariants lab found that at a monthly horizon the cross-sectional edge is
a *sign pattern*: reversal signals pay when market volatility is high and
momentum / trend signals pay when it is low, in every sub-period since 2004.
This study trades that pattern as cheaply as possible:

* two books, rebalanced every 21 trading days and held in between: a monthly
  reversal book (rev_21d + bollinger_z + rsi_14, equal-weighted z-scores) and
  a momentum book (mom_12_1 + resid_mom + high_52w);
* capital split between them from the regime probabilities at the rebalance
  date x each book's per-regime IC on the training block (walk-forward, yearly
  refits, nothing chosen on 2015-2026), vs. 50/50, vs. each book alone;
* regimes from the regime lab's HMM probabilities (``--probs``) and, for
  comparison, terciles of trailing market volatility.

Costs: measured spreads by liquidity tier + 1 bp, charged on every weight change.

    python -m qtrade.research.switch_lab --lab data/lab --probs reports/regime_lab/probs/<best>.parquet
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, rank_ic, setup_logging
from .book_lab import tercile_probs
from .edge import SPLIT, _weights, cost_panel, portfolio_stats, summarize

HORIZON = 21
REV = ["rev_21d", "bollinger_z", "rsi_14"]
MOM = ["mom_12_1", "resid_mom", "high_52w"]


def _z(df: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    x = df.where(mask)
    return x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1) + 1e-12, axis=0)


def composite(X: np.ndarray, names: list[str], members: list[str], index, columns, mask) -> pd.DataFrame:
    zs = [_z(pd.DataFrame(X[..., names.index(m)], index=index, columns=columns), mask) for m in members if m in names]
    return sum(zs) / len(zs)


def monthly_weights(z: pd.DataFrame, mask: pd.DataFrame, rebalance: np.ndarray) -> pd.DataFrame:
    """Unit-gross long/short weights set on rebalance days and held until the next one."""
    w = _weights(z, mask)
    held = w.where(pd.Series(rebalance, index=z.index), np.nan).ffill().fillna(0.0)
    return held


def regime_split(P: pd.DataFrame, ic_rev: pd.Series, ic_mom: pd.Series, rebalance: np.ndarray,
                 signed: bool = False, refit_every: int = 252, min_history: int = 756) -> pd.DataFrame:
    """Capital in each book at each rebalance, from the predicted ICs: the regime
    probabilities x per-regime ICs measured on the training block (ICs are known
    22 days later). Unsigned: shares = predicted ICs floored at zero, summing to
    one. Signed: a book with a negative predicted IC is traded the other way
    (short momentum in a stressed regime), weights normalised to unit gross."""
    idx = P.index
    Pv = P.to_numpy()
    valid = np.isfinite(Pv).all(axis=1)
    first = int(np.argmax(valid))
    out = pd.DataFrame(np.nan, index=idx, columns=["rev", "mom"])
    ir, im = ic_rev.to_numpy(), ic_mom.to_numpy()
    for r in range(first + min_history, len(idx), refit_every):
        train = np.zeros(len(idx), bool)
        train[first:r - HORIZON - 1] = True
        ok = train & np.isfinite(ir) & np.isfinite(im) & valid
        Pt = Pv[ok]
        rev_k = (Pt * ir[ok, None]).sum(0) / (Pt.sum(0) + 1e-9)
        mom_k = (Pt * im[ok, None]).sum(0) / (Pt.sum(0) + 1e-9)
        test = np.zeros(len(idx), bool)
        test[r:min(r + refit_every, len(idx))] = True
        pr, pm = Pv[test] @ rev_k, Pv[test] @ mom_k
        if not signed:
            pr, pm = np.clip(pr, 0, None), np.clip(pm, 0, None)
        tot = np.abs(pr) + np.abs(pm) + 1e-9
        out.loc[test, "rev"], out.loc[test, "mom"] = pr / tot, pm / tot
    # decided at the rebalance date, held until the next
    return out.where(pd.Series(rebalance, index=idx), np.nan).ffill()


def run(md, ctx, X, names, probs: dict[str, pd.DataFrame], out: Path) -> pd.DataFrame:
    dates, tickers = md.dates, md.tickers
    tr = ctx.tradable
    liquid = tr & (ctx.adv.where(tr).rank(axis=1, ascending=False) <= 300)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5)
    cost = cost_panel(ctx)
    fwd = (o.shift(-(1 + HORIZON)) / o.shift(-1) - 1).where(tr).to_numpy()
    rebalance = np.zeros(len(dates), bool)
    rebalance[::HORIZON] = True
    rows, daily = [], {}
    for uni_name, mask in (("all", tr), ("top300", liquid)):
        z_rev = composite(X, names, REV, dates, tickers, mask)
        z_mom = composite(X, names, MOM, dates, tickers, mask)
        ic_rev = pd.Series(rank_ic(z_rev.to_numpy(), fwd), index=dates)
        ic_mom = pd.Series(rank_ic(z_mom.to_numpy(), fwd), index=dates)
        w_rev = monthly_weights(z_rev, mask, rebalance)
        w_mom = monthly_weights(z_mom, mask, rebalance)
        books = {"reversal (monthly)": w_rev, "momentum (monthly)": w_mom, "50/50": 0.5 * w_rev + 0.5 * w_mom}
        for pname, P in probs.items():
            for signed in (False, True):
                s = regime_split(P.reindex(dates), ic_rev, ic_mom, rebalance, signed=signed)
                tag = f"regime switch{' (signed)' if signed else ''}: {pname}"
                books[tag] = w_rev.mul(s["rev"].fillna(0.5), axis=0) + w_mom.mul(s["mom"].fillna(0.5), axis=0)
                daily[f"{uni_name}|share_rev|{tag}"] = s["rev"]
                daily[f"{uni_name}|share_mom|{tag}"] = s["mom"]
        for bname, w in books.items():
            st = summarize(portfolio_stats(w, r1, cost))
            rows.append({"universe": uni_name, "book": bname, **st})
            daily[f"{uni_name}|{bname}"] = portfolio_stats(w, r1, cost)["net"]
            LOG.info("switch lab %s %s: net Sharpe %.2f / %.2f", uni_name, bname, st["net_sharpe_1st"], st["net_sharpe_2nd"])
        # the regime-conditional ICs themselves, 2015-26, for the first regime model
        pname, P = next(iter(probs.items()))
        Pm = P.reindex(dates)
        m = (dates >= SPLIT) & Pm.notna().all(axis=1).to_numpy()
        for k in range(Pm.shape[1]):
            wk = Pm.iloc[:, k].to_numpy()[m]
            okr = np.isfinite(ic_rev.to_numpy()[m]) & np.isfinite(ic_mom.to_numpy()[m])
            rows.append({"universe": uni_name, "book": f"IC in regime {k} ({pname}), 2015-26",
                         "ic_rev": float((wk[okr] * ic_rev.to_numpy()[m][okr]).sum() / wk[okr].sum()),
                         "ic_mom": float((wk[okr] * ic_mom.to_numpy()[m][okr]).sum() / wk[okr].sum()),
                         "share_of_days": float(wk.mean())})
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "switch_lab.csv", index=False)
    pd.DataFrame(daily).to_csv(out / "switch_daily.csv")
    cols = ["universe", "book", "gross_sharpe_1st", "net_sharpe_1st", "breakeven_bp_1st", "turnover_1st",
            "gross_sharpe_2nd", "net_sharpe_2nd", "breakeven_bp_2nd"]
    books = tab[tab["book"].str.contains("IC in regime") == False]
    ics = tab[tab["book"].str.contains("IC in regime")]
    lines = ["# Switch lab: monthly momentum / reversal book that follows the regime", "",
             "Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = "
             "rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share "
             "of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the "
             "prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the "
             "training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.", "",
             books[cols].round(3).to_markdown(index=False), "",
             "## Monthly IC of each book by regime, 2015-2026", "",
             ics[["universe", "book", "ic_rev", "ic_mom", "share_of_days"]].round(4).to_markdown(index=False), ""]
    (out / "switch_lab.md").write_text("\n".join(lines) + "\n")
    return tab


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--probs", nargs="*", default=[])
    ap.add_argument("--out", default="reports/switch_lab")
    ap.add_argument("--rev", default=",".join(REV), help="signals in the reversal book")
    ap.add_argument("--mom", default=",".join(MOM), help="signals in the momentum book")
    args = ap.parse_args(argv)
    REV[:] = args.rev.split(",")
    MOM[:] = args.mom.split(",")
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    md, ctx, X, names = load(args.lab)
    probs = {Path(f).stem: pd.read_parquet(f) for f in args.probs}
    probs["vol_tercile"] = tercile_probs(ctx.market_ret.rolling(21).std())
    tab = run(md, ctx, X, names, probs, out)
    (out / "summary.json").write_text(json.dumps({"rows": len(tab)}, indent=2))
    print(tab[["universe", "book", "net_sharpe_1st", "net_sharpe_2nd"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
