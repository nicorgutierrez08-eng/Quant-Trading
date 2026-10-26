"""Asian markets study: session alignment and a planted US -> Asia lead it must find."""
import numpy as np
import pandas as pd

from qtrade.data.loader import to_yahoo
from qtrade.data.market import MarketData
from qtrade.research import asia as A


def test_exchange_suffixes_survive():
    assert to_yahoo("7203.T") == "7203.T" and to_yahoo("0700.HK") == "0700.HK"
    assert to_yahoo("brk.b") == "BRK-B" and to_yahoo("M&M.NS") == "M&M.NS"


def test_alignment_uses_the_right_session():
    us = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]))
    asia_days = pd.to_datetime(["2024-01-03", "2024-01-04", "2024-01-05"])
    # an Asian session on D follows the US session of D-1
    assert list(A._align_after(us, asia_days, strictly=True)) == [1.0, 2.0, 3.0]
    # the US session on D follows the Asian session of D
    asia = pd.Series([10.0, 20.0], index=pd.to_datetime(["2024-01-03", "2024-01-04"]))
    got = A._align_after(asia, pd.to_datetime(["2024-01-03", "2024-01-04"]), strictly=False)
    assert list(got) == [10.0, 20.0]


def _market(seed=0, n=5600):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2005-01-03", periods=n)
    us_cc = rng.normal(0, 0.01, n)
    cols = {}
    # SPY: open / close random walk
    spy_c = 100 * np.exp(np.cumsum(us_cc))
    spy_o = spy_c * np.exp(-rng.normal(0, 0.004, n))
    cols["SPY"] = (spy_o, spy_c)
    # Nikkei: after its open it moves with yesterday's US day (the planted lead)
    lead = np.r_[0, us_cc[:-1]]
    gap = 0.5 * lead + rng.normal(0, 0.005, n)
    intra = 0.2 * lead + rng.normal(0, 0.008, n)
    c = 20000 * np.exp(np.cumsum(gap + intra))
    o = c * np.exp(-intra)
    cols["^N225"] = (o, c)
    for k in range(12):
        r = rng.normal(0, 0.015, n)
        cc_ = 50 * np.exp(np.cumsum(r))
        cols[A.STOCKS["Japan"][k]] = (cc_ * np.exp(-rng.normal(0, 0.005, n)), cc_)
    o = pd.DataFrame({t: v[0] for t, v in cols.items()}, index=days)
    c = pd.DataFrame({t: v[1] for t, v in cols.items()}, index=days)
    return MarketData(open=o, high=np.maximum(o, c), low=np.minimum(o, c), close=c, volume=c * 0 + 1e6)


def test_lead_lag_finds_the_planted_effect_and_strategies_run():
    md = _market()
    L = A.legs(md)
    ll, st = A.lead_lag(L)
    r = ll[(ll.market == "Japan") & (ll.signal == "US close-to-close (D-1)") & (ll.target == "Japan: after the open")]
    assert r["t_2006_14"].iloc[0] > 5 and r["t_2015_26"].iloc[0] > 5
    noise = ll[(ll.signal == "Japan open-to-close (D)") & (ll.target == "US: US after the open")]
    assert abs(noise["t_2015_26"].iloc[0]) < 4
    s = st[st.strategy.str.startswith("US close-to-close (D-1) -> Japan")]
    assert s["sharpe_2015_26"].iloc[0] > 1
    ms = A.market_strategies(md)
    assert set(ms["market"]) == {"Japan"} and len(ms) == 4 and ms["sharpe_2015_26"].notna().all()


def test_adr_residual_book_runs():
    md = _market(seed=1)
    rng = np.random.default_rng(5)
    days = md.close.index
    n = len(days)
    home = 500 * np.exp(np.cumsum(rng.normal(0, 0.015, n)))
    fx = 30 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
    adr_c = home / fx * np.exp(rng.normal(0, 0.003, n))
    adr_o = adr_c * np.exp(-rng.normal(0, 0.006, n))
    extra_c = pd.DataFrame({"2330.TW": home, "TWD=X": fx, "TSM": adr_c}, index=days)
    extra_o = pd.DataFrame({"2330.TW": home * np.exp(-rng.normal(0, 0.005, n)), "TWD=X": fx, "TSM": adr_o},
                           index=days)
    c, o = pd.concat([md.close, extra_c], axis=1), pd.concat([md.open, extra_o], axis=1)
    md2 = MarketData(open=o, high=np.maximum(o, c), low=np.minimum(o, c), close=c, volume=c * 0 + 1e6)
    per, book = A.adr_study(md2, A.legs(md2))
    assert set(per["adr"]) == {"TSM"} and len(per) == 4
    assert len(book) == 9 and set(book["variant"]) == set(A.ADR_VARIANTS)
    assert book["sharpe_2015_26"].notna().all()


def test_same_day_fx_is_a_peek_and_the_lagged_variant_removes_it():
    """FX that moves during the US session moves the ADR too; a same-day FX bar leaks it."""
    md = _market(seed=2)
    rng = np.random.default_rng(9)
    days = md.close.index
    n = len(days)
    fx_us_hours = rng.normal(0, 0.004, n)                 # local-per-USD move during the US day
    fx = 30 * np.exp(np.cumsum(fx_us_hours))
    home = 500 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    adr_intra = -fx_us_hours + rng.normal(0, 0.002, n)     # a stronger local currency lifts the ADR
    adr_o = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    adr_c = adr_o * np.exp(adr_intra)
    c = pd.concat([md.close, pd.DataFrame({"2330.TW": home, "TWD=X": fx, "TSM": adr_c}, index=days)], axis=1)
    o = pd.concat([md.open, pd.DataFrame({"2330.TW": home * 0.999, "TWD=X": fx, "TSM": adr_o}, index=days)], axis=1)
    md2 = MarketData(open=o, high=np.maximum(o, c), low=np.minimum(o, c), close=c, volume=c * 0 + 1e6)
    _, book = A.adr_study(md2, A.legs(md2))
    b0 = book[book.cost_bp_round_trip == 0].set_index("variant")["sharpe_2015_26"]
    assert b0["same-day FX (peeks: shown for comparison only)"] > 3
    assert abs(b0["FX lagged a day (clean)"]) < 1.5
