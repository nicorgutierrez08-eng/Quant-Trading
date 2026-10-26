"""News and media vs stock moves: a brute-force correlation scan.

Every dataset collected by ``qtrade.data.media`` (GDELT online news and TV,
Hacker News, SEC filings and full-text phrases, Wikipedia) plus the Benzinga
headlines from Alpaca is turned into per-stock daily features and correlated
with the stocks' moves, and ~90 market-wide news themes with ETF moves.

Timing: a feature is dated by the first trading day whose **open** comes after
the information was public (a GDELT or Wikipedia day d -> the next session; an
article or filing at time t -> the first 9:30 after t). Targets, relative to
the average stock that day:

  past_1d     open of the day before -> today's open (the move *during* the news:
              descriptive, not tradable - "the news follows the price")
  intraday    today's open -> close
  next_1d     today's open -> tomorrow's open
  next_5d     today's open -> the open 5 sessions later
  next_20d    ... 20 sessions later
  abs_next_1d the size of next_1d (does attention predict volatility?)

Per-stock features: cross-sectional rank correlation each day (IC), averaged;
t-statistics from the daily IC series (divided by sqrt(horizon) for overlapping
horizons); top-minus-bottom fifth (or event-minus-rest) spread in bp. Market
themes: time-series correlation with next-day / week / month ETF returns and
VIX changes. Both on 2016/17-2021 and 2022-2026: a correlation that is real
should have the same sign in both halves.

Hundreds of tests are run, so about 5% clear |t| > 2 by luck; the report counts
how many clear it against that expectation.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

SPLIT = "2022-01-01"
NY = "America/New_York"
TARGETS = ["past_1d", "intraday", "next_1d", "next_5d", "next_20d", "abs_next_1d"]
HORIZON = {"past_1d": 1, "intraday": 1, "next_1d": 1, "next_5d": 5, "next_20d": 20, "abs_next_1d": 1}
TRADABLE = {"intraday", "next_1d", "next_5d", "next_20d", "abs_next_1d"}

HEADLINE_FLAGS = {
    "upgrade": r"\bupgrad", "downgrade": r"\bdowngrad",
    "pt_raised": r"(raises|lifts|boosts|increases) (price target|pt)|price target (raised|increased)",
    "pt_cut": r"(cuts|lowers|reduces) (price target|pt)|price target (lowered|cut|reduced)",
    "beat": r"\bbeats?\b|tops (estimates|expectations)|above (estimates|expectations)",
    "miss": r"\bmiss(es)?\b|below (estimates|expectations)",
    "guidance_up": r"raises (fy|full[- ]year|annual|guidance|outlook|forecast)|(guidance|outlook) (raised|above)",
    "guidance_down": r"(cuts|lowers|slashes) (fy|full[- ]year|annual|guidance|outlook|forecast)|(guidance|outlook) below",
    "fda": r"\bfda\b", "lawsuit": r"lawsuit|class action|\bsues\b|\bsued\b",
    "investigation": r"investigation|\bprobe\b|subpoena", "buyback": r"buyback|repurchase",
    "dividend_up": r"(raises|increases|hikes|boosts) (quarterly |annual )?dividend",
    "offering": r"\boffering\b|prices .* shares", "deal": r"\bacquir|acquisition|merger|to buy\b",
    "layoffs": r"layoff|job cuts|cuts? .* jobs|workforce reduction",
    "ceo_change": r"\bceo\b.*(steps down|resign|depart|retire|replace)|names .* ceo|new ceo",
    "short_report": r"short (seller|report)", "options_activity": r"unusual options|options activity|option alert",
    "insider_buy": r"insider (buy|purchase)|director (buys|bought)", "halt": r"\bhalt",
    "record": r"record (high|revenue|quarter|sales)", "new_high": r"52-week high|all-time high|record high",
    "new_low": r"52-week low", "contract": r"\bcontract\b|\baward", "partnership": r"partner",
    "recall": r"\brecall", "bankruptcy": r"bankrupt|chapter 11",
}

FILING_EVENTS = {
    "form4": lambda f, it: f == "4", "form3": lambda f, it: f == "3", "form144": lambda f, it: f == "144",
    "13d": lambda f, it: f.startswith("SC 13D"), "13g": lambda f, it: f.startswith("SC 13G"),
    "s3": lambda f, it: f.startswith("S-3"), "424b": lambda f, it: f.startswith("424B"),
    "nt_late": lambda f, it: f.startswith("NT "), "def14a": lambda f, it: f == "DEF 14A",
    "10k": lambda f, it: f == "10-K", "10q": lambda f, it: f == "10-Q",
    **{f"8k_{i}": (lambda i: lambda f, it: f.startswith("8-K") and i in it)(i)
       for i in ("1.01", "1.02", "2.01", "2.03", "2.05", "2.06", "3.01", "3.02", "4.01", "4.02", "5.02", "5.03",
                 "5.07", "7.01", "8.01")},
}


# -----------------------------------------------------------------------------
# alignment
# -----------------------------------------------------------------------------
def entry_of_days(days: pd.DatetimeIndex, dates: pd.DatetimeIndex) -> np.ndarray:
    """Position in ``dates`` of the first session after calendar day d (len(dates) if none)."""
    return dates.searchsorted(pd.DatetimeIndex(days).normalize(), side="right")


def entry_of_times(ts: pd.Series, dates: pd.DatetimeIndex) -> np.ndarray:
    """Position of the first session whose 9:30 open comes after time t."""
    t = pd.to_datetime(ts, utc=True).dt.tz_convert(NY).dt.tz_localize(None) - pd.Timedelta(hours=9, minutes=30)
    return dates.searchsorted(t.dt.normalize(), side="right")


def daily_to_panel(df: pd.DataFrame, dates: pd.DatetimeIndex, tickers, how: str = "sum") -> pd.DataFrame:
    """Calendar-daily (date x ticker) values -> trading-day panel by entry session."""
    if df is None or df.empty:
        return pd.DataFrame(index=dates, columns=list(tickers), dtype=float)
    df = df.reindex(columns=[t for t in tickers if t in df.columns])
    pos = entry_of_days(df.index, dates)
    ok = pos < len(dates)
    g = df[ok].groupby(dates[pos[ok]])
    out = g.sum(min_count=1) if how == "sum" else g.mean()
    first = dates[min(pos[ok].min(), len(dates) - 1)] if ok.any() else dates[-1]
    out = out.reindex(index=dates, columns=list(tickers))
    if how == "sum":
        out = out.fillna(0.0)
    return out.where(pd.Series(dates >= first, index=dates), np.nan, axis=0)


def events_to_panel(ev: pd.DataFrame, dates: pd.DatetimeIndex, tickers, value: str | None = None,
                    entry: np.ndarray | None = None) -> pd.DataFrame:
    """Rows (ticker, entry position[, value]) -> counts (or sums) per session and ticker."""
    pos = entry if entry is not None else ev["entry"].to_numpy()
    ok = (pos < len(dates)) & ev["ticker"].isin(set(tickers)).to_numpy()
    x = ev[ok].assign(day=dates[pos[ok]])
    g = x.groupby(["day", "ticker"])
    m = (g[value].sum() if value else g.size()).unstack()
    return m.reindex(index=dates, columns=list(tickers)).fillna(0.0)


# -----------------------------------------------------------------------------
# features
# -----------------------------------------------------------------------------
def count_features(name: str, C: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Attention features from a count (or views / airtime) panel."""
    base = C.rolling(60, min_periods=20).mean().shift(1)
    L = np.log1p(C.clip(lower=0))
    return {f"{name}:abnormal": L - np.log1p(base),
            f"{name}:abnormal_5d": np.log1p(C.rolling(5).sum()) - np.log1p(5 * C.rolling(60, min_periods=20).mean().shift(5)),
            f"{name}:level": L,
            f"{name}:spike": ((C > 3 * base) & (C > 0)).astype(float).where(base.notna())}


