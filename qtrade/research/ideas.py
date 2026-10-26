"""The ideas lab: new candidate signals, tested as they are written.

Each idea is a function ``(md, ctx, facts) -> panel`` registered with ``@idea``
under a theme and the wave it was added in. ``python -m qtrade.research.zoo
--group ideas`` computes every idea, normalises it like any other signal, and
scores its IC at the job's horizon in 2006-2014 and 2015-2026 plus the
break-even cost of trading it; the results land in best_correlations.csv.
Positive values should mean "expected to outperform" where the literature has
a view; the sign actually found is what the report shows.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

IDEAS: dict[str, tuple[str, int, Callable]] = {}


def idea(theme: str, wave: int):
    def wrap(fn):
        IDEAS[fn.__name__] = (theme, wave, fn)
        return fn
    return wrap


def _pit(facts, tag, md, annual=False):
    from ..data.fundamentals import point_in_time

    if facts is None:
        return None
    return point_in_time(facts, tag, md.dates, md.tickers, annual).shift(1)   # usable the day after filing


# =============================================================================
# wave 1: momentum variants
# =============================================================================
@idea("momentum", 1)
def sharpe_mom(md, ctx, facts):
    """12-1 month return divided by its volatility: momentum per unit of risk."""
    r = ctx.log_ret
    return (r.rolling(231, min_periods=200).sum().shift(21)) / (r.rolling(252, min_periods=200).std() * np.sqrt(252))


@idea("momentum", 1)
def frog_in_pan(md, ctx, facts):
    """Da-Gurun-Warachka: momentum built from many small moves persists more than
    momentum from a few jumps. sign(12-1 return) x (share of down days - share of up days)."""
    r = ctx.ret.shift(21)
    past = r.rolling(231, min_periods=200)
    pos = (r > 0).rolling(231, min_periods=200).mean()
    neg = (r < 0).rolling(231, min_periods=200).mean()
    return -np.sign(past.sum()) * (neg - pos)


@idea("momentum", 1)
def mom_consistency(md, ctx, facts):
    """Share of the last 12 months with a positive return."""
    m = ctx.log_ret.rolling(21).sum()
    months = pd.concat([m.shift(21 * k) > 0 for k in range(1, 13)], keys=range(12))
    return months.groupby(level=1).mean().reindex(m.index)


@idea("momentum", 1)
def cluster_rel_mom(md, ctx, facts):
    """6-1 month return relative to the stock's k-means peer group."""
    r6 = ctx.log_ret.rolling(105, min_periods=90).sum().shift(21)
    cl = ctx.clusters
    out = r6.copy() * np.nan
    for c in np.unique(cl.stack().dropna()):
        m = cl == c
        g = r6.where(m)
        out = out.where(~m, g.sub(g.mean(axis=1), axis=0))
    return out


@idea("momentum", 1)
def stock_tsmom(md, ctx, facts):
    """Each stock's own trend: sign of its 12-month return, scaled by inverse vol."""
    r = ctx.log_ret
    return np.sign(r.rolling(252, min_periods=200).sum()) / (r.rolling(63, min_periods=40).std() + 1e-4)


# =============================================================================
# wave 1: trend shape
# =============================================================================
@idea("trend", 1)
def ma50_200(md, ctx, facts):
    """50-day vs 200-day moving average (golden/death cross distance)."""
    p = md.close
    return np.log(p.rolling(50, min_periods=40).mean() / p.rolling(200, min_periods=150).mean())


@idea("trend", 1)
def macd(md, ctx, facts):
    """MACD (12/26-day EMA gap) relative to price."""
    p = md.close
    return (p.ewm(span=12, min_periods=26).mean() - p.ewm(span=26, min_periods=26).mean()) / p


@idea("trend", 1)
def dist_from_high(md, ctx, facts):
    """Drawdown from the 252-day high (0 at the high)."""
    return md.close / md.close.rolling(252, min_periods=200).max() - 1


