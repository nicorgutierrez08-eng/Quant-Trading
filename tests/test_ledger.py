"""Trade ledger: FIFO round trips and the encryption round trip."""
import subprocess

import numpy as np
import pandas as pd

from qtrade.live import ledger as Lg

NY = "America/New_York"


def _fills(rows):
    return pd.DataFrame([{"time": pd.Timestamp(t, tz=NY), "symbol": s, "side": side, "qty": q, "price": p, "tif": tif}
                         for t, s, side, q, p, tif in rows])


def test_round_trips_fifo_long_short_and_partial():
    f = _fills([("2026-10-21 15:50", "AAA", "buy", 10, 100.0, "cls"),
                ("2026-10-21 15:50", "BBB", "sell", 5, 50.0, "cls"),       # short
                ("2026-10-22 09:30", "AAA", "sell", 4, 101.0, "opg"),      # partial close
                ("2026-10-22 09:30", "BBB", "buy", 5, 49.0, "opg"),
                ("2026-10-22 09:40", "AAA", "sell", 6, 99.0, "day")])
    t, lots = Lg.round_trips(f)
    assert len(t) == 3 and not any(lots.values())
    a1, b, a2 = t.iloc[0], t.iloc[1], t.iloc[2]
    assert a1.symbol == "AAA" and a1.shares == 4 and np.isclose(a1.pnl, 4.0) and a1.exit_order == "opg"
    assert b.side == "short" and np.isclose(b.pnl, 5.0) and np.isclose(b.return_pct, 2.0)
    assert a2.shares == 6 and np.isclose(a2.pnl, -6.0) and a2.entry_order == "cls" and a2.exit_order == "day"


def test_flip_and_open_lots():
    f = _fills([("2026-10-21 15:50", "AAA", "buy", 3, 10.0, "cls"),
                ("2026-10-22 15:50", "AAA", "sell", 5, 12.0, "cls")])        # closes 3, opens a 2-share short
    t, lots = Lg.round_trips(f)
    assert len(t) == 1 and np.isclose(t.iloc[0].pnl, 6.0)
    o = Lg.open_positions(lots, {"AAA": 11.0})
    assert o.iloc[0].side == "short" and o.iloc[0].shares == 2 and np.isclose(o.iloc[0].pnl, 2.0)


def test_encrypt_decrypt_round_trip(tmp_path):
    priv, pub = tmp_path / "k.pem", tmp_path / "k.pub"
    subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(priv)],
                   check=True, capture_output=True)
    subprocess.run(["openssl", "pkey", "-in", str(priv), "-pubout", "-out", str(pub)], check=True, capture_output=True)
    p = tmp_path / "trades.csv"
    p.write_text("symbol,pnl\nAAA,1.5\n")
    enc, kenc = Lg.encrypt(p, str(pub))
    assert not p.exists() and b"AAA" not in enc.read_bytes()
    out = Lg.decrypt(enc, str(priv))
    assert out.read_text() == "symbol,pnl\nAAA,1.5\n"


def test_partial_fills_merge_back_into_one_trade():
    f = _fills([("2026-10-20 09:41:55", "AAA", "buy", 1, 10.0, "day"),
                ("2026-10-20 09:41:56", "AAA", "buy", 3, 10.4, "day"),
                ("2026-10-22 09:30:05", "AAA", "sell", 4, 11.0, "opg")])
    t, _ = Lg.round_trips(f)
    assert len(t) == 2
    m = Lg.merge_pieces(t)
    assert len(m) == 1 and m.iloc[0].shares == 4 and np.isclose(m.iloc[0].entry_price, 10.3)
    assert np.isclose(m.iloc[0].pnl, 1.0 + 3 * 0.6)
