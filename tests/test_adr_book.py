"""The live ADR book: the residual, the weights and the live inputs match the research definitions."""
import numpy as np
import pandas as pd

from qtrade.config import Config
from qtrade.data.market import MarketData
from qtrade.intraday import adr_book as B

NY = "America/New_York"


def test_residual_and_weights():
    # home +3% (local), local currency weakened 1% vs USD yesterday, ADR up 0.5% pre-market
    r = B.residual(0.03, 0.01, 100.0, 100.0 * np.exp(0.005))
    assert np.isclose(r, 0.03 - 0.01 - 0.005)
    assert np.isnan(B.residual(0.03, 0.0, np.nan, 100.0))
    assert np.isclose(B.residual(0.02, np.nan, 50.0, 50.0), 0.02)       # missing FX counts as no move
    w = B.book_weights({"BABA": 0.02, "SONY": -0.01, "KB": 0.0, "TSM": 0.03}, gross=0.5,
                       markets=["China", "Japan", "Korea"])
    assert w == {"BABA": 0.25, "SONY": -0.25}                            # zero residual and Taiwan left out
    w = B.book_weights({"BABA": 0.02, "SONY": -0.01}, gross=0.5, shortable={"BABA"})
    assert w == {"BABA": 0.5}                                            # can't short SONY: dropped
    assert B.book_weights({}, gross=0.5) == {}


def test_home_moves_needs_todays_home_session(monkeypatch):
    from qtrade.data import loader

    days = pd.bdate_range("2026-10-15", "2026-10-22")
    close = pd.DataFrame({"9988.HK": np.linspace(100, 107, len(days)),
                          "6758.T": np.r_[np.linspace(10, 11, len(days) - 1), np.nan],   # Tokyo closed today
                          "HKD=X": np.linspace(7.8, 7.85, len(days)), "JPY=X": 150.0}, index=days)
    md = MarketData(open=close, high=close, low=close, close=close, volume=close * 0 + 1)
    monkeypatch.setattr(loader, "download_prices", lambda t, start=None: md)
    m = B.home_moves(pd.Timestamp("2026-10-22"), ["BABA", "SONY"])
    assert list(m["adr"]) == ["BABA"]
    assert np.isclose(m["home_ret"].iloc[0], np.log(107 / close["9988.HK"].iloc[-2]))
    fx = np.log(close["HKD=X"]).diff()
    assert np.isclose(m["fx_ret_prev"].iloc[0], fx.iloc[-2])              # yesterday's FX, not today's


def test_build_targets_end_to_end():
    acfg = Config().auction
    moves = pd.DataFrame([{"adr": "BABA", "market": "China", "home_ret": 0.04, "fx_ret_prev": 0.0},
                          {"adr": "SONY", "market": "Japan", "home_ret": -0.02, "fx_ret_prev": 0.0},
                          {"adr": "TSM", "market": "Taiwan", "home_ret": 0.05, "fx_ret_prev": 0.0}])
    w, tab = B.build_targets(acfg, pd.Timestamp("2026-10-22"), {"BABA": 100, "SONY": 20, "TSM": 150},
                             {"BABA": 101, "SONY": 20, "TSM": 150}, moves, None)
    # BABA: home +4%, ADR +1% pre-market -> long; SONY: home -2%, flat ADR -> short; Taiwan not in the markets
    assert w["BABA"] > 0 and w["SONY"] < 0 and "TSM" not in w
    assert np.isclose(sum(abs(v) for v in w.values()), acfg.adr_gross)
    assert set(tab["adr"]) == {"BABA", "SONY", "TSM"}


def test_live_reference_prices():
    from qtrade.intraday.auction_live import _adr_prices

    def bar(t, o, c):
        return {"t": pd.Timestamp(t, tz=NY).tz_convert("UTC").isoformat(), "o": o, "h": max(o, c), "l": min(o, c),
                "c": c, "v": 100, "n": 1, "vw": c}

    class Data:
        feed = "iex"

        def bars(self, symbols, tf, start, end):
            return {"BABA": [bar("2026-10-22 08:10", 99, 100), bar("2026-10-22 09:22", 100, 101),
                             bar("2026-10-22 09:26", 101, 105), bar("2026-10-22 09:30", 102, 103)]}

    day = pd.Timestamp("2026-10-22")
    now = pd.Timestamp("2026-10-22 09:40", tz=NY)
    assert _adr_prices(Data(), ["BABA"], day, now, after_open=False) == {"BABA": 101.0}   # last before 9:25
    assert _adr_prices(Data(), ["BABA"], day, now, after_open=True) == {"BABA": 102.0}    # the open


def test_open_phase_flattens_and_opens_the_adr_book_in_one_batch(monkeypatch, tmp_path):
    from qtrade.intraday import auction_live as A

    class Clock:
        is_open = False
        next_open = pd.Timestamp("2026-10-22 09:30", tz=NY)

    class Client:
        def get_clock(self):
            return Clock()

        def get(self, path, params=None):
            return []

    sent = []
    monkeypatch.setattr(A, "_client", lambda: Client())
    monkeypatch.setattr(A, "_now", lambda: pd.Timestamp("2026-10-22 09:20", tz=NY))
    # overnight book: long AAPL 10, short BABA 5; the ADR book wants BABA long, SONY short
    monkeypatch.setattr(A, "_account_state", lambda c: (100_000.0, {"AAPL": 10, "BABA": -5}, {}, {"SONY", "BABA"},
                                                         None, 100_000.0))
    monkeypatch.setattr(A, "adr_book_targets", lambda cfg, client, data, after_open: (
        {"BABA": 0.25, "SONY": -0.25}, {"BABA": 100.0, "SONY": 20.0}, pd.DataFrame()))
    monkeypatch.setattr(A, "AlpacaBars", lambda feed=None: None)
    monkeypatch.setattr(A, "_submit", lambda client, orders, tif: sent.append((tif, orders)) or ["id"] * len(orders))
    cfg = Config()
    cfg.live.capital_fraction, cfg.live.max_capital = 1.0, None
    res = A.run_open(cfg, dry_run=False, out_dir=tmp_path, adr=True)
    tif, orders = sent[0]
    got = {o.symbol: (o.side, o.qty) for o in orders}
    assert tif == "opg" and res["adr_names"] == 2
    assert got["AAPL"] == ("sell", 10)                     # overnight position closed
    assert got["BABA"] == ("buy", 5)                       # short closed first (no flip in one order)
    assert got["SONY"] == ("sell", 1250)                   # -25% of $100k at $20
    # without the ADR book it is a plain flatten
    sent.clear()
    A.run_open(cfg, dry_run=False, out_dir=tmp_path)
    assert {o.symbol for o in sent[0][1]} == {"AAPL", "BABA"}