# =============================================================================
# wave 1: volatility and higher moments
# =============================================================================
@idea("volatility", 1)
def vol_change(md, ctx, facts):
    """Minus log(21-day vol / 252-day vol): falling volatility."""
    r = ctx.ret
    return -np.log(r.rolling(21, min_periods=15).std() / r.rolling(252, min_periods=200).std())


@idea("volatility", 1)
def idio_skew(md, ctx, facts):
    """Minus the skewness of residual returns over 126 days (lottery stocks underperform)."""
    return -ctx.resid.rolling(126, min_periods=90).skew()


@idea("volatility", 1)
def coskew(md, ctx, facts):
    """Minus co-skewness with the market: stocks that crash with the market should pay more."""
    r = ctx.ret
    m = ctx.market_ret
    md_ = m - m.rolling(252, min_periods=200).mean()
    num = (r.sub(r.rolling(252, min_periods=200).mean())).mul(md_ ** 2, axis=0).rolling(252, min_periods=200).mean()
    den = r.rolling(252, min_periods=200).std().mul((md_ ** 2).rolling(252, min_periods=200).mean(), axis=0)
    return num.div(den.where(den > 0))


# =============================================================================
# wave 1: liquidity
# =============================================================================
@idea("liquidity", 1)
def amihud_change(md, ctx, facts):
    """Minus the change in illiquidity (last month vs last year)."""
    x = (ctx.ret.abs() / ctx.dollar_volume.where(ctx.dollar_volume > 0))
    return -np.log(x.rolling(21, min_periods=15).mean() / x.rolling(252, min_periods=200).mean())


@idea("liquidity", 1)
def obv_divergence(md, ctx, facts):
    """On-balance volume trend minus price trend over 63 days (volume leading price)."""
    v = np.sign(ctx.ret) * md.volume
    obv = v.rolling(63, min_periods=40).sum() / md.volume.rolling(63, min_periods=40).sum()
    return obv - np.tanh(ctx.log_ret.rolling(63, min_periods=40).sum() * 5)


# =============================================================================
# wave 1: fundamentals - growth, profitability, financing
# =============================================================================
@idea("fundamental", 1)
def earnings_growth(md, ctx, facts):
    ni = _pit(facts, "NetIncomeLoss", md, annual=True)
    if ni is None:
        return None
    prev = ni.shift(252)
    return (ni - prev) / prev.abs().where(prev.abs() > 0)


@idea("fundamental", 1)
def revenue_growth(md, ctx, facts):
    rev = _pit(facts, "Revenues", md, annual=True)
    if rev is None:
        return None
    rev = rev.fillna(_pit(facts, "RevenueFromContractWithCustomerExcludingAssessedTax", md, annual=True))
    return np.log(rev / rev.shift(252))


@idea("fundamental", 1)
def roe(md, ctx, facts):
    ni, eq = _pit(facts, "NetIncomeLoss", md, annual=True), _pit(facts, "StockholdersEquity", md)
    if ni is None:
        return None
    return (ni / eq).where(eq > 0)


@idea("fundamental", 1)
def low_leverage(md, ctx, facts):
    li, a = _pit(facts, "Liabilities", md), _pit(facts, "Assets", md)
    if li is None:
        return None
    return -(li / a)


@idea("fundamental", 1)
def net_buyback(md, ctx, facts):
    """Minus the 1-year change in shares outstanding (issuers underperform, buyers outperform)."""
    sh = _pit(facts, "dei:EntityCommonStockSharesOutstanding", md)
    if sh is None:
        return None
    return -np.log(sh / sh.shift(252))


@idea("fundamental", 1)
def rd_intensity(md, ctx, facts):
    rd, a = _pit(facts, "ResearchAndDevelopmentExpense", md, annual=True), _pit(facts, "Assets", md)
    if rd is None:
        return None
    return rd / a


@idea("fundamental", 1)
def cash_ratio(md, ctx, facts):
    c, a = _pit(facts, "CashAndCashEquivalentsAtCarryingValue", md), _pit(facts, "Assets", md)
    if c is None:
        return None
    return c / a


