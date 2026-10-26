"""Intraday edge strategies: each signal may only use prices printed before its order."""
import numpy as np

from qtrade.intraday import slice_sim as S
from qtrade.intraday.synthetic import make_intraday


def _bump(bars, d, from_bar):
    rng = np.random.default_rng(0)
    for arr in (bars.open, bars.close, bars.vwap):
        arr[d, from_bar:] *= np.exp(rng.normal(0, 0.05, arr[d, from_bar:].shape)).astype(np.float32)


def test_signals_do_not_see_prices_after_their_order():
    d = 30
    # (strategy, first bar that must not matter): gap trade at 9:35 (bar 1), opening fade at 10:00 (bar 6),
    # last-half-hour fade decided at 15:45 (bar 75)
    for name, cut in (("gap_reversal", 1), ("opening_fade", 6), ("last30_fade", 75)):
        bars = make_intraday(n_stocks=30, n_days=40, seed=5)
        base = S.signals(bars)[name][d].copy()
        _bump(bars, d, cut)
        after = S.signals(bars)[name][d]
        assert np.allclose(base, after, equal_nan=True), name


def test_lite_charges_no_commission_but_regulatory_fees_on_sales():
    from qtrade.intraday.ibkr_sim import order_fees

    f = order_fees(np.array([10.0, 10.0]), np.array([100.0, 100.0]), np.array([False, True]), S.IBKR_LITE)
    assert f["commission"].sum() == 0 and f["exchange_fee"].sum() == 0
    assert f["sec_fee"][1] > 0 and f["sec_fee"][0] == 0


def test_overnight_signal_matches_the_panel_version():
    bars = make_intraday(n_stocks=30, n_days=60, seed=6)
    panel = S.signals(bars)["overnight_persistence"]
    Q0, _, _, qc = S.day_prices(bars)
    prev_c = np.vstack([np.full((1, Q0.shape[1]), np.nan), qc[:-1]])
    d = 45
    live = S.overnight_signal(Q0[d - 20:d + 1], prev_c[d - 20:d + 1])
    assert np.allclose(live, panel[d], equal_nan=True)
