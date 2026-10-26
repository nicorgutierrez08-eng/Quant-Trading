"""Regime lab: can a better hidden Markov model earn its place in the portfolio?

The existing study (``hmm_eval``) showed the Gaussian HMM on rolling market
symptoms is well calibrated for crashes (Brier skill ~0.01) but forecasts
volatility *worse* than last month's realised volatility, and that the only
economic effect found - reversal works 2-4x better in the stressed regime -
did not turn into money. This lab changes three things and scores every
variant on money, not just likelihood:

1. **Symptoms.** Rolling windows overlap, so one bad day is counted ten times
   and the HMM is overconfident. Alternatives: non-overlapping daily symptoms
   (``daily``), GARCH-standardised ones (``garch``: the market return divided by
   its predicted volatility, so the HMM only has to find *shifts* in the
   standardised distribution), the same plus breadth and the day's jump count
   (``dailyplus``) and plus public macro series (``macro``: VIX, credit and term
   spreads from FRED, each lagged a day).
2. **Emissions.** Gaussian vs. Student-t (fat tails: one 5-sigma day should not
   flip the regime) and, for ``dailyplus``, a mixed Gaussian x Poisson emission
   where the number of stocks jumping that day is a Poisson count whose rate
   depends on the regime (``poisson``). Sticky transitions (a prior that favours
   staying put) damp day-to-day flicker.
3. **Economic tests**, all walk-forward with the same yearly refits and nothing
   chosen on 2015-2026:
   * market timing: the regime-conditional mean/variance of next-day market
     returns (learned on the training block) sets the exposure, vs. a plain
     volatility-managed exposure at the same 10% target;
   * reversal sizing: the gross of the 5-day reversal book scaled by the
     regime-conditional IC, vs. constant gross;
   * reversal/momentum switch: capital split between the reversal and 12-1
     momentum books by their regime-conditional ICs, vs. 50/50.

Selection uses 2004-2014 ("1st"); 2015-2026 ("2nd") is the check.

    python -m qtrade.research.regime_lab --lab data/lab --out reports/regime_lab
"""
from __future__ import annotations

import argparse
import json
import os
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gammaln

from ..models.hmm import GaussianHMM
from ..utils import LOG, rank_ic, setup_logging
from .edge import SPLIT, _weights, cost_panel, portfolio_stats, summarize
from .garch import fit_garch, garch_filter
from .hmm_eval import daily_state, evaluate

REFIT_EVERY = 252
MIN_HISTORY = 756
TARGET_VOL = 0.10
ETF_COST = 1e-4


