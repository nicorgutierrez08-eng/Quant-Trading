"""Book lab: does knowing the regime improve how capital is split across strategies?

Hedge funds use regime models mostly for *risk budgeting*: tilt towards the
strategies that have historically paid in the current regime and away from the
ones that have not. This study tests that on the daily net returns of every
strategy in the research (``research_data/studies/strategy_returns.csv``), the
ETF sleeve book and the stock book, with walk-forward regime probabilities from
the regime lab.

Allocation rules, all with yearly refits and nothing chosen on 2015-2026:

* ``inverse_vol``: Arjun's rule, weight 1 / trailing volatility (the baseline);
* ``regime``: inverse vol x clip(predicted Sharpe / average Sharpe, 0, 2), where
  the predicted Sharpe is the regime probabilities times each strategy's
  per-regime Sharpe measured on the training block;
* ``vol_tercile`` / ``vix_tercile``: the same rule with a dumb "regime" - the
  tercile of trailing 21-day market volatility (or of VIX) - to check whether
  the HMM adds anything a volatility filter does not.

Books: the 8 ETF sleeves, the sleeves plus the stock book, and every strategy
positive in 2006-2014 (the research's own selection rule).

    python -m qtrade.research.book_lab --probs reports/regime_lab/probs/garch_t_K3_s0.0_t1.0.parquet
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..portfolio.sleeves import DEFAULT_SLEEVES
from ..utils import LOG, setup_logging

SPLIT = "2015-01-01"
TRAIN_START = "2004-01-01"


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 20 and x.std() > 0 else np.nan


def _stats(r: pd.Series, label: str) -> dict:
    out = {"book": label}
    for tag, m in (("2006_14", (r.index >= "2006-01-01") & (r.index < SPLIT)), ("2015_26", r.index >= SPLIT)):
        x = r[m].dropna()
        out[f"sharpe_{tag}"] = _sharpe(x)
        out[f"return_{tag}"] = float(x.mean() * 252)
        eq = (1 + x).cumprod()
        out[f"max_dd_{tag}"] = float((eq / eq.cummax() - 1).min()) if len(x) else np.nan
    return out


def tercile_probs(x: pd.Series) -> pd.DataFrame:
    """One-hot 'regimes' from the expanding-window terciles of a series (no lookahead)."""
    lo = x.expanding(min_periods=500).quantile(1 / 3).shift(1)
    hi = x.expanding(min_periods=500).quantile(2 / 3).shift(1)
    P = pd.DataFrame({"regime_0": (x <= lo).astype(float), "regime_1": ((x > lo) & (x <= hi)).astype(float),
                      "regime_2": (x > hi).astype(float)}, index=x.index)
    return P.where(lo.notna())


def regime_sharpe_forecast(R: pd.DataFrame, P: pd.DataFrame, refit_every: int = 252) -> pd.DataFrame:
    """Predicted Sharpe of each strategy for each day: regime probabilities x
    per-regime Sharpe on the training block (data up to the last refit, with the
    returns of the refit day itself excluded)."""
    idx = R.index
    P = P.reindex(idx)
    out = pd.DataFrame(np.nan, index=idx, columns=R.columns)
    start = int(np.argmax(idx >= TRAIN_START)) + 504
    for r in range(start, len(idx), refit_every):
        train = slice(0, r)
        test = slice(r, min(r + refit_every, len(idx)))
        Pt = P.iloc[train].to_numpy()
        Rt = R.iloc[train].to_numpy()
        ok = np.isfinite(Pt).all(1)
        for j, col in enumerate(R.columns):
            y = Rt[:, j]
            m = ok & np.isfinite(y)
            if m.sum() < 250:
                continue
            w = Pt[m]
            mu_k = (w * y[m, None]).sum(0) / (w.sum(0) + 1e-9)
            v_k = (w * y[m, None] ** 2).sum(0) / (w.sum(0) + 1e-9) - mu_k ** 2
            sr_k = mu_k / np.sqrt(np.maximum(v_k, 1e-12)) * np.sqrt(252)
            out.iloc[test, j] = P.iloc[test].to_numpy() @ sr_k
    return out


MAX_WEIGHT = 1.0          # per-strategy cap on the share of risk-weighted capital (1 = no cap)


def allocate(R: pd.DataFrame, pred_sr: pd.DataFrame | None, vol_window: int = 756, cap: float = 2.0) -> pd.Series:
    """Book return with inverse-vol weights, optionally tilted by predicted Sharpe
    relative to each strategy's trailing average Sharpe. Weights decided at t
    are held over t+2 (research convention), normalised to sum to one (with an
    optional per-strategy cap, ``MAX_WEIGHT``), 10% vol target."""
    vol = R.rolling(vol_window, min_periods=126).std()
    w = 1 / vol
    if pred_sr is not None:
        avg = (R.rolling(vol_window, min_periods=252).mean() / vol * np.sqrt(252)).clip(lower=0.05)
        tilt = (pred_sr / avg).clip(0, cap)
        w = w * tilt.fillna(1.0)
    w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0)
    if MAX_WEIGHT < 1.0:
        for _ in range(5):                       # clip and renormalise until no weight exceeds the cap
            w = w.clip(upper=MAX_WEIGHT)
            w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0)
    blend = (w.shift(2) * R.fillna(0)).sum(axis=1)
    real = blend.rolling(252, min_periods=126).std() * np.sqrt(252)
    lev = (0.10 / real).clip(0, 3).shift(2)
    return (blend * lev).where(w.shift(2).notna().any(axis=1))


def run(strategies: pd.DataFrame, probs: dict[str, pd.DataFrame], out: Path, stock_book: pd.Series | None) -> pd.DataFrame:
    R = strategies.copy()
    if stock_book is not None:
        R["stock_book"] = stock_book.reindex(R.index)
    sleeves = [s for s in DEFAULT_SLEEVES if s in R]
    first = R[(R.index >= "2006-01-01") & (R.index < SPLIT)]
    positive = [c for c in R if _sharpe(first[c]) > 0.3 and c not in ("spy_buy_hold",)]
    books = {"8 ETF sleeves": sleeves, "sleeves + stock book": sleeves + (["stock_book"] if "stock_book" in R else []),
             f"all {len(positive)} strategies with 2006-14 Sharpe > 0.3": positive}
    if "pairs" in R:
        books["sleeves + pairs"] = sleeves + ["pairs"]
    extras = [c for c in R if c.startswith("switch")]
    if extras:
        books["sleeves + regime switch"] = sleeves + extras
        books["sleeves + stock book + regime switch"] = sleeves + (["stock_book"] if "stock_book" in R else []) + extras
        if "pairs" in R:
            books["sleeves + regime switch + pairs"] = sleeves + extras + ["pairs"]
            books["sleeves + stock book + regime switch + pairs"] = sleeves + (["stock_book"] if "stock_book" in R else []) + extras + ["pairs"]
    rows = []
    for bname, cols in books.items():
        Rb = R[cols]
        rows.append({**_stats(allocate(Rb, None), f"{bname} | inverse_vol"), "rule": "inverse_vol", "book_set": bname})
        for pname, P in probs.items():
            sr = regime_sharpe_forecast(Rb, P)
            rows.append({**_stats(allocate(Rb, sr), f"{bname} | {pname}"), "rule": pname, "book_set": bname})
        LOG.info("book lab: %s done", bname)
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "book_lab.csv", index=False)
    # per-strategy regime-conditional Sharpe (2015-26, out of sample) for the first HMM given
    pname, P = next(iter(probs.items()))
    Pm = P.reindex(R.index)
    m = (R.index >= SPLIT) & Pm.notna().all(axis=1).to_numpy()
    cond = {}
    for c in R:
        y = R[c][m]
        w = Pm[m]
        cond[c] = {f"sharpe_{k}": float(((w.iloc[:, k] * y).sum() / w.iloc[:, k].sum())
                                        / np.sqrt(((w.iloc[:, k] * y ** 2).sum() / w.iloc[:, k].sum())) * np.sqrt(252))
                   for k in range(Pm.shape[1])}
        cond[c]["share_of_days"] = [round(float(v), 2) for v in w.mean()]
    ctab = pd.DataFrame(cond).T
    ctab.to_csv(out / "strategy_by_regime.csv")
    lines = ["# Book lab: regime-aware capital allocation across strategies", "",
             "Baseline: inverse-volatility weights (the research's rule). Regime rules multiply those weights by "
             "the predicted Sharpe relative to each strategy's trailing Sharpe (0-2x), where the prediction is "
             "the regime probabilities times the strategy's Sharpe in each regime on the training block. "
             "``vol_tercile`` / ``vix_tercile`` use terciles of trailing market volatility / VIX instead of an "
             "HMM, to show what a plain volatility filter achieves. All weights decided at t, held over t+2, "
             "scaled to 10% volatility.", "",
             tab[["book_set", "rule", "sharpe_2006_14", "sharpe_2015_26", "return_2015_26", "max_dd_2015_26"]]
             .round(3).to_markdown(index=False), "",
             f"## Each strategy's Sharpe by regime, 2015-2026 ({pname})", "",
             ctab.round(2).to_markdown(), ""]
    (out / "book_lab.md").write_text("\n".join(lines) + "\n")
    return tab


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--probs", nargs="*", default=[], help="walk-forward regime probability parquet files")
    ap.add_argument("--research", default="research_data")
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--out", default="reports/book_lab")
    ap.add_argument("--extra", nargs="*", default=[],
                    help="extra daily-return series to add as strategies, as CSV_PATH::COLUMN::NAME")
    ap.add_argument("--max-weight", type=float, default=1.0, help="cap on any one strategy's share of capital")
    args = ap.parse_args(argv)
    global MAX_WEIGHT
    MAX_WEIGHT = args.max_weight
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rd = Path(args.research)
    strategies = pd.read_csv(rd / "studies" / "strategy_returns.csv", index_col=0, parse_dates=True)
    for spec in args.extra:
        path, col, name = spec.split("::")
        s = pd.read_csv(path, index_col=0, parse_dates=True)[col]
        strategies[name] = s.reindex(strategies.index)
        LOG.info("added strategy %s from %s (%d days)", name, path, s.notna().sum())
    stock = None
    p = rd / "backtest" / "daily.csv"
    if p.exists():
        stock = pd.read_csv(p, index_col=0, parse_dates=True)["ret"]
    probs = {}
    for f in args.probs:
        probs[Path(f).stem] = pd.read_parquet(f)
    spy = strategies["spy_buy_hold"] if "spy_buy_hold" in strategies else None
    if spy is not None:
        probs["vol_tercile"] = tercile_probs(spy.rolling(21).std())
    fp = Path(args.lab) / "fred.parquet"
    if fp.exists():
        fred = pd.read_parquet(fp)
        if "vix" in fred:
            probs["vix_tercile"] = tercile_probs(fred["vix"].reindex(strategies.index).ffill())
    tab = run(strategies, probs, out, stock)
    (out / "summary.json").write_text(json.dumps({"rows": len(tab)}, indent=2))
    print(tab[["book_set", "rule", "sharpe_2006_14", "sharpe_2015_26"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
