"""Daily OHLCV download from Yahoo Finance (via ``yfinance``) with a local cache.

Prices are split- and dividend-adjusted so that close-to-close returns are
total returns. The close and volume as they actually printed are kept too
(``raw_close``, ``raw_volume``), rebuilt from Yahoo's split-only-adjusted
close and its split history: price floors, liquidity and costs must not
depend on splits and dividends that happen later. Because adjustments change
the whole history whenever a dividend is paid, the cache is refreshed by
re-downloading rather than appending.
"""
from __future__ import annotations

import re

import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, load_frame, save_frame
from .market import FIELDS, RAW_FIELDS, MarketData

_YF_FIELDS = {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}


# exchange suffixes Yahoo writes with a dot (Tokyo, Hong Kong, Korea, Taiwan, Sydney, India, China, Singapore)
_EXCHANGE_SUFFIX = re.compile(r"^(.+)\.(T|HK|KS|KQ|TW|TWO|AX|NS|BO|SS|SZ|SI|L|DE|PA|AS|MI|SW|ST|CO|OL|HE|BR|LS|TO)$")


def to_yahoo(ticker: str) -> str:
    """Yahoo uses '-' for share classes: BRK.B -> BRK-B (but keeps exchange suffixes: 7203.T, 0700.HK)."""
    t = ticker.strip().upper()
    m = _EXCHANGE_SUFFIX.match(t)
    if m:
        return m.group(1).replace("/", "-") + "." + m.group(2)
    return t.replace(".", "-").replace("/", "-")


def to_alpaca(ticker: str) -> str:
    """Alpaca uses '.' for share classes: BRK-B -> BRK.B."""
    return ticker.strip().upper().replace("-", ".")


def _download_batch(tickers: list[str], start: str, end: str | None) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    raw = yf.download(
        tickers, start=start, end=end, auto_adjust=False, actions=True,
        group_by="column", threads=True, progress=False,
    )
    if raw is None or raw.empty:
        return {}
    if not isinstance(raw.columns, pd.MultiIndex):  # single ticker
        raw.columns = pd.MultiIndex.from_product([raw.columns, tickers])
    return split_yahoo_frame(raw)


def clean_dividend_factor(factor: pd.DataFrame, max_step: float = 0.25) -> pd.DataFrame:
    """Repair Yahoo's dividend adjustment factor (Adj Close / Close).

    The factor can only move on ex-dividend days, by about the dividend's share
    of the price, so it is a slowly rising step function that ends at 1. Yahoo
    occasionally serves a stretch where Adj Close and Close disagree by a split
    ratio; the factor then jumps by 2x, 10x or more and back. Steps larger than
    ``max_step`` are treated as such glitches and removed, and the factor is
    rebuilt backwards from its (reliable) latest value.
    """
    lf = np.log(factor.ffill().bfill())
    d = lf.diff().fillna(0.0)
    big = d.abs() > np.log1p(max_step)
    for col in d.columns[big.any()]:
        x = d[col].to_numpy().copy()
        pending = 0.0                  # glitch steps not yet undone
        for i in np.nonzero(big[col].to_numpy())[0]:
            pending += x[i]
            x[i] = 0.0
            if abs(pending) <= np.log1p(max_step):   # glitch closed: keep the real change inside it
                x[i] = pending
                pending = 0.0
        d[col] = x
    later = d.iloc[::-1].cumsum().iloc[::-1].shift(-1).fillna(0.0)   # sum of steps after each day
    clean = np.exp(lf.iloc[-1] - later)
    return clean.where(factor.notna())