def compute_ideas(md, ctx, data_dir: str = "data", waves: set[int] | None = None) -> tuple[dict, dict]:
    """All ideas as normalised panels, plus their themes."""
    from pathlib import Path

    from ..signals import normalize_signal
    from ..utils import LOG

    facts = None
    fpath = Path(data_dir) / "fundamentals" / "fundamentals.parquet"
    if fpath.exists():
        from ..data.fundamentals import load_fundamentals

        facts = load_fundamentals(fpath.parent)
    out, themes = {}, {}
    for name, (theme, wave, fn) in IDEAS.items():
        if waves and wave not in waves:
            continue
        try:
            raw = fn(md, ctx, facts)
        except Exception as exc:
            LOG.warning("idea %s failed: %s", name, exc)
            continue
        if raw is None:
            continue
        out[name] = normalize_signal(raw, ctx.tradable)
        themes[name] = f"idea:{theme} (wave {wave})"
    return out, themes


# =============================================================================
# wave 2: public data (short volume, insider trades, filing timing)
# =============================================================================
def _root(ctx):
    return ctx.cfg.data.cache_dir


@idea("public data", 2)
def short_vol_abn(md, ctx, facts):
    """Minus abnormal off-exchange short volume ratio (5 days vs 60): short sellers are informed."""
    from ..data.public import load_short_volume

    sv = load_short_volume(md.dates, md.tickers, _root(ctx))
    if sv.notna().sum().sum() == 0:
        return None
    return -(sv.rolling(5, min_periods=3).mean() - sv.rolling(60, min_periods=30).mean())


@idea("public data", 2)
def short_vol_level(md, ctx, facts):
    """Minus the 20-day average short volume ratio."""
    from ..data.public import load_short_volume

    sv = load_short_volume(md.dates, md.tickers, _root(ctx))
    if sv.notna().sum().sum() == 0:
        return None
    return -sv.rolling(20, min_periods=10).mean()


def _insider_panels(md, ctx):
    from ..data.public import load_insider

    ins = load_insider(_root(ctx))
    if ins.empty:
        return None, None
    ins = ins[ins["ticker"].isin(set(md.tickers))]
    # usable the trading day after the filing
    pos = md.dates.searchsorted(ins["filed"].to_numpy(), side="right")
    ok = pos < len(md.dates)
    ins = ins[ok].assign(day=md.dates[pos[ok]])
    buy_val = ins[ins["value"] > 0].groupby(["day", "ticker"])["value"].sum().unstack()
    sell_val = -ins[ins["value"] < 0].groupby(["day", "ticker"])["value"].sum().unstack()
    buyers = ins[ins["value"] > 0].groupby(["day", "ticker"])["insider"].nunique().unstack()
    f = lambda x: x.reindex(index=md.dates, columns=md.tickers).fillna(0.0)  # noqa: E731
    return (f(buy_val), f(sell_val)), f(buyers)


@idea("public data", 2)
def insider_net_buy(md, ctx, facts):
    """Insider open-market buys minus sells over 90 days, scaled by dollar volume."""
    vals, _ = _insider_panels(md, ctx)
    if vals is None:
        return None
    b, s = vals
    net = (b - s).rolling(63, min_periods=1).sum()
    return net / (ctx.adv * 63)


@idea("public data", 2)
def insider_cluster_buy(md, ctx, facts):
    """Number of distinct insiders buying over 90 days (cluster buying)."""
    _, buyers = _insider_panels(md, ctx)
    if buyers is None:
        return None
    return buyers.rolling(63, min_periods=1).sum()


