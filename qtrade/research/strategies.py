"""Beyond reversal: a zoo of different *kinds* of strategy.

Short-horizon cross-sectional reversal is one corner of the map. This study
tries strategies that make money for different reasons, each as a daily return
series net of costs, and asks two questions: does it work in both 2006-2014 and
2015-2026, and how correlated is it with the reversal book? Uncorrelated
strategies are worth more than their Sharpe suggests, because they diversify.

Timing (signals use data up to the close of day t-2 for the return of day t,
i.e. a full day to trade; ETF costs 1 bp per unit traded):

  spy_buy_hold        the benchmark
  spy_tsmom_12m       long SPY when its 12-month return is positive, else cash
  spy_ma200           long SPY above its 200-day moving average
  spy_vol_managed     SPY scaled by 1 / GARCH volatility forecast (Moreira-Muir)
  spy_hmm_timing      long SPY unless the HMM says "stressed"
  spy_overnight       hold SPY only from the close to the next open
  spy_intraday        hold SPY only from the open to the close
  spy_turn_of_month   long SPY from the last trading day of a month to the 3rd day
  spy_after_vix_spike long SPY for 21 days after the VIX jumps 2 sd above its 1-year mean

Across assets (SPY, EFA, EEM, TLT, IEF, GLD, DBC, VNQ):

  multi_asset_trend   each asset long/short by the sign of its 12-month return, 10% vol each
  risk_parity         long all, weighted by 1 / volatility
  cross_asset_mom     long the top 3 by 6-month return, monthly

Sectors (XLB XLE XLF XLI XLK XLP XLU XLV XLY):

  sector_momentum     long the top 3 by 6-1 month return, short the bottom 3, monthly

Stock factors (long top / short bottom quintile, monthly, measured costs):

  mom_12_1, low_vol, high_52w, gross_prof (quality), book_to_market (value),
  sue (earnings drift), accruals, multi_factor (equal blend), factor_momentum
  (each month, hold the factors whose own 12-month return is positive)

Neutral and scaled versions of the factor books (mom_12_1, low_vol, high_52w, gross_prof):

  *_sector_neutral    ranked inside each peer cluster, so no sector bets
  *_beta_neutral      the book's beta hedged with an equal-weight market leg
  *_vol_scaled        sized by 1 / trailing 6-month volatility (crash protection)
  risk_parity(...)    momentum and the reversal book blended by 1 / trailing volatility

Other stat-arb:

  etf_pairs           the same pairs rule on liquid ETFs (sectors, countries, rates, commodities)

  pairs               pairs of highly correlated peers; trade the price ratio when it
                      is 2 sd from its 60-day mean, exit at 0.5 sd or after 21 days
  earnings_premium    long stocks with an (estimated) earnings release in the next 5
                      days, short the rest - expected date = last filing + 91 days
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

SPLIT = "2015-01-01"
ASSETS = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ"]
SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
# a broader futures-like menu through ETFs: commodities, currencies, rates, credit, countries
BROAD = ["USO", "UNG", "DBA", "DBB", "SLV", "GLD", "UUP", "FXE", "FXY", "FXA", "SHY", "IEF", "TLT", "TIP",
         "LQD", "HYG", "EWJ", "EWG", "EWU", "FXI", "EWZ", "EWC", "EWA", "EWY", "EWT", "SPY", "QQQ", "IWM",
         "VNQ", "EEM"]
VOL = ["SVXY", "VIXY", "^VIX3M"]
ETF_COST = 1e-4


def _etfs(start: str):
    from ..data.loader import download_prices

    return download_prices(list(dict.fromkeys(ASSETS + SECTORS + BROAD + VOL + ["^VIX"])), start=start)


def _net(pos: pd.Series | pd.DataFrame, ret: pd.Series | pd.DataFrame, cost: float = ETF_COST) -> pd.Series:
    """Daily return of holding ``pos`` (decided at the close of t-2) over day t, minus costs."""
    p = pos.shift(2)
    pnl = (p * ret).sum(axis=1) if isinstance(p, pd.DataFrame) else p * ret
    trade = p.diff().abs()
    trade = trade.sum(axis=1) if isinstance(trade, pd.DataFrame) else trade
    return (pnl - trade.fillna(0) * cost).fillna(0.0)


def _month_ends(idx: pd.DatetimeIndex) -> pd.Series:
    s = pd.Series(idx, index=idx)
    return s.groupby([idx.year, idx.month]).transform("max") == s


def timing_strategies(etf, ctx, cfg) -> dict[str, pd.Series]:
    c = etf.close
    spy = c["SPY"]
    r = spy.pct_change(fill_method=None)
    out = {"spy_buy_hold": r.fillna(0)}
    out["spy_tsmom_12m"] = _net((spy / spy.shift(252) - 1 > 0).astype(float), r)
    out["spy_ma200"] = _net((spy > spy.rolling(200).mean()).astype(float), r)
    from .garch import fit_garch, garch_filter

    train = np.asarray(r.index < SPLIT) & r.notna().to_numpy()
    p = fit_garch(np.where(train, r.to_numpy(), np.nan)[: np.flatnonzero(train)[-1] + 1], gjr=True)
    s2 = garch_filter(r.to_numpy(), p["w"], p["a"], p["b"], p["g"], p["s0"])
    lev = pd.Series(np.clip(np.sqrt(np.nanmedian(s2[train])) / np.sqrt(s2), 0, 2), index=r.index)
    out["spy_vol_managed"] = _net(lev.shift(-1), r)            # s2[t] uses returns to t-1; shift(2) in _net -> t-2
    try:
        from ..models.regime import walk_forward_regimes

        rc = cfg.regime
        probs, fits = walk_forward_regimes(ctx.market_state, rc.n_states, rc.refit_every, rc.min_history,
                                           rc.n_init, rc.max_iter, cfg.model.seed, temper=rc.temper, align=rc.align)
        hi = int(np.argmax([np.trace(cv) for cv in fits[-1][1].covars_]))
        calm = (probs.iloc[:, hi] < 0.5).astype(float).reindex(r.index).ffill()
        out["spy_hmm_timing"] = _net(calm, r)
    except Exception as exc:                                     # needs enough history
        LOG.warning("hmm timing skipped: %s", exc)
    o = etf.open["SPY"]
    out["spy_overnight"] = (o / spy.shift(1) - 1).fillna(0) - 2 * ETF_COST * (o.notna())
    out["spy_intraday"] = (spy / o - 1).fillna(0) - 2 * ETF_COST * (o.notna())
    idx = r.index
    me = _month_ends(idx)
    nth = pd.Series(1, index=idx).groupby([idx.year, idx.month]).cumsum()
    # calendar positions are known in advance: hold over the last day of a month and days 1-3
    tom = (me.shift(1, fill_value=False) | (nth <= 3)).astype(float)
    out["spy_turn_of_month"] = tom * r.fillna(0) - tom.diff().abs().fillna(0) * ETF_COST
    vix = c["^VIX"]
    spike = (vix - vix.rolling(252).mean()) / vix.rolling(252).std() > 2
    hold = spike.astype(float).rolling(21, min_periods=1).max()
    out["spy_after_vix_spike"] = _net(hold, r)
    return out


def cross_asset_strategies(etf) -> dict[str, pd.Series]:
    c = etf.close[ASSETS]
    r = c.pct_change(fill_method=None)
    vol = r.rolling(63, min_periods=40).std() * np.sqrt(252)
    sign = np.sign(c / c.shift(252) - 1)
    trend = (sign * 0.10 / vol).clip(-2, 2) / len(ASSETS)
    out = {"multi_asset_trend": _net(trend, r.fillna(0))}
    ivol = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
    out["risk_parity"] = _net(ivol, r.fillna(0))
    me = _month_ends(c.index)
    mom6 = c / c.shift(126) - 1
    top = mom6.rank(axis=1, ascending=False) <= 3
    w = (top.astype(float) / 3).where(me).ffill()
    out["cross_asset_mom"] = _net(w, r.fillna(0))
    s = etf.close[SECTORS]
    rs = s.pct_change(fill_method=None)
    m = s.shift(21) / s.shift(126) - 1
    rk = m.rank(axis=1)
    ws = ((rk >= len(SECTORS) - 2).astype(float) / 3 - (rk <= 3).astype(float) / 3).where(me).ffill()
    out["sector_momentum"] = _net(ws, rs.fillna(0))
    return out


def _quintile_ls(sig: pd.DataFrame, tradable: pd.DataFrame, monthly: pd.Series) -> pd.DataFrame:
    """Equal-weight long top / short bottom quintile, set at month ends, held a month."""
    s = sig.where(tradable)
    rk = s.rank(axis=1, pct=True)
    w = (rk > 0.8).astype(float) - (rk <= 0.2).astype(float)
    w = w.div(w.abs().sum(axis=1), axis=0)
    return w.where(monthly, np.nan).ffill().fillna(0.0)


def factor_strategies(md, ctx, alt: dict) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
    from ..signals import REGISTRY
    from .edge import cost_panel

    cost = cost_panel(ctx)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5).fillna(0)        # decided at close t, open t+1 -> t+2
    monthly = _month_ends(md.dates)
    raw = {k: REGISTRY[k].fn(ctx) for k in ("mom_12_1", "low_vol", "high_52w") if k in REGISTRY}
    for k in ("gross_prof", "book_to_market", "sue", "accruals"):
        if k in alt:
            raw[k] = alt[k]
    out = {}
    for k, s in raw.items():
        w = _quintile_ls(s, ctx.tradable, monthly)
        out[k] = ((w * r1).sum(axis=1) - (w.diff().abs() * cost).sum(axis=1)).shift(1).fillna(0)
    if out:
        f = pd.DataFrame(out)
        out["multi_factor"] = f.mean(axis=1)
        trail = f.rolling(252, min_periods=200).sum().shift(1)
        hold = (trail > 0).astype(float).where(monthly).ffill()
        out["factor_momentum"] = (hold * f).sum(axis=1) / hold.sum(axis=1).replace(0, np.nan)
        out["factor_momentum"] = out["factor_momentum"].fillna(0)
    return out, raw


def neutral_factor_strategies(md, ctx, raw: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
    """The same quintile books made sector-neutral (ranked within peer clusters),
    beta-neutral (market exposure hedged with an equal-weight market leg) and
    volatility-scaled (sized by 1 / trailing 6-month volatility of the book)."""
    from .edge import cost_panel

    cost = cost_panel(ctx)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5).fillna(0)
    monthly = _month_ends(md.dates)
    cl = ctx.clusters
    beta = ctx.beta_252
    mkt = r1.where(ctx.tradable).mean(axis=1)
    out = {}

    def book(w):
        return ((w * r1).sum(axis=1) - (w.diff().abs() * cost).sum(axis=1)).shift(1).fillna(0)

    for k in ("mom_12_1", "low_vol", "high_52w", "gross_prof"):
        if k not in raw:
            continue
        sig = raw[k].where(ctx.tradable)
        # sector-neutral: percentile rank inside each peer cluster
        st = sig.stack()
        g = cl.stack().reindex(st.index)
        dates = st.index.get_level_values(0)
        rk = st.groupby([dates, g.to_numpy()]).rank(pct=True).unstack().reindex_like(sig)
        w = (rk > 0.8).astype(float) - (rk <= 0.2).astype(float)
        w = w.div(w.abs().sum(axis=1), axis=0).where(monthly, np.nan).ffill().fillna(0.0)
        out[f"{k}_sector_neutral"] = book(w)
        # beta-neutral: hedge the book's beta with the equal-weight market (2 bp per unit traded)
        w = _quintile_ls(raw[k], ctx.tradable, monthly)
        b = (w * beta.reindex_like(w)).sum(axis=1)
        hedge = -b.shift(1) * mkt
        out[f"{k}_beta_neutral"] = book(w) + hedge.fillna(0) - b.diff().abs().shift(1).fillna(0) * 2e-4
        if k == "mom_12_1":                                    # macro_timing already has momentum_vol_scaled
            continue
        # volatility-scaled: target the book's period-1 volatility using trailing 126-day vol
        base = book(w)
        vol = base.rolling(126, min_periods=60).std().shift(1)
        out[f"{k}_vol_scaled"] = (base * (base.loc[:SPLIT].std() / vol).clip(0, 2)).fillna(0)
    return out


def etf_pairs(etf, top_pairs: int = 10, entry: float = 2.0, exit_: float = 0.5, max_hold: int = 21) -> pd.Series:
    """Pairs trading among liquid ETFs: each year, the most correlated pairs over the
    previous year; trade the log-price ratio at 2 sd from its 60-day mean."""
    names = list(dict.fromkeys(ASSETS + SECTORS + BROAD))
    c = etf.close[[n for n in names if n in etf.close]]
    lp = np.log(c)
    ret = c.pct_change(fill_method=None).fillna(0)
    dates = c.index
    pnl = pd.Series(0.0, index=dates)
    for yr in sorted(set(dates.year))[2:]:
        start = dates[dates.year == yr][0]
        form = ret.loc[:start].iloc[-252:]
        form = form.loc[:, (form != 0).mean() > 0.9]
        if form.shape[1] < 2:
            continue
        cm = form.corr().to_numpy()
        iu = np.triu_indices(len(cm), 1)
        best = np.argsort(-np.nan_to_num(cm[iu]))[:top_pairs]
        pairs = [(form.columns[iu[0][b]], form.columns[iu[1][b]]) for b in best if cm[iu][b] > 0.8]
        if not pairs:
            continue
        days = dates[dates.year == yr]
        wp = 1.0 / len(pairs)
        for a, b in pairs:
            spread = lp[a] - lp[b]
            z = ((spread - spread.rolling(60).mean()) / spread.rolling(60).std()).loc[days].to_numpy()
            ra, rb = ret[a].loc[days].to_numpy(), ret[b].loc[days].to_numpy()
            pos, held = 0, 0
            x = np.zeros(len(days))
            for i in range(1, len(days)):
                x[i] = pos * (ra[i] - rb[i]) * wp / 2
                new = pos
                if pos == 0 and np.isfinite(z[i]) and abs(z[i]) > entry:
                    new = -int(np.sign(z[i]))
                elif pos != 0 and (abs(z[i]) < exit_ or held >= max_hold or not np.isfinite(z[i])):
                    new = 0
                if new != pos:
                    x[i] -= abs(new - pos) * wp * ETF_COST
                    held = 0
                held += 1 if new != 0 else 0
                pos = new
            pnl.loc[days] += x
    return pnl


def risk_parity_blend(books: dict[str, pd.Series]) -> pd.Series:
    """Blend return series with weights 1 / trailing 126-day volatility (known a day ahead)."""
    R = pd.DataFrame(books).fillna(0)
    iv = 1 / R.rolling(126, min_periods=60).std().shift(1)
    w = iv.div(iv.sum(axis=1), axis=0)
    return (w * R).sum(axis=1).fillna(0)


def pairs_strategy(md, ctx, top_pairs: int = 5, entry: float = 2.0, exit_: float = 0.5,
                   max_hold: int = 21) -> pd.Series:
    """Classic pairs trading inside k-means peer clusters, re-formed every year."""
    from .edge import cost_panel

    lp = np.log(md.close)
    ret = ctx.ret
    cost = cost_panel(ctx)
    fm = ctx.factor_model
    dates = md.dates
    pnl = pd.Series(0.0, index=dates)
    years = sorted(set(dates.year))
    for yr in years[2:]:
        start = dates[dates.year == yr][0]
        snap = fm.snapshot_at(start)
        if snap is None:
            continue
        form = ret.loc[:start].iloc[-252:]
        pairs = []
        for k in np.unique(snap.clusters):
            mem = [t for t, c in zip(snap.tickers, snap.clusters) if c == k and t in form.columns]
            if len(mem) < 2:
                continue
            cm = form[mem].corr().to_numpy()
            iu = np.triu_indices(len(mem), 1)
            best = np.argsort(-np.nan_to_num(cm[iu]))[:top_pairs]
            pairs += [(mem[iu[0][b]], mem[iu[1][b]]) for b in best if cm[iu][b] > 0.6]
        if not pairs:
            continue
        days = dates[dates.year == yr]
        w_pair = 1.0 / len(pairs)
        for a, b in pairs:
            spread = (lp[a] - lp[b])
            z = (spread - spread.rolling(60).mean()) / spread.rolling(60).std()
            zt = z.loc[days].to_numpy()
            ra, rb = ret[a].loc[days].fillna(0).to_numpy(), ret[b].loc[days].fillna(0).to_numpy()
            ca, cb = cost[a].loc[days].to_numpy(), cost[b].loc[days].to_numpy()
            pos, held = 0, 0
            out = np.zeros(len(days))
            for i in range(1, len(days)):
                out[i] = pos * (ra[i] - rb[i]) * w_pair / 2            # position decided at the close of i-1
                new = pos
                if pos == 0 and np.isfinite(zt[i]) and abs(zt[i]) > entry:
                    new = -int(np.sign(zt[i]))
                elif pos != 0 and (abs(zt[i]) < exit_ or held >= max_hold or not np.isfinite(zt[i])):
                    new = 0
                if new != pos:
                    out[i] -= abs(new - pos) * w_pair / 2 * (ca[i] + cb[i])
                    held = 0
                held += 1 if new != 0 else 0
                pos = new
            pnl.loc[days] += out
    return pnl


def earnings_premium(md, ctx, facts: pd.DataFrame | None) -> pd.Series | None:
    if facts is None:
        return None
    from .edge import cost_panel

    f = facts[facts["form"].isin(["10-Q", "10-K"]) & facts["filed"].notna()][["ticker", "filed"]].drop_duplicates()
    dates = md.dates
    day_num = ((dates - pd.Timestamp("1970-01-01")).days).to_numpy(dtype=float)
    nxt = pd.DataFrame(np.nan, index=dates, columns=md.tickers)       # expected next filing, as a day number
    for t, g in f.groupby("ticker"):
        if t not in nxt.columns:
            continue
        filed = pd.DatetimeIndex(sorted(g["filed"].unique()))
        expected = ((filed + pd.Timedelta(days=91)) - pd.Timestamp("1970-01-01")).days.to_numpy(dtype=float)
        s = pd.Series(expected, index=filed + pd.Timedelta(days=1))   # known from the day after a filing
        s = s[~s.index.duplicated(keep="last")]
        nxt[t] = s.reindex(dates, method="ffill").to_numpy()
    days_to = nxt.sub(day_num, axis=0)
    soon = (days_to >= 1) & (days_to <= 7) & ctx.tradable
    w = soon.astype(float).div(soon.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    other = (~soon & ctx.tradable).astype(float)
    w = w - other.div(other.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5).fillna(0)
    cost = cost_panel(ctx)
    return ((w * r1).sum(axis=1) - (w.diff().abs() * cost).sum(axis=1)).shift(1).fillna(0)


# -----------------------------------------------------------------------------
# wave 2
# -----------------------------------------------------------------------------
def broad_strategies(etf) -> dict[str, pd.Series]:
    """Trend following and momentum over ~30 ETFs spanning the major asset classes."""
    have = [t for t in BROAD if t in etf.close.columns]
    c = etf.close[have]
    r = c.pct_change(fill_method=None)
    vol = r.rolling(63, min_periods=40).std() * np.sqrt(252)
    out = {}
    for lb, name in ((63, "trend_3m"), (252, "trend_12m")):
        sign = np.sign(c / c.shift(lb) - 1)
        w = (sign * 0.10 / vol).clip(-2, 2).div(c.notna().sum(axis=1).clip(lower=1), axis=0)
        out[f"broad_{name}"] = _net(w, r.fillna(0))
    blend = (np.sign(c / c.shift(21) - 1) + np.sign(c / c.shift(63) - 1) + np.sign(c / c.shift(252) - 1)) / 3
    w = (blend * 0.10 / vol).clip(-2, 2).div(c.notna().sum(axis=1).clip(lower=1), axis=0)
    out["broad_trend_blend"] = _net(w, r.fillna(0))
    me = _month_ends(c.index)
    rk = (c.shift(21) / c.shift(252) - 1).rank(axis=1, pct=True)
    xs = ((rk > 0.75).astype(float) - (rk <= 0.25).astype(float))
    xs = xs.div(xs.abs().sum(axis=1).replace(0, np.nan), axis=0).where(me).ffill()
    out["broad_xs_momentum"] = _net(xs, r.fillna(0))
    return out


def vol_premium_strategies(etf) -> dict[str, pd.Series]:
    """Short volatility through SVXY, only when the VIX curve is in contango (VIX < VIX3M)."""
    c = etf.close
    out = {}
    if "SVXY" in c and "^VIX3M" in c:
        r = c["SVXY"].pct_change(fill_method=None)
        contango = (c["^VIX"] < c["^VIX3M"]).astype(float)
        out["short_vol_contango"] = _net(contango, r.fillna(0))
        out["short_vol_always"] = r.fillna(0)
    if "VIXY" in c and "^VIX3M" in c:
        r = c["VIXY"].pct_change(fill_method=None)
        back = (c["^VIX"] > c["^VIX3M"]).astype(float)
        out["long_vol_backwardation"] = _net(back, r.fillna(0))
    return out


def sector_seasonality(etf) -> dict[str, pd.Series]:
    """Each month, long the 3 sectors with the best average return in that calendar month over
    the previous 10 years, short the worst 3."""
    s = etf.close[SECTORS]
    r = s.pct_change(fill_method=None)
    m = np.log(s).resample("ME").last().diff()
    seas = sum(m.shift(12 * k) for k in range(1, 11)) / 10                # average for the *coming* month
    seas = seas.shift(-1)
    rk = seas.rank(axis=1)
    w = ((rk >= len(SECTORS) - 2).astype(float) - (rk <= 3).astype(float)) / 3
    w = w.reindex(r.index, method="ffill")
    return {"sector_seasonality": _net(w, r.fillna(0))}


def macro_timing(etf, fred: pd.DataFrame | None, factor_rets: dict) -> tuple[dict, pd.DataFrame]:
    """Macro states (FRED) to time the market and momentum. Each rule is set from
    2006-2014 relationships only; the table shows each variable's correlation with
    the next month's market and momentum returns in both periods."""
    if fred is None or fred.empty:
        return {}, pd.DataFrame()
    spy = etf.close["SPY"]
    r = spy.pct_change(fill_method=None).fillna(0)
    f = fred.reindex(r.index, method="ffill")
    fwd_mkt = np.log(spy.shift(-21) / spy)
    mom = factor_rets.get("mom_12_1")
    fwd_mom = mom[::-1].rolling(21).sum()[::-1].shift(-1).reindex(r.index) if mom is not None else None
    rows = []
    feats = {}
    for col in f.columns:
        x = f[col]
        z = (x - x.rolling(252, min_periods=126).mean()) / x.rolling(252, min_periods=126).std()   # vs. its last year
        feats[col] = z
        row = {"variable": col}
        for per, msk in (("1st", (r.index >= "2006-01-01") & (r.index < SPLIT)), ("2nd", r.index >= SPLIT)):
            row[f"corr_next_month_market_{per}"] = z[msk].corr(fwd_mkt[msk])
            if fwd_mom is not None:
                row[f"corr_next_month_momentum_{per}"] = z[msk].corr(fwd_mom[msk])
        rows.append(row)
    tab = pd.DataFrame(rows)
    out = {}
    # market: hold SPY when the combined macro score (signs from 2006-2014) is positive
    s1 = tab.set_index("variable")["corr_next_month_market_1st"]
    score = sum(np.sign(s1[c]) * feats[c].clip(-3, 3) for c in s1.index if np.isfinite(s1[c]))
    out["spy_macro_timing"] = _net((score > 0).astype(float), r)
    if mom is not None and "corr_next_month_momentum_1st" in tab:
        s2 = tab.set_index("variable")["corr_next_month_momentum_1st"]
        score_m = sum(np.sign(s2[c]) * feats[c].clip(-3, 3) for c in s2.index if np.isfinite(s2[c]))
        lev = (1 + np.tanh(score_m.reindex(mom.index) / 2)).clip(0, 2)    # 0x to 2x, 1x when neutral
        out["momentum_macro_timed"] = (mom * lev.shift(2)).fillna(0)
        # Daniel-Moskowitz style crash protection: scale momentum by 1 / its own recent volatility
        vol = mom.rolling(126, min_periods=60).std().shift(1)
        out["momentum_vol_scaled"] = (mom * (mom.loc[:SPLIT].std() / vol).clip(0, 2)).fillna(0)
    return out, tab


