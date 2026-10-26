"""Intraday model zoo: signals may only use bars up to the decision, and the
walk-forward run must find a planted reversal."""
import numpy as np
import pandas as pd

from qtrade.intraday.features import history
from qtrade.intraday.synthetic import make_intraday
from qtrade.research import intraday_zoo as Z


def _day_signals(bars, hist, d):
    return Z.signals(bars.open[d], bars.close[d], bars.volume[d], bars.vwap[d], hist.prev_close[d],
                     hist.sigma[d], hist.vol_base[d], bars.open[d - 1], bars.close[d - 1])


def test_signals_use_only_earlier_bars():
    bars = make_intraday(n_stocks=40, n_days=40, seed=3)
    hist = history(bars)
    d, b = 30, 20
    base = _day_signals(bars, hist, d)
    rng = np.random.default_rng(0)
    for arr in (bars.open, bars.close, bars.vwap):
        arr[d, b + 1:] *= np.exp(rng.normal(0, 0.05, arr[d, b + 1:].shape)).astype(np.float32)
    bars.volume[d, b + 1:] *= 10
    after = _day_signals(bars, hist, d)
    assert np.allclose(base[: b + 1], after[: b + 1], equal_nan=True)
    assert not np.allclose(base[b + 1:], after[b + 1:], equal_nan=True)


def test_walk_forward_finds_planted_reversal():
    bars = make_intraday(n_stocks=40, n_days=170, seed=1, reversal=0.2)
    bars.days = pd.bdate_range("2020-07-01", periods=len(bars.days))
    daily = Z.run_horizon(bars, 3, ["baseline_ridge", "ridge_all", "tstat_ic"], min_months=2, rows_per_day=500)
    tab = Z.summarize(daily).set_index("model")
    assert len(daily) > 0
    assert (tab["ic_2021_26"] > 0.03).all()
    assert (tab["gross_bp_day_2021_26"] > 0).all()
