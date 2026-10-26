"""Walk-forward training: the only honest way to backtest a learned model.

Timeline for one refit at day r (all at the close of day r)::

    |<-------------- train_window -------------->|<-h-1->| r |---- predict ---->| next refit
     training rows: day d with label known by r      gap      model used for days r .. next-1

The label for day d is the return from the open of d+1 to the open of
d+1+h, which is only known once day d+1+h has opened. So training rows stop at
d = r - 1 - h: no label that is still in the future at r ever enters training.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..utils import LOG
from .combiners import BaseModel, build_model


@dataclass
class WalkForwardResult:
    predictions: dict[str, np.ndarray]                 # model -> T x N
    weights: dict[str, list[tuple[pd.Timestamp, np.ndarray]]] = field(default_factory=dict)
    refit_dates: list[pd.Timestamp] = field(default_factory=list)
    final_models: dict[str, BaseModel] = field(default_factory=dict)
    fit_seconds: dict[str, float] = field(default_factory=dict)
    selected: dict[pd.Timestamp, np.ndarray] = field(default_factory=dict)   # refit date -> kept signals


def _rows(feats, target, lo, hi):
    """Stack (day, stock) rows for days lo..hi where features and target exist."""
    F = feats[lo : hi + 1]
    ok = np.isfinite(F[..., 0])
    if target is not None:
        ok &= np.isfinite(target[lo : hi + 1])
    d, i = np.nonzero(ok)
    return d + lo, i, F[d, i]


def stable_signals(X: np.ndarray, y: np.ndarray, day: np.ndarray, splits: int = 3,
                   min_t: float = 2.0) -> np.ndarray:
    """Signals whose daily IC kept the same sign in each of ``splits``
    consecutive parts of the training window and has |t| >= ``min_t`` overall.

    Features are cross-sectional z-scores and the target is rank-Gaussian, so a
    day's IC is close to mean(x * y) over that day's stocks. Uses only the
    training rows, so nothing after the refit date is involved.
    """
    order = np.argsort(day, kind="stable")
    d, Xs, ys = day[order], X[order], y[order]
    starts = np.r_[0, np.nonzero(np.diff(d))[0] + 1]
    counts = np.diff(np.r_[starts, len(d)])
    ic = np.add.reduceat(Xs * ys[:, None], starts, axis=0) / counts[:, None]    # days x features
    n = len(ic)
    t = ic.mean(axis=0) / (ic.std(axis=0) + 1e-12) * np.sqrt(n)
    parts = np.array_split(np.arange(n), splits)
    signs = np.array([np.sign(ic[p].mean(axis=0)) for p in parts])
    same = (signs == signs[0]).all(axis=0) & (signs[0] != 0)
    return same & (np.abs(t) >= min_t)


def walk_forward(
    feats: np.ndarray,
    target: np.ndarray,
    regimes: np.ndarray,
    dates: pd.DatetimeIndex,
    cfg,
    model_names: list[str] | None = None,
    final_refit: bool = False,
) -> WalkForwardResult:
    m = cfg.model
    names = model_names or list(m.models)
    T, N, _ = feats.shape
    h = m.horizon
    counts = np.isfinite(feats[..., 0]).sum(axis=1)
    first = int(np.argmax(counts >= 20))
    refits = list(range(first + m.min_train, T, m.retrain_every))
    if final_refit and (not refits or refits[-1] != T - 1):
        refits.append(T - 1)
    if not refits:
        raise ValueError("Not enough history for a single walk-forward refit.")

    preds = {n: np.full((T, N), np.nan, dtype=np.float32) for n in names}
    res = WalkForwardResult(predictions=preds, weights={n: [] for n in names},
                            fit_seconds={n: 0.0 for n in names})
    for j, r in enumerate(refits):
        lo = max(first, r - m.train_window)
        hi = r - 1 - h
        d_tr, i_tr, X = _rows(feats, target, lo, hi)
        y = target[d_tr, i_tr].astype(np.float64)
        R = regimes[d_tr]
        nxt = refits[j + 1] if j + 1 < len(refits) else T
        d_te, i_te, Xte = _rows(feats, None, r, nxt - 1)
        Rte = regimes[d_te]
        if m.select_stable:
            keep = stable_signals(X, y, d_tr, m.stable_splits, m.stable_min_t)
            if keep.sum() >= 3:            # always leave the models something to work with
                X = np.where(keep, X, 0.0).astype(X.dtype)
                Xte = np.where(keep, Xte, 0.0).astype(Xte.dtype)
            res.selected[dates[r]] = keep
            LOG.info("  kept %d/%d stable signals", int(keep.sum()), len(keep))
        for n in names:
            t0 = time.time()
            model = build_model(n, cfg).fit(X, y, R, d_tr)
            if len(d_te):
                preds[n][d_te, i_te] = model.predict(Xte, Rte).astype(np.float32)
            w = model.weights()
            if w is not None:
                res.weights[n].append((dates[r], np.asarray(w, dtype=float)))
            res.final_models[n] = model
            res.fit_seconds[n] += time.time() - t0
        res.refit_dates.append(dates[r])
        LOG.info("walk-forward refit %d/%d at %s: %d training rows", j + 1, len(refits),
                 dates[r].date(), len(y))

    # ensemble: average of each member's daily cross-sectional z-scores
    members = [n for n in m.ensemble if n in preds]
    if members:
        zs = [_cs_z(preds[n]) for n in members]
        with np.errstate(invalid="ignore"):
            preds["ensemble"] = np.nanmean(np.stack(zs), axis=0).astype(np.float32)
    LOG.info("fit time by model: %s", {k: round(v, 1) for k, v in res.fit_seconds.items()})
    return res


def _cs_z(P: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.nanmean(P, axis=1, keepdims=True)
        sd = np.nanstd(P, axis=1, keepdims=True)
        return (P - mu) / np.where(sd > 0, sd, np.nan)
