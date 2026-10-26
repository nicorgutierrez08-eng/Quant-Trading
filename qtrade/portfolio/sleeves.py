"""ETF sleeves: the strategies that held up in both 2006-2014 and 2015-2026.

Each sleeve turns ETF closes into target weights decided at the close of day t
(traded at the next open). They are the same rules as the research strategy
zoo (``qtrade.research.strategies``), rewritten to return positions instead of
returns so they can be traded; ``tests/test_sleeves.py`` checks the two agree.

Sleeves (2015-2026 net Sharpe in the strategy zoo):

  spy_vol_managed    SPY scaled by 1 / GJR-GARCH volatility forecast   0.84
  cross_asset_mom    top 3 of 8 asset classes by 6-month return        0.78
  spy_ma200          SPY above its 200-day average                     0.79
  risk_parity        8 asset classes weighted by 1 / volatility        0.70
  spy_tsmom_12m      SPY when its 12-month return is positive          0.69
  broad_trend_12m    12-month trend over ~30 ETFs, 10% vol each        0.54
  spy_turn_of_month  SPY over the turn of the month                    0.48
  multi_asset_trend  12-month trend over 8 asset classes               0.42

They are combined with weights 1 / trailing volatility of each sleeve's own
returns (walk-forward), then scaled to a target volatility.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ASSETS = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ"]
BROAD = ["USO", "UNG", "DBA", "DBB", "SLV", "GLD", "UUP", "FXE", "FXY", "FXA", "SHY", "IEF", "TLT", "TIP",
         "LQD", "HYG", "EWJ", "EWG", "EWU", "FXI", "EWZ", "EWC", "EWA", "EWY", "EWT", "SPY", "QQQ", "IWM",
         "VNQ", "EEM"]
ETF_UNIVERSE = list(dict.fromkeys(ASSETS + BROAD))
ETF_COST = 1e-4
DEFAULT_SLEEVES = ["spy_vol_managed", "cross_asset_mom", "spy_ma200", "risk_parity", "spy_tsmom_12m",
                   "broad_trend_12m", "spy_turn_of_month", "multi_asset_trend"]


def _month_ends(idx: pd.DatetimeIndex) -> pd.Series:
    s = pd.Series(idx, index=idx)
    return s.groupby([idx.year, idx.month]).transform("max") == s


def _spy(close: pd.DataFrame, w: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"SPY": w}, index=close.index)


def spy_ma200(close: pd.DataFrame) -> pd.DataFrame:
    spy = close["SPY"]
    return _spy(close, (spy > spy.rolling(200).mean()).astype(float))


def spy_tsmom_12m(close: pd.DataFrame) -> pd.DataFrame:
    spy = close["SPY"]
    return _spy(close, (spy / spy.shift(252) - 1 > 0).astype(float))


def spy_vol_managed(close: pd.DataFrame, fit_end: str | None = None) -> pd.DataFrame:
    """Leverage = median variance / forecast variance for the next day, square-rooted, capped at 2.

    ``fit_end``: estimate the GARCH parameters on returns before this date only
    (the research used 2015-01-01); by default all but the last year."""
    from ..research.garch import fit_garch, garch_filter

    r = close["SPY"].pct_change(fill_method=None)
    x = r.to_numpy()
    end = pd.Timestamp(fit_end) if fit_end else r.index[-1] - pd.Timedelta(days=365)
    train = np.asarray(r.index < end) & np.isfinite(x)
    p = fit_garch(np.where(train, x, np.nan)[: np.flatnonzero(train)[-1] + 1], gjr=True)
    # one extra step: the variance forecast for the day after each close
    s2f = garch_filter(np.append(x, np.nan), p["w"], p["a"], p["b"], p["g"], p["s0"])
    lev = np.clip(np.sqrt(np.nanmedian(s2f[: len(x)][train])) / np.sqrt(s2f[1:]), 0, 2)
    return _spy(close, pd.Series(lev, index=r.index))


def spy_turn_of_month(close: pd.DataFrame) -> pd.DataFrame:
    """Hold SPY over the last trading day of a month and the first three of the next.

    The calendar is known ahead, so the weight at close t is the holding for day
    t+2 (the convention every sleeve shares: decided at t, entered at the open of
    t+1, earning day t+2's close-to-close return in the backtest)."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    from pandas.tseries.offsets import CustomBusinessDay

    cbd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    idx = close.index
    ext = idx.append(pd.DatetimeIndex([idx[-1] + k * cbd for k in (1, 2, 3)]))
    month = np.asarray(ext.month)
    is_last = np.append(month[1:] != month[:-1], False)
    nth = pd.Series(1, index=ext).groupby([ext.year, ext.month]).cumsum().to_numpy()
    tom = np.append(False, is_last[:-1]) | (nth <= 3)
    hold = pd.Series(tom.astype(float), index=ext).shift(-2).reindex(idx)
    return _spy(close, hold)


def risk_parity(close: pd.DataFrame) -> pd.DataFrame:
    c = close[ASSETS]
    vol = c.pct_change(fill_method=None).rolling(63, min_periods=40).std() * np.sqrt(252)
    return (1 / vol).div((1 / vol).sum(axis=1), axis=0)


def cross_asset_mom(close: pd.DataFrame) -> pd.DataFrame:
    c = close[ASSETS]
    top = (c / c.shift(126) - 1).rank(axis=1, ascending=False) <= 3
    return (top.astype(float) / 3).where(_month_ends(c.index)).ffill()


def multi_asset_trend(close: pd.DataFrame) -> pd.DataFrame:
    c = close[ASSETS]
    vol = c.pct_change(fill_method=None).rolling(63, min_periods=40).std() * np.sqrt(252)
    return (np.sign(c / c.shift(252) - 1) * 0.10 / vol).clip(-2, 2) / len(ASSETS)


def broad_trend_12m(close: pd.DataFrame) -> pd.DataFrame:
    c = close[[t for t in BROAD if t in close.columns]]
    vol = c.pct_change(fill_method=None).rolling(63, min_periods=40).std() * np.sqrt(252)
    sign = np.sign(c / c.shift(252) - 1)
    return (sign * 0.10 / vol).clip(-2, 2).div(c.notna().sum(axis=1).clip(lower=1), axis=0)


SLEEVES = {f.__name__: f for f in (spy_vol_managed, cross_asset_mom, spy_ma200, risk_parity, spy_tsmom_12m,
                                   broad_trend_12m, spy_turn_of_month, multi_asset_trend)}


def sleeve_returns(w: pd.DataFrame, close: pd.DataFrame, cost: float = ETF_COST) -> pd.Series:
    """Daily net return of holding ``w`` (decided at the close of t-2) over day t, as in the research."""
    r = close[w.columns].pct_change(fill_method=None).fillna(0)
    p = w.shift(2)
    return ((p * r).sum(axis=1) - p.diff().abs().sum(axis=1).fillna(0) * cost).fillna(0.0)


def combine(close: pd.DataFrame, sleeves: list[str] | None = None, target_vol: float = 0.10,
            vol_window: int = 756, max_gross: float = 1.5, fit_end: str | None = None) -> dict:
    """Sleeves weighted by 1 / trailing volatility of their own returns, scaled to ``target_vol``
    with the trailing year's realised volatility of the blend. Everything uses data up to the
    close the weights are decided at."""
    names = sleeves or DEFAULT_SLEEVES
    W = {}
    for n in names:
        W[n] = SLEEVES[n](close, fit_end) if n == "spy_vol_managed" else SLEEVES[n](close)
    R = pd.DataFrame({n: sleeve_returns(w, close) for n, w in W.items()})
    vol = R.rolling(vol_window, min_periods=126).std()
    sw = (1 / vol).div((1 / vol).sum(axis=1), axis=0)            # sleeve weights at each close
    blend = (sw.shift(2) * R).sum(axis=1)                       # the blend as it would have been held
    real = blend.rolling(252, min_periods=126).std() * np.sqrt(252)
    lev = (target_vol / real).clip(0, 3).fillna(0)
    cols = sorted({c for w in W.values() for c in w.columns})
    book = pd.DataFrame(0.0, index=close.index, columns=cols)
    for n, w in W.items():
        book = book.add(w.reindex(columns=cols).fillna(0).mul(sw[n].fillna(0), axis=0), fill_value=0)
    book = book.mul(lev, axis=0)
    gross = book.abs().sum(axis=1)
    book = book.mul((max_gross / gross).clip(upper=1).fillna(0), axis=0)
    return {"weights": book, "sleeve_weights": sw, "sleeve_returns": R, "returns": sleeve_returns(book, close)}


def needed_tickers(sleeves: list[str]) -> list[str]:
    need = []
    for n in sleeves:
        need += BROAD if n == "broad_trend_12m" else ASSETS if n in ("cross_asset_mom", "risk_parity",
                                                                      "multi_asset_trend") else ["SPY"]
    return list(dict.fromkeys(need))


def etf_targets(cfg, end=None) -> tuple[dict[str, float], dict[str, float], pd.Timestamp, pd.DataFrame]:
    """Today's ETF book: weights (as a fraction of the ETF capital), as-traded prices, the
    date of the last close used, and the sleeve weights over the last days (for the log)."""
    from ..data import get_market_data

    m = cfg.multi
    md = get_market_data(needed_tickers(m.sleeves), m.history_start, None, cfg.data.cache_dir + "/live_etf",
                         cfg.data.batch_size)
    if end is not None:
        md = md.subset(end=end)
    out = combine(md.close, m.sleeves, m.target_vol, m.vol_window, m.max_gross)
    w = out["weights"].iloc[-1]
    prices = {t: float(p) for t, p in md.traded_close.iloc[-1].items() if np.isfinite(p)}
    return ({t: float(v) for t, v in w.items() if abs(v) > 1e-6}, prices, md.dates[-1],
            out["sleeve_weights"].tail(5))
