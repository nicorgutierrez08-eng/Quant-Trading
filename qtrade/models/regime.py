"""Walk-forward market-regime probabilities from the Gaussian HMM.

At each refit date R the HMM is re-estimated on all market-state data up to R
(expanding window, warm-started from the previous fit). Filtered probabilities
for the days after R - until the next refit - come from that model's forward
recursion, which only ever looks backwards. Before the first fit every regime
gets equal probability.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils import LOG
from .hmm import GaussianHMM


def walk_forward_regimes(
    state: pd.DataFrame,
    n_states: int = 3,
    refit_every: int = 252,
    min_history: int = 756,
    n_init: int = 5,
    max_iter: int = 200,
    seed: int = 0,
    vol_column: str = "log_rvol",
    temper: float = 1.0,
    align: bool = False,
) -> tuple[pd.DataFrame, list[tuple[pd.Timestamp, GaussianHMM]]]:
    """``temper`` < 1 down-weights each day's evidence (see GaussianHMM).
    ``align`` keeps state labels attached to the same regime across refits by
    matching each new state to the closest previous one, instead of re-sorting
    by volatility every year. The returned frame's ``attrs["predictive_ll"]``
    holds the out-of-sample one-step predictive log-likelihood per day."""
    X_all = state.to_numpy(dtype=float)
    T = len(X_all)
    probs = np.full((T, n_states), 1.0 / n_states)
    pred_ll = np.full(T, np.nan)
    valid = np.isfinite(X_all).all(axis=1)
    first = int(np.argmax(valid)) if valid.any() else T
    sort_col = list(state.columns).index(vol_column) if vol_column in state.columns else None

    fits: list[tuple[pd.Timestamp, GaussianHMM]] = []
    prev: GaussianHMM | None = None
    refits = list(range(first + min_history, T, refit_every))
    for i, r in enumerate(refits):
        train = X_all[first : r + 1]
        # standardise with training statistics only
        mu = np.nanmean(train, axis=0)
        sd = np.nanstd(train, axis=0) + 1e-12
        hmm = GaussianHMM(n_states, n_init=n_init if prev is None else 2,
                          max_iter=max_iter, seed=seed + i, temper=temper)
        warm = _restandardize(prev, mu, sd) if prev is not None else None
        hmm.fit((train - mu) / sd, warm=warm, sort_by=sort_col if (prev is None or not align) else None)
        hmm.mu_, hmm.sd_ = mu, sd
        if align and prev is not None:
            _align_to(hmm, prev)
        end = refits[i + 1] if i + 1 < len(refits) else T - 1
        # filter from the start of history through the end of this block
        Z = (X_all[first : end + 1] - mu) / sd
        alpha = hmm.filter(Z)
        probs[r + 1 : end + 1] = alpha[r + 1 - first :]
        # log-density in original units (subtract log sd), so blocks are comparable
        pred_ll[r + 1 : end + 1] = hmm.predictive_logpdf(Z)[r + 1 - first :] - np.log(sd).sum()
        if i == 0:
            probs[r] = alpha[r - first]
        prev = hmm
        fits.append((state.index[r], hmm))
    LOG.info("regime HMM: %d walk-forward fits, %d states", len(fits), n_states)
    cols = [f"regime_{k}" for k in range(n_states)]
    out = pd.DataFrame(probs, index=state.index, columns=cols)
    out.attrs["predictive_ll"] = pd.Series(pred_ll, index=state.index)
    return out, fits


def _restandardize(prev: GaussianHMM, mu: np.ndarray, sd: np.ndarray) -> GaussianHMM:
    """The previous model expressed in the new standardisation, for warm starts."""
    import copy

    w = copy.deepcopy(prev)
    scale = prev.sd_ / sd
    w.means_ = (prev.means_ * prev.sd_ + prev.mu_ - mu) / sd
    w.covars_ = prev.covars_ * np.outer(scale, scale)[None]
    return w


def _align_to(hmm: GaussianHMM, prev: GaussianHMM) -> None:
    """Relabel ``hmm``'s states so each sits where the closest previous state was."""
    from scipy.optimize import linear_sum_assignment

    new = hmm.means_ * hmm.sd_ + hmm.mu_
    old = prev.means_ * prev.sd_ + prev.mu_
    cost = (((new[:, None, :] - old[None, :, :]) / hmm.sd_) ** 2).sum(axis=2)
    rows, cols = linear_sum_assignment(cost)
    order = rows[np.argsort(cols)]          # order[j] = new state that becomes label j
    hmm.startprob_ = hmm.startprob_[order]
    hmm.transmat_ = hmm.transmat_[np.ix_(order, order)]
    hmm.means_ = hmm.means_[order]
    hmm.covars_ = hmm.covars_[order]


def latest_regime_model(fits):
    return fits[-1][1] if fits else None