def optimize_strategies(R: pd.DataFrame, keep: list[str]) -> pd.DataFrame:
    """Mean-variance across strategies with a Ledoit-Wolf covariance, estimated on 2006-2014,
    vs. inverse-volatility and equal weights, all judged on 2015-2026."""
    from sklearn.covariance import LedoitWolf

    first = R.loc[:SPLIT, keep]
    rows = []
    lw = LedoitWolf().fit(first.to_numpy())
    cov = lw.covariance_
    mu = first.mean().to_numpy()
    w_mv = np.clip(np.linalg.solve(cov + 1e-10 * np.eye(len(keep)), mu), 0, None)   # long-only tangency
    w_mv = w_mv / w_mv.sum() if w_mv.sum() > 0 else np.full(len(keep), 1 / len(keep))
    w_iv = (1 / first.std()).to_numpy().copy()
    w_iv /= w_iv.sum()
    w_eq = np.full(len(keep), 1 / len(keep))
    for name, w in (("Ledoit-Wolf mean-variance", w_mv), ("inverse volatility", w_iv), ("equal weight", w_eq)):
        book = R[keep] @ w
        book = book * (0.10 / (book.loc[:SPLIT].std() * np.sqrt(252)))
        rows.append({"weights": name, **_stats(book),
                     "top_weights": ", ".join(f"{k} {v:.0%}" for k, v in
                                              sorted(zip(keep, w), key=lambda kv: -kv[1])[:5])})
    return pd.DataFrame(rows)