@idea("public data", 2)
def filing_delay(md, ctx, facts):
    """Minus how late the latest 10-Q/10-K came vs. the company's usual delay (late filers underperform)."""
    if facts is None:
        return None
    f = facts[facts["form"].isin(["10-Q", "10-K"]) & facts["filed"].notna() & facts["end"].notna()]
    f = f.drop_duplicates(["ticker", "accn"])[["ticker", "end", "filed"]].copy()
    f["delay"] = (f["filed"] - f["end"]).dt.days
    f = f[(f["delay"] > 0) & (f["delay"] < 200)].sort_values(["ticker", "filed"])
    f["usual"] = f.groupby("ticker")["delay"].transform(lambda x: x.shift(1).rolling(8, min_periods=3).median())
    f["late"] = f["delay"] - f["usual"]
    out = pd.DataFrame(np.nan, index=md.dates, columns=md.tickers)
    for t, g in f.dropna(subset=["late"]).groupby("ticker"):
        if t in out.columns:
            s = pd.Series(g["late"].to_numpy(), index=g["filed"] + pd.Timedelta(days=1))
            out[t] = s[~s.index.duplicated(keep="last")].reindex(md.dates, method="ffill", limit=63).to_numpy()
    return -out


# =============================================================================
# wave 2: price-based
# =============================================================================
@idea("network", 2)
def network_mom(md, ctx, facts):
    """Correlation-weighted average of other stocks' last-month return (the stock's
    most similar peers by 1-year return correlation; information diffuses slowly)."""
    r = ctx.ret
    r21 = ctx.log_ret.rolling(21, min_periods=15).sum()
    out = pd.DataFrame(np.nan, index=r.index, columns=r.columns)
    month_ends = r.index[pd.Series(r.index.month, index=r.index).diff().fillna(1).ne(0).to_numpy()]
    for i, d in enumerate(month_ends):
        hist = r.loc[:d].iloc[-252:]
        ok = hist.notna().mean() > 0.9
        if ok.sum() < 50:
            continue
        c = np.nan_to_num(np.corrcoef(hist.loc[:, ok].fillna(0).to_numpy().T))
        np.fill_diagonal(c, 0)
        c[c < 0.3] = 0                                          # keep real neighbours only
        w = c / (c.sum(axis=1, keepdims=True) + 1e-12)
        nxt = month_ends[i + 1] if i + 1 < len(month_ends) else r.index[-1] + pd.Timedelta(days=1)
        block = r21.loc[(r21.index > d) & (r21.index <= nxt), ok]
        out.loc[block.index, block.columns] = np.nan_to_num(block.to_numpy()) @ w.T
    return out - r21                                             # peers up, stock not (yet)


@idea("seasonality", 2)
def calendar_month_seasonality(md, ctx, facts):
    """The stock's average return in this calendar month over the past 1-10 years (Heston-Sadka)."""
    m = ctx.log_ret.resample("ME").sum()
    seas = sum(m.shift(12 * k) for k in range(1, 11)) / 10
    seas = seas.shift(-1)                                        # next month's seasonal average, known now
    return seas.reindex(ctx.ret.index, method="ffill")


@idea("momentum", 2)
def overnight_momentum(md, ctx, facts):
    """Average overnight return over a year: overnight returns persist (Lou-Polk-Skouras)."""
    return ctx.overnight.rolling(252, min_periods=200).mean()


@idea("trend", 2)
def near_52w_low(md, ctx, facts):
    """Minus distance above the 52-week low (stocks near their lows keep falling?)."""
    return -(md.close / md.close.rolling(252, min_periods=200).min() - 1)


@idea("price level", 2)
def low_nominal_price(md, ctx, facts):
    """Minus log of the as-traded share price (low-priced stocks behave differently)."""
    return -np.log(md.traded_close)


@idea("volume", 2)
def volume_spike_continuation(md, ctx, facts):
    """Last 5 days' return when volume spiked (> 2x normal): high-volume moves continue."""
    spike = md.volume.rolling(5).mean() / md.volume.rolling(63).mean() > 2
    return ctx.log_ret.rolling(5).sum().where(spike, 0.0)


@idea("fundamental", 2)
def sue_revision(md, ctx, facts):
    """Change in earnings surprise between the last two quarters (improving surprises)."""
    if facts is None:
        return None
    from .alt_signals import fundamental_signals

    sue = fundamental_signals(md, ctx, facts).get("sue")
    if sue is None:
        return None
    return sue - sue.shift(63)


