"""The earnings leg of the auction trader: ``last_reaction``.

Research (``qtrade.research.consumer_earnings``): a company whose previous
earnings release moved its stock up (relative to the market, from the close
before the release to the open after) tends to move up again on the next
release, and vice versa. Rank correlation 0.025 on 2016-20, Sharpe 0.76 / 0.40
on 2016-20 / 2021-26 trading 2% of capital per release at 0 bp.

Live, at the close of day d:

* releases due tonight or before tomorrow's open come from Nasdaq's public
  earnings calendar (the companies announce the dates weeks ahead);
* each company's previous release comes from its SEC 8-K item 2.02 filings and
  its announcement return from Alpaca daily bars, minus SPY's over the same
  close -> open;
* the book goes long the names whose last reaction was positive and short the
  negative ones, ``earnings_per_event`` of capital each, through the same
  market-on-close / market-on-open orders as the rest of the auction book.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils import LOG

NY = "America/New_York"
NASDAQ_URL = "https://api.nasdaq.com/api/calendar/earnings"
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def _norm(sym: str) -> str:
    return str(sym).strip().upper().replace("/", "-").replace(".", "-")


def parse_calendar(payload: dict) -> dict[str, str]:
    """{ticker: "after_close" | "before_open"} from a Nasdaq calendar response (unknown times dropped)."""
    rows = ((payload or {}).get("data") or {}).get("rows") or []
    out = {}
    for r in rows:
        t = {"time-after-hours": "after_close", "time-pre-market": "before_open"}.get(r.get("time"))
        if t and r.get("symbol"):
            out[_norm(r["symbol"])] = t
    return out


def nasdaq_calendar(day: pd.Timestamp, session=None) -> dict[str, str]:
    import requests

    s = session or requests.Session()
    r = s.get(NASDAQ_URL, params={"date": pd.Timestamp(day).strftime("%Y-%m-%d")}, timeout=30,
              headers={"User-Agent": BROWSER_UA, "Accept": "application/json"})
    r.raise_for_status()
    return parse_calendar(r.json())


def releases_tonight(today: pd.Timestamp, fetch=nasdaq_calendar) -> list[str]:
    """Tickers reporting after today's close or before the next session's open."""
    names = {t for t, s in fetch(today).items() if s == "after_close"}
    nxt = today + pd.offsets.BDay(1)
    for _ in range(3):                         # skip a market holiday with no releases listed
        got = fetch(nxt)
        if got:
            names |= {t for t, s in got.items() if s == "before_open"}
            break
        nxt += pd.offsets.BDay(1)
    return sorted(names)


def _session_of(accepted: pd.Timestamp) -> str:
    m = accepted.hour * 60 + accepted.minute
    return "before_open" if m < 9 * 60 + 30 else ("after_close" if m >= 16 * 60 else "during")


def previous_release(rows: list[dict], before: pd.Timestamp) -> tuple[pd.Timestamp, str] | None:
    """Most recent earnings release (accepted time NY, session) strictly before ``before``,
    ignoring releases during the session, as the backtest does."""
    best = None
    for r in rows:
        a = pd.Timestamp(r["accepted"])
        a = (a.tz_localize("UTC") if a.tzinfo is None else a).tz_convert(NY)
        s = _session_of(a)
        if s == "during" or a >= before:
            continue
        if best is None or a > best[0]:
            best = (a, s)
    return best


def announcement_return(accepted: pd.Timestamp, session: str, bars: pd.DataFrame,
                        spy: pd.DataFrame) -> float:
    """Close before the release -> open after it, minus SPY's (the backtest's entry / exit rule)."""
    def _daily(f):
        g = f.copy()
        g.index = g.index.tz_convert(NY).tz_localize(None).normalize() if g.index.tz is not None else g.index.normalize()
        return g[~g.index.duplicated(keep="last")]

    b, m = _daily(bars), _daily(spy)
    dates = m.index
    day = accepted.tz_localize(None).normalize()
    pos = dates.searchsorted(day)
    if pos >= len(dates):
        return np.nan
    entry = pos if (session == "after_close" and dates[pos] == day) else pos - 1
    if entry < 0 or entry + 1 >= len(dates):
        return np.nan
    d0, d1 = dates[entry], dates[entry + 1]
    if d0 not in b.index or d1 not in b.index:
        return np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        r = b.at[d1, "open"] / b.at[d0, "close"] - 1
        mk = m.at[d1, "open"] / m.at[d0, "close"] - 1
    return float(np.clip(r, -0.5, 0.5) - mk)


def last_reactions(tickers: list[str], now: pd.Timestamp, daily: dict[str, pd.DataFrame],
                   spy: pd.DataFrame, sec=None, deadline: pd.Timestamp | None = None) -> dict[str, float]:
    """{ticker: previous release's market-relative announcement return} (SEC filings + daily bars).
    Stops looking up names at ``deadline`` (the orders must not wait for it)."""
    from ..data.consumer import SUBMISSIONS_URL, _earnings_rows
    from ..data.fundamentals import SecClient, ticker_to_cik

    sec = sec or SecClient()
    ciks = ticker_to_cik(sec)
    out = {}
    for t in tickers:
        if deadline is not None and pd.Timestamp.now(tz=NY) > deadline:
            LOG.warning("last_reaction: out of time after %d of %d names", len(out), len(tickers))
            break
        if t not in ciks or t not in daily:
            continue
        try:
            sub = sec.get_json(SUBMISSIONS_URL.format(cik=ciks[t]))
        except Exception as exc:
            LOG.warning("SEC submissions %s: %s", t, exc)
            continue
        prev = previous_release(_earnings_rows(t, (sub or {}).get("filings", {}).get("recent", {})), now)
        if prev is None:
            continue
        r = announcement_return(prev[0], prev[1], daily[t], spy)
        if np.isfinite(r):
            out[t] = r
    return out


def earnings_weights(tickers: list[str], reactions: dict[str, float], ok: np.ndarray, sign: float,
                     per_event: float, max_gross: float) -> np.ndarray:
    """Long / short ``per_event`` per name by the sign of its last reaction; total capped at ``max_gross``."""
    w = np.zeros(len(tickers))
    for i, t in enumerate(tickers):
        r = reactions.get(t)
        if r is not None and np.isfinite(r) and r != 0 and ok[i]:
            w[i] = sign * np.sign(r) * per_event
    g = np.abs(w).sum()
    if g > max_gross > 0:
        w *= max_gross / g
    return w