def capacity(md, ctx, signal: pd.DataFrame, name: str, aums=(1e4, 1e6, 1e7, 1e8, 1e9)) -> pd.DataFrame:
    """Net Sharpe of a monthly quintile long-short in ``signal`` as the account grows:
    square-root market impact on top of the spread, 0.5 x daily vol x sqrt(trade / ADV)."""
    from .edge import cost_panel

    monthly = _month_ends(md.dates)
    w = _quintile_ls(signal, ctx.tradable, monthly)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5).fillna(0)
    spread = cost_panel(ctx)
    sig = ctx.vol_63.fillna(0.02)
    adv = ctx.adv.where(ctx.adv > 0)
    gross = (w * r1).sum(axis=1)
    dw = w.diff().abs()
    rows = []
    for aum in aums:
        impact = 0.5 * sig * np.sqrt((dw * aum) / adv).fillna(0)
        net = (gross - (dw * (spread + impact)).sum(axis=1)).shift(1).fillna(0)
        rows.append({"strategy": name, "account_usd": aum, **_stats(net)})
    return pd.DataFrame(rows)


def execution_comparison(md, ctx, sigs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """The same daily long-short traded at the next open vs. the next close (auction choice)."""
    from .edge import cost_panel

    cost = cost_panel(ctx)
    o, c = md.open, md.close
    r_open = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5).fillna(0)     # trade at open t+1, hold to open t+2
    r_close = (c.shift(-2) / c.shift(-1) - 1).clip(-0.5, 0.5).fillna(0)    # trade at close t+1, hold to close t+2
    rows = []
    for name, z in sigs.items():
        x = z.ewm(halflife=5, ignore_na=True).mean().where(ctx.tradable)
        x = x.sub(x.mean(axis=1), axis=0)
        w = x.div(x.abs().sum(axis=1), axis=0).fillna(0)
        tc = (w.diff().abs() * cost).sum(axis=1)
        for fill, rr in (("next open", r_open), ("next close", r_close)):
            net = ((w * rr).sum(axis=1) - tc).shift(1).fillna(0)
            rows.append({"signal": name, "fill": fill, **_stats(net)})
    return pd.DataFrame(rows)


