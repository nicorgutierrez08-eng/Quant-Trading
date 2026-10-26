"""Nico's momentum flip sleeve: staggered target, VIX sign, daily mark and rebalance."""
import numpy as np
import pandas as pd

from qtrade.intraday import flip_sleeve as F
from qtrade.research.flip_check import staggered_flip


def _close(n_days=320, n=40, seed=0):
    rng = np.random.default_rng(seed)
    drift = np.linspace(-0.001, 0.001, n)
    r = rng.normal(drift, 0.02, (n_days, n))
    idx = pd.bdate_range("2025-01-01", periods=n_days)
    return pd.DataFrame(50 * np.exp(np.cumsum(r, axis=0)), index=idx, columns=[f"S{i}" for i in range(n)])


def test_target_is_the_average_of_the_last_21_sub_books():
    close = _close()
    vix = pd.Series(15.0, index=close.index)
    w, sign = F.target(close, vix)
    assert sign == 1.0 and abs(w.sum()) < 1e-9 and 0.5 < w.abs().sum() <= 1 + 1e-9
    # the staggered backtest's position on the last day is the same book
    z = F.scores(close)
    mask = close.notna()
    held = []
    for k in range(F.EVERY):
        reb = pd.Series(False, index=close.index)
        reb.iloc[k::F.EVERY] = True
        last = reb[reb].index[-1]
        held.append(F.unit_weights(z.loc[last]))
    expect = pd.concat(held, axis=1).fillna(0).mean(axis=1)
    assert np.allclose(w.reindex(expect.index).fillna(0), expect, atol=1e-9)
    assert staggered_flip  # the research version this mirrors


def test_high_vix_flips_the_new_sub_book():
    close = _close()
    calm = pd.Series(15.0, index=close.index)
    stress = calm.copy()
    stress.iloc[-1] = 30.0
    w0, _ = F.target(close, calm)
    w1, sign = F.target(close, stress)
    assert sign == -1.0
    today = F.unit_weights(F.scores(close).iloc[-1])
    assert np.allclose(w1.reindex(today.index).fillna(0), (w0.reindex(today.index).fillna(0) - 2 * today / F.EVERY),
                       atol=1e-9)


def test_step_marks_then_rebalances():
    close = _close(n_days=5, n=3)
    prev = pd.DataFrame({"Symbol": ["S0", "S1"], "Weight": [0.5, -0.5], "Position $": [2500.0, -2500.0],
                         "Mark price": close.iloc[-2][["S0", "S1"]].values})
    w = pd.Series({"S0": -0.5, "S2": 0.5})
    pnl, turnover, hold = F.step(prev, 5000.0, close, w)
    r = close.iloc[-1] / close.iloc[-2] - 1
    assert np.isclose(pnl, 2500 * r["S0"] - 2500 * r["S1"])
    assert set(hold["Symbol"]) == {"S0", "S2"} and np.isclose(hold["Position $"].abs().sum(), 5000 + pnl, atol=0.02)
    assert turnover > 0


def test_new_capital_is_added_once():
    old = pd.DataFrame([["2026-10-22", 16.7, "long", 1, 1, 4900, 0, 0, 5000, 4900, ""]], columns=F.LOG_HEADER)
    assert F.capital_so_far(old) == 5000.0                      # rows from before the column: their start
    new = pd.concat([old, pd.DataFrame([["2026-10-23", 16, "long", 1, 1, 9700, 12, 0.1, 9738.27, 4800, 9726.27]],
                                       columns=F.LOG_HEADER)])
    assert F.capital_so_far(new) == 9726.27                     # after the deposit: no second deposit
