"""Jump lab: make the Poisson jump-rate regressions work out of sample.

The original study (``poisson.jump_regressions``) fitted one Poisson GLM on
2004-2014 and applied it to 2015-2026: the up-jump model's deviance explained
collapsed to -2.2 out of sample. Two likely causes, both fixable:

* **Level drift.** Dollar volume, volatility and jump memory all trend over 20
  years; with a log link, an extrapolated feature multiplies the rate. Fix:
  rank-gaussianise every stock-level feature within each day, so the model
  only sees *relative* position, and refit walk-forward every year on the
  previous five.
* **Base-rate drift.** The market-wide jump rate moves with the regime. Fix: an
  exposure offset - the model predicts each stock's rate *relative to* the
  trailing market jump rate - and a negative-binomial error for the
  overdispersion (variance / mean of daily jump counts is 24).

Each variant is scored on out-of-sample deviance explained and on the daily
cross-sectional rank correlation between predicted and realised next-month
jump counts (what matters for ranking stocks). The predicted intensities are
then tested two ways, walk-forward:

1. as alpha signals (``pred_crash_intensity``, ``pred_jump_skew``), net of costs;
2. as a *risk filter* on the 5-day reversal book: drop or down-weight the stocks
   most likely to jump, and see whether the book's net Sharpe improves.

    python -m qtrade.research.jump_lab --lab data/lab --out reports/jump_lab
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, cs_rank_gauss, rank_ic, setup_logging
from .edge import SPLIT, Bench, _weights, portfolio_stats, summarize
from .poisson import decayed_sums, jump_panels

TRAIN_YEARS = 5
HORIZON = 21


def features(md, ctx, up: pd.DataFrame, down: pd.DataFrame) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Stock-level features (T x N, to be ranked within each day) and
    market-level ones (T, shared by every stock), all known at the close of t."""
    tr = ctx.tradable
    both = (up.fillna(0) + down.fillna(0)).to_numpy()
    n_trad = tr.sum(1).clip(lower=1).to_numpy()
    mkt_rate = (up.sum(1) + down.sum(1)).to_numpy() / n_trad                     # share of stocks jumping
    stock = {
        "own_jumps_fast": decayed_sums(both, np.log(2) / 5),
        "own_jumps_slow": decayed_sums(both, np.log(2) / 63),
        "own_down_slow": decayed_sums(down.fillna(0).to_numpy(), np.log(2) / 63),
        "log_vol_63": np.log(ctx.vol_63.to_numpy() + 1e-4),
        "vol_ratio_5_63": np.log((ctx.ret.rolling(5).std() / ctx.vol_63).to_numpy() + 1e-3),
        "abn_volume_5d": np.log((md.volume.rolling(5).mean() / md.volume.rolling(63).mean()).to_numpy() + 1e-6),
        "log_dollar_volume": np.log(ctx.adv.to_numpy() + 1),
        "ret_21d": ctx.log_ret.rolling(21).sum().to_numpy(),
        "ret_5d": ctx.log_ret.rolling(5).sum().to_numpy(),
        "idio_share": (ctx.resid.rolling(63, min_periods=40).var() / ctx.ret.rolling(63, min_periods=40).var()
                       ).clip(0, 1).to_numpy(),
    }
    market = {
        "market_jumps_fast": decayed_sums(mkt_rate[:, None], np.log(2) / 5)[:, 0],
        "market_jumps_slow": decayed_sums(mkt_rate[:, None], np.log(2) / 63)[:, 0],
        "log_market_vol_21": np.log(ctx.market_ret.rolling(21).std().to_numpy() + 1e-5),
    }
    return stock, market


def design(stock: dict, market: dict, ranked: bool) -> tuple[np.ndarray, list[str]]:
    """T x N x F design: stock features (raw or rank-gaussianised per day) plus market features."""
    T, N = next(iter(stock.values())).shape
    cols, names = [], []
    for k, v in stock.items():
        x = cs_rank_gauss(pd.DataFrame(v)).to_numpy() if ranked else v
        cols.append(x.astype(np.float32))
        names.append(k)
    for k, v in market.items():
        cols.append(np.repeat(v[:, None], N, axis=1).astype(np.float32))
        names.append(k)
    return np.stack(cols, axis=-1), names


