"""International lab: does the US finding hold on other exchanges, and in Asian financials?

The US research (research_night/) found one stable pattern: cross-sectional
stock momentum (12-1 month, residual, 52-week high) pays when the VIX is low
and reverses when it is high, so a monthly momentum book held *short* whenever
the VIX is above 20 earned Sharpe ~0.6 / 0.7 / 0.2 in 2006-14 / 2015-20 /
2021-26, staggered and net of costs. This module runs the same tests, with the
same conventions, on each international market:

* signal stability (invariants): rank IC of each signal in four sub-periods,
  and in calm (VIX <= 20) vs. stressed (VIX > 20) markets;
* the momentum flip, staggered across start days, long/short and long-only
  (long the top quintile, short the local index; in stress long the losers);
* the same on financials only, and on a pooled, country-neutral book of all
  Asian financials;
* local frictions: bid-ask spreads by liquidity tier (wider than the US),
  stamp duties and transaction taxes, and a note on where shorting is
  restricted.

Everything is self-contained (pandas/numpy only) and runs on the output of
universes.py and download.py:

    python research_international/code/intl_lab.py --prices data/prices --universe data/universe.csv --out reports/intl
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

PERIODS = (("2006_14", "2006", "2014"), ("2015_20", "2015", "2020"), ("2021_26", "2021", "2026"))
IC_PERIODS = (("2004_09", "2004", "2009"), ("2010_14", "2010", "2014"), ("2015_20", "2015", "2020"), ("2021_26", "2021", "2026"))
MOM = ("mom_12_1", "resid_mom", "high_52w")
REBAL = 21
COHORTS = tuple(range(0, REBAL, 3))         # 7 staggered cohorts average out the start-day effect

# ---------------------------------------------------------------------------
# frictions. half_spread: one-way bp by liquidity tercile within the market
# (top, middle, bottom by 21-day median traded value); tax: bp per unit traded
# (a sell-only or buy-only tax of x% counts as x/2 per unit traded, since half
# of turnover is sells); from: year the tax applies from (None = whole sample).
# Approximations from exchange fee schedules; refine before trading.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Frictions:
    half_spread: tuple[float, float, float]
    taxes: tuple[tuple[float, str | None], ...] = ()
    short_note: str = "shorting available for index constituents"


FRICTIONS = {
    "Japan": Frictions((4, 8, 15)),
    "Hong Kong": Frictions((8, 15, 30), ((10, None),), "designated securities can be shorted; stamp duty 0.1-0.13% each side"),
    "Hong Kong (H-shares)": Frictions((8, 15, 30), ((10, None),), "as Hong Kong"),
    "China": Frictions((4, 8, 15), ((5, None),), "A-shares effectively cannot be shorted (securities lending very limited)"),
    "Korea": Frictions((6, 12, 25), ((12, None),), "short-selling bans Mar 2020-May 2021 (all) and Nov 2023-Mar 2025"),
    "Taiwan": Frictions((6, 12, 25), ((15, None), (3, None)), "0.3% sell tax; shorting via securities lending possible"),
    "Singapore": Frictions((8, 15, 30), ((1.5, None),), "limited securities lending"),
    "Australia": Frictions((4, 8, 15)),
    "India": Frictions((5, 10, 20), ((10, "2004"),), "no overnight short of cash equities; shorts via single-stock futures only"),
    "Malaysia": Frictions((10, 20, 35), ((5, None),), "regulated short selling, limited"),
    "Thailand": Frictions((10, 20, 35), (), "regulated short selling, limited"),
    "New Zealand": Frictions((10, 20, 40)),
    "UK": Frictions((3, 6, 12), ((25, None),), "0.5% stamp duty on purchases"),
    "Germany": Frictions((3, 5, 10)),
    "France": Frictions((3, 5, 10), ((15, "2012-08"),), "0.3% FTT on purchases of large caps from Aug 2012"),
    "Switzerland": Frictions((3, 5, 10), ((4, None),), "0.075% stamp each side via Swiss brokers"),
    "Netherlands": Frictions((3, 5, 10)),
    "Spain": Frictions((4, 8, 15), ((10, "2021"),), "0.2% FTT on purchases from 2021"),
    "Italy": Frictions((4, 8, 15), ((5, "2013-03"),), "0.1% FTT on purchases from 2013"),
    "Sweden": Frictions((4, 8, 15)),
    "Canada": Frictions((3, 6, 12)),
    # second wave of exchanges (deep_universe.py); wider spreads, rougher tax schedules
    "Indonesia": Frictions((10, 20, 40), ((5, None),), "0.1% sell tax; shorting effectively unavailable"),
    "Vietnam": Frictions((10, 20, 35), ((5, None),), "0.1% sell tax; no short selling; foreign ownership limits"),
    "Pakistan": Frictions((10, 20, 40), ((5, None),), "fees and CVT approximated; shorting very limited"),
    "Brazil": Frictions((5, 10, 20), (), "securities lending available"),
    "Mexico": Frictions((8, 15, 30), (), "limited securities lending"),
    "Chile": Frictions((8, 15, 30), (), "limited securities lending"),
    "South Africa": Frictions((6, 12, 25), ((12.5, None),), "0.25% securities transfer tax on purchases"),
    "Turkey": Frictions((6, 12, 25), (), "short-selling bans in stress (e.g. 2020, 2023)"),
    "Saudi Arabia": Frictions((6, 12, 25), (), "short selling permitted since 2017, rarely available"),
    "Kuwait": Frictions((10, 20, 40), (), "no practical short selling"),
    "Qatar": Frictions((10, 20, 40), (), "no practical short selling"),
    "Israel": Frictions((6, 12, 25), (), "limited securities lending"),
    "Poland": Frictions((6, 12, 25), (), "limited securities lending"),
    "Greece": Frictions((8, 15, 30), ((7.5, None),), "0.1-0.2% sales tax; limited lending"),
    "Portugal": Frictions((6, 12, 25), ((15, "2013"),), "0.3% FTT on purchases from 2013"),
    "Belgium": Frictions((4, 8, 15), ((27, None), (8, "2018")), "TOB 0.27-0.35% on every trade"),
    "Austria": Frictions((5, 10, 20)),
    "Norway": Frictions((4, 8, 15)),
    "Denmark": Frictions((4, 8, 15)),
    "Finland": Frictions((4, 8, 15)),
    # South America (south_america_universe.py)
    "Argentina": Frictions((10, 20, 40), (), "no practical short selling; capital controls 2011-15 and 2019-25"),
    "Colombia": Frictions((10, 20, 40), (), "securities lending (TTV) thin"),
    "Peru": Frictions((10, 20, 40), (), "no practical short selling"),
    "South America ADRs": Frictions((4, 8, 15), (), "New York listings: borrowable, USD; ADR custody fees not modelled"),
}
SLIPPAGE_BP = 1.0


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 60 and x.std() > 0 else np.nan


def _dd(x: pd.Series) -> float:
    eq = (1 + x.fillna(0)).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(eq) else np.nan


def rank_ic(a: pd.DataFrame, b: pd.DataFrame, min_names: int = 15) -> pd.Series:
    ok = a.notna() & b.notna()
    ra, rb = a.where(ok).rank(axis=1), b.where(ok).rank(axis=1)
    ra, rb = ra.sub(ra.mean(axis=1), axis=0), rb.sub(rb.mean(axis=1), axis=0)
    ic = (ra * rb).sum(axis=1) / np.sqrt((ra ** 2).sum(axis=1) * (rb ** 2).sum(axis=1))
    return ic.where(ok.sum(axis=1) >= min_names)


def zscore(df: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    x = df.where(mask)
    return x.sub(x.mean(axis=1), axis=0).div(x.std(axis=1) + 1e-12, axis=0)


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------
class Market:
    def __init__(self, name: str, path: Path, universe: pd.DataFrame, vix: pd.Series):
        self.name = name
        f = {k: pd.read_parquet(path / f"{k}.parquet") for k in ("open", "high", "low", "close", "adj_close", "volume")}
        adj = f["adj_close"]
        keep = adj.columns[adj.notna().sum() > 252]
        adj = adj[keep]
        # drop days on which almost nothing traded (exchange holidays filled by other calendars)
        live = adj.notna().sum(axis=1) >= max(10, 0.3 * adj.notna().sum(axis=1).max())
        self.adj = adj.loc[live]
        self.open = f["open"][keep].loc[self.adj.index]
        self.close = f["close"][keep].loc[self.adj.index]
        self.volume = f["volume"][keep].loc[self.adj.index]
        self.dates, self.tickers = self.adj.index, self.adj.columns
        u = universe.set_index("ticker")
        self.financial = u["financial"].reindex(self.tickers).fillna(False).astype(bool)
        self.vix = vix.reindex(self.dates, method="ffill")
        ret = self.adj.pct_change(fill_method=None).clip(-0.5, 0.5)
        # suspected bad prints: |return| > 40% that fully reverses the next day
        bad = (ret.abs() > 0.4) & (ret.shift(-1).abs() > 0.3) & (np.sign(ret) != np.sign(ret.shift(-1)))
        self.ret = ret.mask(bad)
        self.r1 = (self.open.shift(-2) / self.open.shift(-1) - 1).clip(-0.5, 0.5)
        traded_value = (self.close * self.volume).where(self.volume > 0)
        self.adv = traded_value.rolling(21, min_periods=10).median()
        history = self.adj.notna().rolling(252, min_periods=1).sum() >= 240
        stale = (self.ret.abs() < 1e-12).rolling(10).sum() >= 8          # price not moving: suspended / illiquid
        self.tradable = history & self.adv.gt(0) & ~stale & self.adj.notna()
        self.mkt = self.ret.where(self.tradable).mean(axis=1)
        self.cost = self._cost_panel()

    def _cost_panel(self) -> pd.DataFrame:
        fr = FRICTIONS.get(self.name, Frictions((8, 15, 30)))
        pct = self.adv.where(self.tradable).rank(axis=1, pct=True, ascending=False)
        hs = pd.DataFrame(fr.half_spread[2], index=self.dates, columns=self.tickers, dtype=float)
        hs = hs.mask(pct <= 2 / 3, fr.half_spread[1]).mask(pct <= 1 / 3, fr.half_spread[0])
        tax = pd.Series(0.0, index=self.dates)
        for bp, start in fr.taxes:
            tax = tax + (bp if start is None else bp * (self.dates >= pd.Timestamp(start)))
        return (hs.add(tax, axis=0) + SLIPPAGE_BP) / 1e4

    # -- signals -------------------------------------------------------------
    def signals(self) -> dict[str, pd.DataFrame]:
        r, adj, tr = self.ret, self.adj, self.tradable
        lr = np.log1p(r)
        mom_12_1 = lr.rolling(231, min_periods=200).sum().shift(21)
        mom_6_1 = lr.rolling(105, min_periods=90).sum().shift(21)
        mkt = self.mkt
        cov = r.rolling(252, min_periods=150).cov(mkt)
        beta = cov.div(mkt.rolling(252, min_periods=150).var(), axis=0)
        resid = r - beta.mul(mkt, axis=0)
        resid_mom = resid.rolling(231, min_periods=200).sum().shift(21) / (resid.rolling(252, min_periods=150).std() * np.sqrt(231))
        high_52w = adj / adj.rolling(252, min_periods=200).max()
        sig = {
            "mom_12_1": mom_12_1, "mom_6_1": mom_6_1, "resid_mom": resid_mom, "high_52w": high_52w,
            "rev_1d": -r, "rev_5d": -lr.rolling(5).sum(), "rev_21d": -lr.rolling(21).sum(),
            "low_vol": -r.rolling(63, min_periods=40).std(), "low_beta": -beta,
            "size_proxy": -np.log(self.adv + 1), "max_effect": -r.rolling(21).max(),
            "amihud": np.log((r.abs() / (self.close * self.volume)).replace(np.inf, np.nan).rolling(21, min_periods=10).mean() + 1e-12),
        }
        return {k: zscore(v, tr) for k, v in sig.items()}


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
def ic_table(m: Market, sigs: dict, horizon: int) -> pd.DataFrame:
    fwd = (m.open.shift(-(1 + horizon)) / m.open.shift(-1) - 1).where(m.tradable)
    stress = m.vix > 20
    rows = []
    for name, z in sigs.items():
        ic = rank_ic(z, fwd)
        row = {"market": m.name, "signal": name, "horizon": horizon}
        for tag, a, b in IC_PERIODS:
            s = ic[a:b].dropna()
            row[f"ic_{tag}"] = s.mean() if len(s) > 50 else np.nan
        s = ic.dropna()
        row["ic_all"] = s.mean()
        row["t_all"] = s.mean() / s.std() * np.sqrt(len(s) / horizon) if len(s) > 50 else np.nan
        row["ic_calm"] = ic[~stress].mean()
        row["ic_stressed"] = ic[stress].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def unit_weights(z: pd.DataFrame, mask: pd.DataFrame, top_frac: float | None = None) -> pd.DataFrame:
    x = z.where(mask)
    if top_frac:
        pct = x.rank(axis=1, pct=True)
        x = x.where((pct >= 1 - top_frac) | (pct <= top_frac))
    x = x.sub(x.mean(axis=1), axis=0)
    return x.div(x.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def held(w: pd.DataFrame, offset: int) -> pd.DataFrame:
    reb = np.zeros(len(w), bool)
    reb[offset::REBAL] = True
    return w.where(pd.Series(reb, index=w.index), np.nan).ffill().fillna(0.0)


def held_sign(sign: pd.Series, offset: int) -> pd.Series:
    reb = np.zeros(len(sign), bool)
    reb[offset::REBAL] = True
    return sign.where(pd.Series(reb, index=sign.index), np.nan).ffill().fillna(1.0)


def pnl(W: pd.DataFrame, m: Market, hedge: pd.Series | None = None) -> pd.DataFrame:
    gross = (W * m.r1).sum(axis=1)
    turnover = W.diff().abs().sum(axis=1)
    cost = (W.diff().abs() * m.cost).sum(axis=1)
    net = gross - cost
    if hedge is not None:
        net = net - hedge
    return pd.DataFrame({"gross": gross, "net": net, "turnover": turnover})


def staggered(m: Market, z: pd.DataFrame, mask: pd.DataFrame, sign: pd.Series | None, top_frac: float | None = None) -> pd.DataFrame:
    w = unit_weights(z, mask, top_frac)
    W = 0
    for k in COHORTS:
        wk = held(w, k)
        if sign is not None:
            wk = wk.mul(held_sign(sign, k), axis=0)
        W = W + wk / len(COHORTS)
    return W


def long_only_flip(m: Market, z: pd.DataFrame, mask: pd.DataFrame, sign: pd.Series, quantile: float = 0.2) -> pd.DataFrame:
    """Long only, index-hedged: in calm long the top momentum quintile, in stress
    long the bottom quintile (the losers that rebound), equal-weighted, minus
    the equal-weighted market of the same universe (an index future in practice)."""
    x = z.where(mask)
    pct = x.rank(axis=1, pct=True)
    top = (pct >= 1 - quantile).astype(float)
    bot = (pct <= quantile).astype(float)
    W = 0
    for k in COHORTS:
        s = held_sign(sign, k)
        pick = top.mul(s > 0, axis=0) + bot.mul(s < 0, axis=0)
        pick = pick.div(pick.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        W = W + held(pick, k) / len(COHORTS)
    return W


def period_stats(net: pd.Series, label: str, extra: dict | None = None) -> dict:
    row = {"book": label}
    for tag, a, b in PERIODS:
        row[f"sharpe_{tag}"] = _sharpe(net[a:b])
    row["sharpe_2015_26"] = _sharpe(net["2015":])
    row["ret_2015_26"] = float(net["2015":].mean() * 252)
    row["vol_2015_26"] = float(net["2015":].std() * np.sqrt(252))
    row["maxdd_2015_26"] = _dd(net["2015":])
    row["first_year"] = int(net[net != 0].index[0].year) if (net != 0).any() else np.nan
    return {**row, **(extra or {})}


def run_market(m: Market, out: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    sigs = m.signals()
    ics = pd.concat([ic_table(m, sigs, 5), ic_table(m, sigs, 21)])
    comp = sum(sigs[s] for s in MOM) / len(MOM)
    vix_sign = pd.Series(np.where(m.vix > 20, -1.0, 1.0), index=m.dates)
    tr = m.tradable
    fin = tr & pd.DataFrame(np.repeat(m.financial.to_numpy()[None, :], len(m.dates), axis=0), index=m.dates, columns=m.tickers)
    mkt_r1 = m.r1.where(tr).mean(axis=1)
    fin_r1 = m.r1.where(fin).mean(axis=1)
    rows, daily = [], {}

    def book(label, W, hedge=None, **extra):
        p = pnl(W, m, hedge)
        rows.append(period_stats(p["net"], label, {"turnover": float(p["turnover"]["2015":].mean()),
                                                     "breakeven_bp": float(p["gross"]["2015":].sum() / max(p["turnover"]["2015":].sum(), 1e-9) * 1e4),
                                                     **extra}))
        daily[label] = p["net"]
        return p

    book("momentum, never flipped (L/S)", staggered(m, comp, tr, None))
    flip = book("momentum flip VIX>20 (L/S)", staggered(m, comp, tr, vix_sign))
    # local stress gauge: the market's own 21-day realised volatility above its expanding median (lagged a day)
    lv = m.mkt.rolling(21, min_periods=15).std()
    local_stress = lv > lv.expanding(min_periods=500).median().shift(1)
    local_sign = pd.Series(np.where(local_stress, -1.0, 1.0), index=m.dates)
    book("momentum flip, local-vol regime (L/S)", staggered(m, comp, tr, local_sign))
    beta = (flip["net"].rolling(252).cov(mkt_r1) / mkt_r1.rolling(252).var()).shift(1)
    rows.append(period_stats((flip["net"] - beta * mkt_r1).dropna(), "  flip, beta-hedged"))
    book("momentum flip, top/bottom 20% (L/S)", staggered(m, comp, tr, vix_sign, top_frac=0.2))
    lo = long_only_flip(m, comp, tr, vix_sign)
    book("long-only flip, minus market (hedged)", lo, hedge=mkt_r1)
    book("long-only, never flipped, minus market", long_only_flip(m, comp, tr, pd.Series(1.0, index=m.dates)), hedge=mkt_r1)
    book("reversal 21d (L/S, monthly)", staggered(m, sigs["rev_21d"], tr, None))
    n_fin = int(fin.sum(axis=1).median())
    if n_fin >= 10:
        book("financials only: momentum flip (L/S)", staggered(m, comp, fin, vix_sign), n_names=n_fin)
        book("financials only: long-only flip minus financials", long_only_flip(m, comp, fin, vix_sign, quantile=0.3), hedge=fin_r1, n_names=n_fin)
    res = pd.DataFrame(rows)
    res.insert(0, "market", m.name)
    pd.DataFrame(daily).to_csv(out / f"daily_{m.name.replace(' ', '_').replace('(', '').replace(')', '')}.csv")
    meta = {"market": m.name, "stocks": int(len(m.tickers)), "median_tradable": int(tr.sum(axis=1)["2015":].median()),
            "first_date": str(m.dates[0].date()), "financials": int(m.financial.sum()),
            "median_tradable_financials": n_fin, "short_note": FRICTIONS.get(m.name, Frictions((8, 15, 30))).short_note}
    return ics, res, meta


def pooled_financials(markets: dict[str, Market], region: tuple[str, ...], label: str) -> pd.DataFrame:
    """Country-neutral book of all financials in the region: within each market,
    rank financials on the momentum composite; unit-gross long/short per market,
    markets combined with equal risk (inverse trailing vol of each market's book),
    flipped by the US VIX. Local-currency returns (currency-hedged)."""
    books = {}
    for name in region:
        m = markets.get(name)
        if m is None:
            continue
        sigs = m.signals()
        comp = sum(sigs[s] for s in MOM) / len(MOM)
        fin = m.tradable & pd.DataFrame(np.repeat(m.financial.to_numpy()[None, :], len(m.dates), axis=0), index=m.dates, columns=m.tickers)
        if int(fin.sum(axis=1).median()) < 6:
            continue
        sign = pd.Series(np.where(m.vix > 20, -1.0, 1.0), index=m.dates)
        books[name] = {"flip": pnl(staggered(m, comp, fin, sign), m)["net"], "plain": pnl(staggered(m, comp, fin, None), m)["net"]}
    rows = []
    for kind in ("plain", "flip"):
        R = pd.DataFrame({k: v[kind] for k, v in books.items()}).sort_index()
        R = R.groupby(R.index).last()
        vol = R.rolling(252, min_periods=126).std().shift(1)
        w = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
        port = (w * R).sum(axis=1).where(w.notna().any(axis=1))
        rows.append(period_stats(port.dropna(), f"{label}: momentum {'flip VIX>20' if kind == 'flip' else 'never flipped'}",
                                 {"markets": ", ".join(books)}))
        if kind == "flip":
            port.to_csv(Path(OUT) / f"daily_pooled_{label.replace(' ', '_')}.csv")
    return pd.DataFrame(rows)


def country_etf_flip(series: pd.DataFrame, vix: pd.Series) -> pd.DataFrame:
    """Cross-country momentum on the US-listed country ETFs (USD), monthly,
    long the top third / short the bottom third by 12-1 month return, flipped by
    the VIX; 5 bp per unit traded."""
    etf = series[[c for c in series.columns if c.startswith("etf:") and c not in ("etf:US", "etf:Emerging", "etf:EAFE", "etf:Asia ex-Japan")]]
    etf = etf.dropna(axis=1, thresh=252 * 5)
    r = etf.pct_change(fill_method=None)
    mom = np.log1p(r).rolling(231, min_periods=200).sum().shift(21)
    v = vix.reindex(etf.index, method="ffill")
    rows = []
    for label, sign in (("country ETF momentum, never flipped", pd.Series(1.0, index=etf.index)),
                        ("country ETF momentum flip VIX>20", pd.Series(np.where(v > 20, -1.0, 1.0), index=etf.index))):
        pct = mom.rank(axis=1, pct=True)
        w = ((pct >= 2 / 3).astype(float) - (pct <= 1 / 3).astype(float)).where(mom.notna(), 0.0)
        w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        W = 0
        for k in COHORTS:
            W = W + held(w, k).mul(held_sign(sign, k), axis=0) / len(COHORTS)
        net = (W.shift(2) * r).sum(axis=1) - W.diff().abs().sum(axis=1) * 5e-4
        rows.append(period_stats(net["2004":], label, {"etfs": int(etf.shape[1])}))
    return pd.DataFrame(rows)


def market_selection(res: pd.DataFrame, out: Path) -> pd.DataFrame:
    """The honest way to use the per-market results: decide per market on
    2006-14 only (flip if the flip beat plain momentum then, else plain
    momentum), then combine the chosen books with equal weights and report
    2015-26. Compared with 'flip everywhere' and 'never flip anywhere'."""
    piv = res.pivot(index="market", columns="book", values="sharpe_2006_14")
    flip_col, plain_col = "momentum flip VIX>20 (L/S)", "momentum, never flipped (L/S)"
    choice = {mk: (flip_col if piv.loc[mk, flip_col] > piv.loc[mk, plain_col] else plain_col)
              for mk in piv.index if np.isfinite(piv.loc[mk, flip_col]) and np.isfinite(piv.loc[mk, plain_col])}
    daily = {}
    for mk in choice:
        f = out / f"daily_{mk.replace(' ', '_').replace('(', '').replace(')', '')}.csv"
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        daily[mk] = d
    rows = []
    for label, pick in (("chosen per market on 2006-14", choice), ("flip in every market", {k: flip_col for k in choice}),
                        ("never flip anywhere", {k: plain_col for k in choice})):
        R = pd.DataFrame({k: daily[k][c] for k, c in pick.items()}).sort_index()
        R = R.groupby(R.index).last()
        vol = R.rolling(252, min_periods=126).std().shift(1)
        w = (1 / vol).div((1 / vol).sum(axis=1), axis=0)
        port = (w * R).sum(axis=1).where(w.notna().any(axis=1)).dropna()
        rows.append(period_stats(port, f"equal-risk book across markets: {label}"))
    tab = pd.DataFrame(rows)
    pd.Series(choice).rename("chosen").to_csv(out / "market_choice.csv")
    tab.to_csv(out / "market_selection.csv", index=False)
    print(tab.round(2).to_string(index=False))
    return tab


OUT = "reports/intl"


def main(argv=None):
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices")
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--out", default="reports/intl")
    ap.add_argument("--markets", default=None)
    args = ap.parse_args(argv)
    OUT = args.out
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    u = pd.read_csv(args.universe)
    series = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")
    vix = series["vol:US"].dropna()
    names = args.markets.split(",") if args.markets else list(dict.fromkeys(u["market"]))
    markets, all_ics, all_res, metas = {}, [], [], []
    for name in names:
        p = Path(args.prices) / name.replace(" ", "_").replace("(", "").replace(")", "")
        if not (p / "adj_close.parquet").exists():
            print(f"{name}: no prices")
            continue
        try:
            m = Market(name, p, u[u["market"] == name], vix)
            ics, res, meta = run_market(m, out)
        except Exception as exc:  # noqa: BLE001 - one market must not stop the rest
            print(f"{name}: FAILED {type(exc).__name__}: {exc}")
            continue
        markets[name] = m
        all_ics.append(ics), all_res.append(res), metas.append(meta)
        f = res.set_index("book")
        print(f"{name:22s} flip L/S {f.loc['momentum flip VIX>20 (L/S)', 'sharpe_2006_14']:5.2f} / "
              f"{f.loc['momentum flip VIX>20 (L/S)', 'sharpe_2015_20']:5.2f} / {f.loc['momentum flip VIX>20 (L/S)', 'sharpe_2021_26']:5.2f}"
              f"   never flipped {f.loc['momentum, never flipped (L/S)', 'sharpe_2015_26']:5.2f} (2015-26)")
    ics = pd.concat(all_ics)
    res = pd.concat(all_res)
    asia = ("Japan", "Hong Kong", "Hong Kong (H-shares)", "China", "Korea", "Taiwan", "Singapore", "Australia", "India",
            "Malaysia", "Thailand", "New Zealand")
    europe = ("UK", "Germany", "France", "Switzerland", "Netherlands", "Spain", "Italy", "Sweden")
    pooled = pd.concat([pooled_financials(markets, asia, "Asian financials"),
                        pooled_financials(markets, europe, "European financials"),
                        pooled_financials(markets, asia + europe + ("Canada",), "All non-US financials")])
    etf = country_etf_flip(series, vix)
    selection = market_selection(res, out)
    ics.to_csv(out / "signal_ic.csv", index=False)
    res.to_csv(out / "books.csv", index=False)
    pooled.to_csv(out / "pooled_financials.csv", index=False)
    etf.to_csv(out / "country_etf.csv", index=False)
    pd.DataFrame(metas).to_csv(out / "markets.csv", index=False)
    print(pooled.round(2).to_string(index=False))
    print(etf.round(2).to_string(index=False))
    (out / "summary.json").write_text(json.dumps({"markets": len(markets)}, indent=2))


if __name__ == "__main__":
    main()
