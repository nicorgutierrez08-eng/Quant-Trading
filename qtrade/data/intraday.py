"""Intraday bars from Alpaca's market-data API.

Alpaca's free market-data plan serves historical stock bars from all US
exchanges (the consolidated "SIP" feed) back to 2016. The only restriction is
that the latest 15 minutes are off limits, and requests are capped at 200 per
minute. This module:

* picks the most liquid stocks in the universe (median daily dollar volume);
* downloads N-minute bars for each, page by page, staying under the rate
  limit and backing off on HTTP 429;
* keeps only regular-hours bars (09:30-16:00 New York time);
* stores one parquet file per symbol and appends new bars on later runs, so a
  download can be interrupted and resumed, and a weekly refresh only fetches
  the newest data.

Prices are split- and dividend-adjusted (``adjustment=all``), matching the
daily data used by the backtest.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG
from .loader import to_alpaca, to_yahoo

DATA_URL = "https://data.alpaca.markets/v2/stocks/bars"
COLUMNS = ["open", "high", "low", "close", "volume", "trades", "vwap"]
_RENAME = {"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", "n": "trades", "vw": "vwap"}


@dataclass
class RateLimiter:
    """Allow at most ``per_minute`` calls in any rolling 60-second window."""

    per_minute: int = 190
    calls: deque = field(default_factory=deque)

    def wait(self) -> None:
        now = time.monotonic()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        if len(self.calls) >= self.per_minute:
            time.sleep(60 - (now - self.calls[0]) + 0.05)
        self.calls.append(time.monotonic())


class AlpacaBars:
    """Minimal client for ``GET /v2/stocks/bars`` with paging and back-off."""

    def __init__(self, key: str | None = None, secret: str | None = None, feed: str = "sip",
                 per_minute: int | None = None, session=None):
        import requests

        key = key or os.environ.get("ALPACA_API_KEY") or os.environ.get("APCA_API_KEY_ID")
        secret = secret or os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY")
        if not key or not secret:
            raise SystemExit("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to download intraday data.")
        self.session = session or requests.Session()
        self.session.headers.update({"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret})
        self.feed = feed
        per_minute = per_minute or int(os.environ.get("ALPACA_RATE_PER_MIN", "190"))
        self.limiter = RateLimiter(per_minute)
        self.calls = 0

    def _get(self, params: dict, url: str = DATA_URL) -> dict:
        for attempt in range(10):
            self.limiter.wait()
            r = self.session.get(url, params=params, timeout=60)
            self.calls += 1
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429 or r.status_code >= 500:
                pause = min(60, 2 ** attempt)
                LOG.warning("Alpaca HTTP %d, retrying in %ds", r.status_code, pause)
                time.sleep(pause)
                continue
            raise RuntimeError(f"Alpaca data API error {r.status_code}: {r.text[:300]}")
        raise RuntimeError("Alpaca data API: too many retries")

    def bars(self, symbols: list[str], timeframe: str, start: str, end: str) -> dict[str, list[dict]]:
        """All bars for ``symbols`` between ``start`` and ``end`` (RFC-3339), following pages."""
        out: dict[str, list[dict]] = {}
        params = {
            "symbols": ",".join(to_alpaca(s) for s in symbols), "timeframe": timeframe,
            "start": start, "end": end, "limit": 10000, "adjustment": getattr(self, "adjustment", "all"),
            "feed": self.feed, "sort": "asc",
        }
        while True:
            data = self._get(params)
            for sym, rows in (data.get("bars") or {}).items():
                out.setdefault(to_yahoo(sym), []).extend(rows)
            token = data.get("next_page_token")
            if not token:
                return out
            params["page_token"] = token


def bars_to_frame(rows: list[dict], regular_hours: bool = True) -> pd.DataFrame:
    """Alpaca bar dicts -> DataFrame indexed by New York time, regular hours only."""
    if not rows:
        return pd.DataFrame(columns=COLUMNS, index=pd.DatetimeIndex([], name="time"))
    df = pd.DataFrame(rows).rename(columns=_RENAME)
    idx = pd.to_datetime(df.pop("t"), utc=True).dt.tz_convert("America/New_York")
    df.index = pd.DatetimeIndex(idx, name="time")
    for c in COLUMNS:
        if c not in df:
            df[c] = np.nan
    df = df[COLUMNS]
    if regular_hours:
        mins = df.index.hour * 60 + df.index.minute
        df = df[(mins >= 9 * 60 + 30) & (mins < 16 * 60)]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df.astype({"open": "float32", "high": "float32", "low": "float32", "close": "float32",
                      "volume": "float64", "trades": "float64", "vwap": "float32"})


def most_liquid(client: AlpacaBars, tickers: list[str], n: int, lookback_days: int = 90) -> pd.DataFrame:
    """Rank tickers by median daily dollar volume over the last ``lookback_days``."""
    end = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)).isoformat()
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=lookback_days)).isoformat()
    rows = []
    for i in range(0, len(tickers), 100):
        got = client.bars(tickers[i : i + 100], "1Day", start, end)
        for sym, bars in got.items():
            dv = [b["c"] * b["v"] for b in bars if b.get("v")]
            if dv:
                rows.append({"ticker": sym, "median_dollar_volume": float(np.median(dv)), "days": len(dv)})
    ranked = pd.DataFrame(rows).sort_values("median_dollar_volume", ascending=False)
    ranked = ranked[ranked["days"] >= lookback_days * 0.5]
    return ranked.head(n).reset_index(drop=True)


def store_path(store_dir: str | Path, symbol: str) -> Path:
    return Path(store_dir) / f"{symbol}.parquet"


def load_symbol(store_dir: str | Path, symbol: str) -> pd.DataFrame | None:
    p = store_path(store_dir, symbol)
    return pd.read_parquet(p) if p.exists() else None


def update_symbol(client: AlpacaBars, store_dir: str | Path, symbol: str, timeframe: str,
                  start: str, end: str, chunk_years: int = 2) -> tuple[int, int]:
    """Fetch bars newer than what is stored (or from ``start``) and append.

    Returns (rows added, total rows). Requests are split into multi-year chunks
    so a failure part-way loses at most one chunk, and the file is rewritten
    after each chunk so progress survives interruptions.
    """
    Path(store_dir).mkdir(parents=True, exist_ok=True)
    have = load_symbol(store_dir, symbol)
    begin = pd.Timestamp(start, tz="UTC")
    if have is not None and len(have):
        begin = max(begin, have.index[-1].tz_convert("UTC") + pd.Timedelta(seconds=1))
    stop = pd.Timestamp(end).tz_convert("UTC") if pd.Timestamp(end).tzinfo else pd.Timestamp(end, tz="UTC")
    added = 0
    cur = begin
    while cur < stop:
        nxt = min(stop, cur + pd.DateOffset(years=chunk_years))
        got = client.bars([symbol], timeframe, cur.isoformat(), nxt.isoformat())
        new = bars_to_frame(got.get(symbol, []))
        if len(new):
            have = new if have is None or not len(have) else pd.concat([have, new])
            have = have[~have.index.duplicated(keep="last")].sort_index()
            have.to_parquet(store_path(store_dir, symbol))
            added += len(new)
        cur = nxt
    return added, 0 if have is None else len(have)


def download(tickers: list[str], store_dir: str | Path, timeframe: str = "5Min",
             start: str = "2016-01-01", client: AlpacaBars | None = None,
             time_budget_min: float | None = None) -> pd.DataFrame:
    """Download / refresh every ticker; returns a per-symbol manifest.

    ``time_budget_min`` stops cleanly before a CI time limit; re-running
    resumes where it stopped.
    """
    client = client or AlpacaBars()
    end = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)).isoformat()
    t0 = time.time()
    complete = True
    for k, sym in enumerate(tickers):
        if time_budget_min and (time.time() - t0) / 60 > time_budget_min:
            LOG.warning("time budget reached after %d/%d symbols; re-run to resume", k, len(tickers))
            complete = False
            break
        try:
            added, total = update_symbol(client, store_dir, sym, timeframe, start, end)
        except RuntimeError as exc:
            LOG.warning("%s: %s", sym, exc)
            complete = False
            continue
        LOG.info("[%d/%d] %-6s +%d bars (total %d, %d API calls so far)",
                 k + 1, len(tickers), sym, added, total, client.calls)
    m = manifest(store_dir, tickers, timeframe)
    m.attrs["complete"] = complete
    return m


def manifest(store_dir: str | Path, tickers: list[str], timeframe: str) -> pd.DataFrame:
    rows = []
    for sym in tickers:
        df = load_symbol(store_dir, sym)
        if df is None or not len(df):
            rows.append({"ticker": sym, "rows": 0})
            continue
        rows.append({"ticker": sym, "rows": len(df), "first": str(df.index[0]), "last": str(df.index[-1]),
                     "days": int(df.index.normalize().nunique()),
                     "bars_per_day": round(len(df) / max(1, df.index.normalize().nunique()), 1)})
    m = pd.DataFrame(rows)
    m.attrs["timeframe"] = timeframe
    return m


def write_manifest(m: pd.DataFrame, store_dir: str | Path, extra: dict | None = None) -> Path:
    summary = {
        "timeframe": m.attrs.get("timeframe"), "symbols": int((m["rows"] > 0).sum()),
        "symbols_requested": len(m), "total_rows": int(m["rows"].sum()),
        "first": min((x for x in m.get("first", []) if isinstance(x, str)), default=None),
        "last": max((x for x in m.get("last", []) if isinstance(x, str)), default=None),
        "updated": pd.Timestamp.now(tz="UTC").isoformat(),
        "complete": bool(m.attrs.get("complete", True)),
    } | (extra or {})
    path = Path(store_dir) / "manifest.json"
    path.write_text(json.dumps(summary, indent=2))
    m.to_csv(Path(store_dir) / "manifest.csv", index=False)
    return path


def load_panel(store_dir: str | Path, tickers: list[str] | None = None,
               start: str | None = None, end: str | None = None) -> dict[str, pd.DataFrame]:
    """Load stored bars as {field: DataFrame(time x ticker)} for research."""
    store_dir = Path(store_dir)
    tickers = tickers or sorted(p.stem for p in store_dir.glob("*.parquet"))
    frames = {}
    for sym in tickers:
        df = load_symbol(store_dir, sym)
        if df is not None and len(df):
            frames[sym] = df.loc[start:end] if (start or end) else df
    return {c: pd.DataFrame({s: f[c] for s, f in frames.items()}).sort_index() for c in COLUMNS}
