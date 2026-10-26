"""The shadow HFT simulation: orders execute after the latency at the book prevailing then."""
import numpy as np
import pandas as pd

from qtrade.intraday import hft_shadow as S

T0 = pd.Timestamp("2026-10-22 15:00:00", tz="UTC")


def at(s, ms=0):
    return T0 + pd.Timedelta(seconds=s) + pd.Timedelta(milliseconds=ms)


def test_taker_fills_after_the_latency_and_exits_passively():
    h = S.ShadowHFT(["AAA"], latency_ms=5, jitter_ms=0)
    h.on_quote("AAA", at(0), 100.00, 900, 100.01, 50)          # lopsided (0.89), 1 bp wide: decide at t=0
    h.on_quote("AAA", at(0, 3), 100.01, 900, 100.02, 50)       # the order arrives at 5 ms: pays 100.02
    h.on_quote("AAA", at(0, 9), 100.02, 500, 100.03, 500)      # exit rests at the ask then (100.02), live at 10 ms
    h.on_trade("AAA", at(0, 8), 100.05, 100)                   # before the exit is live: nothing
    h.on_trade("AAA", at(2), 100.02, 100)                      # a trade at our ask: the exit fills there
    t = h.take_closed()
    tk = t[t.strategy == "imbalance_taker"].iloc[0]
    assert tk.entry_price == 100.02 and tk.exit_price == 100.02 and tk.exit_by == "passive"
    assert np.isclose(tk.latency_ms, 5.0) and np.isclose(tk.pnl_bp, 0.0)


def test_fade_takes_the_other_side():
    h = S.ShadowHFT(["AAA"], latency_ms=5, jitter_ms=0)
    h.on_quote("AAA", at(0), 100.00, 900, 100.01, 50)
    sides = {o["strategy"]: o["side"] for o in h.pending}
    assert sides == {"imbalance_taker": "buy", "imbalance_fade": "sell"}


def test_weak_imbalance_or_wide_spread_does_not_take():
    h = S.ShadowHFT(["AAA", "BBB"], latency_ms=5, jitter_ms=0)
    h.on_quote("AAA", at(0), 100.00, 700, 100.01, 300)         # imbalance 0.4
    h.on_quote("BBB", at(0), 100.00, 900, 100.05, 50)          # 5 bp wide
    assert not h.pending


def test_unfilled_exit_crosses_the_spread_after_the_timeout():
    h = S.ShadowHFT(["AAA"], latency_ms=5, jitter_ms=0)
    h.on_quote("AAA", at(0), 100.00, 900, 100.01, 50)
    h.on_quote("AAA", at(0, 9), 99.90, 500, 99.91, 500)        # entries fill at 99.91 (buy) / 99.90 (sell)
    h.on_quote("AAA", at(29), 99.80, 500, 99.81, 500)          # price falls; no trades reach the exits
    h.step(at(31))
    t = h.take_closed().set_index("strategy")
    assert set(t.exit_by) == {"market"}
    assert t.loc["imbalance_taker", "exit_price"] == 99.80     # the long sells at the bid
    assert t.loc["imbalance_fade", "exit_price"] == 99.81      # the short buys at the ask
    assert t.loc["imbalance_fade", "pnl_usd"] > 0 > t.loc["imbalance_taker", "pnl_usd"]


def test_one_position_per_stock_per_strategy():
    h = S.ShadowHFT(["AAA"], latency_ms=5, jitter_ms=0)
    for i in range(5):
        h.on_quote("AAA", at(0, 20 * i), 100.00, 900, 100.01, 50)
    assert len(h.pending) + len(h.positions) == 2               # one taker, one fade


def test_maker_orders_go_live_after_the_latency():
    h = S.ShadowHFT(["AAA"], latency_ms=5, jitter_ms=0)
    h.on_quote("AAA", at(0), 50.00, 300, 50.02, 300)           # balanced book: no taker
    h.step(at(1))                                              # maker orders decided at 1.000, live at 1.005
    h.on_trade("AAA", at(1, 2), 50.00, 100)                    # before ours arrived: no fill
    h.on_trade("AAA", at(1, 8), 50.00, 100)                    # after: our bid fills at 50.00, exit rests at 50.02
    h.on_trade("AAA", at(3), 50.02, 100)                       # the exit fills: the whole spread
    t = h.take_closed()
    mm = t[t.strategy == "market_maker"]
    assert len(mm) == 1 and mm.iloc[0].side == "buy" and mm.iloc[0].entry_price == 50.00
    assert mm.iloc[0].exit_price == 50.02 and mm.iloc[0].exit_by == "passive"
    assert (t.strategy == "maker_with_signal").sum() == 0
    assert set(S.summary(t)["strategy"]) == {"market_maker"}


