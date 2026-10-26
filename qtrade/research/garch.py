"""Volatility models: GARCH and friends, judged on forecasts.

Models for tomorrow's variance (all one-step-ahead, using data up to today):

  rolling_21   / rolling_63   sample variance of the last 21 / 63 days
  ewma         RiskMetrics: s2_t = 0.94 s2_{t-1} + 0.06 r2_{t-1}
  garch        GARCH(1,1):  s2_t = w + a r2_{t-1} + b s2_{t-1}
  gjr          GJR-GARCH:   + g r2_{t-1} 1[r_{t-1} < 0] (bad news raises volatility more)
  *_t          the same with Student-t errors (fat tails)

Parameters are estimated on 2004-2014 and the forecasts scored on 2015-2026
with QLIKE = log s2 + r2 / s2 (the standard loss for variance forecasts; lower
is better; it does not reward a forecast for being too low the way squared
error does). For the market index and a sample of stocks' factor residuals
(the volatility the portfolio sizes positions by).

Then the practical question: scale the long-short composite by its own GARCH
volatility forecast (a "volatility-managed" portfolio) - does Sharpe improve?
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.signal import lfilter
from scipy.special import gammaln

from ..utils import LOG

SPLIT = "2015-01-01"


def garch_filter(r: np.ndarray, w: float, a: float, b: float, g: float = 0.0, s0: float | None = None) -> np.ndarray:
    """Conditional variance for day t from returns up to t-1.

    Given the returns the recursion s2_t = b s2_{t-1} + (w + (a + g 1[r<0]) r2_{t-1})
    is linear, so it runs as one IIR filter. A missing return contributes the
    unconditional variance (keeps the level instead of collapsing it)."""
    s0 = s0 if s0 is not None else np.nanvar(r)
    x = np.where(np.isfinite(r), r, 0.0)
    u = np.where(np.isfinite(r), (a + g * (x < 0)) * x * x, (a + g / 2) * s0)
    v = w + u[:-1]
    out = np.empty(len(r))
    out[0] = s0
    if len(r) > 1:
        out[1:] = lfilter([1.0], [1.0, -b], v, zi=[b * s0])[0]
    return out


def _nll(r, s2, nu=None):
    ok = np.isfinite(r) & (s2 > 0)
    x, v = r[ok], s2[ok]
    if nu is None:
        return 0.5 * np.sum(np.log(2 * np.pi * v) + x * x / v)
    # Student-t scaled to unit variance
    c = gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2))
    return -np.sum(c - 0.5 * np.log(v) - (nu + 1) / 2 * np.log1p(x * x / (v * (nu - 2))))


def fit_garch(r: np.ndarray, gjr: bool = False, student: bool = False) -> dict:
    var = np.nanvar(r)

    def unpack(p):
        a = 1 / (1 + np.exp(-p[0])) * 0.5
        b = 1 / (1 + np.exp(-p[1]))
        g = (1 / (1 + np.exp(-p[2])) * 0.5) if gjr else 0.0
        nu = 2.05 + np.exp(p[3]) if student else None
        persist = a + b + g / 2
        w = var * max(1 - persist, 1e-4)            # variance targeting: unconditional variance = sample variance
        return w, a, b, g, nu, persist

    def obj(p):
        w, a, b, g, nu, persist = unpack(p)
        if persist >= 0.9995:
            return 1e12
        return _nll(r, garch_filter(r, w, a, b, g, var), nu)

    res = None
    for a0, b0 in ((0.06, 0.85), (0.1, 0.8), (0.03, 0.93)):          # starts inside the stationary region
        x0 = [np.log(a0 / (0.5 - a0)), np.log(b0 / (1 - b0)), np.log(0.04 / 0.46), np.log(6.0)]
        r_ = minimize(obj, x0, method="Nelder-Mead", options={"maxiter": 3000, "xatol": 1e-6, "fatol": 1e-6})
        if res is None or r_.fun < res.fun:
            res = r_
    w, a, b, g, nu, persist = unpack(res.x)
    return {"w": w, "a": a, "b": b, "g": g, "nu": nu, "persistence": persist,
            "half_life_days": np.log(0.5) / np.log(persist) if 0 < persist < 1 else np.inf, "s0": var}


def forecasts(r: pd.Series, train: np.ndarray) -> tuple[dict[str, np.ndarray], dict]:
    x = r.to_numpy(dtype=float)
    out, params = {}, {}
    sq = pd.Series(x * x, index=r.index)
    out["rolling_21"] = sq.rolling(21, min_periods=15).mean().shift(1).to_numpy()
    out["rolling_63"] = sq.rolling(63, min_periods=40).mean().shift(1).to_numpy()
    ew = np.empty(len(x))
    ew[0] = np.nanvar(x[train])
    for t in range(1, len(x)):
        ew[t] = 0.94 * ew[t - 1] + 0.06 * x[t - 1] ** 2 if np.isfinite(x[t - 1]) else ew[t - 1]
    out["ewma"] = ew
    xt = np.where(train, x, np.nan)
    for name, gjr, st in (("garch", False, False), ("gjr", True, False), ("garch_t", False, True), ("gjr_t", True, True)):
        p = fit_garch(xt[: np.flatnonzero(train)[-1] + 1], gjr, st)
        params[name] = p
        out[name] = garch_filter(x, p["w"], p["a"], p["b"], p["g"], p["s0"])
    return out, params


def qlike(r2: np.ndarray, s2: np.ndarray) -> float:
    ok = np.isfinite(r2) & np.isfinite(s2) & (s2 > 0)
    return float(np.mean(np.log(s2[ok]) + r2[ok] / s2[ok]))


def score(r: pd.Series, fc: dict, horizon: int = 1) -> dict:
    """QLIKE per model on the out-of-sample period; for horizon > 1 compare the
    forecast (held flat) with the average squared return over the next days."""
    x = r.to_numpy(dtype=float)
    r2 = pd.Series(x * x).rolling(horizon).mean().shift(-(horizon - 1)).to_numpy()
    test = np.asarray(r.index >= SPLIT)
    return {k: qlike(r2[test], v[test]) for k, v in fc.items()}


def run(md, ctx, out: Path, composite: pd.DataFrame | None = None, n_stocks: int = 150) -> dict:
    train_mask = lambda s: np.asarray(s.index < SPLIT)  # noqa: E731
    lines = ["## Volatility models (GARCH family)", "",
             "QLIKE loss out of sample (2015-2026), parameters estimated on 2004-2014. Lower is better; "
             "differences of 0.01 are meaningful over thousands of days.", ""]
    res = {}
    mkt = ctx.market_ret.where(ctx.market_ret.abs() < 0.25)
    fc, params = forecasts(mkt, train_mask(mkt))
    tab = pd.DataFrame({"1-day": score(mkt, fc, 1), "21-day": score(mkt, fc, 21)})
    ptab = pd.DataFrame(params).T[["a", "b", "g", "nu", "persistence", "half_life_days"]]
    lines += ["### Market (equal-weighted universe)", "", tab.round(4).to_markdown(), "",
              "Fitted parameters (g = extra reaction to down days; nu = tail thickness, lower = fatter):", "",
              ptab.round(4).to_markdown(), ""]
    res["market_best_1d"] = tab["1-day"].idxmin()

    # stock residual volatility: the quantity the portfolio sizes positions with
    rng = np.random.default_rng(0)
    resid = ctx.resid
    cols = [c for c in resid.columns if resid[c].loc[:SPLIT].notna().sum() > 1500]
    cols = list(rng.choice(cols, min(n_stocks, len(cols)), replace=False))
    per = []
    for c in cols:
        s = resid[c].where(resid[c].abs() < 0.3)
        f, _ = forecasts(s, train_mask(s))
        per.append(score(s, f, 1) | {"stock": c})
    pt = pd.DataFrame(per).set_index("stock")
    wins = pt.idxmin(axis=1).value_counts()
    lines += [f"### Stock residual volatility ({len(cols)} stocks)", "",
              "Average QLIKE and how often each model was best for a stock:", "",
              pd.DataFrame({"mean_qlike": pt.mean(), "best_for_n_stocks": wins}).fillna(0).round(4).to_markdown(), "",
              "The portfolio currently sizes with rolling_63. A clearly lower loss for a GARCH variant means "
              "position sizes (and the vol target) would track risk better with it.", ""]
    res["stock_best"] = pt.mean().idxmin()

    # volatility-managed composite
    if composite is not None:
        from .edge import Bench, _weights

        bench = Bench(md, ctx)
        w = _weights(composite.ewm(halflife=5, ignore_na=True).mean(), ctx.tradable)
        g = (w * bench.r1).sum(axis=1) - (w.diff().abs() * bench.cost).sum(axis=1)       # net daily return
        g = g[g.index >= g.ne(0).idxmax()]
        f, p = forecasts(g, train_mask(g))
        rows = []
        for name in ("none", "rolling_63", "ewma", "garch", "gjr_t"):
            if name == "none":
                scaled = g
            else:
                s = np.sqrt(f[name])
                lev = (np.nanmedian(s[train_mask(g)]) / s)
                lev = np.clip(lev, 0, 3)            # at most 3x the normal size
                scaled = g * lev
            row = {"scaling": name}
            for perd, m in (("1st", g.index < SPLIT), ("2nd", g.index >= SPLIT)):
                x = scaled[m]
                row[f"sharpe_{perd}"] = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
                eq = (1 + x).cumprod()
                row[f"max_dd_{perd}"] = (eq / eq.cummax() - 1).min()
            rows.append(row)
        vt = pd.DataFrame(rows)
        lines += ["### Volatility-managed composite (net of costs)", "",
                  "The long-short composite (5-day smoothing), scaled each day by 1 / its forecast volatility "
                  "(capped at 3x). If Sharpe rises, the strategy's own risk is forecastable and the vol target "
                  "should use the better forecast.", "", vt.round(3).to_markdown(index=False), ""]
        res["vol_managed"] = vt.round(3).to_dict(orient="records")
    (out / "garch.md").write_text("\n".join(lines) + "\n")
    LOG.info("garch: best market model %s, best stock model %s", res["market_best_1d"], res["stock_best"])
    return res
