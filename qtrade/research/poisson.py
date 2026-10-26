"""Poisson and Hawkes models for the things that arrive as counts.

A "jump" is a day on which a stock's factor-residual return is beyond 3 times
its trailing volatility. Jumps, like news articles, are discrete events, and a
Poisson model is the natural first description of how often they happen.

1. Market jump counts N_t (stocks jumping on day t):
   * overdispersion: var/mean = 1 for a Poisson process; >> 1 means jumps
     cluster in time
   * INGARCH(1,1): lambda_t = w + a N_{t-1} + b lambda_{t-1}, a self-exciting
     Poisson model (a discrete-time Hawkes process). a + b near 1 = jump
     storms persist. Scored on out-of-sample predictive log-likelihood vs. a
     constant-rate Poisson.
   * Poisson HMM: hidden regimes with their own jump rate. Walk-forward,
     scored like the Gaussian HMM (crash calibration, reversal IC by regime).
2. Stock jump intensities (Gamma-Poisson shrinkage toward the cross-section):
   crash_risk (down-jump rate) and jump_skew (up minus down rate).
3. After a jump: average market-relative return over the next 1-10 days,
   split by direction and (if news data exists) whether there was news.
4. news_surprise: 3-day article count vs. the stock's own expected Poisson
   rate, as a Pearson residual (N - lambda) / sqrt(lambda).
5. Hawkes processes: up and down jumps exciting themselves and each other
   (branching matrix), and a fast + slow kernel for long memory. Poisson
   regressions: next-month jump counts per stock on Hawkes-style decayed
   jump memory and stock features (incidence-rate ratios, out-of-sample
   deviance explained; the predicted crash intensity becomes a signal), and
   daily news counts on moves, volume and size (the unexplained part is a
   cleaner news surprise).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

from ..utils import LOG, rank_ic

SPLIT = "2015-01-01"


# -----------------------------------------------------------------------------
# jumps
# -----------------------------------------------------------------------------
def jump_panels(ctx, k: float = 3.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(up, down) jump indicators from factor residuals vs. trailing vol (known at the close)."""
    e = ctx.resid
    sd = e.rolling(63, min_periods=40).std().shift(1)
    z = e / sd
    tr = ctx.tradable
    return (z > k).where(tr), (z < -k).where(tr)


