"""The tradable ETF sleeves must earn exactly what the research strategies earned."""
import numpy as np
import pandas as pd
import pytest

from qtrade.data import make_market
from qtrade.portfolio import sleeves as S
from qtrade.research import strategies as R


@pytest.fixture(scope="module")
def etf():
    names = list(dict.fromkeys(R.ASSETS + R.SECTORS + R.BROAD + R.VOL + ["^VIX"]))
    md, _ = make_market(n_stocks=len(names), n_days=1600, seed=7, start="2009-01-02", late_listing_frac=0)
    md.close.columns = names
    md.open.columns = names
    return md


def test_sleeves_match_research(etf):
    c = etf.close
    research = R.cross_asset_strategies(etf) | R.broad_strategies(etf)
    r_spy = c["SPY"].pct_change(fill_method=None)
    research["spy_ma200"] = R._net((c["SPY"] > c["SPY"].rolling(200).mean()).astype(float), r_spy)
    research["spy_tsmom_12m"] = R._net((c["SPY"] / c["SPY"].shift(252) - 1 > 0).astype(float), r_spy)
    for name in ("cross_asset_mom", "risk_parity", "multi_asset_trend", "broad_trend_12m", "spy_ma200",
                 "spy_tsmom_12m"):
        mine = S.sleeve_returns(S.SLEEVES[name](c), c)
        pd.testing.assert_series_equal(mine, research[name], check_names=False, atol=1e-12)


def test_turn_of_month_matches_research(etf):
    c = etf.close
    r = c["SPY"].pct_change(fill_method=None)
    idx = c.index
    me = R._month_ends(idx)
    nth = pd.Series(1, index=idx).groupby([idx.year, idx.month]).cumsum()
    tom = (me.shift(1, fill_value=False) | (nth <= 3)).astype(float)
    ref = tom * r.fillna(0) - tom.diff().abs().fillna(0) * R.ETF_COST
    mine = S.sleeve_returns(S.spy_turn_of_month(c), c)
    # the first two days have no position yet in the sleeve; the last month needs the future calendar
    a, b = mine.iloc[2:-25], ref.iloc[2:-25]
    assert np.allclose(a.to_numpy(), b.to_numpy(), atol=1e-12)


def test_vol_managed_matches_research(etf):
    from qtrade.research.garch import fit_garch, garch_filter

    c = etf.close
    r = c["SPY"].pct_change(fill_method=None)
    split = "2012-01-01"
    train = np.asarray(r.index < split) & r.notna().to_numpy()
    p = fit_garch(np.where(train, r.to_numpy(), np.nan)[: np.flatnonzero(train)[-1] + 1], gjr=True)
    s2 = garch_filter(r.to_numpy(), p["w"], p["a"], p["b"], p["g"], p["s0"])
    lev = pd.Series(np.clip(np.sqrt(np.nanmedian(s2[train])) / np.sqrt(s2), 0, 2), index=r.index)
    ref = R._net(lev.shift(-1), r)
    mine = S.sleeve_returns(S.spy_vol_managed(c, fit_end=split), c)
    assert np.allclose(mine.iloc[:-2].to_numpy(), ref.iloc[:-2].to_numpy(), atol=1e-12)


def test_weights_use_only_the_past(etf):
    """Changing prices after day t must not change any weight decided at t."""
    c = etf.close.copy()
    t = 1200
    base = S.combine(c, fit_end="2012-01-01")["weights"].iloc[: t + 1]
    c2 = c.copy()
    c2.iloc[t + 1:] *= np.exp(np.random.default_rng(0).normal(0, 0.05, c2.iloc[t + 1:].shape)).cumprod(axis=0)
    after = S.combine(c2, fit_end="2012-01-01")["weights"].iloc[: t + 1]
    pd.testing.assert_frame_equal(base, after)


def test_combined_book_is_sane(etf):
    out = S.combine(etf.close, fit_end="2012-01-01")
    w = out["weights"].iloc[400:]
    assert (w.abs().sum(axis=1) <= 1.5 + 1e-9).all()
    sw = out["sleeve_weights"].dropna()
    assert np.allclose(sw.sum(axis=1), 1.0)
    assert (sw >= 0).all().all()