# =============================================================================
# wave 3: from 5-minute bars (daily statistics built by research/intraday_stats.py)
# =============================================================================
def _intra(md, ctx, name):
    from .intraday_stats import load

    st = load(_root(ctx))
    if st is None or name not in st:
        return None
    return st[name].reindex(index=md.dates, columns=md.tickers)


@idea("intraday", 3)
def realized_skew(md, ctx, facts):
    """Minus the average realized skewness of 5-minute returns over 5 days (lottery-like intraday moves)."""
    x = _intra(md, ctx, "rskew")
    return None if x is None else -x.rolling(5, min_periods=3).mean()


@idea("intraday", 3)
def realized_kurtosis(md, ctx, facts):
    x = _intra(md, ctx, "rkurt")
    return None if x is None else -x.rolling(21, min_periods=10).mean()


@idea("intraday", 3)
def jump_share(md, ctx, facts):
    """Minus the share of variance from jumps over a month (jumpy stocks underperform?)."""
    x = _intra(md, ctx, "jump_share")
    return None if x is None else -x.rolling(21, min_periods=10).mean()


@idea("intraday", 3)
def last_half_hour(md, ctx, facts):
    """Yesterday's last-half-hour return relative to the market (late-day informed trading continues)."""
    x = _intra(md, ctx, "last30")
    return None if x is None else x.sub(x.mean(axis=1), axis=0)


@idea("intraday", 3)
def first_half_hour_rev(md, ctx, facts):
    """Minus today's first-half-hour return (opening overreaction)."""
    x = _intra(md, ctx, "first30")
    return None if x is None else -x.sub(x.mean(axis=1), axis=0)


@idea("intraday", 3)
def realized_vol_ratio(md, ctx, facts):
    """Minus intraday realized vol over the last 5 days vs. the last 63 (vol spikes mean-revert)."""
    x = _intra(md, ctx, "rv")
    return None if x is None else -np.log(x.rolling(5, min_periods=3).mean() / x.rolling(63, min_periods=40).mean())


# =============================================================================
# wave 4: combinations that stuck in the pair study, as single signals
# =============================================================================
def _z(ctx, raw):
    from ..utils import cs_zscore

    return cs_zscore(raw.where(ctx.tradable)).clip(-4, 4)


def _reg(ctx, name):
    from ..signals import REGISTRY

    return _z(ctx, REGISTRY[name].fn(ctx))


@idea("combination", 4)
def mom_plus_52w_high(md, ctx, facts):
    """12-1 momentum + nearness to the 52-week high (the strongest sticky pair)."""
    return _reg(ctx, "mom_12_1") + _reg(ctx, "high_52w")


@idea("combination", 4)
def rev5_plus_resid_mom(md, ctx, facts):
    """Short-term reversal among medium-term (residual) winners."""
    return _reg(ctx, "rev_5d") + _reg(ctx, "resid_mom")


@idea("combination", 4)
def rev21_plus_resid_mom(md, ctx, facts):
    return _reg(ctx, "rev_21d") + _reg(ctx, "resid_mom")


@idea("combination", 4)
def bollinger_plus_resid_mom(md, ctx, facts):
    return _reg(ctx, "bollinger_z") + _reg(ctx, "resid_mom")


@idea("combination", 4)
def cluster_mom_plus_peer_gap(md, ctx, facts):
    return _reg(ctx, "cluster_mom") + _reg(ctx, "peer_gap")


@idea("combination", 4)
def momentum_trio(md, ctx, facts):
    """Momentum + 52-week high + volatility-scaled momentum + overnight momentum."""
    return (_reg(ctx, "mom_12_1") + _reg(ctx, "high_52w") + _z(ctx, sharpe_mom(md, ctx, facts))
            + _z(ctx, overnight_momentum(md, ctx, facts)))


