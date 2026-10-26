"""Invariants: transformations of the input that must not change any decision.

1. Corporate actions. Yahoo back-adjusts the whole price history for every
   split and dividend, so the adjusted price of a stock on day t depends on
   what happens after t. Rescaling a stock's adjusted prices and volumes (which
   is exactly what a later split or dividend does) must leave every signal,
   every tradability flag and every trade unchanged, as long as the as-traded
   close and volume are the same.
2. Relabelling. Reordering the tickers must just reorder the output.
3. Confidence scale. When the gross or volatility cap sets leverage, the
   target book does not depend on the size of the IC estimate at all: alpha
   and the cap both scale with it, and cancel.
"""
import numpy as np
import pandas as pd

from qtrade.backtest.engine import run_backtest
from qtrade.data.loader import split_yahoo_frame
from qtrade.data.market import FIELDS, MarketData
from qtrade.features.context import FeatureContext
from qtrade.pipeline import forward_returns
from qtrade.portfolio.optimizer import construct
from qtrade.signals import REGISTRY, compute_signals


def _with_raw(md: MarketData) -> MarketData:
    """Synthetic data has no corporate actions: as traded = adjusted."""
    panels = {f: getattr(md, f) for f in FIELDS}
    return MarketData(**panels, raw_close=md.close.copy(), raw_volume=md.volume.copy())


def _readjusted(md: MarketData, cols, price_mult: float, volume_mult: float) -> MarketData:
    """The same trading history as seen through later corporate actions: a 40:1
    split multiplies past adjusted prices by 1/40 and past volumes by 40; a
    dividend scales past prices only. The as-traded panels do not change."""
    panels = {}
    for f in FIELDS:
        df = getattr(md, f).copy()
        df[cols] = df[cols] * (volume_mult if f == "volume" else price_mult)
        panels[f] = df
    return MarketData(**panels, raw_close=md.raw_close, raw_volume=md.raw_volume)


def test_yahoo_frame_recovers_as_traded_prices():
    idx = pd.bdate_range("2020-01-01", periods=6)
    printed = np.array([100.0, 102.0, 51.0, 52.0, 50.0, 51.0])     # 2:1 split on day 2
    shares = np.array([1e6, 1e6, 2e6, 2e6, 2e6, 2e6])
    split_adj = printed / np.array([2, 2, 1, 1, 1, 1])
    div_factor = np.array([0.98, 0.98, 0.98, 0.98, 1.0, 1.0])      # dividend ex on day 4
    cols = pd.MultiIndex.from_product
    raw = pd.concat({
        "Open": pd.DataFrame({"X": split_adj}, idx), "High": pd.DataFrame({"X": split_adj}, idx),
        "Low": pd.DataFrame({"X": split_adj}, idx), "Close": pd.DataFrame({"X": split_adj}, idx),
        "Adj Close": pd.DataFrame({"X": split_adj * div_factor}, idx),
        "Volume": pd.DataFrame({"X": shares * np.array([2, 2, 1, 1, 1, 1])}, idx),
        "Stock Splits": pd.DataFrame({"X": [0, 0, 2.0, 0, 0, 0]}, idx),
    }, axis=1)
    out = split_yahoo_frame(raw)
    np.testing.assert_allclose(out["raw_close"]["X"], printed)
    np.testing.assert_allclose(out["raw_volume"]["X"], shares)
    np.testing.assert_allclose(out["close"]["X"], split_adj * div_factor)
    np.testing.assert_allclose(out["open"]["X"], split_adj * div_factor)
    md = MarketData(**{f: out[f] for f in FIELDS}, raw_close=out["raw_close"], raw_volume=out["raw_volume"])
    np.testing.assert_allclose(md.dollar_volume["X"], printed * shares)


def test_decisions_ignore_later_splits_and_dividends(market, cfg):
    md = _with_raw(market[0])
    cols = md.tickers[:8]
    split = _readjusted(md, cols, price_mult=1 / 64, volume_mult=64)   # pushes them under $5
    div = _readjusted(md, cols, price_mult=0.6, volume_mult=1.0)
    a = FeatureContext(md, cfg)
    for other in (split, div):
        b = FeatureContext(other, cfg)
        pd.testing.assert_frame_equal(a.tradable, b.tradable)
        sa, sb = compute_signals(a), compute_signals(b)
        for name in REGISTRY:
            np.testing.assert_allclose(sa[name].to_numpy(), sb[name].to_numpy(), atol=2e-5,
                                       equal_nan=True, err_msg=name)