def gamma_poisson_rate(events: pd.DataFrame, window: int = 252, prior_days: float = 252) -> pd.DataFrame:
    """Shrunk daily event rate per stock: (count + a) / (exposure + b), with the
    prior mean set to the cross-sectional average rate that day."""
    cnt = events.rolling(window, min_periods=window // 2).sum()
    expo = events.notna().rolling(window, min_periods=window // 2).sum()
    pooled = cnt.sum(axis=1) / expo.sum(axis=1)
    a = pooled * prior_days
    return cnt.add(a, axis=0).div(expo + prior_days)


# -----------------------------------------------------------------------------
# INGARCH(1,1): self-exciting Poisson counts
# -----------------------------------------------------------------------------
def ingarch_filter(n: np.ndarray, w: float, a: float, b: float) -> np.ndarray:
    lam = np.empty(len(n))
    lam[0] = max(np.nanmean(n), 1e-3)
    for t in range(1, len(n)):
        prev = n[t - 1] if np.isfinite(n[t - 1]) else lam[t - 1]
        lam[t] = w + a * prev + b * lam[t - 1]
    return lam


def poisson_ll(n: np.ndarray, lam: np.ndarray) -> np.ndarray:
    lam = np.maximum(lam, 1e-9)
    return n * np.log(lam) - lam - gammaln(n + 1)


def fit_ingarch(n: np.ndarray) -> tuple[float, float, float]:
    ok = np.isfinite(n)
    m = np.nanmean(n)

    def nll(p):
        w, a, b = np.exp(p[0]), 1 / (1 + np.exp(-p[1])), 1 / (1 + np.exp(-p[2]))
        if a + b >= 0.999:
            return 1e12
        lam = ingarch_filter(n, w, a, b)
        return -poisson_ll(n[ok], lam[ok]).sum()

    best = None
    for a0, b0 in ((0.3, 0.5), (0.1, 0.8), (0.5, 0.3)):
        x0 = [np.log(m * (1 - a0 - b0)), np.log(a0 / (1 - a0)), np.log(b0 / (1 - b0))]
        r = minimize(nll, x0, method="Nelder-Mead", options={"maxiter": 2000, "xatol": 1e-6, "fatol": 1e-6})
        if best is None or r.fun < best.fun:
            best = r
    p = best.x
    return float(np.exp(p[0])), float(1 / (1 + np.exp(-p[1]))), float(1 / (1 + np.exp(-p[2])))


# -----------------------------------------------------------------------------
# Poisson HMM
# -----------------------------------------------------------------------------
class PoissonHMM:
    """Hidden Markov model whose regimes differ in their event rate."""

    def __init__(self, k: int = 3, n_iter: int = 200, seed: int = 0):
        self.K, self.n_iter = k, n_iter
        self.rng = np.random.default_rng(seed)

    def _logB(self, n):
        out = np.zeros((len(n), self.K))
        ok = np.isfinite(n)
        out[ok] = poisson_ll(n[ok, None], self.rates[None, :])
        return out

    def _forward(self, logB):
        T = len(logB)
        alpha = np.empty((T, self.K))
        scale = np.empty(T)
        m = logB.max(axis=1, keepdims=True)
        B = np.exp(logB - m)
        a = self.pi * B[0]
        for t in range(T):
            if t:
                a = (alpha[t - 1] @ self.A) * B[t]
            scale[t] = a.sum()
            alpha[t] = a / scale[t]
        return alpha, scale, B

    def fit(self, n: np.ndarray, warm: "PoissonHMM | None" = None) -> "PoissonHMM":
        x = n[np.isfinite(n)]
        if warm is not None:
            self.rates, self.A, self.pi = warm.rates.copy(), warm.A.copy(), warm.pi.copy()
        else:
            self.rates = np.quantile(x, np.linspace(0.2, 0.95, self.K)) + 0.1
            self.A = np.full((self.K, self.K), 0.05 / max(self.K - 1, 1))
            np.fill_diagonal(self.A, 0.95)
            self.pi = np.full(self.K, 1 / self.K)
        prev = -np.inf
        for _ in range(self.n_iter):
            logB = self._logB(x)
            alpha, scale, B = self._forward(logB)
            beta = np.empty_like(alpha)
            beta[-1] = 1
            for t in range(len(x) - 2, -1, -1):
                beta[t] = (self.A @ (B[t + 1] * beta[t + 1])) / scale[t + 1]
            g = alpha * beta
            g /= g.sum(axis=1, keepdims=True)
            xi = self.A * (alpha[:-1].T @ ((B[1:] * beta[1:]) / scale[1:, None]))
            self.A = xi / xi.sum(axis=1, keepdims=True)
            self.pi = g[0] + 1e-6
            self.pi /= self.pi.sum()
            self.rates = (g * x[:, None]).sum(axis=0) / (g.sum(axis=0) + 1e-9) + 1e-6
            ll = np.log(scale).sum() + logB.max(axis=1).sum()
            if ll - prev < 1e-6 * abs(ll):
                break
            prev = ll
        order = np.argsort(self.rates)                         # state 0 = calmest
        self.rates, self.pi = self.rates[order], self.pi[order]
        self.A = self.A[np.ix_(order, order)]
        return self

    def filter(self, n: np.ndarray) -> np.ndarray:
        return self._forward(self._logB(n))[0]

    def predictive_ll(self, n: np.ndarray) -> np.ndarray:
        alpha = self.filter(n)
        prior = np.vstack([self.pi[None], alpha[:-1] @ self.A])
        return np.log((prior * np.exp(self._logB(n))).sum(axis=1))


def walk_forward_poisson_hmm(n: pd.Series, k: int, refit_every: int = 252, min_history: int = 756):
    x = n.to_numpy(dtype=float)
    T = len(x)
    first = int(np.argmax(np.isfinite(x)))
    probs = np.full((T, k), np.nan)
    pll = np.full(T, np.nan)
    prev = None
    refits = list(range(first + min_history, T, refit_every))
    for i, r in enumerate(refits):
        hmm = PoissonHMM(k).fit(x[first:r + 1], warm=prev)
        end = refits[i + 1] if i + 1 < len(refits) else T - 1
        a = hmm.filter(x[first:end + 1])
        probs[r + 1:end + 1] = a[r + 1 - first:]
        pll[r + 1:end + 1] = hmm.predictive_ll(x[first:end + 1])[r + 1 - first:]
        prev = hmm
    return pd.DataFrame(probs, index=n.index), pd.Series(pll, index=n.index), prev


# -----------------------------------------------------------------------------
# the study
# -----------------------------------------------------------------------------
def run(md, ctx, out: Path, news_counts: pd.DataFrame | None = None) -> tuple[dict, dict]:
    up, down = jump_panels(ctx)
    n_up = up.sum(axis=1)
    n_dn = down.sum(axis=1)
    N = (n_up + n_dn).where(ctx.resid.notna().sum(axis=1) > 50)
    lines = ["## Poisson models of jumps and news", ""]
    res = {}

    # 1a. overdispersion
    disp = {}
    for name, s in (("all jumps", N), ("up jumps", n_up.where(N.notna())), ("down jumps", n_dn.where(N.notna()))):
        s = s.dropna()
        disp[name] = {"mean_per_day": s.mean(), "variance": s.var(), "var_over_mean": s.var() / s.mean()}
    dtab = pd.DataFrame(disp).T
    res["dispersion"] = float(dtab.loc["all jumps", "var_over_mean"])
    lines += ["### Do jumps cluster? (Poisson: variance / mean = 1)", "", dtab.round(2).to_markdown(), ""]

    # 1b. INGARCH: fit on 2004-2014, score both periods out of sample
    x = N.to_numpy(dtype=float)
    idx = N.index
    tr = (idx < SPLIT) & np.isfinite(x)
    w, a, b = fit_ingarch(np.where(idx < SPLIT, x, np.nan)[: tr.nonzero()[0][-1] + 1])
    lam = ingarch_filter(x, w, a, b)
    const = np.nanmean(x[tr])
    ok = np.isfinite(x)
    rows = []
    for per, m in (("2004-2014 (fit)", (idx < SPLIT) & ok), ("2015-2026 (out of sample)", (idx >= SPLIT) & ok)):
        rows.append({"period": per, "ll_ingarch": poisson_ll(x[m], lam[m]).mean(),
                     "ll_constant_rate": poisson_ll(x[m], np.full(m.sum(), const)).mean(),
                     "corr(predicted, actual)": np.corrcoef(lam[m], x[m])[0, 1]})
    itab = pd.DataFrame(rows)
    res["ingarch"] = {"w": w, "a": a, "b": b, "persistence": a + b}
    lines += [f"### Self-exciting jumps: INGARCH(1,1) lambda_t = {w:.2f} + {a:.3f} N_t-1 + {b:.3f} lambda_t-1", "",
              f"Persistence a + b = **{a + b:.3f}** (1 = jump storms never die out; the half-life of a shock is "
              f"{np.log(0.5) / np.log(a + b) if 0 < a + b < 1 else float('nan'):.1f} days).", "",
              itab.round(4).to_markdown(index=False), ""]

    # 1c. Poisson HMM vs. crash calibration and reversal IC
    mkt = ctx.market_ret
    fwd5 = mkt[::-1].rolling(5).sum()[::-1].shift(-1)
    event = (fwd5 < -0.03).astype(float).where(fwd5.notna())
    from ..signals import compute_signals

    rev = compute_signals(ctx, ["rev_5d"])["rev_5d"].to_numpy()
    o = md.open
    fwd = (o.shift(-6) / o.shift(-1) - 1).where(ctx.tradable).to_numpy()
    rev_ic = pd.Series(rank_ic(rev, fwd), index=md.dates)
    hrows = []
    for k in (2, 3):
        P, pll, last = walk_forward_poisson_hmm(N, k)
        row = {"states": k, "rates (jumps/day)": np.round(last.rates, 1).tolist(),
               "expected_days_in_state": np.round(1 / (1 - np.diag(last.A)), 1).tolist()}
        for per, m in (("1st", (idx >= "2006-01-01") & (idx < SPLIT)), ("2nd", idx >= SPLIT)):
            m = m & P.notna().all(axis=1).to_numpy()
            Pm = P[m].to_numpy()
            row[f"pred_ll_{per}"] = float(np.nanmean(pll[m]))
            # crash probability from per-state frequencies learned on 2004-2014
            ftr = (idx < SPLIT) & P.notna().all(axis=1).to_numpy() & event.notna().to_numpy()
            f_k = (P[ftr].to_numpy() * event[ftr].to_numpy()[:, None]).sum(0) / P[ftr].to_numpy().sum(0)
            p_ev = Pm @ f_k
            y = event[m].to_numpy()
            okk = np.isfinite(y)
            base = event[ftr].mean()
            row[f"brier_skill_{per}"] = 1 - np.mean((p_ev[okk] - y[okk]) ** 2) / np.mean((base - y[okk]) ** 2)
            ric = rev_ic[m].to_numpy()
            okr = np.isfinite(ric)
            for tag, j in (("calm", 0), ("stormy", k - 1)):
                wj = Pm[okr, j]
                row[f"rev_ic_{tag}_{per}"] = float((wj * ric[okr]).sum() / wj.sum()) if wj.sum() > 1 else np.nan
        hrows.append(row)
    htab = pd.DataFrame(hrows)
    lines += ["### Poisson HMM on daily jump counts (walk-forward)", "",
              "Compare brier_skill and rev_ic with the Gaussian HMM table: same tests, different symptoms.", "",
              htab.round(4).to_markdown(index=False), ""]

    # 2. stock-level jump intensity signals
    lam_up = gamma_poisson_rate(up)
    lam_dn = gamma_poisson_rate(down)
    signals = {"crash_risk": -lam_dn, "jump_skew": -(lam_up - lam_dn), "jump_intensity": -(lam_up + lam_dn)}

    # 3. what happens after a jump
    ar = ctx.ret.sub(mkt, axis=0)
    has_news = None
    if news_counts is not None:
        has_news = news_counts.reindex_like(up).fillna(0).rolling(2).sum() > 0
    ev_rows = []
    car = {h: ar[::-1].rolling(h).sum()[::-1].shift(-1) for h in (1, 3, 5, 10)}   # days t+1..t+h
    for name, ev in (("up jump", up), ("down jump", down)):
        groups = [("all", ev == 1)]
        if has_news is not None:
            groups += [("with news", (ev == 1) & has_news), ("no news", (ev == 1) & ~has_news)]
        for g, m in groups:
            for per, sel in (("1st", (ar.index >= "2006-01-01") & (ar.index < SPLIT)), ("2nd", ar.index >= SPLIT)):
                mm = m[sel]
                row = {"event": name, "news": g, "period": per, "events": int(mm.sum().sum())}
                for h, c in car.items():
                    v = c[sel].where(mm).stack()
                    row[f"car_{h}d_bp"] = v.mean() * 1e4
                    if h == 5:
                        row["t_5d"] = v.mean() / v.std() * np.sqrt(len(v)) if len(v) > 10 else np.nan
                ev_rows.append(row)
    etab = pd.DataFrame(ev_rows)
    lines += ["### After a jump: market-relative return over the next days (bp)", "",
              "Negative after an up jump (or positive after a down jump) = reversal; same sign = drift.", "",
              etab.round(2).to_markdown(index=False), ""]

    # 4. news surprise
    if news_counts is not None:
        c = news_counts.reindex_like(up).fillna(0.0).where(ctx.tradable.reindex_like(up))
        lam_n = gamma_poisson_rate(c.shift(3), window=250, prior_days=60) * 3        # expected 3-day count
        c3 = c.rolling(3).sum()
        signals["news_surprise"] = -((c3 - lam_n) / np.sqrt(lam_n.clip(lower=0.05)))

    # 5. Hawkes processes and Poisson regressions
    res |= hawkes_study(n_up.where(N.notna()), n_dn.where(N.notna()), lines)
    r, s = jump_regressions(md, ctx, up, down, news_counts, lines)
    res["jump_regressions"] = r
    signals.update(s)
    if news_counts is not None:
        r, s = news_regression(md, ctx, news_counts, lines)
        res["news_regression"] = r
        signals.update(s)

    pd.DataFrame({"N": N, "lambda_ingarch": lam}).to_csv(out / "poisson_jump_counts.csv")
    etab.to_csv(out / "poisson_after_jumps.csv", index=False)
    htab.to_csv(out / "poisson_hmm.csv", index=False)
    (out / "poisson.md").write_text("\n".join(lines) + "\n")
    LOG.info("poisson: dispersion %.1f, INGARCH persistence %.3f", res["dispersion"], a + b)
    return res, signals


# -----------------------------------------------------------------------------
# Hawkes processes on daily jump counts
# -----------------------------------------------------------------------------
def decayed_sums(counts: np.ndarray, beta: float) -> np.ndarray:
    """S_t = sum_{s<t} N_s exp(-beta (t-1-s)): the Hawkes memory entering day t
    (only past days; NaN days count as zero). Works on (T,) or (T, N)."""
    c = np.nan_to_num(counts)
    S = np.zeros_like(c, dtype=float)
    d = np.exp(-beta)
    for t in range(1, len(c)):
        S[t] = d * S[t - 1] + c[t - 1]
    return S


def _fit_nm(nll, x0s):
    best = None
    for x0 in x0s:
        r = minimize(nll, x0, method="Nelder-Mead", options={"maxiter": 6000, "xatol": 1e-7, "fatol": 1e-7})
        if best is None or r.fun < best.fun:
            best = r
    return best


def fit_hawkes_bivariate(up: np.ndarray, dn: np.ndarray) -> dict:
    """lambda_U = mu_U + a_UU S_U + a_UD S_D,  lambda_D = mu_D + a_DU S_U + a_DD S_D,
    with one decay rate beta shared by both kernels."""
    ok = np.isfinite(up) & np.isfinite(dn)

    def unpack(p):
        mu = np.exp(p[:2])
        a = np.exp(p[2:6]).reshape(2, 2)            # a[i, j]: effect of type j on type i
        beta = np.exp(p[6])
        return mu, a, beta

    def lam(p):
        mu, a, beta = unpack(p)
        SU, SD = decayed_sums(up, beta), decayed_sums(dn, beta)
        return mu[0] + a[0, 0] * SU + a[0, 1] * SD, mu[1] + a[1, 0] * SU + a[1, 1] * SD

    def nll(p):
        lu, ld = lam(p)
        return -(poisson_ll(up[ok], lu[ok]).sum() + poisson_ll(dn[ok], ld[ok]).sum())

    m_u, m_d = np.nanmean(up), np.nanmean(dn)
    x0s = [np.log([m_u * 0.3, m_d * 0.3, 0.05, 0.03, 0.03, 0.05, b]) for b in (0.1, 0.3, 0.7)]
    r = _fit_nm(nll, x0s)
    mu, a, beta = unpack(r.x)
    branching = a / (1 - np.exp(-beta))             # expected follow-on jumps of type i per jump of type j
    return {"mu": mu, "alpha": a, "beta": beta, "branching": branching,
            "spectral_radius": float(np.max(np.abs(np.linalg.eigvals(branching)))),
            "params": r.x, "lam": lam}


def fit_hawkes_two_kernels(n: np.ndarray) -> dict:
    """lambda_t = mu + a1 S_t(beta1) + a2 S_t(beta2): a fast and a slow memory."""
    ok = np.isfinite(n)

    def lam(p):
        mu, a1, a2, b1, db = np.exp(p)
        b2 = b1 + db                                # beta2 > beta1: kernel 2 is the fast one
        return mu + a1 * decayed_sums(n, b1) + a2 * decayed_sums(n, b2)

    def nll(p):
        return -poisson_ll(n[ok], lam(p)[ok]).sum()

    m = np.nanmean(n)
    r = _fit_nm(nll, [np.log([m * 0.2, 0.01, 0.2, 0.02, 0.5]), np.log([m * 0.3, 0.02, 0.3, 0.05, 1.0])])
    mu, a1, a2, b1, db = np.exp(r.x)
    return {"mu": mu, "a_slow": a1, "beta_slow": b1, "a_fast": a2, "beta_fast": b1 + db,
            "halflife_slow_days": np.log(2) / b1, "halflife_fast_days": np.log(2) / (b1 + db),
            "branching": a1 / (1 - np.exp(-b1)) + a2 / (1 - np.exp(-(b1 + db))), "params": r.x, "lam": lam}


def hawkes_study(up_n: pd.Series, dn_n: pd.Series, lines: list) -> dict:
    idx = up_n.index
    first = idx < SPLIT
    u, d = up_n.to_numpy(float), dn_n.to_numpy(float)
    n = u + d
    utr, dtr, ntr = np.where(first, u, np.nan), np.where(first, d, np.nan), np.where(first, n, np.nan)
    bi = fit_hawkes_bivariate(utr, dtr)
    two = fit_hawkes_two_kernels(ntr)
    w, a, b = fit_ingarch(ntr)
    lam_ing = ingarch_filter(n, w, a, b)
    # parameters fitted on 2004-2014, applied to the whole series (each day only sees earlier days)
    lu = bi["mu"][0] + bi["alpha"][0, 0] * decayed_sums(u, bi["beta"]) + bi["alpha"][0, 1] * decayed_sums(d, bi["beta"])
    ld = bi["mu"][1] + bi["alpha"][1, 0] * decayed_sums(u, bi["beta"]) + bi["alpha"][1, 1] * decayed_sums(d, bi["beta"])
    p = two["params"]
    mu2, a1, a2, b1, db = np.exp(p)
    lam_two = mu2 + a1 * decayed_sums(n, b1) + a2 * decayed_sums(n, b1 + db)
    rows = []
    ok = np.isfinite(n)
    for per, m in (("2004-2014 (fit)", first & ok), ("2015-2026 (out of sample)", ~first & ok)):
        rows.append({"period": per,
                     "constant": poisson_ll(n[m], np.full(m.sum(), np.nanmean(ntr))).mean(),
                     "INGARCH(1,1)": poisson_ll(n[m], lam_ing[m]).mean(),
                     "Hawkes, 2 kernels": poisson_ll(n[m], lam_two[m]).mean(),
                     "Hawkes up/down (total)": (poisson_ll(u[m], lu[m]) + poisson_ll(d[m], ld[m])).mean()})
    tab = pd.DataFrame(rows)
    br = pd.DataFrame(bi["branching"], index=["-> up jumps", "-> down jumps"], columns=["from up jump", "from down jump"])
    lines += ["### Hawkes processes", "",
              f"**Up/down Hawkes** (shared decay, half-life {np.log(2) / bi['beta']:.1f} days). Branching matrix: "
              "expected follow-on jumps of each type caused by one jump (spectral radius "
              f"{bi['spectral_radius']:.2f}; below 1 = storms die out):", "", br.round(3).to_markdown(), "",
              f"**Two-kernel Hawkes** on all jumps: fast half-life {two['halflife_fast_days']:.1f} days, slow "
              f"half-life {two['halflife_slow_days']:.1f} days, total branching ratio {two['branching']:.2f}.", "",
              "Average daily log-likelihood (higher is better; the up/down model scores two series, so compare it "
              "only across periods):", "", tab.round(4).to_markdown(index=False), ""]
    return {"hawkes_branching": bi["branching"].round(3).tolist(), "hawkes_half_life": float(np.log(2) / bi["beta"]),
            "two_kernel_halflives": [float(two["halflife_fast_days"]), float(two["halflife_slow_days"])]}


# -----------------------------------------------------------------------------
# Poisson regressions
# -----------------------------------------------------------------------------
def _poisson_glm(Xtr, ytr, Xte, yte, names, alpha: float = 1e-4) -> tuple[pd.DataFrame, dict]:
    from sklearn.linear_model import PoissonRegressor

    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0) + 1e-12
    m = PoissonRegressor(alpha=alpha, max_iter=1000).fit((Xtr - mu) / sd, ytr)
    pr_tr, pr_te = m.predict((Xtr - mu) / sd), m.predict((Xte - mu) / sd)

    def d2(y, p):                                   # share of Poisson deviance explained vs. a constant rate
        ym = ytr.mean()
        dev = 2 * np.sum(np.where(y > 0, y * np.log(np.maximum(y, 1e-12) / p), 0) - (y - p))
        dev0 = 2 * np.sum(np.where(y > 0, y * np.log(np.maximum(y, 1e-12) / ym), 0) - (y - ym))
        return 1 - dev / dev0

    coef = pd.DataFrame({"feature": names, "coef_per_sd": m.coef_,
                         "rate_ratio_per_sd": np.exp(m.coef_)}).sort_values("coef_per_sd", key=np.abs, ascending=False)
    return coef, {"deviance_explained_train": d2(ytr, pr_tr), "deviance_explained_test": d2(yte, pr_te),
                  "model": m, "mu": mu, "sd": sd}


def jump_regressions(md, ctx, up: pd.DataFrame, down: pd.DataFrame, news_counts, lines: list):
    """Per-stock jump counts over the next 21 days ~ Hawkes-style memory and stock features."""
    tr = ctx.tradable
    feats = {
        "own_jumps_fast (5d half-life)": decayed_sums((up.fillna(0) + down.fillna(0)).to_numpy(), np.log(2) / 5),
        "own_jumps_slow (63d half-life)": decayed_sums((up.fillna(0) + down.fillna(0)).to_numpy(), np.log(2) / 63),
        "own_down_jumps_slow": decayed_sums(down.fillna(0).to_numpy(), np.log(2) / 63),
        "market_jumps_fast": np.repeat(decayed_sums((up.sum(1) + down.sum(1)).to_numpy()[:, None]
                                                    / tr.sum(1).clip(lower=1).to_numpy()[:, None],
                                                    np.log(2) / 5), up.shape[1], axis=1),
        "log_vol_63": np.log(ctx.vol_63.to_numpy() + 1e-4),
        "abn_volume_5d": np.log((md.volume.rolling(5).mean() / md.volume.rolling(63).mean()).to_numpy() + 1e-6),
        "log_dollar_volume": np.log(ctx.adv.to_numpy() + 1),
        "ret_21d": ctx.log_ret.rolling(21).sum().to_numpy(),
    }
    if news_counts is not None:
        nc = news_counts.reindex_like(up).fillna(0).to_numpy()
        feats["news_fast (5d half-life)"] = np.log1p(decayed_sums(nc, np.log(2) / 5) + nc)
    names = list(feats)
    F = np.stack([feats[k] for k in names], axis=-1)                       # T x N x K, all known at day t
    fut = {name: ev.fillna(0)[::-1].rolling(21).sum()[::-1].shift(-1).where(tr).to_numpy()
           for name, ev in (("up", up), ("down", down))}
    T = len(md.dates)
    sample_days = np.arange(300, T - 22, 21)                                # non-overlapping 21-day windows
    first = np.asarray(md.dates < SPLIT)
    out, preds = {}, {}
    for kind, Y in fut.items():
        Xs, ys, period = [], [], []
        for t in sample_days:
            X, y = F[t], Y[t]
            ok = np.isfinite(X).all(axis=1) & np.isfinite(y) & tr.iloc[t].to_numpy()
            Xs.append(X[ok]); ys.append(y[ok]); period.append(np.full(ok.sum(), first[t]))
        X, y, p1 = np.vstack(Xs), np.concatenate(ys), np.concatenate(period)
        coef, st = _poisson_glm(X[p1], y[p1], X[~p1], y[~p1], names)
        out[kind] = st
        lines += [f"### Poisson regression: {kind}-jumps in the next 21 days", "",
                  f"{int(p1.sum())} training rows (2004-2014), {int((~p1).sum())} test rows (2015-2026). Deviance "
                  f"explained: {st['deviance_explained_train']:.3f} in-sample, **{st['deviance_explained_test']:.3f} "
                  "out of sample**. rate_ratio_per_sd: how much one standard deviation of the feature multiplies "
                  "the jump rate.", "", coef.round(3).to_markdown(index=False), ""]
        # predicted intensity for every day (coefficients from 2004-2014 only)
        Z = (F - st["mu"]) / st["sd"]
        lam = np.exp(np.nan_to_num(Z) @ st["model"].coef_ + st["model"].intercept_)
        lam[~np.isfinite(F).all(axis=-1)] = np.nan
        preds[kind] = pd.DataFrame(lam, index=md.dates, columns=md.tickers)
    signals = {"pred_crash_intensity": -preds["down"], "pred_jump_skew": -(preds["up"] - preds["down"])}
    return {k: {"deviance_explained_test": float(v["deviance_explained_test"])} for k, v in out.items()}, signals


def news_regression(md, ctx, news_counts: pd.DataFrame, lines: list):
    """Daily article counts ~ recent moves, volume, size, weekday. The part the
    model cannot explain (Pearson residual) is the news surprise."""
    nc = news_counts.reindex_like(ctx.ret).fillna(0)
    cov = nc.rolling(250, min_periods=60).sum() > 0
    feats = {
        "abs_ret_today": ctx.ret.abs(),
        "abs_ret_5d": ctx.log_ret.rolling(5).sum().abs(),
        "abn_volume": np.log(md.volume / md.volume.rolling(63).mean() + 1e-6),
        "log_dollar_volume": np.log(ctx.adv + 1),
        "past_news_rate": np.log1p(nc.shift(1).rolling(60).mean()),
        "monday": pd.DataFrame(np.repeat((md.dates.dayofweek == 0)[:, None], nc.shape[1], 1).astype(float),
                               index=nc.index, columns=nc.columns),
    }
    names = list(feats)
    F = np.stack([feats[k].to_numpy() for k in names], axis=-1)
    Y = nc.to_numpy()
    ok = np.isfinite(F).all(axis=-1) & cov.to_numpy() & ctx.tradable.to_numpy()
    first = np.asarray(md.dates < SPLIT)[:, None] & ok
    rng = np.random.default_rng(0)
    tr_idx = np.flatnonzero(first.ravel())
    te_idx = np.flatnonzero((ok & ~first).ravel())
    tr_idx = rng.choice(tr_idx, min(400_000, len(tr_idx)), replace=False) if len(tr_idx) else tr_idx
    te_idx = rng.choice(te_idx, min(400_000, len(te_idx)), replace=False) if len(te_idx) else te_idx
    if len(tr_idx) < 1000:                     # news starts in 2015: train on the first two years instead
        cut = np.asarray(md.dates < "2017-01-01")[:, None] & ok
        tr_idx = rng.choice(np.flatnonzero(cut.ravel()), min(400_000, int(cut.sum())), replace=False)
        te_idx = rng.choice(np.flatnonzero((ok & ~cut).ravel()), min(400_000, int((ok & ~cut).sum())), replace=False)
        train_label = "2015-2016"
    else:
        train_label = "before 2015"
    Ff, Yf = F.reshape(-1, len(names)), Y.ravel()
    coef, st = _poisson_glm(Ff[tr_idx], Yf[tr_idx], Ff[te_idx], Yf[te_idx], names)
    lam = np.exp(((np.nan_to_num(F) - st["mu"]) / st["sd"]) @ st["model"].coef_ + st["model"].intercept_)
    surprise = (Y - lam) / np.sqrt(lam)
    surprise[~ok] = np.nan
    s3 = pd.DataFrame(surprise, index=nc.index, columns=nc.columns).rolling(3).sum()
    lines += ["### Poisson regression: what makes news arrive", "",
              f"Trained on {train_label}. Deviance explained out of sample: "
              f"**{st['deviance_explained_test']:.3f}**.", "", coef.round(3).to_markdown(index=False), ""]
    return {"deviance_explained_test": float(st["deviance_explained_test"])}, {"news_surprise_glm": -s3}