def deviance_explained(y: np.ndarray, p: np.ndarray, base: float | np.ndarray) -> float:
    def dev(mu):
        return 2 * np.sum(np.where(y > 0, y * np.log(np.maximum(y, 1e-12) / mu), 0) - (y - mu))
    return float(1 - dev(np.maximum(p, 1e-9)) / dev(np.maximum(base, 1e-9)))


def fit_predict(Xtr, ytr, Xte, family: str, off_tr=None, off_te=None, alpha_l2: float = 1e-4):
    """Poisson (sklearn) or negative binomial (statsmodels) GLM with log link and optional log-exposure offset."""
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12
    Ztr, Zte = (Xtr - mu) / sd, (Xte - mu) / sd
    if family == "poisson":
        from sklearn.linear_model import PoissonRegressor

        if off_tr is None:
            m = PoissonRegressor(alpha=alpha_l2, max_iter=1000).fit(Ztr, ytr)
            return m.predict(Zte), m.coef_
        # sklearn has no offset: fit with the exposure as sample weight on y/exposure (equivalent for Poisson)
        e_tr = np.exp(off_tr)
        m = PoissonRegressor(alpha=alpha_l2, max_iter=1000).fit(Ztr, ytr / e_tr, sample_weight=e_tr)
        return m.predict(Zte) * np.exp(off_te), m.coef_
    import statsmodels.api as sm

    A = sm.add_constant(Ztr, has_constant="add")
    B = sm.add_constant(Zte, has_constant="add")
    fam = sm.families.NegativeBinomial(alpha=1.0) if family == "negbin" else sm.families.Poisson()
    res = sm.GLM(ytr, A, family=fam, offset=off_tr).fit()           # IRLS; the features are standardised
    pred = res.predict(B, offset=off_te) if off_te is not None else res.predict(B)
    return np.asarray(pred), np.asarray(res.params)[1:]


def walk_forward_glm(F: np.ndarray, Y: np.ndarray, dates: pd.DatetimeIndex, tradable: np.ndarray, family: str,
                     offset: np.ndarray | None, once: bool) -> tuple[np.ndarray, pd.DataFrame]:
    """Per-stock predicted next-21-day jump counts for every day. ``once``
    reproduces the original design (one fit on 2004-2014); otherwise refit
    yearly on the previous five years of non-overlapping 21-day windows."""
    T, N, K = F.shape
    sample_days = np.arange(300, T - HORIZON - 1, HORIZON)
    pred = np.full((T, N), np.nan, dtype=np.float32)
    rows = []
    years = sorted(set(dates.year))
    first_year = 2010 if once else dates[0].year + TRAIN_YEARS + 1

    def gather(days):
        Xs, ys, offs = [], [], []
        for t in days:
            ok = np.isfinite(F[t]).all(1) & np.isfinite(Y[t]) & tradable[t]
            if offset is not None:
                ok &= np.isfinite(offset[t])
            Xs.append(F[t][ok])
            ys.append(Y[t][ok])
            if offset is not None:
                offs.append(offset[t][ok])
        return (np.vstack(Xs).astype(np.float64), np.concatenate(ys),
                np.concatenate(offs) if offset is not None else None)

    train = gather(sample_days[dates[sample_days] < SPLIT]) if once else None
    for yr in [y for y in years if y >= first_year]:
        if not once:
            d = dates[sample_days]
            train = gather(sample_days[(d.year >= yr - TRAIN_YEARS) & (d.year < yr)])
        Xtr, ytr, otr = train
        te = np.flatnonzero(dates.year == yr)
        Xte = F[te].reshape(-1, K).astype(np.float64)
        ote = offset[te].ravel() if offset is not None else None
        ok = np.isfinite(Xte).all(1)
        if ote is not None:
            ok &= np.isfinite(ote)
        p = np.full(len(Xte), np.nan)
        if ok.sum():
            p[ok], beta = fit_predict(Xtr, ytr, Xte[ok], family, otr, ote[ok] if ote is not None else None)
            rows.append({"year": yr, **{f"b{i}": b for i, b in enumerate(beta)}})
        pred[te] = p.reshape(len(te), -1)
        LOG.info("jump glm %s%s: %d (%d training rows)", family, " once" if once else "", yr, len(ytr))
    return pred, pd.DataFrame(rows)


