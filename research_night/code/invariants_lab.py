"""Invariants lab: which relationships in this market are stable, which drift, which depend on the regime?

For every signal in the library, the daily cross-sectional rank IC against the
next 5 days' open-to-open return, then:

* **invariant**: same sign in all four sub-periods (2004-09, 2010-14, 2015-20,
  2021-26), |t| > 3 overall, and no significant trend in the yearly IC;
* **decaying** (a monovariant - it only goes one way): the yearly |IC| has a
  significantly negative slope; the table gives the slope and the year the
  trend line crosses zero;
* **regime-dependent**: the IC in the most stressed regime differs from the
  calmest by more than 2x (walk-forward HMM probabilities if given, else
  terciles of trailing market volatility);
* **noise**: none of the above.

Also a few structural series by year (average correlation, dispersion, jump
frequency, market autocorrelation) so drifts in the market itself are visible.

    python -m qtrade.research.invariants_lab --lab data/lab --probs reports/regime_lab/probs/<best>.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..signals import REGISTRY
from ..utils import LOG, rank_ic, setup_logging

PERIODS = [("2004_09", "2004-01-01", "2010-01-01"), ("2010_14", "2010-01-01", "2015-01-01"),
           ("2015_20", "2015-01-01", "2021-01-01"), ("2021_26", "2021-01-01", "2027-01-01")]
HORIZON = 5


def trend(yearly: pd.Series) -> tuple[float, float, float]:
    """OLS slope of yearly |IC| on year, its t-stat, and the zero-crossing year."""
    y = yearly.dropna()
    if len(y) < 6:
        return np.nan, np.nan, np.nan
    x = y.index.to_numpy(dtype=float)
    X = np.column_stack([np.ones_like(x), x])
    beta, res, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
    resid = y.to_numpy() - X @ beta
    s2 = (resid ** 2).sum() / max(len(y) - 2, 1)
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1])
    zero = -beta[0] / beta[1] if beta[1] != 0 else np.nan
    return float(beta[1]), float(beta[1] / se) if se > 0 else np.nan, float(zero)


def classify(row: pd.Series) -> str:
    signs = np.sign([row[f"ic_{p}"] for p, *_ in PERIODS])
    same = (signs == signs[0]).all() and signs[0] != 0
    if same and abs(row["t_all"]) > 3 and abs(row["trend_t"]) < 2:
        return "invariant"
    if row["trend_t"] < -2.5 and abs(row["ic_2004_09"]) > 0.005:
        return "decaying"
    if np.isfinite(row["ic_ratio_stressed_calm"]) and (row["ic_ratio_stressed_calm"] > 2 or row["ic_ratio_stressed_calm"] < 0.5) \
            and abs(row["t_all"]) > 2:
        return "regime-dependent"
    if same and abs(row["t_all"]) > 2:
        return "stable but weak"
    return "noise"


def main(argv=None):
    global HORIZON
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--probs")
    ap.add_argument("--out", default="reports/invariants_lab")
    ap.add_argument("--horizon", type=int, default=HORIZON, help="forecast horizon in days (5 or 21)")
    args = ap.parse_args(argv)
    HORIZON = args.horizon
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    md, ctx, X, names = load(args.lab)
    o = md.open
    fwd = (o.shift(-(1 + HORIZON)) / o.shift(-1) - 1).where(ctx.tradable).to_numpy()
    dates = md.dates
    years = dates.year
    # regime weights: HMM probabilities (calm = col 0, stressed = last) or vol terciles
    if args.probs:
        P = pd.read_parquet(args.probs).reindex(dates)
        calm, stressed = P.iloc[:, 0].to_numpy(), P.iloc[:, -1].to_numpy()
        regime_label = Path(args.probs).stem
    else:
        v = ctx.market_ret.rolling(21).std()
        lo, hi = v.expanding(500).quantile(1 / 3).shift(1), v.expanding(500).quantile(2 / 3).shift(1)
        calm, stressed = (v <= lo).astype(float).to_numpy(), (v > hi).astype(float).to_numpy()
        regime_label = "trailing-vol terciles"
    rows, yearly_all = [], {}
    for j, name in enumerate(names):
        ic = pd.Series(rank_ic(X[..., j], fwd), index=dates)
        ok = ic.notna().to_numpy()
        row = {"signal": name, "family": REGISTRY[name].family if name in REGISTRY else ""}
        a = ic.dropna()
        row["ic_all"] = a.mean()
        row["t_all"] = a.mean() / a.std() * np.sqrt(len(a) / HORIZON)
        for p, lo_, hi_ in PERIODS:
            b = ic[(ic.index >= lo_) & (ic.index < hi_)].dropna()
            row[f"ic_{p}"] = b.mean()
            row[f"t_{p}"] = b.mean() / b.std() * np.sqrt(len(b) / HORIZON) if len(b) > 50 else np.nan
        yr = ic.groupby(years).mean()
        yr = yr[(yr.index >= 2004) & (yr.index <= 2026)]
        yearly_all[name] = yr
        sgn = np.sign(row["ic_all"]) or 1.0
        row["trend_slope_per_decade"], row["trend_t"], row["zero_year"] = trend(yr * sgn)
        row["trend_slope_per_decade"] *= 10
        row["years_positive"] = float((yr * sgn > 0).mean())
        w_c, w_s = calm[ok], stressed[ok]
        icv = ic.to_numpy()[ok]
        ic_c = (w_c * icv).sum() / w_c.sum() if w_c.sum() > 10 else np.nan
        ic_s = (w_s * icv).sum() / w_s.sum() if w_s.sum() > 10 else np.nan
        row["ic_calm"], row["ic_stressed"] = ic_c, ic_s
        row["ic_ratio_stressed_calm"] = ic_s / ic_c if ic_c not in (0, np.nan) and np.isfinite(ic_c) and abs(ic_c) > 1e-4 else np.nan
        rows.append(row)
        LOG.info("invariants: %s ic %.4f t %.1f trend_t %.1f", name, row["ic_all"], row["t_all"], row["trend_t"])
    tab = pd.DataFrame(rows)
    tab["class"] = tab.apply(classify, axis=1)
    tab = tab.sort_values(["class", "t_all"], key=lambda s: s if s.name != "class" else s.map(
        {"invariant": 0, "decaying": 1, "regime-dependent": 2, "stable but weak": 3, "noise": 4}), ascending=[True, False])
    tab.to_csv(out / "signal_invariants.csv", index=False)
    pd.DataFrame(yearly_all).to_csv(out / "signal_ic_by_year.csv")

    # structural series by year
    r = ctx.ret.clip(-0.5, 0.5).where(ctx.tradable)
    mkt = ctx.market_ret
    e = ctx.resid
    z = e / e.rolling(63, min_periods=40).std().shift(1)
    struct = pd.DataFrame({
        "market_vol_ann": mkt.groupby(years).std() * np.sqrt(252),
        "avg_dispersion": r.std(axis=1).groupby(years).mean(),
        "corr_share": ctx.market_state["corr_share"].groupby(years).mean(),
        "jumps_per_day": (z.abs() > 3).sum(axis=1).groupby(years).mean(),
        "mkt_autocorr_1d": mkt.groupby(years).apply(lambda s: s.autocorr(1)),
        "stock_autocorr_1d_avg": r.groupby(years).apply(lambda d: d.apply(lambda s: s.autocorr(1)).mean()),
        "n_tradable": ctx.tradable.sum(axis=1).groupby(years).mean(),
    })
    struct = struct[(struct.index >= 2004)]
    struct.to_csv(out / "structure_by_year.csv")
    st_rows = []
    for c in struct:
        s, t, _ = trend(struct[c])
        st_rows.append({"series": c, "mean_2004_14": struct[c][struct.index < 2015].mean(),
                        "mean_2015_26": struct[c][struct.index >= 2015].mean(), "trend_t": t})
    stt = pd.DataFrame(st_rows)

    cols = ["signal", "family", "class", "ic_all", "t_all", "ic_2004_09", "ic_2010_14", "ic_2015_20", "ic_2021_26",
            "years_positive", "trend_slope_per_decade", "trend_t", "zero_year", "ic_calm", "ic_stressed",
            "ic_ratio_stressed_calm"]
    lines = ["# Invariants lab: what is stable, what decays, what depends on the regime", "",
             f"5-day rank IC of every library signal, 2004-2026, 1,000-stock universe. Regimes: {regime_label}.", "",
             "Classes: **invariant** = same sign in all four sub-periods, |t| > 3, no trend in the yearly IC; "
             "**decaying** = yearly |IC| falls significantly (slope per decade and the year the trend hits zero); "
             "**regime-dependent** = IC in the stressed regime is >2x or <0.5x the calm one.", "",
             tab[cols].round(4).to_markdown(index=False), "",
             "## Class counts", "", tab["class"].value_counts().to_frame("signals").to_markdown(), "",
             "## Market structure by year (trend t-stat: is the market itself drifting?)", "",
             stt.round(3).to_markdown(index=False), "", struct.round(4).to_markdown(), ""]
    (out / "invariants_lab.md").write_text("\n".join(lines) + "\n")
    print(tab["class"].value_counts())


if __name__ == "__main__":
    main()
