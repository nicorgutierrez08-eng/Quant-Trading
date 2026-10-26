"""Different model families on the same signals: which turns them into the best forecast?

Target: each stock's open-to-open return over the next 5 days. Inputs: the 44
signal z-scores. Every model is refit once a year on the previous 5 years
(every 5th day, so labels don't overlap) and predicts the following year.

  ridge      Gaussian GLM (linear regression, L2 penalty) on rank-Gaussian returns
  logistic   binomial GLM: P(stock beats the median) - only the direction counts
  huber      robust regression: big moves can't dominate the fit
  mlp        a small neural network (one hidden layer of 32), nonlinear

Scored on out-of-sample IC (2010-2014 and 2015-2026) and the break-even cost
of trading each forecast.

Also a Gamma GLM (log link) for volatility: next month's realized residual
volatility from recent volatilities, volume and jumps, compared with the
63-day rolling estimate the portfolio uses, on QLIKE.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..signals import compute_signals
from ..utils import LOG, cs_rank_gauss
from .edge import SPLIT, Bench

TRAIN_YEARS = 5


def _models():
    from sklearn.linear_model import HuberRegressor, LogisticRegression, Ridge
    from sklearn.neural_network import MLPRegressor

    return {
        "ridge": (lambda: Ridge(alpha=10.0), "rank", None),
        "logistic": (lambda: LogisticRegression(C=0.05, max_iter=500), "sign", None),
        "huber": (lambda: HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=200), "raw", 150_000),
        "mlp": (lambda: MLPRegressor(hidden_layer_sizes=(32,), alpha=1e-3, learning_rate_init=1e-3, max_iter=30,
                                     early_stopping=True, random_state=0), "rank", 300_000),
    }


def run(md, ctx, out: Path) -> dict:
    sigs = compute_signals(ctx)
    names = list(sigs)
    X = np.stack([sigs[n].to_numpy(dtype=np.float32) for n in names], axis=-1)       # T x N x F
    o = md.open
    fwd = (o.shift(-6) / o.shift(-1) - 1).where(ctx.tradable).clip(-0.5, 0.5)
    y_rank = cs_rank_gauss(fwd).to_numpy()
    y_raw = fwd.sub(fwd.mean(axis=1), axis=0).to_numpy()
    y_sign = (y_rank > 0).astype(float)
    y_sign[~np.isfinite(y_rank)] = np.nan
    dates = md.dates
    years = sorted(set(dates.year))
    start_year = dates[0].year + TRAIN_YEARS + 1
    preds = {m: np.full(X.shape[:2], np.nan, dtype=np.float32) for m in _models()}
    rng = np.random.default_rng(0)
    for yr in [y for y in years if y >= start_year]:
        tr_days = np.flatnonzero((dates.year >= yr - TRAIN_YEARS) & (dates.year < yr))[:-6:5]
        te_days = np.flatnonzero(dates.year == yr)
        Xt = X[tr_days].reshape(-1, len(names))
        ok = np.isfinite(Xt).all(axis=1) & np.isfinite(y_rank[tr_days].ravel())
        Xte = X[te_days].reshape(-1, len(names))
        okte = np.isfinite(Xte).all(axis=1)
        for m, (make, target, cap) in _models().items():
            y = {"rank": y_rank, "raw": y_raw, "sign": y_sign}[target][tr_days].ravel()
            idx = np.flatnonzero(ok & np.isfinite(y))
            if cap and len(idx) > cap:
                idx = rng.choice(idx, cap, replace=False)
            model = make().fit(Xt[idx], y[idx])
            p = np.full(len(Xte), np.nan)
            p[okte] = model.predict_proba(Xte[okte])[:, 1] if m == "logistic" else model.predict(Xte[okte])
            preds[m][te_days] = p.reshape(len(te_days), -1)
        LOG.info("glm: models for %d fitted", yr)

    bench = Bench(md, ctx)
    rows = []
    for m, P in preds.items():
        z = pd.DataFrame(P, index=dates, columns=md.tickers)
        ic = pd.Series([np.corrcoef(a[ok], b[ok])[0, 1] if (ok := np.isfinite(a) & np.isfinite(b)).sum() > 30
                        else np.nan for a, b in zip(P, y_rank)], index=dates)
        row = {"model": m, "ic5_2010_14": ic[(dates.year >= 2010) & (dates < SPLIT)].mean(),
               "ic5_2015_26": ic[dates >= SPLIT].mean(),
               "years_positive": float((ic.groupby(dates.year).mean().dropna() > 0).mean())}
        for hl in (0, 5):
            st = bench.score(z, hl, "all")
            row[f"hl{hl}_breakeven_2nd"] = st["breakeven_bp_2nd"]
            row[f"hl{hl}_net_sharpe_2nd"] = st["net_sharpe_2nd"]
        rows.append(row)
    tab = pd.DataFrame(rows)
    corr = pd.DataFrame({m: pd.DataFrame(P).stack() for m, P in preds.items()}).corr()

    vol = gamma_vol_model(md, ctx)
    lines = ["## Model families on the same signals", "",
             "Each refit yearly on the previous 5 years; out-of-sample IC of the 5-day forecast, and the "
             "break-even cost / net Sharpe of trading it in 2015-2026 (hl = smoothing half-life).", "",
             tab.round(4).to_markdown(index=False), "",
             "How similar are their forecasts? (correlation of predictions)", "", corr.round(2).to_markdown(), "",
             "### Gamma GLM for volatility", "",
             "Next 21 days' realized residual volatility (log link, Gamma errors), fit on 2004-2014, vs. the "
             "63-day rolling estimate the portfolio uses. QLIKE out of sample (lower is better):", "",
             pd.DataFrame(vol["qlike"], index=["QLIKE 2015-2026"]).T.round(4).to_markdown(), "",
             vol["coef"].round(3).to_markdown(index=False), ""]
    (out / "glm.md").write_text("\n".join(lines) + "\n")
    tab.to_csv(out / "glm_models.csv", index=False)
    return {"models": tab.round(4).to_dict(orient="records"), "vol_qlike": vol["qlike"]}


def gamma_vol_model(md, ctx) -> dict:
    from sklearn.linear_model import GammaRegressor

    e = ctx.resid
    r2 = e ** 2
    feats = {
        "log_var_5": np.log(r2.rolling(5, min_periods=4).mean() + 1e-8),
        "log_var_21": np.log(r2.rolling(21, min_periods=15).mean() + 1e-8),
        "log_var_63": np.log(r2.rolling(63, min_periods=40).mean() + 1e-8),
        "log_abn_volume": np.log(md.volume.rolling(5).mean() / md.volume.rolling(63).mean() + 1e-6),
        "log_mkt_var_21": pd.DataFrame(np.repeat(np.log(ctx.market_ret.pow(2).rolling(21).mean() + 1e-8)
                                                 .to_numpy()[:, None], e.shape[1], 1), index=e.index, columns=e.columns),
        "log_dollar_volume": np.log(ctx.adv + 1),
    }
    names = list(feats)
    F = np.stack([feats[k].to_numpy() for k in names], axis=-1)
    target = r2[::-1].rolling(21, min_periods=15).mean()[::-1].shift(-1).to_numpy()        # next 21 days
    base = r2.rolling(63, min_periods=40).mean().to_numpy()
    dates = md.dates
    first = np.asarray(dates < SPLIT)
    days = np.arange(300, len(dates) - 22, 21)
    ok = np.isfinite(F).all(axis=-1) & np.isfinite(target) & (target > 0) & ctx.tradable.to_numpy()
    tr = np.concatenate([np.flatnonzero(ok[t]) + t * F.shape[1] for t in days if first[t]])
    te = np.concatenate([np.flatnonzero(ok[t]) + t * F.shape[1] for t in days if not first[t]])
    Ff, yf, bf = F.reshape(-1, len(names)), target.ravel(), base.ravel()
    mu, sd = Ff[tr].mean(0), Ff[tr].std(0) + 1e-12
    m = GammaRegressor(alpha=1e-4, max_iter=1000).fit((Ff[tr] - mu) / sd, yf[tr])
    pred = m.predict((Ff[te] - mu) / sd)

    def ql(y, s):
        okk = np.isfinite(y) & np.isfinite(s) & (s > 0)
        return float(np.mean(np.log(s[okk]) + y[okk] / s[okk]))

    coef = pd.DataFrame({"feature": names, "coef_per_sd": m.coef_, "vol_ratio_per_sd": np.exp(m.coef_ / 2)})
    return {"qlike": {"gamma_glm": ql(yf[te], pred), "rolling_63": ql(yf[te], bf[te])}, "coef": coef}
