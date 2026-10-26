"""Foreign HFT tracker: picks parsed, one session simulated, a per-market summary."""
import numpy as np
import pandas as pd

from qtrade.intraday import foreign_hft_sheet as T


def test_parse_pick():
    assert T.parse_pick("reversal k=3 h=12") == (-1.0, 3, 12)
    assert T.parse_pick("momentum k=1 h=6") == (1.0, 1, 6)


def test_session_rows_and_summary():
    rng = np.random.default_rng(0)
    days = [pd.Timestamp("2026-10-22"), pd.Timestamp("2026-10-23")]
    idx = pd.DatetimeIndex([d + pd.Timedelta(hours=9, minutes=5 * i) for d in days for i in range(70)])
    c = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.002, (len(idx), 30)), 0)), index=idx,
                     columns=[f"S{i}" for i in range(30)])
    o = c.shift(1).fillna(100.0)
    rows = T.session_rows("Germany", "reversal k=3 h=12", o, c, days[1].date(), 10_000 / 9)
    assert np.isclose(rows[0][10], round(10_000 / 9 * rows[0][9] / 1e4, 2), atol=0.011)
    assert rows and all(r[0] == "2026-10-23" for r in rows) and len(rows[0]) == len(T.HEADER)
    assert all(len(r[5].split()) == 6 and len(r[6].split()) == 6 for r in rows)    # a fifth of 30 each side
    s = T.summarise(rows)
    assert s[0][0] == "Market" and s[-1][0] == "ALL" and np.isclose(s[-1][5], round(sum(r[10] for r in rows), 2))
