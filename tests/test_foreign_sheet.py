"""Foreign sleeve: overnight books per market, settled at the first open after entry."""
import numpy as np
import pandas as pd

from qtrade.intraday import foreign_sheet as F


def _market(n=12, days=40, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2026-08-01", periods=days)
    cols = [f"S{i}" for i in range(n)]
    c = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.01, (days, n)), 0)), index=idx, columns=cols)
    o = c.shift(1) * np.exp(rng.normal(0, 0.005, (days, n)))
    return o, c


def test_books_are_dollar_neutral_with_equal_capital_per_market():
    o, c = _market()
    day = c.index[-1]
    h = F.open_books({"Korea": (o, c), "India": (o, c)}, day, 5000.0, set())
    for m, g in h.groupby("Market"):
        assert abs(g["Position $"].sum()) < 0.05
        assert np.isclose(g["Position $"].abs().sum(), 5000.0 / len(F.MARKETS), atol=0.05)
    assert set(h["Entry date"]) == {f"{day:%Y-%m-%d}"}


def test_settle_at_the_first_open_after_entry_and_hold_through_holidays():
    o, c = _market()
    entry = c.index[-3]
    hold = pd.DataFrame([["Korea", "S0", f"{entry:%Y-%m-%d}", 100.0, 500.0],
                         ["Taiwan", "S1", f"{c.index[-1]:%Y-%m-%d}", 50.0, -250.0]], columns=F.HOLD_HEADER)
    trades, still = F.settle(hold, {"Korea": o, "Taiwan": o})
    t = trades.iloc[0]
    nxt = o["S0"][o.index > entry].iloc[0]
    assert t["Exit date"] == f"{c.index[-2]:%Y-%m-%d}" and np.isclose(t["P&L $"], round(500 * (nxt / 100 - 1), 2))
    assert list(still["Symbol"]) == ["S1"]                       # no session after its entry yet: still held


def test_step_compounds_and_takes_deposits():
    o, c = _market()
    r = F.step(pd.DataFrame(columns=F.HOLD_HEADER), {"Korea": (o, c)}, c.index[-1], 0.0, 3242.09)
    assert r["pnl"] == 0 and np.isclose(r["equity"], 3242.09) and r["opened"] > 0


def test_a_session_still_open_is_not_used_as_a_close(monkeypatch):
    import sys
    import types

    idx = pd.bdate_range("2026-09-01", "2026-10-23")
    raw = {}
    for t in F.STOCKS["Germany"]:
        raw[(t, "Open")] = np.linspace(100, 110, len(idx))
        raw[(t, "Close")] = np.linspace(100.5, 110.5, len(idx))
    frame = pd.DataFrame(raw, index=idx)
    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=lambda *a, **k: frame))
    during = F.download(["Germany"], pd.Timestamp("2026-10-23 12:00", tz="UTC"))
    after = F.download(["Germany"], pd.Timestamp("2026-10-23 17:11", tz="UTC"))
    assert during["Germany"][1].index[-1] == pd.Timestamp("2026-10-22")
    assert after["Germany"][1].index[-1] == pd.Timestamp("2026-10-23")
