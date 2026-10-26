"""Signal library: ``compute_signals`` turns market data into normalised panels."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from ..features.context import FeatureContext
from ..utils import LOG, cs_zscore
from . import library  # noqa: F401  (registers every signal)
from .registry import REGISTRY, SignalSpec, list_signals, signal


def normalize_signal(raw: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    """Mask to tradable names, winsorise and z-score per day; missing = 0 (no view)."""
    raw = raw.reindex_like(mask).replace([np.inf, -np.inf], np.nan).where(mask)
    z = cs_zscore(raw).clip(-4, 4)
    return z.where(~mask, z.fillna(0.0)).where(mask).astype("float32")


def compute_signals(ctx: FeatureContext, names: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Compute, mask to tradable names, winsorise and z-score each signal per day.

    Missing values on tradable names become 0 (= no view), so every model sees
    a dense feature matrix; non-tradable cells stay NaN.
    """
    names = names or list(REGISTRY)
    mask = ctx.tradable
    out: dict[str, pd.DataFrame] = {}
    for name in names:
        t0 = time.time()
        out[name] = normalize_signal(REGISTRY[name].fn(ctx), mask)
        LOG.debug("signal %-22s %.1fs", name, time.time() - t0)
    if len(names) > 1:
        LOG.info("computed %d signals", len(out))
    return out


__all__ = ["REGISTRY", "SignalSpec", "compute_signals", "list_signals", "normalize_signal", "signal",
           "signal_array"]


def signal_array(ctx: FeatureContext, names: list[str] | None = None) -> tuple[np.ndarray, list[str]]:
    """Like ``compute_signals`` but writes straight into a (T, N, F) float32
    array, which keeps memory bounded for 1000 stocks x 25 years x 45 signals."""
    names = names or list(REGISTRY)
    T, N = ctx.md.close.shape
    arr = np.full((T, N, len(names)), np.nan, dtype=np.float32)
    for k, name in enumerate(names):
        arr[:, :, k] = compute_signals(ctx, [name])[name].to_numpy(dtype=np.float32)
    LOG.info("signal tensor: %d days x %d stocks x %d signals", T, N, len(names))
    return arr, names
