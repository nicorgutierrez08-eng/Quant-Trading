"""The earnings-premium strategy runs on filing dates and only uses filings already made."""
import numpy as np
import pandas as pd

from qtrade.features.context import FeatureContext
from qtrade.research.strategies import earnings_premium


def test_earnings_premium_runs(market, cfg):
    md, _ = market
    ctx = FeatureContext(md, cfg)
    rows = [{"ticker": t, "form": "10-Q", "filed": d}
            for t in md.tickers[:20] for d in pd.date_range(md.dates[0], md.dates[-1], freq="91D")]
    r = earnings_premium(md, ctx, pd.DataFrame(rows))
    assert len(r) == len(md.dates) and np.isfinite(r).all() and r.abs().sum() > 0
