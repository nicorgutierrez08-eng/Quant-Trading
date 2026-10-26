"""Minute-level foreign study: the simulator finds a planted reversal and charges the spread."""
import numpy as np
import pandas as pd

from qtrade.research import foreign_hft as H


def test_planted_reversal_is_found_and_spread_is_charged():
    rng = np.random.default_rng(1)
    idx = pd.DatetimeIndex([pd.Timestamp(f"2026-09-{d:02d} 09:00") + pd.Timedelta(minutes=5 * i)
                            for d in range(1, 11) for i in range(60)])
    n = 30
    shock = rng.normal(0, 0.003, (len(idx), n))
    ret = shock - 0.5 * np.vstack([np.zeros((1, n)), shock[:-1]])   # half of each bar's move reverses next bar
    c = pd.DataFrame(100 * np.exp(np.cumsum(ret, 0)), index=idx, columns=[f"S{i}" for i in range(n)])
    o = c.shift(1).fillna(100.0)                                      # open = previous close
    rev = H.simulate(o, c, 1, 1, -1.0, 4.0)
    mom = H.simulate(o, c, 1, 1, 1.0, 4.0)
    assert rev["gross"].mean() > 0 > mom["gross"].mean()
    assert np.allclose(rev["gross"] - rev["net"], 4.0 / 1e4)
    assert rev["time"].dt.date.nunique() == 10                        # never held across days