# -----------------------------------------------------------------------------
# the model
# -----------------------------------------------------------------------------
class LabHMM(GaussianHMM):
    """GaussianHMM plus Student-t emissions, an optional Poisson count column
    and sticky transitions.

    ``count_col`` names a column of ``X`` holding non-negative integer counts;
    it gets a state-specific Poisson rate instead of entering the Gaussian.
    ``sticky`` is a Dirichlet pseudo-count added to the diagonal of the
    transition matrix in every M-step (0 = plain Baum-Welch).
    """

    def __init__(self, n_states: int = 3, emission: str = "gauss", nu: float = 5.0, sticky: float = 0.0,
                 count_col: int | None = None, **kw):
        super().__init__(n_states, **kw)
        self.emission, self.nu, self.sticky, self.count_col = emission, nu, sticky, count_col

    # -- helpers ------------------------------------------------------------
    def _cont(self, X: np.ndarray) -> list[int]:
        return [j for j in range(X.shape[1]) if j != self.count_col]

    def _maha(self, Xc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        maha = np.empty((len(Xc), self.K))
        logdet = np.empty(self.K)
        for k in range(self.K):
            L = np.linalg.cholesky(self.covars_[k])
            diff = np.linalg.solve(L, (Xc - self.means_[k]).T)
            maha[:, k] = (diff ** 2).sum(axis=0)
            logdet[k] = 2 * np.log(np.diag(L)).sum()
        return maha, logdet

    def _log_emission(self, X: np.ndarray) -> np.ndarray:
        cont = self._cont(X)
        T, D = len(X), len(cont)
        out = np.zeros((T, self.K))
        ok = np.isfinite(X).all(axis=1)
        maha, logdet = self._maha(X[ok][:, cont])
        if self.emission == "t":
            nu = self.nu
            out[ok] = (gammaln((nu + D) / 2) - gammaln(nu / 2) - 0.5 * (D * np.log(nu * np.pi) + logdet)
                       - (nu + D) / 2 * np.log1p(maha / nu))
        else:
            out[ok] = -0.5 * (D * np.log(2 * np.pi) + logdet + maha)
        if self.count_col is not None:
            n = X[ok, self.count_col]
            out[ok] += (n[:, None] * np.log(self.rates_)[None, :] - self.rates_[None, :]
                        - gammaln(n + 1)[:, None])
        return out

    # -- EM -------------------------------------------------------------------
    def _init_params(self, X: np.ndarray, warm: "LabHMM | None" = None) -> None:
        cont = self._cont(X)
        if warm is not None and warm.fitted:
            self.startprob_, self.transmat_ = warm.startprob_.copy(), warm.transmat_.copy()
            self.means_, self.covars_ = warm.means_.copy(), warm.covars_.copy()
            if self.count_col is not None:
                self.rates_ = warm.rates_.copy()
            return
        super()._init_params(X[:, cont])
        if self.count_col is not None:
            n = X[:, self.count_col]
            self.rates_ = np.quantile(n, np.linspace(0.2, 0.95, self.K)) + 0.1

    def _em(self, X: np.ndarray) -> float:
        cont = self._cont(X)
        Xc = X[:, cont]
        D = len(cont)
        prev = -np.inf
        loglik = prev
        for _ in range(self.max_iter):
            logB = self._log_emission(X) * self.temper
            alpha, scale, B, loglik = self._forward(logB)
            beta = self._backward(B, scale)
            gamma = alpha * beta
            gamma /= gamma.sum(axis=1, keepdims=True)
            bb = (B[1:] * beta[1:]) / scale[1:, None]
            xi_sum = self.transmat_ * (alpha[:-1].T @ bb)
            # M-step
            self.startprob_ = gamma[0] + 1e-6
            self.startprob_ /= self.startprob_.sum()
            self.transmat_ = xi_sum + self.sticky * np.eye(self.K) + 1e-6
            self.transmat_ /= self.transmat_.sum(axis=1, keepdims=True)
            if self.emission == "t":
                maha, _ = self._maha(Xc)
                u = (self.nu + D) / (self.nu + maha)        # ECM weights: outliers count less
            else:
                u = np.ones_like(gamma)
            gu = gamma * u
            w = gamma.sum(axis=0) + 1e-10
            self.means_ = (gu.T @ Xc) / (gu.sum(axis=0) + 1e-10)[:, None]
            for k in range(self.K):
                diff = Xc - self.means_[k]
                self.covars_[k] = (gu[:, k, None] * diff).T @ diff / w[k] + self.reg * np.eye(D)
            if self.count_col is not None:
                self.rates_ = (gamma * X[:, self.count_col, None]).sum(axis=0) / w + 1e-3
            if abs(loglik - prev) < self.tol * max(1.0, abs(prev)):
                break
            prev = loglik
        return loglik

    def fit(self, X: np.ndarray, warm: "LabHMM | None" = None, sort_by: int | None = None) -> "LabHMM":
        X = X[np.isfinite(X).all(axis=1)]
        best = None
        tries = [warm] + [None] * (self.n_init - 1) if warm is not None else [None] * self.n_init
        for w in tries:
            self._init_params(X, w)
            ll = self._em(X)
            if best is None or ll > best[0]:
                best = (ll, self.startprob_.copy(), self.transmat_.copy(), self.means_.copy(), self.covars_.copy(),
                        self.rates_.copy() if self.count_col is not None else None)
        self.loglik_, self.startprob_, self.transmat_, self.means_, self.covars_, rates = best
        if rates is not None:
            self.rates_ = rates
        if sort_by is not None:                 # state 0 = lowest value of the sort column (calmest)
            order = np.argsort(self.means_[:, sort_by])
            self.startprob_ = self.startprob_[order]
            self.transmat_ = self.transmat_[np.ix_(order, order)]
            self.means_, self.covars_ = self.means_[order], self.covars_[order]
            if rates is not None:
                self.rates_ = self.rates_[order]
        self.fitted = True
        return self


def walk_forward(state: pd.DataFrame, make, vol_col: int, count_col: int | None = None,
                 refit_every: int = REFIT_EVERY, min_history: int = MIN_HISTORY):
    """Yearly refits on an expanding window; filtered probabilities for the days
    after each refit. Continuous columns are standardised with the statistics of
    the first training window only, so warm starts carry over unchanged."""
    X_all = state.to_numpy(dtype=float)
    T = len(X_all)
    valid = np.isfinite(X_all).all(axis=1)
    first = int(np.argmax(valid))
    cont = [j for j in range(X_all.shape[1]) if j != count_col]
    Z = X_all.copy()
    mu = np.nanmean(X_all[first:first + min_history][:, cont], axis=0)
    sd = np.nanstd(X_all[first:first + min_history][:, cont], axis=0) + 1e-12
    Z[:, cont] = (X_all[:, cont] - mu) / sd
    sort_col = cont.index(vol_col)
    K = make(0).K
    probs = np.full((T, K), 1.0 / K)
    pll = np.full(T, np.nan)
    fits, prev = [], None
    for i, r in enumerate(range(first + min_history, T, refit_every)):
        hmm = make(i)
        hmm.n_init = hmm.n_init if prev is None else 2
        hmm.fit(Z[first:r + 1], warm=prev, sort_by=sort_col)
        end = min(r + refit_every, T - 1)
        alpha = hmm.filter(Z[first:end + 1])
        probs[r + 1:end + 1] = alpha[r + 1 - first:]
        pll[r + 1:end + 1] = hmm.predictive_logpdf(Z[first:end + 1])[r + 1 - first:] - np.log(sd).sum()
        if i == 0:
            probs[r] = alpha[r - first]
        prev = hmm
        fits.append((state.index[r], hmm))
    out = pd.DataFrame(probs, index=state.index, columns=[f"regime_{k}" for k in range(K)])
    out.attrs["predictive_ll"] = pd.Series(pll, index=state.index)
    return out, fits


# -----------------------------------------------------------------------------
# symptoms
# -----------------------------------------------------------------------------
def garch_sigma(mkt: pd.Series, fit_days: int = MIN_HISTORY) -> pd.Series:
    """Predicted daily volatility from a GARCH(1,1) whose parameters are fitted
    on the first ``fit_days`` observations only; the filter itself uses past
    returns, so every later value is out of sample."""
    x = mkt.to_numpy(dtype=float)
    first = int(np.argmax(np.isfinite(x)))
    p = fit_garch(x[first:first + fit_days])
    s2 = np.full(len(x), np.nan)
    s2[first:] = garch_filter(x[first:], p["w"], p["a"], p["b"], p["g"], p["s0"])
    return pd.Series(np.sqrt(s2), index=mkt.index)


def jump_counts(ctx) -> pd.Series:
    """Number of tradable stocks whose factor residual is beyond 3 trailing sigmas that day."""
    e = ctx.resid
    z = e / e.rolling(63, min_periods=40).std().shift(1)
    return (z.abs() > 3).where(ctx.tradable).sum(axis=1).astype(float)


def symptom_sets(ctx, fred: pd.DataFrame | None) -> dict[str, tuple[pd.DataFrame, str, str | None]]:
    """name -> (frame, volatility column, count column or None)."""
    r = ctx.ret.clip(-0.5, 0.5)
    mkt = ctx.market_ret
    daily = daily_state(ctx)
    breadth = (r.where(ctx.tradable) > 0).sum(axis=1) / ctx.tradable.sum(axis=1).clip(lower=1) - 0.5
    sig = garch_sigma(mkt)
    garch = pd.DataFrame({"z_mkt": mkt / sig, "log_sigma": np.log(sig), "log_dispersion": daily["log_dispersion"],
                          "corr_1d": daily["corr_1d"], "breadth": breadth})
    jumps = jump_counts(ctx)
    plus = garch.assign(log_jumps=np.log1p(jumps))
    # direction-free versions: with the signed market return as a symptom the HMM
    # learns up-day / down-day "regimes" lasting 1-2 days (first sweep), which is
    # not a regime. These keep only the size of the standardised move.
    garch_abs = garch.drop(columns="z_mkt").assign(log_abs_z=np.log((mkt / sig).abs() + 0.1))
    out = {"rolling": (ctx.market_state, "log_rvol", None), "daily": (daily, "log_abs_mkt", None),
           "garch": (garch, "log_sigma", None), "dailyplus": (plus, "log_sigma", None),
           "poisson": (garch.assign(jumps=jumps), "log_sigma", "jumps"),
           "garch_abs": (garch_abs, "log_sigma", None),
           "poisson_abs": (garch_abs.assign(jumps=jumps), "log_sigma", "jumps")}
    if fred is not None and "vix" in fred:
        # VIX and the term spread go back to 2000 whatever the source; credit spreads from
        # the Yahoo stand-ins (HYG-LQD) only start in 2007, so they are left out
        f = fred.reindex(mkt.index).ffill()
        macro = garch.assign(log_vix=np.log(f["vix"]), term=f["term_spread_10y3m"])
        out["macro"] = (macro, "log_sigma", None)
        out["macro_abs"] = (garch_abs.assign(log_vix=np.log(f["vix"]), term=f["term_spread_10y3m"]), "log_sigma", None)
        out["vix_only"] = (pd.DataFrame({"log_vix": np.log(f["vix"]), "log_sigma": garch["log_sigma"]}), "log_sigma", None)
        # the term-spread *level* kept the macro model in "stress" through the 2023 inversion:
        # the same symptoms without it, and with its 63-day change instead
        out["vixplus"] = (garch.assign(log_vix=np.log(f["vix"])), "log_sigma", None)
        out["vix_dterm"] = (garch.assign(log_vix=np.log(f["vix"]), dterm=f["term_spread_10y3m"].diff(63)), "log_sigma", None)
    return out


# -----------------------------------------------------------------------------
# economic tests
# -----------------------------------------------------------------------------
def _sharpe(x: pd.Series) -> float:
    return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan


def _blocks(probs: pd.DataFrame, fits):
    idx = probs.index
    dates = [d for d, _ in fits] + [idx[-1] + pd.Timedelta(days=1)]
    for a, b in zip(dates[:-1], dates[1:]):
        yield (idx <= a - pd.Timedelta(days=35)), ((idx > a) & (idx < b))


def market_timing(probs: pd.DataFrame, fits, mkt: pd.Series) -> dict:
    """Exposure from the regime-conditional mean and variance of the next day's
    market return (training block only), scaled to the target volatility, vs. a
    volatility-managed exposure at the same target. Decided at the close of t,
    held over day t+2 (next-open execution convention), 1 bp per unit traded."""
    P = probs.to_numpy()
    r_next = mkt.shift(-1).to_numpy()
    raw = pd.Series(np.nan, index=probs.index)
    for train, test in _blocks(probs, fits):
        ok = train & np.isfinite(r_next)
        Pt = P[ok]
        m_k = (Pt * r_next[ok, None]).sum(0) / (Pt.sum(0) + 1e-9)
        v_k = (Pt * r_next[ok, None] ** 2).sum(0) / (Pt.sum(0) + 1e-9) - m_k ** 2
        kelly = (P @ m_k) / (P @ v_k).clip(1e-8)
        s = TARGET_VOL / np.sqrt(252) / np.nanstd(kelly[ok] * r_next[ok])
        raw[test] = np.clip(s * kelly[test], -2, 2)
    trail = mkt.rolling(21, min_periods=15).std() * np.sqrt(252)
    volm = (TARGET_VOL / trail).clip(upper=2)
    out = {}
    for name, pos in (("regime", raw), ("volmanaged", volm), ("regime_x_volmanaged", (raw * volm / volm.mean()).clip(-2, 2))):
        held = pos.shift(2)
        ret = held * mkt - held.diff().abs() * ETF_COST
        for per, m in (("1st", (ret.index < SPLIT) & (ret.index >= "2004-01-01")), ("2nd", ret.index >= SPLIT)):
            x = ret[m].dropna()
            out[f"timing_{name}_sharpe_{per}"] = _sharpe(x)
            out[f"timing_{name}_return_{per}"] = float(x.mean() * 252)
    for per in ("1st", "2nd"):
        out[f"timing_gain_{per}"] = out[f"timing_regime_sharpe_{per}"] - out[f"timing_volmanaged_sharpe_{per}"]
    return out


def conditional_ic(probs: pd.DataFrame, fits, ic: pd.Series, lag_days: int = 6) -> pd.Series:
    """Predicted IC for each day: regime probabilities x per-regime mean IC
    learned on the training block (ICs known ``lag_days`` later)."""
    P = probs.to_numpy()
    ic_known = ic.to_numpy()
    pred = pd.Series(np.nan, index=probs.index)
    base = pd.Series(np.nan, index=probs.index)
    for train, test in _blocks(probs, fits):
        ok = train & np.isfinite(ic_known)
        Pt = P[ok]
        ic_k = (Pt * ic_known[ok, None]).sum(0) / (Pt.sum(0) + 1e-9)
        pred[test] = P[test] @ ic_k
        base[test] = ic_known[ok].mean()            # unconditional IC on the same training block
    pred.attrs["base"] = base
    return pred


def sized_book(z: pd.DataFrame, scale: pd.Series, mask: pd.DataFrame, r1: pd.DataFrame, cost: pd.DataFrame) -> dict:
    w = _weights(z, mask).mul(scale.fillna(0.0), axis=0)
    return summarize(portfolio_stats(w, r1, cost))


def book_tests(probs, fits, G) -> dict:
    """Reversal sizing and the reversal/momentum switch, net of costs."""
    out = {}
    rev_pred = conditional_ic(probs, fits, G["ic_rev"])
    mom_pred = conditional_ic(probs, fits, G["ic_mom"])
    # scale by predicted IC relative to the training block's mean IC, 0..2.5 (same gross on average)
    s_rev = (rev_pred / rev_pred.attrs["base"].abs().clip(lower=1e-4)).clip(0, 2.5)
    s_mom = (mom_pred / mom_pred.attrs["base"].abs().clip(lower=1e-4)).clip(0, 2.5)
    ones = pd.Series(1.0, index=probs.index)
    for name, z, s in (("rev", G["rev_z"], s_rev), ("mom", G["mom_z"], s_mom)):
        sized = sized_book(z, s, G["tradable"], G["r1"], G["cost"])
        flat = sized_book(z, ones.where(s.notna()), G["tradable"], G["r1"], G["cost"])
        for per in ("1st", "2nd"):
            out[f"{name}_sized_net_sharpe_{per}"] = sized[f"net_sharpe_{per}"]
            out[f"{name}_flat_net_sharpe_{per}"] = flat[f"net_sharpe_{per}"]
            out[f"{name}_sizing_gain_{per}"] = sized[f"net_sharpe_{per}"] - flat[f"net_sharpe_{per}"]
    # switch: split capital by predicted IC share (reversal share in 0..1), vs 50/50
    share = (rev_pred.clip(lower=0) / (rev_pred.clip(lower=0) + mom_pred.clip(lower=0) + 1e-9)).clip(0, 1)
    w_rev, w_mom = _weights(G["rev_z"], G["tradable"]), _weights(G["mom_z"], G["tradable"])
    for name, a in (("switch", share), ("fifty", pd.Series(0.5, index=probs.index).where(share.notna()))):
        w = w_rev.mul(a.fillna(0), axis=0) + w_mom.mul((1 - a).fillna(0), axis=0)
        st = summarize(portfolio_stats(w, G["r1"], G["cost"]))
        for per in ("1st", "2nd"):
            out[f"{name}_net_sharpe_{per}"] = st[f"net_sharpe_{per}"]
    for per in ("1st", "2nd"):
        out[f"switch_gain_{per}"] = out[f"switch_net_sharpe_{per}"] - out[f"fifty_net_sharpe_{per}"]
    return out


def describe_states(hmm: LabHMM, state: pd.DataFrame, probs: pd.DataFrame, mkt: pd.Series) -> pd.DataFrame:
    """What each regime looks like (last fit): expected duration, share of days,
    market return and volatility while in it (2015-2026, probability-weighted)."""
    P = probs[probs.index >= SPLIT]
    r = mkt.reindex(P.index)
    rows = []
    for k in range(hmm.K):
        w = P.iloc[:, k].to_numpy()
        m = (w * r).sum() / w.sum()
        v = np.sqrt((w * (r - m) ** 2).sum() / w.sum())
        rows.append({"regime": k, "expected_days": 1 / (1 - hmm.transmat_[k, k]), "share_2015_26": w.mean(),
                     "ann_return": m * 252, "ann_vol": v * np.sqrt(252), "sharpe": m / v * np.sqrt(252) if v > 0 else np.nan})
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# driver
# -----------------------------------------------------------------------------
G: dict = {}


def run_variant(v: dict) -> dict:
    t0 = time.time()
    state, vol_col, count_col = G["states"][v["features"]]
    cols = list(state.columns)
    cc = cols.index(count_col) if count_col else None

    def make(i):
        return LabHMM(v["states"], emission=v["emission"], nu=5.0, sticky=v["sticky"], count_col=cc,
                      n_init=5, max_iter=200, seed=100 * i + 7, temper=v["temper"])

    try:
        probs, fits = walk_forward(state, make, cols.index(vol_col), cc)
        res = evaluate(probs, fits, G["event"], G["fwd_vol"], G["trail_vol"], G["ic_rev"])
        res.update(market_timing(probs, fits, G["mkt"]))
        res.update(book_tests(probs, fits, G))
        res["seconds"] = time.time() - t0
        tag = "{features}_{emission}_K{states}_s{sticky}_t{temper}".format(**v)
        # attrs (the predictive log-likelihood Series) cannot go into parquet metadata
        pd.DataFrame(probs.to_numpy(), index=probs.index, columns=probs.columns).to_parquet(
            Path(G["out"]) / "probs" / f"{tag}.parquet")
        res["described"] = describe_states(fits[-1][1], state, probs, G["mkt"]).round(4).to_dict(orient="records")
        LOG.info("%s: timing gain %.2f/%.2f, rev sizing gain %.2f/%.2f, switch gain %.2f/%.2f (%.0fs)", tag,
                 res["timing_gain_1st"], res["timing_gain_2nd"], res["rev_sizing_gain_1st"], res["rev_sizing_gain_2nd"],
                 res["switch_gain_1st"], res["switch_gain_2nd"], res["seconds"])
    except Exception as exc:  # noqa: BLE001 - one variant must not kill the sweep
        LOG.exception("variant %s failed", v)
        res = {"error": f"{type(exc).__name__}: {exc}"}
    return {**v, **res}


def variants(quick: bool, features: list[str]) -> list[dict]:
    out = []
    for f in features:
        temper = 0.5 if f == "rolling" else 1.0
        for em in ("gauss", "t"):
            for k in ((2, 3) if quick else (2, 3, 4)):
                for st in ((0.0,) if quick else (0.0, 20.0)):
                    out.append({"features": f, "emission": em, "states": k, "sticky": st, "temper": temper})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--out", default="reports/regime_lab")
    ap.add_argument("--features", default="rolling,daily,garch,dailyplus,poisson,macro")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args(argv)
    setup_logging()
    out = Path(args.out)
    (out / "probs").mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    md, ctx, X, names = load(args.lab)
    fred = None
    fp = Path(args.lab) / "fred.parquet"
    if fp.exists():
        fred = pd.read_parquet(fp)
    states = symptom_sets(ctx, fred)
    feats = [f for f in args.features.split(",") if f in states]
    mkt = ctx.market_ret
    o = md.open
    fwd5 = mkt[::-1].rolling(5).sum()[::-1].shift(-1)
    rev_z = pd.DataFrame(X[..., names.index("rev_5d")], index=md.dates, columns=md.tickers)
    mom_z = pd.DataFrame(X[..., names.index("mom_12_1")], index=md.dates, columns=md.tickers)
    fwd = (o.shift(-6) / o.shift(-1) - 1).where(ctx.tradable).to_numpy()
    G.update({
        "out": str(out), "states": states, "mkt": mkt,
        "event": (fwd5 < -0.03).astype(float).where(fwd5.notna()),
        "fwd_vol": np.log(mkt[::-1].rolling(21).std()[::-1].shift(-1)),
        "trail_vol": np.log(mkt.rolling(21).std()),
        "ic_rev": pd.Series(rank_ic(rev_z.to_numpy(), fwd), index=md.dates),
        "ic_mom": pd.Series(rank_ic(mom_z.to_numpy(), fwd), index=md.dates),
        "rev_z": rev_z, "mom_z": mom_z, "tradable": ctx.tradable, "cost": cost_panel(ctx),
        "r1": (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5),
    })
    del X
    vs = variants(args.quick, feats)
    LOG.info("regime lab: %d variants on %d workers", len(vs), args.workers)
    if args.workers > 1:
        with Pool(args.workers) as pool:
            rows = pool.map(run_variant, vs, chunksize=1)
    else:
        rows = [run_variant(v) for v in vs]
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "regime_lab.csv", index=False)
    write_report(tab, out)
    (out / "summary.json").write_text(json.dumps({"variants": len(tab)}, indent=2))


