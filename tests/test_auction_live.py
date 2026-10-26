"""The live auction trader builds exactly the book the backtest holds for the same day."""
import numpy as np
import pandas as pd

from qtrade.config import Config
from qtrade.intraday import slice_sim as S
from qtrade.intraday.auction_live import build_book
from qtrade.intraday.synthetic import make_intraday

NY = "America/New_York"


def _frames(bars, d):
    """Today's 5-minute bars and the daily bars (official open / close) as Alpaca would return them."""
    Q0, _, _, qc = S.day_prices(bars)
    five, daily = {}, {}
    for i, t in enumerate(bars.tickers):
        idx = (bars.days[d] + pd.to_timedelta(9 * 60 + 30 + 5 * np.arange(bars.n_bars), unit="min")).tz_localize(NY)
        five[t] = pd.DataFrame({"open": bars.open[d, :, i], "close": bars.close[d, :, i]}, index=idx)
        didx = pd.DatetimeIndex(bars.days[d - 25:d + 1]).tz_localize(NY)
        daily[t] = pd.DataFrame({"open": Q0[d - 25:d + 1, i], "close": qc[d - 25:d + 1, i]}, index=didx)
    return five, daily


def test_live_book_matches_backtest():
    bars = make_intraday(n_stocks=50, n_days=60, seed=8)
    d = 45
    signs = {"last30_fade": 1.0, "overnight_persistence": -1.0}
    acfg = Config().auction
    five, daily = _frames(bars, d)
    book = build_book(five, daily, bars.tickers, signs, acfg, bars.days[d])
    sig = S.signals(bars)
    _, _, _, qc = S.day_prices(bars)
    ok = np.isfinite(qc[d]) & (qc[d] > 0)
    ref = np.zeros(len(bars.tickers))
    for s in ("last30_fade", "overnight_persistence"):      # no earnings tonight: the two price strategies
        ref += S._weights(signs[s] * sig[s][d], ok & np.isfinite(sig[s][d]), acfg.frac) * acfg.gross / 2
    live = np.array([book["weights"][t] for t in bars.tickers])
    assert np.allclose(live, ref)
    assert np.abs(live).sum() <= acfg.gross + 1e-9               # at most the target gross (strategies can net)
    assert abs(live.sum()) < 1e-9                                 # dollar-neutral


def test_unshortable_names_are_not_shorted():
    bars = make_intraday(n_stocks=50, n_days=60, seed=8)
    five, daily = _frames(bars, 45)
    book = build_book(five, daily, bars.tickers, {}, Config().auction, bars.days[45], shortable=set())
    assert all(w >= 0 for w in book["weights"].values())


def test_flat_signal_is_left_out():
    """Before 15:15 the last-half-hour move does not exist yet: that strategy must sit out."""
    bars = make_intraday(n_stocks=50, n_days=60, seed=8)
    five, daily = _frames(bars, 45)
    early = bars.days[45].tz_localize(NY) + pd.Timedelta(hours=11)
    five = {t: f[f.index < early] for t, f in five.items()}
    book = build_book(five, daily, bars.tickers, {}, Config().auction, bars.days[45])
    assert book["strategies"] == ["overnight_persistence"]


def test_sent_today_sees_earlier_market_on_close_orders():
    from qtrade.intraday.auction_live import _sent_today

    class Client:
        def __init__(self, orders):
            self.orders = orders

        def get(self, path, params):
            return [o for o in self.orders if o["status"] == params["status"]]

    assert _sent_today(Client([{"status": "open", "time_in_force": "cls"}]), "cls")
    assert _sent_today(Client([{"status": "closed", "time_in_force": "cls"}]), "cls")
    assert not _sent_today(Client([{"status": "closed", "time_in_force": "day"}]), "cls")