def score_predictions(pred: np.ndarray, Y: np.ndarray, dates: pd.DatetimeIndex, tradable: np.ndarray,
                      base_rate: np.ndarray) -> dict:
    """Out-of-sample deviance explained vs. the trailing market base rate, and
    the daily cross-sectional rank correlation of predicted vs. realised counts,
    on non-overlapping 21-day windows."""
    T = len(dates)
    sample_days = np.arange(300, T - HORIZON - 1, HORIZON)
    out = {}
    ic = pd.Series(rank_ic(np.where(tradable, pred, np.nan), np.where(tradable, Y, np.nan)), index=dates)
    for per, m in (("1st", dates < SPLIT), ("2nd", dates >= SPLIT)):
        days = sample_days[m[sample_days]]
        y = np.concatenate([Y[t][tradable[t] & np.isfinite(pred[t]) & np.isfinite(Y[t])] for t in days])
        p = np.concatenate([pred[t][tradable[t] & np.isfinite(pred[t]) & np.isfinite(Y[t])] for t in days])
        b = np.concatenate([np.full((tradable[t] & np.isfinite(pred[t]) & np.isfinite(Y[t])).sum(), base_rate[t])
                            for t in days])
        if len(y) > 100:
            out[f"dev_explained_{per}"] = deviance_explained(y, p, b)
            out[f"dev_explained_vs_const_{per}"] = deviance_explained(y, p, y.mean())
            out[f"calibration_{per}"] = float(p.mean() / y.mean())
        s = ic[m].dropna()
        out[f"rank_ic_{per}"] = float(s.mean())
        out[f"rank_ic_t_{per}"] = float(s.mean() / s.std() * np.sqrt(len(s) / HORIZON)) if len(s) > 10 else np.nan
    return out