def test_jitter_is_a_few_milliseconds():
    h = S.ShadowHFT(["AAA"], seed=3)
    d = [h._delay().total_seconds() * 1e3 for _ in range(200)]
    assert min(d) >= S.LATENCY_MS and max(d) <= S.LATENCY_MS + S.JITTER_MS


def test_sheet_rows_summary_and_book_line():
    t = pd.DataFrame([{"strategy": "market_maker", "symbol": "AAA", "side": "buy", "decision_time": at(0),
                       "entry_time": at(0, 5), "entry_price": 50.0, "exit_time": at(30, 6), "exit_price": 50.01,
                       "notional": 250.0, "pnl_usd": 0.05, "pnl_mid_usd": 0.075, "pnl_bp": 2.0, "pnl_mid_bp": 3.0,
                       "spread_bp": 4.0, "imbalance": 0.1, "latency_ms": 5.5, "exit_by": "passive"}])
    rows = S.SheetWriter._rows(t)
    assert len(rows[0]) == len(S.HEADER) and rows[0][3].endswith(".005") and rows[0][7] == 250.0
    assert rows[0][-1] == "passive"
    s = S._summary_rows(t)
    assert s[0][:4] == ["Strategy", "Trades", "Net P&L $", "Net P&L mid $"] and s[-1][0] == "TOTAL"
    eq = {k: S.BOOK_USD / 4 for k in S.STRATEGIES}
    eq["market_maker"] += 0.05
    line = S.book_line(t, eq)
    assert "$10,000" in line and "net P&L $+0.05" in line


def test_the_10k_book_is_shared_and_compounds():
    n = S.SLOTS + 2
    h = S.ShadowHFT([f"S{i}" for i in range(n)], latency_ms=5, jitter_ms=0)
    for i in range(n):                                          # more lopsided books than slots
        h.on_quote(f"S{i}", at(0, i), 100.00, 900, 100.01, 50)
    taker = [o for o in h.pending + h.positions if o["strategy"] == "imbalance_taker"]
    assert len(taker) == S.SLOTS
    assert np.isclose(taker[0]["notional"], S.BOOK_USD / 4 / S.SLOTS)
    for i in range(n):
        h.on_quote(f"S{i}", at(29, i), 101.00, 500, 101.01, 500)  # everything rose ~1% before the timeouts
    h.step(at(32))
    t = h.take_closed()
    tk = t[t.strategy == "imbalance_taker"]
    assert len(tk) == S.SLOTS and (tk.pnl_usd > 0).all()
    assert np.isclose(h.equity["imbalance_taker"], S.BOOK_USD / 4 + tk.pnl_usd.sum())
    assert h.reserved["imbalance_taker"] < 1e-9                 # cash released after the exits


def test_broken_wide_quotes_are_not_traded():
    h = S.ShadowHFT(["AAA"], latency_ms=5, jitter_ms=0)
    h.on_quote("AAA", at(0), 380.0, 900, 393.0, 100)           # 336 bp wide and lopsided: no taker
    h.step(at(1))                                              # ... and no maker quotes either
    assert not h.pending and not h.resting


def test_tracker_mode_loads_the_replay_picks_even_when_disabled(tmp_path):
    import json
    picks = {"market_maker": {"enabled": False, "rules": {"exit_timeout_s": 600.0, "mm_min_ticks": 3,
                                                          "strategies": ["market_maker"]}},
             "imbalance_taker": {"enabled": False, "reason": "too few trades"}}
    f = tmp_path / "rules.json"
    f.write_text(json.dumps(picks))
    assert S.load_rules(f) == {}
    r = S.load_rules(f, include_disabled=True)
    assert list(r) == ["market_maker"] and r["market_maker"].exit_timeout_s == 600.0
    assert r["market_maker"].strategies == ("market_maker",)
    assert "TRACKER" in S.book_line(pd.DataFrame(columns=S.COLUMNS), {"market_maker": 10_000.0}, 10_000.0, "TRACKER")
