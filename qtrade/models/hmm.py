"""Gaussian hidden Markov model, written from scratch in NumPy.

Leonard Baum - co-author of the Baum-Welch algorithm - was one of Jim Simons'
first partners, and HMMs were among the earliest tools used at what became
Renaissance. The idea: the market moves between a few unobservable *regimes*
(calm, normal, crisis). We only observe noisy symptoms (returns, volatility,
dispersion, correlation); the HMM infers the regime probabilities from them.

Model
-----
    hidden state      s_t in {0..K-1},   P(s_1 = k) = pi_k
    transition        P(s_t = j | s_{t-1} = i) = A_ij
    emission          x_t | s_t = k  ~  Normal(mu_k, Sigma_k)

Algorithms
----------
* forward  (filtering)   alpha_t(k) = P(s_t = k | x_1..x_t)      <- used for trading
* backward / smoothing   gamma_t(k) = P(s_t = k | x_1..x_T)      <- only for fitting
* Baum-Welch (EM)        re-estimate pi, A, mu, Sigma from gamma and xi
* Viterbi                most likely single state path (diagnostics)

Only the *filtered* probabilities may be used for trading: smoothing uses
future observations.
"""
from __future__ import annotations

import numpy as np


class GaussianHMM:
    def __init__(self, n_states: int = 3, n_init: int = 5, max_iter: int = 200,
                 tol: float = 1e-4, reg: float = 1e-3, seed: int = 0, temper: float = 1.0):
        self.K = n_states
        # weight of each day's evidence (1 = standard HMM). Below 1 when the
        # observations overlap (rolling windows), so one piece of news isn't
        # counted ten times and the regime probabilities aren't overconfident.
        self.temper = temper
        self.n_init = n_init
        self.max_iter = max_iter
        self.tol = tol
        self.reg = reg
        self.rng = np.random.default_rng(seed)
        self.fitted = False

    # ------------------------------------------------------------------
    # emissions
    # ------------------------------------------------------------------
    def _log_emission(self, X: np.ndarray) -> np.ndarray:
        """log N(x_t; mu_k, Sigma_k) for every t, k. Rows with NaN get 0 (no info)."""
        T, D = X.shape
        out = np.zeros((T, self.K))
        ok = np.isfinite(X).all(axis=1)
        Xo = X[ok]
        for k in range(self.K):
            L = np.linalg.cholesky(self.covars_[k])
            diff = np.linalg.solve(L, (Xo - self.means_[k]).T)
            maha = (diff ** 2).sum(axis=0)
            logdet = 2 * np.log(np.diag(L)).sum()
            out[ok, k] = -0.5 * (D * np.log(2 * np.pi) + logdet + maha)
        return out

    # ------------------------------------------------------------------
    # forward / backward (scaled, so probabilities never underflow)
    # ------------------------------------------------------------------
    def _forward(self, logB: np.ndarray):
        T = len(logB)
        alpha = np.empty((T, self.K))
        scale = np.empty(T)
        # turn log-likelihoods into likelihoods safely: subtract each row's max
        m = logB.max(axis=1, keepdims=True)
        B = np.exp(logB - m)
        a = self.startprob_ * B[0]
        scale[0] = a.sum()
        alpha[0] = a / scale[0]
        A = self.transmat_
        for t in range(1, T):
            a = (alpha[t - 1] @ A) * B[t]
            s = a.sum()
            scale[t] = s
            alpha[t] = a / s
        loglik = np.log(scale).sum() + m.sum()
        return alpha, scale, B, loglik

    def _backward(self, B: np.ndarray, scale: np.ndarray) -> np.ndarray:
        T = len(B)
        beta = np.empty((T, self.K))
        beta[-1] = 1.0
        A = self.transmat_
        for t in range(T - 2, -1, -1):
            beta[t] = (A @ (B[t + 1] * beta[t + 1])) / scale[t + 1]
        return beta

    # ------------------------------------------------------------------
    # Baum-Welch
    # ------------------------------------------------------------------
    def _init_params(self, X: np.ndarray, warm: "GaussianHMM | None" = None) -> None:
        D = X.shape[1]
        if warm is not None and warm.fitted:
            self.startprob_ = warm.startprob_.copy()
            self.transmat_ = warm.transmat_.copy()
            self.means_ = warm.means_.copy()
            self.covars_ = warm.covars_.copy()
            return
        # k-means++ style: spread initial means over the data
        idx = [self.rng.integers(len(X))]
        for _ in range(1, self.K):
            d2 = np.min([((X - X[i]) ** 2).sum(axis=1) for i in idx], axis=0)
            idx.append(self.rng.choice(len(X), p=d2 / d2.sum()))
        self.means_ = X[idx].copy()
        cov = np.cov(X.T) + self.reg * np.eye(D)
        self.covars_ = np.stack([cov.copy() for _ in range(self.K)])
        self.startprob_ = np.full(self.K, 1.0 / self.K)
        self.transmat_ = np.full((self.K, self.K), 0.05 / max(self.K - 1, 1))
        np.fill_diagonal(self.transmat_, 0.95)

    def _em(self, X: np.ndarray) -> float:
        T, D = X.shape
        prev = -np.inf
        loglik = prev
        for _ in range(self.max_iter):
            logB = self._log_emission(X) * self.temper
            alpha, scale, B, loglik = self._forward(logB)
            beta = self._backward(B, scale)
            gamma = alpha * beta
            gamma /= gamma.sum(axis=1, keepdims=True)
            # expected transitions: xi_t(i,j) proportional to alpha_t(i) A_ij B_{t+1}(j) beta_{t+1}(j)
            bb = (B[1:] * beta[1:]) / scale[1:, None]
            xi_sum = self.transmat_ * (alpha[:-1].T @ bb)
            # M-step
            self.startprob_ = gamma[0] + 1e-6
            self.startprob_ /= self.startprob_.sum()
            self.transmat_ = xi_sum + 1e-6
            self.transmat_ /= self.transmat_.sum(axis=1, keepdims=True)
            w = gamma.sum(axis=0) + 1e-10
            self.means_ = (gamma.T @ X) / w[:, None]
            for k in range(self.K):
                diff = X - self.means_[k]
                self.covars_[k] = (gamma[:, k, None] * diff).T @ diff / w[k] + self.reg * np.eye(D)
            if abs(loglik - prev) < self.tol * max(1.0, abs(prev)):
                break
            prev = loglik
        return loglik

    def fit(self, X: np.ndarray, warm: "GaussianHMM | None" = None, sort_by: int | None = None) -> "GaussianHMM":
        """Fit by EM with ``n_init`` restarts (plus a warm start if given).

        ``sort_by``: feature column used to order states, so that state 0 always
        has the lowest mean of that feature (e.g. volatility). This keeps labels
        stable across refits.
        """
        X = X[np.isfinite(X).all(axis=1)]
        best = None
        tries = [warm] + [None] * (self.n_init - 1) if warm is not None else [None] * self.n_init
        for w in tries:
            self._init_params(X, w)
            ll = self._em(X)
            if best is None or ll > best[0]:
                best = (ll, self.startprob_.copy(), self.transmat_.copy(), self.means_.copy(), self.covars_.copy())
        self.loglik_, self.startprob_, self.transmat_, self.means_, self.covars_ = best
        if sort_by is not None:
            order = np.argsort(self.means_[:, sort_by])
            self.startprob_ = self.startprob_[order]
            self.transmat_ = self.transmat_[np.ix_(order, order)]
            self.means_ = self.means_[order]
            self.covars_ = self.covars_[order]
        self.fitted = True
        return self

    # ------------------------------------------------------------------
    # inference
    # ------------------------------------------------------------------
    def filter(self, X: np.ndarray) -> np.ndarray:
        """P(s_t | x_1..x_t): uses only the past - safe for trading."""
        alpha, *_ = self._forward(self._log_emission(X) * self.temper)
        return alpha

    def predictive_logpdf(self, X: np.ndarray) -> np.ndarray:
        """log p(x_t | x_1..x_{t-1}) for every t: how well yesterday's regime
        beliefs, pushed one step through the chain, predicted today. The honest
        out-of-sample score for comparing models (NaN for rows with gaps)."""
        logB = self._log_emission(X)
        alpha = self.filter(X)
        prior = np.vstack([self.startprob_[None], alpha[:-1] @ self.transmat_])
        m = logB.max(axis=1, keepdims=True)
        out = np.log((prior * np.exp(logB - m)).sum(axis=1)) + m[:, 0]
        out[~np.isfinite(X).all(axis=1)] = np.nan
        return out

    def predictive_states(self, X: np.ndarray) -> np.ndarray:
        """P(s_{t+1} | x_1..x_t): tomorrow's regime as seen at today's close."""
        return self.filter(X) @ self.transmat_

    def smooth(self, X: np.ndarray) -> np.ndarray:
        """P(s_t | x_1..x_T): uses the future - diagnostics only."""
        alpha, scale, B, _ = self._forward(self._log_emission(X) * self.temper)
        beta = self._backward(B, scale)
        g = alpha * beta
        return g / g.sum(axis=1, keepdims=True)

    def viterbi(self, X: np.ndarray) -> np.ndarray:
        logB = self._log_emission(X)
        T = len(logB)
        logA = np.log(self.transmat_)
        delta = np.log(self.startprob_) + logB[0]
        back = np.zeros((T, self.K), dtype=int)
        for t in range(1, T):
            cand = delta[:, None] + logA
            back[t] = cand.argmax(axis=0)
            delta = cand.max(axis=0) + logB[t]
        path = np.empty(T, dtype=int)
        path[-1] = delta.argmax()
        for t in range(T - 1, 0, -1):
            path[t - 1] = back[t, path[t]]
        return path

    def score(self, X: np.ndarray) -> float:
        return self._forward(self._log_emission(X))[3]

    def bic(self, X: np.ndarray) -> float:
        D = X.shape[1]
        n_params = (self.K - 1) + self.K * (self.K - 1) + self.K * D + self.K * D * (D + 1) / 2
        n = np.isfinite(X).all(axis=1).sum()
        return -2 * self.score(X) + n_params * np.log(n)

    def expected_durations(self) -> np.ndarray:
        """Average days spent in each regime once entered: 1 / (1 - A_kk)."""
        return 1.0 / (1.0 - np.diag(self.transmat_))