def test_keeper_acts_once_per_window(monkeypatch):
    """The keeper queues the open exactly once in its window (9:18-9:27 with the pre-market ADR book),
    whatever the poll count."""
    from qtrade.intraday import auction_live as A

    times = iter(pd.date_range("2026-10-22 09:16", periods=6, freq="1min", tz=NY))
    calls = []

    class Clock:
        is_open = False
        next_open = pd.Timestamp("2026-10-22 09:30", tz=NY)

    class Client:
        def get_clock(self):
            return Clock()

    clock_now = {"t": None}

    def fake_now():
        clock_now["t"] = next(times)
        return clock_now["t"]

    monkeypatch.setattr(A, "_client", lambda: Client())
    monkeypatch.setattr(A, "_now", fake_now)
    monkeypatch.setattr(A, "fill_report", lambda **k: None)
    monkeypatch.setattr(A, "run_open", lambda cfg, **k: calls.append("open") or {"status": "done"})
    monkeypatch.setattr(A.time, "sleep", lambda s: None)
    t0 = [0.0]
    monkeypatch.setattr(A.time, "time", lambda: t0.__setitem__(0, t0[0] + 1) or t0[0])
    res = A.run_keeper(Config(), [], {}, hours=4 / 3600, dry_run=True)
    assert calls == ["open"]


def test_flatten_after_the_open_ignores_expired_market_on_open_orders(monkeypatch, tmp_path):
    """2026-10-22: Alpaca paper left 33 of 36 market-on-open orders unfilled; the 9:31 flatten saw them
    still listed as open and did nothing. After the open, only working market orders mean 'in progress'."""
    from qtrade.intraday import auction_live as A

    class Clock:
        is_open = True
        next_open = pd.Timestamp("2026-10-23 09:30", tz=NY)

    working = {"orders": [{"time_in_force": "opg", "status": "new"}]}

    class Client:
        def get_clock(self):
            return Clock()

        def get(self, path, params=None):
            return working["orders"]

    sent = []
    monkeypatch.setattr(A, "_client", lambda: Client())
    monkeypatch.setattr(A, "_now", lambda: pd.Timestamp("2026-10-22 09:35", tz=NY))
    monkeypatch.setattr(A, "_account_state", lambda c: (1e5, {"ACN": 1, "CLF": -31}, {}, set(), None, 1e5))
    monkeypatch.setattr(A, "_submit", lambda client, orders, tif: sent.append((tif, orders)) or [])
    res = A.run_open(Config(), dry_run=False, out_dir=tmp_path)
    assert res["status"] == "done" and sent[0][0] == "day"
    assert {(o.symbol, o.side, o.qty) for o in sent[0][1]} == {("ACN", "sell", 1), ("CLF", "buy", 31)}
    working["orders"] = [{"time_in_force": "day", "status": "new"}]       # our own market orders still working
    assert A.run_open(Config(), dry_run=False, out_dir=tmp_path)["status"] == "in progress"


def test_keeper_retries_the_late_flatten_until_flat(monkeypatch):
    from qtrade.intraday import auction_live as A

    times = iter(pd.date_range("2026-10-22 09:34", periods=40, freq="1min", tz=NY))

    class Clock:
        is_open = True
        next_open = pd.Timestamp("2026-10-23 09:30", tz=NY)

    class Client:
        def get_clock(self):
            return Clock()

    state = {"pos": {"ACN": 1}, "calls": 0}

    def flatten(cfg, **k):
        state["calls"] += 1
        if state["calls"] == 2:            # the second attempt gets filled
            state["pos"] = {}
        return {"status": "done"}

    monkeypatch.setattr(A, "_client", lambda: Client())
    monkeypatch.setattr(A, "_now", lambda: next(times))
    monkeypatch.setattr(A, "_account_state", lambda c: (1e5, dict(state["pos"]), {}, set(), None, 1e5))
    monkeypatch.setattr(A, "run_open", flatten)
    monkeypatch.setattr(A.time, "sleep", lambda s: None)
    t0 = [0.0]
    monkeypatch.setattr(A.time, "time", lambda: t0.__setitem__(0, t0[0] + 1) or t0[0])
    A.run_keeper(Config(), [], {}, hours=30 / 3600, dry_run=True)
    assert state["calls"] == 2              # 9:34 and 9:39, then flat: no more attempts