def tone_features(name: str, T: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {f"{name}:tone": T, f"{name}:tone_change": T - T.rolling(30, min_periods=10).mean().shift(1)}


def event_features(name: str, E: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {f"{name}": (E > 0).astype(float), f"{name}:last_5d": (E.rolling(5).sum() > 0).astype(float)}


def targets(md) -> dict[str, pd.DataFrame]:
    o, c = md.open, md.close
    out = {"past_1d": o / o.shift(1) - 1, "intraday": c / o - 1, "next_1d": o.shift(-1) / o - 1,
           "next_5d": o.shift(-5) / o - 1, "next_20d": o.shift(-20) / o - 1}
    out = {k: v.clip(-0.5, 0.5) for k, v in out.items()}
    out = {k: v.sub(v.mean(axis=1), axis=0) for k, v in out.items()}
    raw = (o.shift(-1) / o - 1).clip(-0.5, 0.5)
    out["abs_next_1d"] = raw.abs()
    return out


# -----------------------------------------------------------------------------
# statistics
# -----------------------------------------------------------------------------
def _row_ranks(a: np.ndarray) -> np.ndarray:
    return pd.DataFrame(a).rank(axis=1).to_numpy()


def daily_ic(F: np.ndarray, R: np.ndarray, mask: np.ndarray, binary: bool,
             min_names: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """(daily rank IC, daily top-minus-bottom spread) over the names valid in both."""
    valid = mask & np.isfinite(F) & np.isfinite(R)
    Fv = np.where(valid, F, np.nan)
    Fr = _row_ranks(Fv)
    Rr = _row_ranks(np.where(valid, R, np.nan))                # ranks among the names valid in both
    n = valid.sum(axis=1)
    fm, rm = np.nanmean(Fr, axis=1, keepdims=True), np.nanmean(Rr, axis=1, keepdims=True)
    num = np.nansum((Fr - fm) * (Rr - rm), axis=1)
    den = np.sqrt(np.nansum((Fr - fm) ** 2, axis=1) * np.nansum((Rr - rm) ** 2, axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        ic = np.where((n >= min_names) & (den > 0), num / den, np.nan)
    Rv = np.where(valid, R, np.nan)
    if binary:
        hit = valid & (Fv > 0)
        with np.errstate(invalid="ignore"):
            top = np.where(hit.sum(axis=1) > 0, np.nansum(np.where(hit, Rv, 0), axis=1) / hit.sum(axis=1), np.nan)
            rest = valid & ~hit
            bot = np.where(rest.sum(axis=1) > 0, np.nansum(np.where(rest, Rv, 0), axis=1) / rest.sum(axis=1), np.nan)
    else:
        q = Fr / np.maximum(n, 1)[:, None]
        hi, lo = valid & (q > 0.8), valid & (q <= 0.2)
        with np.errstate(invalid="ignore"):
            top = np.where(hi.sum(axis=1) > 0, np.nansum(np.where(hi, Rv, 0), axis=1) / hi.sum(axis=1), np.nan)
            bot = np.where(lo.sum(axis=1) > 0, np.nansum(np.where(lo, Rv, 0), axis=1) / lo.sum(axis=1), np.nan)
    spread = np.where(n >= min_names, top - bot, np.nan)
    return ic, spread


def _t(x: np.ndarray, h: int) -> tuple[float, float, int]:
    x = x[np.isfinite(x)]
    if len(x) < 60 or x.std() == 0:
        return np.nan, np.nan, len(x)
    return float(x.mean()), float(x.mean() / x.std() * np.sqrt(len(x) / h)), len(x)


def scan_cross(feats: dict[str, pd.DataFrame], tg: dict[str, pd.DataFrame], mask: pd.DataFrame,
               source: str) -> list[dict]:
    dates = mask.index
    a = np.asarray(dates < SPLIT)
    rows = []
    for fname, F in feats.items():
        Fa = F.reindex(index=dates, columns=mask.columns).to_numpy(dtype=float)
        if not np.isfinite(Fa).any():
            continue
        binary = bool(np.isin(Fa[np.isfinite(Fa)], (0.0, 1.0)).all())
        if binary and np.nansum(Fa) < 50:                  # too few events to say anything
            continue
        names_per_day = float(np.mean((np.isfinite(Fa) & (Fa != 0) & mask.to_numpy()).sum(axis=1)))
        for tname, R in tg.items():
            ic, sp = daily_ic(Fa, R, mask.to_numpy(), binary)
            h = HORIZON[tname]
            row = {"source": source, "feature": fname, "target": tname, "tradable": tname in TRADABLE,
                   "binary": binary, "names_per_day": round(names_per_day, 1)}
            for tag, m in (("A", a), ("B", ~a), ("all", np.ones_like(a))):
                row[f"ic_{tag}"], row[f"t_{tag}"], row[f"days_{tag}"] = _t(ic[m], h)
                sm = sp[m]
                sm = sm[np.isfinite(sm)]
                row[f"spread_bp_{tag}"] = float(sm.mean() * 1e4) if len(sm) else np.nan
            rows.append(row)
    return rows


def scan_market(series: dict[str, pd.Series], etf_close: pd.DataFrame) -> list[dict]:
    """Market-wide news series (dated by entry session) vs ETF returns from that session's close."""
    rows = []
    dates = etf_close.index
    a = np.asarray(dates < SPLIT)
    rets = {}
    for col in etf_close.columns:
        c = etf_close[col]
        if col.startswith("^"):                                        # VIX: change in level
            rets[(col, "same_day")] = c - c.shift(1)
            for h in (1, 5):
                rets[(col, f"next_{h}d")] = c.shift(-h) - c
        else:
            lr = np.log(c)
            rets[(col, "same_day")] = lr - lr.shift(1)
            for h in (1, 5, 20):
                rets[(col, f"next_{h}d")] = lr.shift(-h) - lr
    for name, s in series.items():
        x = s.reindex(dates)
        if x.notna().sum() < 250:
            continue
        for (col, hz), r in rets.items():
            h = 1 if hz == "same_day" else int(hz.split("_")[1][:-1])
            row = {"feature": name, "asset": col, "horizon": hz, "tradable": hz != "same_day"}
            for tag, m in (("A", a), ("B", ~a), ("all", np.ones_like(a))):
                xx, rr = x[m], r[m]
                ok = xx.notna() & rr.notna()
                n = int(ok.sum())
                cr = float(np.corrcoef(xx[ok], rr[ok])[0, 1]) if n > 60 and xx[ok].std() > 0 else np.nan
                row[f"corr_{tag}"], row[f"t_{tag}"], row[f"n_{tag}"] = cr, cr * np.sqrt(n / h) if n else np.nan, n
            rows.append(row)
    return rows


# -----------------------------------------------------------------------------
# sources -> features
# -----------------------------------------------------------------------------
def _read(root: Path, name: str) -> pd.DataFrame | None:
    p = root / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else None


def media_feature_sets(md, mroot: Path, data_root: str, names: dict[str, str]) -> dict[str, dict]:
    """{source: {feature name: panel}} for every dataset that is present."""
    dates, tickers = md.dates, list(md.tickers)
    out = {}
    v = _read(mroot, "gdelt_company_timelinevolraw")
    if v is not None:
        out["gdelt_news"] = count_features("gdelt_news", daily_to_panel(v, dates, tickers))
    t = _read(mroot, "gdelt_company_timelinetone")
    if t is not None:
        out["gdelt_tone"] = tone_features("gdelt_news", daily_to_panel(t, dates, tickers, "mean"))
    tv = _read(mroot, "tv_company_timelinevol")
    if tv is not None:
        out["tv_news"] = count_features("tv_news", daily_to_panel(tv * 1000, dates, tickers))
    hn = _read(mroot, "hn_stories")
    if hn is not None and len(hn):
        m = hn_mentions(hn, names)
        if len(m):
            m["entry"] = entry_of_times(m["created_at"], dates)
            out["hacker_news"] = {**count_features("hn_stories", events_to_panel(m, dates, tickers)),
                                  **count_features("hn_points", events_to_panel(m, dates, tickers, "points"))}
    views = []
    for p in (Path(data_root) / "public" / "consumer" / "wiki_pageviews.parquet", mroot / "wiki_extra_pageviews.parquet"):
        if p.exists():
            views.append(pd.read_parquet(p))
    if views:
        w = pd.concat(views, axis=1)
        w = w.loc[:, ~w.columns.duplicated()]
        out["wikipedia"] = count_features("wiki_views", daily_to_panel(w, dates, tickers))
    f = _read(mroot, "sec_filings")
    if f is not None and len(f):
        f = f.assign(entry=entry_of_times(f["accepted"], dates))
        feats = {}
        for ev, rule in FILING_EVENTS.items():
            sel = f[[rule(str(a), str(b)) for a, b in zip(f["form"], f["items"])]]
            if len(sel) >= 50:
                feats.update(event_features(f"sec_{ev}", events_to_panel(sel, dates, tickers)))
        f4 = f[f["form"] == "4"]
        if len(f4):
            feats.update(count_features("sec_form4_count", events_to_panel(f4, dates, tickers)))
        out["sec_filings"] = feats
    ph = _read(mroot, "sec_phrase_hits")
    if ph is not None and len(ph):
        from ..data.fundamentals import SecClient, ticker_to_cik

        try:
            inv = {c: t for t, c in ticker_to_cik(SecClient()).items()}
            ph = ph.assign(ticker=ph["cik"].map(inv)).dropna(subset=["ticker"])
            ph["entry"] = entry_of_days(pd.to_datetime(ph["file_date"]), dates)
            feats = {}
            for p_, g in ph.groupby("phrase"):
                if len(g) >= 50:
                    feats.update(event_features(f"8k_says:{p_}", events_to_panel(g, dates, tickers)))
            out["sec_phrases"] = feats
        except Exception as exc:
            LOG.warning("SEC phrase mapping failed: %s", exc)
    return out


def hn_mentions(hn: pd.DataFrame, names: dict[str, str]) -> pd.DataFrame:
    """Stories whose title names a company (exact, case-sensitive word n-gram match)."""
    lookup = {}
    for t, n in names.items():
        if len(n) >= 4 or " " in n:
            lookup.setdefault(n, t)
    rows = []
    for title, ts, pts in zip(hn["title"].astype(str), hn["created_at"], hn["points"]):
        words = re.findall(r"[A-Za-z0-9&'.\-]+", title)
        found = set()
        for k in (1, 2, 3, 4):
            for i in range(len(words) - k + 1):
                g = " ".join(words[i:i + k]).rstrip(".'")
                if g in lookup:
                    found.add(lookup[g])
        rows += [{"ticker": t, "created_at": ts, "points": pts} for t in found]
    return pd.DataFrame(rows)


def benzinga_feature_sets(md, news: pd.DataFrame) -> dict[str, dict]:
    from .alt_signals import _tone

    if news is None or news.empty:
        return {}
    dates, tickers = md.dates, list(md.tickers)
    x = news[["created_at", "headline", "symbols"]].copy()
    x["headline"] = x["headline"].fillna("").astype(str)
    x["tone"] = x["headline"].map(_tone)
    low = x["headline"].str.lower()
    for k, pat in HEADLINE_FLAGS.items():
        pat = re.sub(r"\((?!\?)", "(?:", pat)                  # non-capturing: no pandas warning
        x[k] = low.str.contains(pat, regex=True).astype(float)
    x["entry"] = entry_of_times(x["created_at"], dates)
    x["ticker"] = x["symbols"].fillna("").str.split(",")
    x["n_tagged"] = x["ticker"].str.len()
    x = x.explode("ticker")
    x = x[x["ticker"].isin(set(tickers))]
    C = events_to_panel(x, dates, tickers)
    solo = events_to_panel(x[x["n_tagged"] == 1], dates, tickers)
    T = events_to_panel(x, dates, tickers, "tone") / C.replace(0, np.nan)
    feats = {**count_features("benzinga_articles", C), **count_features("benzinga_solo_articles", solo),
             **tone_features("benzinga", T)}
    kw = {}
    for k in HEADLINE_FLAGS:
        E = events_to_panel(x[x[k] > 0], dates, tickers) if (x[k] > 0).any() else None
        if E is not None and E.to_numpy().sum() >= 50:
            kw.update(event_features(f"headline:{k}", E))
    return {"benzinga": feats, "benzinga_headlines": kw}


def market_series(mroot: Path, dates: pd.DatetimeIndex, news: pd.DataFrame | None) -> dict[str, pd.Series]:
    """Market-wide news series by entry session: abnormal share of coverage, tone, TV airtime."""
    out = {}
    tot = _read(mroot, "gdelt_total_articles")
    total = tot["all"] if tot is not None and "all" in tot else None

    def to_sessions(s: pd.Series, how="mean") -> pd.Series:
        pos = entry_of_days(s.index, dates)
        ok = pos < len(dates)
        g = s[ok].groupby(dates[pos[ok]])
        return (g.sum() if how == "sum" else g.mean()).reindex(dates)

    def abnormal(s: pd.Series) -> pd.Series:
        ls = np.log(s.clip(lower=1e-9))
        return ls - ls.rolling(60, min_periods=20).mean().shift(1)

    v = _read(mroot, "gdelt_theme_timelinevolraw")
    if v is not None:
        for k in v.columns:
            s = v[k] / total.reindex(v.index) if total is not None else v[k]
            out[f"news_share:{k}"] = abnormal(to_sessions(s.dropna()))
    t = _read(mroot, "gdelt_theme_timelinetone")
    if t is not None:
        for k in t.columns:
            s = to_sessions(t[k].dropna())
            out[f"news_tone:{k}"] = s
            out[f"news_tone_change:{k}"] = s - s.rolling(30, min_periods=10).mean().shift(1)
    tv = _read(mroot, "tv_theme_timelinevol")
    if tv is not None:
        for k in tv.columns:
            out[f"tv_airtime:{k}"] = abnormal(to_sessions(tv[k].dropna() + 1e-4))
    hn = _read(mroot, "hn_stories")
    if hn is not None and len(hn):
        cnt = pd.Series(1.0, index=pd.to_datetime(hn["created_at"], utc=True).dt.tz_convert(NY).dt.tz_localize(None))
        out["hacker_news:stories"] = abnormal(to_sessions(cnt.resample("D").sum(), "sum").replace(0, np.nan))
    ph = _read(mroot, "sec_phrase_hits")
    if ph is not None and len(ph):
        for p_, g in ph.groupby("phrase"):
            s = g.groupby(pd.to_datetime(g["file_date"])).size().astype(float)
            s = s.reindex(pd.date_range(s.index.min(), s.index.max()), fill_value=0.0)
            out[f"8k_says:{p_}"] = abnormal(to_sessions(s.rolling(5, min_periods=1).sum() + 1, "mean"))
    if news is not None and len(news):
        nt = pd.Series(1.0, index=pd.to_datetime(news["created_at"], utc=True).dt.tz_convert(NY).dt.tz_localize(None))
        out["benzinga:all_articles"] = abnormal(to_sessions(nt.resample("D").sum(), "sum").replace(0, np.nan))
    return out


# -----------------------------------------------------------------------------
def _top(df: pd.DataFrame, t: str, n: int = 25) -> pd.DataFrame:
    d = df[np.sign(df[f"{t}_A"]) == np.sign(df[f"{t}_B"])].copy()
    d["weaker_half_t"] = np.minimum(d[f"t_A"].abs(), d[f"t_B"].abs())
    return d.sort_values("weaker_half_t", ascending=False).head(n)


def run(md, ctx, out: Path, cfg) -> dict:
    from ..data.media import company_names, inventory, media_root

    mroot = media_root()
    data_root = cfg.data.cache_dir
    inv = inventory(mroot)
    inv.to_csv(out / "news_zoo_inventory.csv", index=False)
    names = company_names(list(md.tickers), data_root)
    news = None
    npath = Path(data_root) / "news"
    if any(npath.glob("news_*.parquet")):
        from ..data.news import load_news

        news = load_news(npath)
    sets = media_feature_sets(md, mroot, data_root, names)
    sets.update(benzinga_feature_sets(md, news))
    LOG.info("news zoo: %s", {k: len(v) for k, v in sets.items()})
    tg = {k: v.to_numpy(dtype=float) for k, v in targets(md).items()}
    mask = ctx.tradable.reindex(index=md.dates, columns=md.tickers).fillna(False)
    rows = []
    for src, feats in sets.items():
        LOG.info("news zoo: scanning %s (%d features)", src, len(feats))
        rows += scan_cross(feats, tg, mask, src)
    cross = pd.DataFrame(rows)
    cross.to_csv(out / "news_zoo_cross.csv", index=False)
    mk = pd.DataFrame()
    try:
        from .strategies import _etfs

        etf = _etfs("2015-06-01").close
        keep = [c for c in ["SPY", "QQQ", "IWM", "TLT", "GLD", "USO", "HYG", "UUP"] + [
            "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "^VIX"] if c in etf.columns]
        ser = market_series(mroot, etf.index, news)
        mk = pd.DataFrame(scan_market(ser, etf[keep]))
        mk.to_csv(out / "news_zoo_market.csv", index=False)
    except Exception as exc:
        LOG.warning("market-wide scan failed: %s", exc)
    return report(cross, mk, inv, out)


def report(cross: pd.DataFrame, mk: pd.DataFrame, inv: pd.DataFrame, out: Path) -> dict:
    lines = ["## News and media vs stock moves: correlation scan", "",
             "Every collected news / media dataset turned into per-stock daily features (dated by the first open "
             "after the information was public) and correlated with the stocks' moves (relative to the average "
             "stock); market-wide news themes against ETF returns. A = 2016/17-2021, B = 2022-2026. "
             "'weaker half t' = the smaller |t| of the two halves (same sign required).", "",
             "### Data collected", "", inv.to_markdown(index=False) if len(inv) else "(no media data yet)", ""]
    summary = {}
    if len(cross):
        n = len(cross)
        both = ((np.sign(cross["ic_A"]) == np.sign(cross["ic_B"])) & (cross["t_A"].abs() > 2)
                & (cross["t_B"].abs() > 2)).sum()
        big = (cross["t_all"].abs() > 2).sum()
        lines += ["### Per-stock features", "",
                  f"{n} feature-target pairs. |t| > 2 over the whole period: {big} (about {0.05 * n:.0f} expected by "
                  f"luck). Same sign and |t| > 2 in both halves: {both} (about {0.0013 * n:.1f} expected by luck).", ""]
        cols = ["source", "feature", "target", "names_per_day", "ic_A", "t_A", "ic_B", "t_B", "spread_bp_A",
                "spread_bp_B", "weaker_half_t"]
        trad = cross[cross["tradable"] & (cross["target"] != "abs_next_1d")]
        lines += ["#### Predict the next move (tradable)", "",
                  _top(trad, "ic")[cols].round(4).to_markdown(index=False), "",
                  "#### Predict the size of the next move (volatility)", "",
                  _top(cross[cross["target"] == "abs_next_1d"], "ic")[cols].round(4).to_markdown(index=False), "",
                  "#### Move together with the news (same window: descriptive, not tradable)", "",
                  _top(cross[cross["target"] == "past_1d"], "ic")[cols].round(4).to_markdown(index=False), ""]
        summary["cross_tests"], summary["cross_both_halves_t2"] = int(n), int(both)
        summary["top_tradable"] = _top(trad, "ic", 10)[["feature", "target", "ic_A", "ic_B", "t_A", "t_B"]].round(
            4).to_dict(orient="records")
    if len(mk):
        n = len(mk)
        both = ((np.sign(mk["corr_A"]) == np.sign(mk["corr_B"])) & (mk["t_A"].abs() > 2) & (mk["t_B"].abs() > 2)).sum()
        cols = ["feature", "asset", "horizon", "corr_A", "t_A", "corr_B", "t_B", "weaker_half_t"]
        lines += ["### Market-wide news themes vs ETFs", "",
                  f"{n} theme-asset-horizon pairs; same sign and |t| > 2 in both halves: {both} "
                  f"(about {0.0013 * n:.1f} expected by luck).", "",
                  "#### Predictive (from the next close on)", "",
                  _top(mk[mk["tradable"]], "corr")[cols].round(4).to_markdown(index=False), "",
                  "#### Same day (descriptive)", "",
                  _top(mk[~mk["tradable"]], "corr")[cols].round(4).to_markdown(index=False), ""]
        summary["market_tests"], summary["market_both_halves_t2"] = int(n), int(both)
    (out / "news_zoo.md").write_text("\n".join(lines) + "\n")
    return summary
