"""GARCH estimation recovers a simulated process, and its filter is exact."""
import numpy as np

from qtrade.research.garch import fit_garch, garch_filter


def _simulate(T=6000, w=2e-6, a=0.05, b=0.88, g=0.08, nu=6, seed=0):
    rng = np.random.default_rng(seed)
    r, s2 = np.zeros(T), np.zeros(T)
    s2[0] = w / (1 - a - b - g / 2)
    for t in range(T):
        if t:
            s2[t] = w + (a + g * (r[t - 1] < 0)) * r[t - 1] ** 2 + b * s2[t - 1]
        r[t] = np.sqrt(s2[t]) * rng.standard_t(nu) / np.sqrt(nu / (nu - 2))
    return r, s2


def test_filter_matches_recursion():
    r, s2 = _simulate()
    np.testing.assert_allclose(garch_filter(r, 2e-6, 0.05, 0.88, 0.08, s2[0]), s2, rtol=1e-10)


def test_gjr_t_recovers_parameters():
    r, _ = _simulate()
    p = fit_garch(r, gjr=True, student=True)
    assert abs(p["a"] - 0.05) < 0.03 and abs(p["b"] - 0.88) < 0.04 and abs(p["g"] - 0.08) < 0.05
    assert 4 < p["nu"] < 10 and p["persistence"] < 1
