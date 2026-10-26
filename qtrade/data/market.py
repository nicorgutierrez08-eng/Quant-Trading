"""Container for the OHLCV panels everything else is computed from."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FIELDS = ("open", "high", "low", "close", "volume")
RAW_FIELDS = ("raw_close", "raw_volume")


def bad_prints(open_: pd.DataFrame, close: pd.DataFrame, jump: float = 0.4,
               net: float = 0.1) -> pd.DataFrame:
    """Bars that are almost certainly vendor errors: the price jumps by more than
    ``jump`` (in log terms, ~50%) and comes straight back, so the net move is
    under ``net``. Checked on consecutive closes and on open vs. surrounding
    closes. A real 50% gap that sticks is kept; a one-day 30x spike is not."""
    with np.errstate(divide="ignore", invalid="ignore"):
        lc = np.log(close.where(close > 0))
        lo = np.log(open_.where(open_ > 0))
    r1, r2 = lc.diff(), lc.diff().shift(-1)
    close_spike = (r1.abs() > jump) & (r2.abs() > jump) & (r1 * r2 < 0) & ((r1 + r2).abs() < net)
    a, b = lo - lc.shift(1), lc - lo
    open_spike = (a.abs() > jump) & (b.abs() > jump) & (a * b < 0) & ((a + b).abs() < net)
    return (close_spike | open_spike).fillna(False)


@dataclass
class MarketData:
    """Split- and dividend-adjusted OHLCV, plus (optionally) the close and volume
    as they actually printed that day.

    Adjusted prices give correct returns, but their *level* on day t depends on
    splits and dividends paid after t: a stock that later splits 40-for-1 shows
    a 2005 "price" of $0.50. Anything that judges a price or a dollar volume -
    the $5 price floor, liquidity filters, cost tiers, whole-share rounding -
    must use the as-traded values, or the backtest peeks at future corporate
    actions. Without raw panels (synthetic data, old caches) the adjusted ones
    stand in.
    """

    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame
    raw_close: pd.DataFrame | None = None
    raw_volume: pd.DataFrame | None = None

    def __post_init__(self) -> None:
        idx = self.close.index
        cols = self.close.columns
        for f in FIELDS:
            df = getattr(self, f).reindex(index=idx, columns=cols).astype("float64")
            setattr(self, f, df)
        for f in RAW_FIELDS:
            if getattr(self, f) is not None:
                setattr(self, f, getattr(self, f).reindex(index=idx, columns=cols).astype("float64"))
        # a bar is valid only when open and close both exist and are positive,
        # and is not an isolated bad print
        bad = ~((self.close > 0) & (self.open > 0)) | bad_prints(self.open, self.close)
        for f in ("open", "high", "low", "close"):
            setattr(self, f, getattr(self, f).mask(bad))
        if self.raw_close is not None:
            self.raw_close = self.raw_close.mask(bad)
        # repair impossible highs/lows that occasionally appear in vendor data
        o, c = self.open.values, self.close.values
        self.high = pd.DataFrame(np.fmax(np.fmax(self.high.values, o), c), index=idx, columns=cols)
        self.low = pd.DataFrame(np.fmin(np.fmin(self.low.values, o), c), index=idx, columns=cols)

    # -- convenience -----------------------------------------------------
    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.close.index

    @property
    def tickers(self) -> list[str]:
        return list(self.close.columns)

    @property
    def has_raw(self) -> bool:
        return self.raw_close is not None and self.raw_volume is not None

    @property
    def traded_close(self) -> pd.DataFrame:
        """The close as it printed on each day (adjusted close if unknown)."""
        return self.raw_close if self.raw_close is not None else self.close

    @property
    def dollar_volume(self) -> pd.DataFrame:
        """Dollars that changed hands each day. Splits cancel in price x volume,
        but dividend adjustment does not, so this needs the raw panels."""
        if self.has_raw:
            return self.raw_close * self.raw_volume
        return self.close * self.volume

    def subset(self, tickers=None, start=None, end=None) -> "MarketData":
        tickers = list(tickers) if tickers is not None else self.tickers
        sl = slice(start, end)
        panels = {f: getattr(self, f).loc[sl, tickers] for f in FIELDS}
        if self.has_raw:
            panels.update({f: getattr(self, f).loc[sl, tickers] for f in RAW_FIELDS})
        return MarketData(**panels)

    def first_valid_dates(self) -> pd.Series:
        return self.close.apply(lambda s: s.first_valid_index())