def test_adjusted_prices_alone_would_look_ahead(market, cfg):
    """Without the as-traded panels, a later 40:1 split makes a stock look like
    a penny stock today and drops it from the universe."""
    md = market[0]
    cols = md.tickers[:8]
    later_split = MarketData(**{f: getattr(md, f).assign(**{c: getattr(md, f)[c] * (64 if f == "volume" else 1 / 64)
                                                            for c in cols}) for f in FIELDS})
    before = FeatureContext(md, cfg).tradable[cols].values.mean()
    after = FeatureContext(later_split, cfg).tradable[cols].values.mean()
    assert before > 0.5 and after < 0.2 * before


def test_whole_share_backtest_ignores_later_splits(market, cfg):
    import copy

    c = copy.deepcopy(cfg)
    c.portfolio.whole_shares = True
    c.portfolio.max_names = 20
    c.costs.aum = 20_000
    md = _with_raw(market[0])
    # powers of two rescale exactly, so whole-share rounding sees identical numbers
    split = _readjusted(md, md.tickers[:8], price_mult=1 / 64, volume_mult=64)
    runs = []
    for m in (md, split):
        ctx = FeatureContext(m, c)
        fwd = forward_returns(m, c.model.horizon).where(ctx.tradable).to_numpy()
        runs.append(run_backtest(ctx, fwd, fwd, c, start=m.dates[400], record_weights=False))
    np.testing.assert_allclose(runs[0].returns, runs[1].returns, atol=1e-12)


# k-means peer groups depend on the order the rows are fed in (its random
# initialisation), so the three signals built on them are not order-free.
CLUSTER_SIGNALS = {"cluster_mom", "peer_gap", "peer_lead"}


def test_signals_are_permutation_equivariant(market, cfg):
    md = market[0]
    perm = list(np.random.default_rng(0).permutation(md.tickers))
    shuffled = md.subset(tickers=perm)
    names = [n for n in REGISTRY if n not in CLUSTER_SIGNALS]
    sa = compute_signals(FeatureContext(md, cfg), names)
    sb = compute_signals(FeatureContext(shuffled, cfg), names)
    for name in names:
        np.testing.assert_allclose(sa[name][perm].to_numpy(), sb[name].to_numpy(), atol=2e-5,
                                   equal_nan=True, err_msg=name)


def test_target_book_is_invariant_to_ic_when_a_cap_binds():
    from qtrade.config import Config

    rng = np.random.default_rng(0)
    z, sig, B = rng.standard_normal(300), rng.uniform(0.01, 0.03, 300), rng.standard_normal((300, 5))
    w1, i1 = construct(z, sig, B, 0.01, Config())
    w2, i2 = construct(z, sig, B, 0.04, Config())
    assert i1.binding == i2.binding == "gross"
    np.testing.assert_allclose(w1, w2, atol=1e-12)


def test_price_cache_keeps_as_traded_panels(tmp_path, market):
    from qtrade.data.loader import load_market, save_market

    md = _with_raw(market[0])
    save_market(md, tmp_path)
    back = load_market(tmp_path)
    assert back.has_raw
    np.testing.assert_allclose(back.dollar_volume.to_numpy(), md.dollar_volume.to_numpy(), rtol=1e-6)
    save_market(market[0], tmp_path / "old")         # a cache written before raw panels existed
    assert not load_market(tmp_path / "old").has_raw


def test_bad_prints_are_masked_but_real_jumps_kept(market):
    md = market[0]
    t, other = md.tickers[0], md.tickers[1]
    panels = {f: getattr(md, f).copy() for f in FIELDS}
    day, jump_day = md.dates[500], md.dates[600]
    for f in ("open", "high", "low", "close"):
        panels[f].loc[day, t] *= 30                 # a one-day 30x print
        panels[f].loc[jump_day:, other] *= 1.8      # a genuine +80% gap that sticks
    clean = MarketData(**panels)
    assert np.isnan(clean.close.loc[day, t])
    assert np.isfinite(clean.close.loc[jump_day, other])
    assert FeatureContext(clean).ret[t].abs().max() < 0.5


def test_dividend_factor_glitch_is_repaired():
    from qtrade.data.loader import clean_dividend_factor

    idx = pd.bdate_range("2020-01-01", periods=8)
    true = np.array([0.95, 0.95, 0.96, 0.96, 0.98, 0.98, 1.0, 1.0])
    seen = true.copy()
    seen[2:4] /= 20                                 # Yahoo glitch: off by a split ratio for two days
    out = clean_dividend_factor(pd.DataFrame({"X": seen}, idx))
    # a dividend that falls on the glitch's edge is lost with it: a couple of percent at most
    np.testing.assert_allclose(out["X"], true, rtol=0.03)
