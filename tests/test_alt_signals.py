"""Fundamental and news signals: run end to end, and never use data before it was public."""
import numpy as np
import pandas as pd

from qtrade.features.context import FeatureContext
from qtrade.research.alt_signals import fundamental_signals, news_signals


def _facts(md):
    rows = []
    rng = np.random.default_rng(0)
    for t in md.tickers[:6]:
        for q in range(30):
            end = pd.Timestamp("2006-03-31") + pd.offsets.QuarterEnd(q)
            filed = end + pd.Timedelta(days=35)
            common = {"ticker": t, "cik": 1, "unit": "USD", "fy": 2006, "fp": "Q1", "form": "10-Q", "accn": "x",
                      "frame": None, "end": end, "filed": filed}
            rows.append(common | {"tag": "EarningsPerShareDiluted", "value": 1 + q * 0.05 + rng.normal(0, .1),
                                  "start": end - pd.Timedelta(days=90)})
            rows.append(common | {"tag": "Assets", "value": 1e9 * (1 + q * 0.02), "start": pd.NaT})
            rows.append(common | {"tag": "StockholdersEquity", "value": 4e8, "start": pd.NaT})
            rows.append(common | {"tag": "dei:EntityCommonStockSharesOutstanding", "value": 1e7, "start": pd.NaT})
            rows.append(common | {"tag": "NetIncomeLoss", "value": 5e7, "start": end - pd.Timedelta(days=364)})
    return pd.DataFrame(rows)


def test_fundamental_signals_respect_filing_dates(market):
    md, _ = market
    ctx = FeatureContext(md)
    facts = _facts(md)
    sig = fundamental_signals(md, ctx, facts)
    assert {"sue", "ear", "earnings_yield", "book_to_market", "asset_growth"} <= set(sig)
    t = md.tickers[0]
    first_filed = facts[facts["ticker"] == t]["filed"].min()
    before = sig["book_to_market"].loc[:first_filed, t]
    assert before.isna().all()                      # nothing known before the first filing
    assert sig["sue"][t].notna().any()


def test_news_signals(market):
    md, _ = market
    ctx = FeatureContext(md)
    t = md.tickers[0]
    d = md.dates[300]
    news = pd.DataFrame({
        "created_at": [pd.Timestamp(f"{d.date()} 15:00", tz="America/New_York").tz_convert("UTC"),
                       pd.Timestamp(f"{d.date()} 17:00", tz="America/New_York").tz_convert("UTC")],
        "headline": ["Company beats estimates, raises guidance", "Analyst downgrade after probe"],
        "symbols": [t, t]})
    sig = news_signals(md, ctx, news)
    tone = sig["news_tone"][t]
    assert tone.loc[d] == 1.0                          # the 15:00 article counts at that day's close
    assert tone.loc[md.dates[301]] == 0.0              # the 17:00 one only from the next day (1 - 1)
