"""Signals from fundamentals (SEC filings) and news (Benzinga headlines).

These move far more slowly than price reversal, so they trade much less and
costs matter much less: the question is whether they carry any edge at all.
Every value is used only from the trading day *after* it became public
(filing date or article time), so nothing is known before it was announced.

Fundamentals
  sue            standardized unexpected earnings: this quarter's EPS minus the
                 same quarter last year, over the volatility of that change;
                 held for 63 trading days after the filing (post-earnings drift)
  ear            the stock's return relative to the market over the 3 days
                 around the filing (earnings-announcement return), held 63 days
  earnings_yield annual net income / market value
  book_to_market shareholders' equity / market value
  gross_prof     annual gross profit / total assets (Novy-Marx)
  asset_growth   minus the 1-year growth in total assets
  accruals       minus (net income - operating cash flow) / assets

News
  news_volume    minus abnormal article count (last 5 days vs. prior 60)
  news_tone      headline tone over the last 3 days (word lists)
  no_news_rev    5-day reversal, only for stocks with no news in those 5 days
  news_mom       5-day momentum, only for stocks that had news
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.fundamentals import load_fundamentals, point_in_time
from ..data.news import load_news
from ..utils import LOG

HOLD_DAYS = 63

POSITIVE = {"beat", "beats", "tops", "upgrade", "upgrades", "upgraded", "raises", "raised", "record",
            "surge", "surges", "soars", "jumps", "rallies", "strong", "outperform", "buy", "approval",
            "approved", "wins", "awarded", "exceeds", "boosts", "higher", "growth", "profit"}
NEGATIVE = {"miss", "misses", "missed", "downgrade", "downgrades", "downgraded", "cuts", "cut", "lowers",
            "lawsuit", "sues", "probe", "investigation", "plunge", "plunges", "falls", "drops", "slumps",
            "recall", "weak", "underperform", "sell", "loss", "losses", "warning", "warns", "delay",
            "halt", "fraud", "bankruptcy", "layoffs", "decline", "lower"}


def _next_day(dates: pd.DatetimeIndex, when: pd.Series) -> pd.Series:
    """First trading day strictly after each timestamp's date (safe: after-hours filings)."""
    d = pd.to_datetime(when).dt.normalize()
    pos = dates.searchsorted(d, side="right")
    ok = pos < len(dates)
    out = pd.Series(pd.NaT, index=when.index)
    out[ok] = dates[pos[ok]]
    return out


def _event_panel(events: pd.DataFrame, dates, tickers, hold: int = HOLD_DAYS) -> pd.DataFrame:
    """events: ticker, day (first usable day), value -> panel held for ``hold`` days."""
    out = pd.DataFrame(np.nan, index=dates, columns=tickers)
    for t, g in events.dropna(subset=["day", "value"]).groupby("ticker"):
        if t not in out.columns:
            continue
        s = pd.Series(g["value"].to_numpy(), index=pd.DatetimeIndex(g["day"]))
        s = s[~s.index.duplicated(keep="last")].reindex(dates)
        out[t] = s.ffill(limit=hold)
    return out