def split_yahoo_frame(raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Turn an unadjusted ``yf.download(..., actions=True)`` frame into adjusted
    OHLCV panels plus the as-traded close and volume.

    Yahoo's ``Close``/``Volume`` are adjusted for splits only and ``Adj Close``
    for splits and dividends. Undoing the splits needs the split history: the
    as-traded price on day t is the split-adjusted price times every split
    ratio with an ex-date after t.
    """
    fields = raw.columns.get_level_values(0)
    get = lambda name: raw[name].copy() if name in fields else None  # noqa: E731
    out: dict[str, pd.DataFrame] = {}
    close, adj = get("Close"), get("Adj Close")
    if close is None:
        return out
    factor = (adj / close) if adj is not None else close * 0 + 1.0   # dividend adjustment
    factor = clean_dividend_factor(factor.where(np.isfinite(factor) & (factor > 0)))
    for f, yf_name in _YF_FIELDS.items():
        df = get(yf_name)
        if df is None:
            continue
        if f != "volume":              # volume is already split-adjusted, and dividends don't touch it
            df = df * factor
        out[f] = df
    splits = get("Stock Splits")   # absent only when the batch had none
    ratio = (splits.where(splits > 0).fillna(1.0).reindex_like(close)
             if splits is not None else close * 0 + 1.0).fillna(1.0)
    # product of the ratios of all splits strictly after each day
    later = ratio.iloc[::-1].cumprod().iloc[::-1].shift(-1).fillna(1.0)
    out["raw_close"] = close * later
    if "volume" in out:
        out["raw_volume"] = out["volume"] / later
    for f in out:
        out[f].index = pd.to_datetime(out[f].index).tz_localize(None).normalize()
    return out


def download_prices(
    tickers: list[str],
    start: str = "2000-01-01",
    end: str | None = None,
    batch_size: int = 100,
    retries: int = 2,
) -> MarketData:
    """Download OHLCV for many tickers in batches. Tickers that fail are dropped."""
    tickers = list(dict.fromkeys(to_yahoo(t) for t in tickers))
    frames: dict[str, list[pd.DataFrame]] = {f: [] for f in FIELDS + RAW_FIELDS}
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        for attempt in range(retries + 1):
            try:
                got = _download_batch(batch, start, end)
                break
            except Exception as exc:  # network hiccups, rate limits
                LOG.warning("batch %d failed (%s); retry %d", i // batch_size, exc, attempt + 1)
                time.sleep(5 * (attempt + 1))
                got = {}
        for f in FIELDS + RAW_FIELDS:
            if f in got:
                frames[f].append(got[f])
        LOG.info("downloaded %d / %d tickers", min(i + batch_size, len(tickers)), len(tickers))

    if not frames["close"]:
        raise RuntimeError("No price data downloaded - check your internet connection.")
    # raw panels only when every batch had them, so they cover every ticker
    fields = FIELDS + tuple(f for f in RAW_FIELDS if len(frames[f]) == len(frames["close"]))
    panels = {f: pd.concat(frames[f], axis=1).sort_index() for f in fields}
    close = panels["close"]
    close = close.loc[:, ~close.columns.duplicated()]
    keep = close.columns[close.notna().sum() > 0]
    panels = {f: panels[f].loc[:, ~panels[f].columns.duplicated()].reindex(columns=keep) for f in fields}
    # drop dates where (almost) nothing traded: holidays that sneak in
    active = panels["close"].notna().mean(axis=1) > 0.05
    panels = {f: df.loc[active] for f, df in panels.items()}
    return MarketData(**panels)


def cache_paths(cache_dir: str | Path) -> dict[str, Path]:
    cache_dir = Path(cache_dir)
    return {f: cache_dir / "prices" / f for f in FIELDS + RAW_FIELDS}


CACHE_VERSION = "3"   # bump when the download's processing changes, to force a fresh download


def save_market(md: MarketData, cache_dir: str | Path) -> None:
    for f, p in cache_paths(cache_dir).items():
        if getattr(md, f) is not None:
            save_frame(getattr(md, f).astype("float32"), p)
    (Path(cache_dir) / "prices" / "VERSION").write_text(CACHE_VERSION)


def load_market(cache_dir: str | Path) -> MarketData | None:
    panels = {}
    for f, p in cache_paths(cache_dir).items():
        df = load_frame(p)
        if df is None:
            if f in RAW_FIELDS:
                continue
            return None
        panels[f] = df
    return MarketData(**panels)


def last_completed_session(now: pd.Timestamp | None = None) -> pd.Timestamp:
    """Most recent weekday whose US session has closed (ignores holidays)."""
    now = now or pd.Timestamp.now(tz="America/New_York")
    day = now.normalize().tz_localize(None)
    if now.hour < 17:  # data for today is not final before ~5pm ET
        day -= pd.Timedelta(days=1)
    while day.weekday() >= 5:
        day -= pd.Timedelta(days=1)
    return day


def get_market_data(
    tickers: list[str], start: str, end: str | None, cache_dir: str | Path,
    batch_size: int = 100, force: bool = False,
) -> MarketData:
    """Load from cache when it is fresh and covers the tickers, else download."""
    cached = None if force else load_market(cache_dir)
    want = {to_yahoo(t) for t in tickers}
    if cached is not None:
        have = set(cached.tickers)
        target_end = pd.Timestamp(end) - pd.Timedelta(days=1) if end else last_completed_session()
        # allow for a holiday: fresh if within 4 calendar days of the target
        fresh = cached.dates[-1] >= target_end - pd.Timedelta(days=4)
        covered = len(want - have) <= max(5, 0.01 * len(want))
        starts_ok = cached.dates[0] <= pd.Timestamp(start) + pd.Timedelta(days=10)
        vfile = Path(cache_dir) / "prices" / "VERSION"
        if not cached.has_raw or not vfile.exists() or vfile.read_text().strip() != CACHE_VERSION:
            LOG.info("cached prices come from an older version of the downloader; downloading again")
        elif fresh and covered and starts_ok:
            LOG.info("using cached prices (%d tickers, through %s)", len(have), cached.dates[-1].date())
            return cached.subset(tickers=[t for t in cached.tickers if t in want])
    md = download_prices(sorted(want), start=start, end=end, batch_size=batch_size)
    save_market(md, cache_dir)
    return md