def risk_filter_tests(bench: Bench, rev_z: pd.DataFrame, lam_down: pd.DataFrame, lam_up: pd.DataFrame) -> pd.DataFrame:
    """The 5-day reversal book with jump-prone stocks removed or down-weighted."""
    rows = []
    tr = bench.tradable
    total = lam_down + lam_up
    for name, mask, scale in (
        ("plain reversal", tr, None),
        ("drop top-10% crash risk", tr & (lam_down.rank(axis=1, pct=True) <= 0.9), None),
        ("drop top-20% crash risk", tr & (lam_down.rank(axis=1, pct=True) <= 0.8), None),
        ("drop top-10% jump intensity", tr & (total.rank(axis=1, pct=True) <= 0.9), None),
        ("weights / predicted intensity", tr, 1 / total.clip(lower=1e-3)),
        ("weights / sqrt(intensity)", tr, 1 / np.sqrt(total.clip(lower=1e-3))),
    ):
        z = rev_z if scale is None else rev_z * scale.where(tr)
        for hl in (0, 5):
            zz = z.ewm(halflife=hl, ignore_na=True).mean() if hl else z
            st = summarize(portfolio_stats(_weights(zz, mask), bench.r1, bench.cost))
            rows.append({"book": name, "halflife": hl, **{k: v for k, v in st.items() if "sharpe" in k or "breakeven" in k}})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--out", default="reports/jump_lab")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    t0 = time.time()
    md, ctx, X, names = load(args.lab)
    rev_z = pd.DataFrame(X[..., names.index("rev_5d")], index=md.dates, columns=md.tickers)
    del X
    up, down = jump_panels(ctx)
    stock, market = features(md, ctx, up, down)
    tradable = ctx.tradable.to_numpy()
    dates = md.dates
    fut = {k: ev.fillna(0)[::-1].rolling(HORIZON).sum()[::-1].shift(-1).to_numpy() for k, ev in (("up", up), ("down", down))}
    # exposure: trailing 63-day market rate of that jump type x 21 days (per stock-day, known at t)
    n_trad = ctx.tradable.sum(1).clip(lower=1)
    base = {k: ((ev.sum(1) / n_trad).rolling(63, min_periods=40).mean() * HORIZON).to_numpy()
            for k, ev in (("up", up), ("down", down))}
    LOG.info("jump lab: features ready (%.0fs)", time.time() - t0)

    F_raw, fnames = design(stock, market, ranked=False)
    F_rank, _ = design(stock, market, ranked=True)
    configs = [
        ("original: raw features, one fit on 2004-14", F_raw, "poisson", False, True),
        ("walk-forward, raw features", F_raw, "poisson", False, False),
        ("walk-forward, ranked features", F_rank, "poisson", False, False),
        ("walk-forward, ranked + market offset", F_rank, "poisson", True, False),
        ("walk-forward, ranked + offset, negative binomial", F_rank, "negbin", True, False),
    ]
    if args.quick:
        configs = configs[:1] + configs[3:4]
    rows, preds = [], {}
    for label, F, family, use_offset, once in configs:
        for kind in ("down", "up"):
            off = np.log(np.repeat(base[kind][:, None], F.shape[1], axis=1).clip(1e-6)) if use_offset else None
            try:
                pred, ctab = walk_forward_glm(F, fut[kind], dates, tradable, family, off, once)
            except Exception as exc:  # noqa: BLE001
                LOG.exception("%s %s failed", label, kind)
                rows.append({"model": label, "jumps": kind, "error": str(exc)})
                continue
            sc = score_predictions(pred, fut[kind], dates, tradable, base[kind])
            rows.append({"model": label, "jumps": kind, **sc})
            preds[(label, kind)] = pd.DataFrame(pred, index=dates, columns=md.tickers)
            ctab.to_csv(out / f"coef_{len(rows):02d}_{kind}.csv", index=False)
            LOG.info("%s / %s: dev %.3f / %.3f, rank IC %.3f / %.3f", label, kind, sc.get("dev_explained_1st", np.nan),
                     sc.get("dev_explained_2nd", np.nan), sc["rank_ic_1st"], sc["rank_ic_2nd"])
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "jump_glm.csv", index=False)

    # signals and risk filter from the best walk-forward model by 1st-period rank IC on down jumps
    wf = tab[(~tab["model"].str.startswith("original")) & (tab["jumps"] == "down")].dropna(subset=["rank_ic_1st"])
    best = wf.sort_values("rank_ic_1st", ascending=False).iloc[0]["model"]
    lam_dn, lam_up = preds[(best, "down")], preds[(best, "up")]
    from ..signals import normalize_signal

    bench = Bench(md, ctx)
    sigs = {"pred_crash_intensity": normalize_signal(-lam_dn, ctx.tradable),
            "pred_jump_skew": normalize_signal(-(lam_up - lam_dn), ctx.tradable),
            "pred_jump_intensity": normalize_signal(-(lam_up + lam_dn), ctx.tradable)}
    stab, sdec = bench.table(sigs, {k: "jump_lab" for k in sigs})
    stab.to_csv(out / "jump_signals.csv", index=False)
    sdec.to_csv(out / "jump_signal_decay.csv", index=False)
    risk = risk_filter_tests(bench, rev_z, lam_dn, lam_up)
    risk.to_csv(out / "risk_filter.csv", index=False)

    cols = ["model", "jumps", "dev_explained_1st", "dev_explained_2nd", "dev_explained_vs_const_2nd", "calibration_2nd",
            "rank_ic_1st", "rank_ic_t_1st", "rank_ic_2nd", "rank_ic_t_2nd"]
    lines = ["# Jump lab: Poisson regressions for next-month jump counts", "",
             "Deviance explained is measured against the trailing market jump rate (a moving base rate), and "
             "against a constant for comparison with the original study. rank_ic: daily cross-sectional rank "
             "correlation between predicted and realised next-21-day jump counts. calibration: predicted / "
             "realised mean count (1 = right level).", "",
             tab[[c for c in cols if c in tab]].round(3).to_markdown(index=False), "",
             f"## Signals from the best walk-forward model ({best})", "",
             sdec.round(4).to_markdown(index=False), "",
             stab[["signal", "halflife", "universe", "breakeven_bp_1st", "breakeven_bp_2nd", "net_sharpe_1st",
                   "net_sharpe_2nd", "turnover_1st"]].round(3).to_markdown(index=False), "",
             "## Jump intensity as a risk filter on the 5-day reversal book", "",
             risk.round(3).to_markdown(index=False), ""]
    (out / "jump_lab.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps({"best_model": best, "rows": len(tab)}, indent=2))
    LOG.info("jump lab done (%.0fs)", time.time() - t0)


if __name__ == "__main__":
    main()