def fundamental_signals(md, ctx, facts: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dates, tickers = md.dates, md.tickers
    lag = lambda p: p.shift(1)  # noqa: E731   value filed on day d is usable from d+1
    pit = lambda tag, annual=False: lag(point_in_time(facts, tag, dates, tickers, annual))  # noqa: E731
    shares = pit("dei:EntityCommonStockSharesOutstanding")
    shares = shares.fillna(pit("WeightedAverageNumberOfDilutedSharesOutstanding"))
    mcap = md.traded_close * shares
    mcap = mcap.where(mcap > 0)
    ni = pit("NetIncomeLoss", annual=True)
    eq = pit("StockholdersEquity")
    assets = pit("Assets")
    gp = pit("GrossProfit", annual=True)
    rev = pit("Revenues", annual=True).fillna(pit("RevenueFromContractWithCustomerExcludingAssessedTax", annual=True))
    gp = gp.fillna(rev - pit("CostOfRevenue", annual=True))
    ocf = pit("NetCashProvidedByUsedInOperatingActivities", annual=True)
    sig = {
        "earnings_yield": ni / mcap,
        "book_to_market": (eq / mcap).where(eq > 0),
        "gross_prof": gp / assets,
        "asset_growth": -(assets / assets.shift(252) - 1),
        "accruals": -(ni - ocf) / assets,
    }

    # earnings surprise and announcement return, per filing
    eps = facts[(facts["tag"] == "EarningsPerShareDiluted") & facts["filed"].notna() & facts["start"].notna()].copy()
    eps = eps[((eps["end"] - eps["start"]).dt.days.between(70, 110))]
    eps = eps.sort_values("filed").groupby(["ticker", "end"]).head(1)          # as first reported
    rows = []
    for t, g in eps.groupby("ticker"):
        g = g.sort_values("end")
        ends, vals = g["end"].to_numpy(), g["value"].to_numpy(dtype=float)
        diffs = []
        for i in range(len(g)):
            j = np.nonzero(np.abs((ends[i] - ends[:i]).astype("timedelta64[D]").astype(int) - 365) <= 20)[0]
            d = vals[i] - vals[j[-1]] if len(j) else np.nan
            prev = [x for x in diffs[-8:] if np.isfinite(x)]
            sd = np.std(prev) if len(prev) >= 4 else np.nan
            rows.append({"ticker": t, "filed": g["filed"].iloc[i], "value": d / sd if sd and sd > 0 else np.nan})
            diffs.append(d)
    ev = pd.DataFrame(rows)
    if len(ev):
        ev["day"] = _next_day(dates, ev["filed"])
        sig["sue"] = _event_panel(ev, dates, tickers).clip(-10, 10)
        # 3-day market-relative return around the filing: days filed-1 .. filed+1, known at the close of filed+1
        ar = ctx.ret.sub(ctx.market_ret, axis=0)
        ar3 = ar.rolling(3).sum()
        ev2 = ev[["ticker", "filed"]].copy()
        d0 = pd.to_datetime(ev2["filed"]).dt.normalize()
        pos = dates.searchsorted(d0, side="left") + 1                             # filed+1 (trading days)
        ok = pos + 1 < len(dates)
        ev2 = ev2[ok].assign(known=dates[pos[ok]], day=dates[pos[ok] + 1])
        ev2["value"] = [ar3.at[k, t] if t in ar3.columns else np.nan for k, t in zip(ev2["known"], ev2["ticker"])]
        sig["ear"] = _event_panel(ev2, dates, tickers)
    LOG.info("fundamental signals: %s", list(sig))
    return sig


def _tone(text: str) -> float:
    words = re.findall(r"[a-z]+", text.lower())
    p = sum(w in POSITIVE for w in words)
    n = sum(w in NEGATIVE for w in words)
    return (p - n) / max(p + n, 1)


def news_signals(md, ctx, news: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dates, tickers = md.dates, md.tickers
    x = news[["created_at", "headline", "symbols"]].copy()
    x["tone"] = x["headline"].fillna("").map(_tone)
    x["ticker"] = x["symbols"].str.split(",")
    x = x.explode("ticker")
    x = x[x["ticker"].isin(set(tickers))]
    # an article is usable from the first trading day whose close comes after it
    ny = x["created_at"].dt.tz_convert("America/New_York")
    after_close = ny.dt.hour >= 16
    day = ny.dt.tz_localize(None).dt.normalize()
    pos = dates.searchsorted(day, side="left")
    pos = np.where(after_close.to_numpy(), dates.searchsorted(day, side="right"), pos)
    ok = pos < len(dates)
    x = x[ok].assign(day=dates[pos[ok]])
    cnt = x.groupby(["day", "ticker"]).size().unstack().reindex(index=dates, columns=tickers).fillna(0.0)
    tone = x.groupby(["day", "ticker"])["tone"].sum().unstack().reindex(index=dates, columns=tickers).fillna(0.0)
    # signals are decided at the close of day t; articles up to that close count
    c5 = cnt.rolling(5).sum()
    base = cnt.rolling(60).sum().shift(5) / 12
    has_news = c5 > 0
    rev5 = -ctx.log_ret.rolling(5, min_periods=4).sum()
    covered = cnt.rolling(250, min_periods=60).sum() > 0                    # names the feed covers at all
    sig = {
        "news_volume": -(np.log1p(c5) - np.log1p(base)).where(covered),
        "news_tone": tone.rolling(3).sum().where(covered),
        "no_news_rev": rev5.where(covered & ~has_news),
        "news_mom": (-rev5).where(covered & has_news),
    }
    LOG.info("news signals: %d articles mapped to the universe", len(x))
    return sig


def load_alt(md, ctx, data_dir: str = "data") -> tuple[dict, dict]:
    """Return (signals, families) for whichever alternative datasets are present."""
    sigs, fam = {}, {}
    fpath = Path(data_dir) / "fundamentals" / "fundamentals.parquet"
    if fpath.exists():
        s = fundamental_signals(md, ctx, load_fundamentals(fpath.parent))
        sigs.update(s)
        fam.update({k: "fundamental" for k in s})
    npath = Path(data_dir) / "news"
    if any(npath.glob("news_*.parquet")):
        s = news_signals(md, ctx, load_news(npath))
        sigs.update(s)
        fam.update({k: "news" for k in s})
    return sigs, fam