def _stats(r: pd.Series) -> dict:
    out = {}
    for tag, m in (("1st", (r.index >= "2006-01-01") & (r.index < SPLIT)), ("2nd", r.index >= SPLIT)):
        x = r[m]
        out[f"sharpe_{tag}"] = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
        out[f"ret_{tag}"] = x.mean() * 252
        eq = (1 + x).cumprod()
        out[f"max_dd_{tag}"] = (eq / eq.cummax() - 1).min() if len(x) else np.nan
    out["vol"] = r[r.index >= "2006-01-01"].std() * np.sqrt(252)
    return out


def run(md, ctx, out: Path, cfg, alt: dict | None = None, reversal: pd.Series | None = None) -> dict:
    alt = alt or {}
    etf = _etfs("2003-01-01")
    strat = {}
    fpath = Path(cfg.data.cache_dir) / "fundamentals" / "fundamentals.parquet"

    def earnings():
        from ..data.fundamentals import load_fundamentals

        ep = earnings_premium(md, ctx, load_fundamentals(fpath.parent)) if fpath.exists() else None
        return {"earnings_premium": ep} if ep is not None else {}

    # each block is independent: one failing must not lose the others
    fac, fac_raw = {}, {}
    try:
        fac, fac_raw = factor_strategies(md, ctx, alt)
    except Exception as exc:
        LOG.exception("factor strategies failed: %s", exc)
    strat |= fac
    fred = None
    try:
        from ..data.public import load_fred

        fred = load_fred(cfg.data.cache_dir)
    except Exception as exc:
        LOG.warning("FRED unavailable: %s", exc)
    macro_tab = pd.DataFrame()

    def macro():
        nonlocal macro_tab
        o, macro_tab = macro_timing(etf, fred, fac)
        return o

    for name, block in (("timing", lambda: timing_strategies(etf, ctx, cfg)),
                        ("cross-asset", lambda: cross_asset_strategies(etf)),
                        ("broad ETFs", lambda: broad_strategies(etf)),
                        ("volatility premium", lambda: vol_premium_strategies(etf)),
                        ("sector seasonality", lambda: sector_seasonality(etf)),
                        ("macro", macro),
                        ("pairs", lambda: {"pairs": pairs_strategy(md, ctx)}),
                        ("ETF pairs", lambda: {"etf_pairs": etf_pairs(etf)}),
                        ("neutral factor books", lambda: neutral_factor_strategies(md, ctx, fac_raw)),
                        ("earnings premium", earnings)):
        try:
            strat |= block()
        except Exception as exc:
            LOG.exception("strategy block %s failed: %s", name, exc)
    if reversal is not None:
        strat["REVERSAL BOOK (current system)"] = reversal
        for k in ("mom_12_1", "momentum_vol_scaled"):
            if k in strat:
                strat[f"risk_parity({k} + reversal)"] = risk_parity_blend({"m": strat[k], "r": reversal})
    R = pd.DataFrame(strat).loc["2006-01-01":].fillna(0.0)
    R = R.loc[:, R.abs().sum() > 0]
    tab = pd.DataFrame({k: _stats(R[k]) for k in R}).T
    rev_col = "REVERSAL BOOK (current system)"
    if rev_col in R:
        tab["corr_with_reversal"] = R.corr()[rev_col]
    tab["corr_with_spy"] = R.corr()["spy_buy_hold"] if "spy_buy_hold" in R else np.nan
    tab = tab.sort_values("sharpe_2nd", ascending=False)

    # a diversified book chosen on period 1: strategies with period-1 Sharpe > 0.3, inverse-vol weighted
    first = R.loc[:SPLIT]
    sh1 = first.mean() / first.std() * np.sqrt(252)
    keep = [k for k in R if sh1[k] > 0.3 and k != "spy_buy_hold"]
    combo_rows = []
    if keep:
        vol1 = first[keep].std()
        w = (1 / vol1) / (1 / vol1).sum()
        book = (R[keep] * w).sum(axis=1)
        book = book * (0.10 / (book.loc[:SPLIT].std() * np.sqrt(252)))          # 10% vol, scaled on period 1
        combo_rows.append({"portfolio": f"diversified ({len(keep)} strategies chosen on 2006-2014)", **_stats(book)})
        if rev_col in R:
            rv = R[rev_col] * (0.10 / (R[rev_col].loc[:SPLIT].std() * np.sqrt(252)))
            combo_rows.append({"portfolio": "reversal book alone (10% vol)", **_stats(rv)})
    combo = pd.DataFrame(combo_rows)
    opt = optimize_strategies(R, keep) if len(keep) >= 2 else pd.DataFrame()
    cap_rows = []
    for nm in ("mom_12_1", "high_52w", "gross_prof"):
        if nm in fac_raw:
            try:
                cap_rows.append(capacity(md, ctx, fac_raw[nm], nm))
            except Exception as exc:
                LOG.warning("capacity %s failed: %s", nm, exc)
    cap = pd.concat(cap_rows) if cap_rows else pd.DataFrame()
    exe = pd.DataFrame()
    try:
        from ..signals import compute_signals

        exe = execution_comparison(md, ctx, compute_signals(ctx, ["rev_5d", "resid_rev_1d", "mom_12_1"]))
    except Exception as exc:
        LOG.warning("execution comparison failed: %s", exc)
    corr = R.corr()
    R.to_csv(out / "strategy_returns.csv")
    tab.to_csv(out / "strategies.csv")
    corr.to_csv(out / "strategy_correlations.csv")
    lines = ["## Beyond reversal: other kinds of strategy", "",
             "Daily returns net of costs. Sharpe in 2006-2014 and 2015-2026; correlation with the current "
             "reversal book and with the S&P 500 over the whole period (low = diversifying).", "",
             tab.round(3).to_markdown(), "",
             "### A diversified book", "",
             f"Strategies with period-1 Sharpe > 0.3 ({', '.join(keep) if keep else 'none'}), weighted by "
             "1 / volatility, scaled to 10% volatility on period 1 only.", "",
             combo.round(3).to_markdown(index=False) if len(combo) else "(none)", "",
             "### Optimising across strategies (weights from 2006-2014 only)", "",
             opt.round(3).to_markdown(index=False) if len(opt) else "(not enough strategies)", "",
             "### Macro variables vs. next month's market and momentum returns", "",
             macro_tab.round(3).to_markdown(index=False) if len(macro_tab) else "(no FRED data)", "",
             "### Capacity: net Sharpe as the account grows (square-root market impact)", "",
             cap.round(3).to_markdown(index=False) if len(cap) else "(none)", "",
             "### Execution: trade at the next open or the next close?", "",
             exe.round(3).to_markdown(index=False) if len(exe) else "(none)", "",
             "### Correlation matrix", "", corr.round(2).to_markdown(), ""]
    (out / "strategies.md").write_text("\n".join(lines) + "\n")
    return {"strategies": len(tab), "chosen_for_diversified_book": keep,
            "diversified": combo.round(3).to_dict(orient="records")}