@idea("combination", 4)
def reversal_in_winners(md, ctx, facts):
    """Product: 5-day reversal, only counted for stocks with positive 12-1 momentum."""
    mom = _reg(ctx, "mom_12_1")
    return _reg(ctx, "rev_5d").where(mom > 0, 0.0)


# wave 5: news events found in the event study (headline types; news since 2015)
_EVENT_CACHE: dict = {}


def _event_counts(md, ctx, kind: str) -> pd.DataFrame | None:
    """Headlines of one event type per (day, stock), dated the day the news is
    known at the close: an article before the open counts on that day, one
    during or after the session on the next trading day."""
    from pathlib import Path

    from .events import EVENT_RULES, _usable_day

    key = (id(md), kind)
    if key in _EVENT_CACHE:
        return _EVENT_CACHE[key]
    npath = Path(_root(ctx)) / "news"
    if not any(npath.glob("news_*.parquet")):
        return None
    if (id(md), "_x") not in _EVENT_CACHE:
        from ..data.news import load_news

        x = load_news(npath)[["created_at", "headline", "symbols"]]
        x = x.assign(ticker=x["symbols"].str.split(",")).explode("ticker")
        tick = {t: i for i, t in enumerate(md.tickers)}
        x = x[x["ticker"].isin(tick)]
        x = x.assign(row=_usable_day(md.dates, x["created_at"]), col=x["ticker"].map(tick),
                     hl=x["headline"].fillna("").str.lower())
        x = x[x["row"] < len(md.dates)]
        _EVENT_CACHE[(id(md), "_x")] = x
    x = _EVENT_CACHE[(id(md), "_x")]
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ev = x[x["hl"].str.contains(EVENT_RULES[kind], regex=True)].drop_duplicates(["row", "col"])
    a = np.zeros((len(md.dates), len(md.tickers)), dtype=np.float32)
    np.add.at(a, (ev["row"].to_numpy(), ev["col"].to_numpy()), 1.0)
    out = pd.DataFrame(a, index=md.dates, columns=md.tickers)
    out[out.index < "2015-01-01"] = np.nan                    # no news archive before 2015
    _EVENT_CACHE[key] = out
    return out


def _recent(md, ctx, kind: str, days: int):
    c = _event_counts(md, ctx, kind)
    return None if c is None else c.rolling(days, min_periods=1).sum()


@idea("news events (in-sample: picked from the 2015-26 event study)", 5)
def buyback_news(md, ctx, facts):
    """Buyback headlines in the last 10 days (event study: +33 bp the first day, still +37 bp at 21)."""
    return _recent(md, ctx, "buyback", 10)


@idea("news events (in-sample: picked from the 2015-26 event study)", 5)
def lawsuit_news_reversal(md, ctx, facts):
    """Lawsuit / probe headlines in the last 21 days: the selloff reverses (+76 bp over 21 days)."""
    return _recent(md, ctx, "lawsuit / probe", 21)


@idea("news events (in-sample: picked from the 2015-26 event study)", 5)
def mna_news_drift(md, ctx, facts):
    """M&A headlines in the last 21 days, negative: names in deal news drift down (-22 bp)."""
    r = _recent(md, ctx, "merger / acquisition", 21)
    return None if r is None else -r


@idea("news events (in-sample: picked from the 2015-26 event study)", 5)
def analyst_net_upgrades(md, ctx, facts):
    """Upgrades minus downgrades over the last 10 days."""
    up, dn = _recent(md, ctx, "analyst upgrade", 10), _recent(md, ctx, "analyst downgrade", 10)
    return None if up is None else up - dn


@idea("news events (in-sample: picked from the 2015-26 event study)", 5)
def dividend_raise_news(md, ctx, facts):
    """Dividend-raise headlines in the last 5 days."""
    return _recent(md, ctx, "dividend raise", 5)


@idea("news events (in-sample: picked from the 2015-26 event study)", 5)
def ceo_change_news(md, ctx, facts):
    """CEO-change headlines in the last 5 days, negative (-38 bp the first day)."""
    r = _recent(md, ctx, "CEO change", 5)
    return None if r is None else -r
