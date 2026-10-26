"""The live earnings leg (last_reaction) uses the backtest's release timing and entry / exit rule."""
import numpy as np
import pandas as pd

from qtrade.config import Config
from qtrade.intraday import earnings_live as E

NY = "America/New_York"


def test_calendar_parsing_and_tonight():
    payload = {"data": {"rows": [{"symbol": "AAPL", "time": "time-after-hours"},
                                 {"symbol": "BRK/B", "time": "time-pre-market"},
                                 {"symbol": "XYZ", "time": "time-not-supplied"}]}}
    assert E.parse_calendar(payload) == {"AAPL": "after_close", "BRK-B": "before_open"}
    assert E.parse_calendar({"data": None}) == {}
    cal = {pd.Timestamp("2026-10-22"): {"AAA": "after_close", "BBB": "before_open"},
           pd.Timestamp("2026-10-23"): {"CCC": "before_open", "DDD": "after_close"}}
    got = E.releases_tonight(pd.Timestamp("2026-10-22"), fetch=lambda d: cal.get(pd.Timestamp(d), {}))
    assert got == ["AAA", "CCC"]          # tonight after the close, or tomorrow before the open


def _bars(dates, opens, closes):
    return pd.DataFrame({"open": opens, "close": closes}, index=pd.DatetimeIndex(dates).tz_localize(NY))


def test_previous_release_and_announcement_return():
    rows = [{"accepted": "2026-07-23T20:05:00.000Z"},           # 16:05 New York: after the close
            {"accepted": "2026-07-24T15:00:00.000Z"},           # 11:00: during the session, ignored
            {"accepted": "2026-10-22T20:05:00.000Z"}]           # tonight: not "previous"
    now = pd.Timestamp("2026-10-22 15:40", tz=NY)
    a, s = E.previous_release(rows, now)
    assert s == "after_close" and a.date() == pd.Timestamp("2026-07-23").date()
    dates = pd.bdate_range("2026-07-20", periods=6)
    stock = _bars(dates, [10, 10, 10, 10, 11, 11], [10, 10, 10, 10, 11, 11])   # 23rd close 10 -> 24th open 11
    spy = _bars(dates, [100, 100, 100, 100, 101, 101], [100] * 6)              # market +1% overnight
    assert np.isclose(E.announcement_return(a, s, stock, spy), 0.10 - 0.01)
    # a release before the open of the 24th is traded from the 23rd's close too
    pre = pd.Timestamp("2026-07-24 08:00", tz=NY)
    assert np.isclose(E.announcement_return(pre, "before_open", stock, spy), 0.09)


def test_earnings_weights_and_book():
    t = ["A", "B", "C", "D"]
    ok = np.array([True, True, True, False])
    w = E.earnings_weights(t, {"A": 0.05, "B": -0.02, "D": 0.1}, ok, 1.0, 0.02, 0.5)
    assert np.allclose(w, [0.02, -0.02, 0, 0])                # D has no price: left out
    w = E.earnings_weights(t, {"A": 0.05, "B": -0.02, "C": 0.01}, np.ones(4, bool), 1.0, 0.3, 0.6)
    assert np.isclose(np.abs(w).sum(), 0.6)                   # capped on a busy night


def test_build_book_adds_the_earnings_leg():
    from qtrade.intraday.auction_live import build_book
    from tests.test_auction_live import _frames
    from qtrade.intraday.synthetic import make_intraday

    bars = make_intraday(n_stocks=30, n_days=50, seed=3)
    d = 40
    acfg = Config().auction
    five, daily = _frames(bars, d)
    signs = {"last30_fade": 1.0, "overnight_persistence": 1.0, "last_reaction": 1.0}
    base = build_book(five, daily, bars.tickers, signs, acfg, bars.days[d])
    t0, t1 = bars.tickers[0], bars.tickers[1]
    book = build_book(five, daily, bars.tickers, signs, acfg, bars.days[d], reactions={t0: 0.03, t1: -0.04})
    assert "last_reaction" in book["strategies"] and "last_reaction" not in base["strategies"]
    assert np.isclose(book["weights"][t0] - base["weights"][t0], acfg.earnings_per_event)
    assert np.isclose(book["weights"][t1] - base["weights"][t1], -acfg.earnings_per_event)
