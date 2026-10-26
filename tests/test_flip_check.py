"""Momentum flip check: flipping the sign mirrors the book exactly (before costs)."""
import numpy as np
import pandas as pd

from qtrade.research.flip_check import staggered_flip


def test_always_short_mirrors_never_flipped():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2015-01-01", periods=300)
    cols = [f"S{i}" for i in range(40)]
    z = pd.DataFrame(rng.standard_normal((300, 40)), idx, cols)
    r1 = pd.DataFrame(rng.normal(0, 0.01, (300, 40)), idx, cols)
    mask = pd.DataFrame(True, idx, cols)
    vix = pd.Series(25.0, index=idx)
    long_ = staggered_flip(z, mask, vix, r1, None, threshold=1e9)
    short = staggered_flip(z, mask, vix, r1, None, threshold=20.0)
    assert np.allclose(long_.to_numpy(), -short.to_numpy())