def write_report(tab: pd.DataFrame, out: Path) -> None:
    ok = tab[tab["error"].isna()] if "error" in tab else tab
    if ok.empty:
        (out / "regime_lab.md").write_text("every variant failed - see regime_lab.csv\n")
        return
    key = ["features", "emission", "states", "sticky"]
    lines = ["# Regime lab: HMM variants scored on money, walk-forward", "",
             "Every variant is refit yearly on all data to date; 2004-2014 ('1st') is for choosing, 2015-2026 "
             "('2nd') is the check. Gains are Sharpe differences against the matching regime-free baseline "
             "(volatility-managed market exposure; constant-gross reversal or momentum book; a 50/50 "
             "reversal/momentum split).", ""]
    stat = ["pred_ll_1st", "pred_ll_2nd", "brier_skill_1st", "brier_skill_2nd", "vol_r2_vs_trailing_1st",
            "vol_r2_vs_trailing_2nd", "confident_share_2nd"]
    lines += ["## Statistical scores", "", ok[key + stat].round(4).to_markdown(index=False), ""]
    econ = ["timing_volmanaged_sharpe_1st", "timing_regime_sharpe_1st", "timing_gain_1st", "timing_volmanaged_sharpe_2nd",
            "timing_regime_sharpe_2nd", "timing_gain_2nd"]
    lines += ["## Market timing: regime-conditional exposure vs. volatility-managed (10% target)", "",
              ok[key + econ].sort_values("timing_gain_1st", ascending=False).round(3).to_markdown(index=False), ""]
    rev = ["rev_flat_net_sharpe_1st", "rev_sized_net_sharpe_1st", "rev_sizing_gain_1st", "rev_flat_net_sharpe_2nd",
           "rev_sized_net_sharpe_2nd", "rev_sizing_gain_2nd", "rev_ic_calm_2nd", "rev_ic_stressed_2nd"]
    lines += ["## Reversal book sized by regime-conditional IC (net of costs)", "",
              ok[key + rev].sort_values("rev_sizing_gain_1st", ascending=False).round(3).to_markdown(index=False), ""]
    mom = ["mom_flat_net_sharpe_1st", "mom_sized_net_sharpe_1st", "mom_sizing_gain_1st", "mom_flat_net_sharpe_2nd",
           "mom_sized_net_sharpe_2nd", "mom_sizing_gain_2nd"]
    lines += ["## Momentum book sized by regime-conditional IC (net of costs)", "",
              ok[key + mom].sort_values("mom_sizing_gain_1st", ascending=False).round(3).to_markdown(index=False), ""]
    sw = ["fifty_net_sharpe_1st", "switch_net_sharpe_1st", "switch_gain_1st", "fifty_net_sharpe_2nd",
          "switch_net_sharpe_2nd", "switch_gain_2nd"]
    lines += ["## Reversal / momentum capital split by regime (net of costs)", "",
              ok[key + sw].sort_values("switch_gain_1st", ascending=False).round(3).to_markdown(index=False), ""]
    # the honest pick: best by the sum of first-period gains, then its second-period result
    ok = ok.assign(score_1st=ok["timing_gain_1st"] + ok["rev_sizing_gain_1st"] + ok["switch_gain_1st"],
                   score_2nd=ok["timing_gain_2nd"] + ok["rev_sizing_gain_2nd"] + ok["switch_gain_2nd"])
    best = ok.sort_values("score_1st", ascending=False).head(5)
    lines += ["## Picked on 2004-2014, checked on 2015-2026", "",
              "score = timing gain + reversal sizing gain + switch gain (Sharpe units).", "",
              best[key + ["score_1st", "score_2nd", "timing_gain_2nd", "rev_sizing_gain_2nd", "switch_gain_2nd"]]
              .round(3).to_markdown(index=False), ""]
    if "described" in best and isinstance(best.iloc[0]["described"], list):
        lines += ["### The chosen model's regimes (last fit, 2015-2026 statistics)", "",
                  pd.DataFrame(best.iloc[0]["described"]).round(3).to_markdown(index=False), ""]
    lines += [f"Rank correlation of score between periods across all variants: "
              f"{ok['score_1st'].corr(ok['score_2nd'], method='spearman'):.2f}", ""]
    (out / "regime_lab.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
