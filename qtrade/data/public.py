"""Free public datasets beyond prices: macro series, index changes, short
volume, insider trades, and a survivorship-free stock universe.

Every loader caches what it downloads under ``data/public/`` and returns
point-in-time data: each value carries the date it became public.

* FRED macro series (St. Louis Fed; no key needed)
* S&P 500 additions and removals (Wikipedia's change table)
* FINRA Reg SHO daily short-sale volume (off-exchange; consolidated file since Aug 2018)
* SEC insider transactions (Forms 3/4/5 data sets, quarterly since 2006)
* Alpaca daily bars for every US stock, including delisted ones, since 2016
"""
from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
# series: (FRED id, days of publication lag to apply)
FRED_SERIES = {
    "term_spread_10y2y": ("T10Y2Y", 1),
    "term_spread_10y3m": ("T10Y3M", 1),
    "credit_spread_baa": ("BAA10Y", 1),
    "real_rate_10y": ("DFII10", 1),
    "dollar_index": ("DTWEXBGS", 1),
    "oil_wti": ("DCOILWTICO", 1),
    "vix": ("VIXCLS", 1),
    "fin_conditions": ("NFCI", 7),          # weekly, published the following Wednesday
    "jobless_claims": ("ICSA", 7),          # weekly, published the following Thursday
}
SP500_WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
REGSHO_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt"
INSIDER_URL = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{y}q{q}_form345.zip"


def _session(sec: bool = False):
    import os

    import requests

    s = requests.Session()
    ua = os.environ.get("SEC_USER_AGENT") or "qtrade-research (github.com/ASCoding11/Quant-Trading)"
    s.headers.update({"User-Agent": ua if sec else "Mozilla/5.0 (qtrade research)"})
    return s


def _cache(root: str | Path) -> Path:
    p = Path(root) / "public"
    p.mkdir(parents=True, exist_ok=True)
    return p


# -----------------------------------------------------------------------------
# FRED
# -----------------------------------------------------------------------------
def load_fred(root: str | Path = "data", refresh: bool = False) -> pd.DataFrame:
    """Daily frame of macro series, each shifted by its publication lag."""
    import os

    path = _cache(root) / "fred.parquet"
    if path.exists() and not refresh:
        cached = pd.read_parquet(path)
        # a cache built from the Yahoo stand-ins is replaced once a FRED key is available
        if "jobless_claims" in cached.columns or not os.environ.get("FRED_API_KEY"):
            return cached
    s = _session()
    cols = _fred_api(s)                                               # with a free key: reliable from CI
    fails = 0 if not cols else 99
    for name, (sid, lag) in FRED_SERIES.items():
        if fails >= 2:                                                # FRED often times out from cloud runners
            break
        try:
            r = s.get(FRED_URL.format(sid=sid), timeout=20)
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text))
            df.columns = ["date", "value"]
            x = pd.Series(pd.to_numeric(df["value"], errors="coerce").to_numpy(),
                          index=pd.to_datetime(df["date"])).dropna()
            x.index = x.index + pd.Timedelta(days=lag)                # when it was known
            cols[name] = x
            LOG.info("FRED %s: %d values", sid, len(x))
        except Exception as exc:
            fails += 1
            LOG.warning("FRED %s failed: %s", sid, exc)
    if not cols:
        cols = _macro_from_yahoo()
    if not cols:
        return pd.DataFrame()
    out = pd.DataFrame(cols).sort_index()
    out = out.resample("D").last().ffill()
    out.to_parquet(path)
    return out


def _fred_api(s) -> dict:
    """FRED's JSON API (needs FRED_API_KEY, free at fred.stlouisfed.org/docs/api/api_key.html).
    The keyless CSV endpoint times out from GitHub's runners."""
    import os

    key = os.environ.get("FRED_API_KEY")
    if not key:
        return {}
    cols = {}
    for name, (sid, lag) in FRED_SERIES.items():
        try:
            r = s.get("https://api.stlouisfed.org/fred/series/observations",
                      params={"series_id": sid, "api_key": key, "file_type": "json"}, timeout=30)
            r.raise_for_status()
            obs = pd.DataFrame(r.json()["observations"])
            x = pd.Series(pd.to_numeric(obs["value"], errors="coerce").to_numpy(),
                          index=pd.to_datetime(obs["date"])).dropna()
            x.index = x.index + pd.Timedelta(days=lag)
            cols[name] = x
            LOG.info("FRED API %s: %d values", sid, len(x))
        except Exception as exc:
            LOG.warning("FRED API %s failed: %s", sid, exc.__class__.__name__)   # never log the key
    return cols


def _macro_from_yahoo() -> dict:
    """Market-traded stand-ins for the FRED series, from Yahoo, each lagged a day."""
    import yfinance as yf

    syms = ["^TNX", "^IRX", "^FVX", "^VIX", "DX-Y.NYB", "CL=F", "HYG", "LQD", "TIP", "IEF"]
    try:
        px = yf.download(syms, start="2000-01-01", auto_adjust=True, progress=False)["Close"]
    except Exception as exc:
        LOG.warning("Yahoo macro fallback failed: %s", exc)
        return {}
    px = px.dropna(how="all")
    if px.empty:
        return {}
    px.index = pd.to_datetime(px.index).tz_localize(None) + pd.Timedelta(days=1)
    g = lambda c: px[c] if c in px else pd.Series(dtype=float)
    cols = {
        "term_spread_10y3m": g("^TNX") - g("^IRX"),
        "term_spread_10y5y": g("^TNX") - g("^FVX"),
        "credit_spread_hyg_lqd": -np.log(g("HYG") / g("LQD")),      # rises when high yield lags
        "breakeven_tip_ief": np.log(g("TIP") / g("IEF")),
        "dollar_index": g("DX-Y.NYB"),
        "oil_wti": g("CL=F").where(g("CL=F") > 0),
        "vix": g("^VIX"),
    }
    cols = {k: v.dropna() for k, v in cols.items() if v.notna().sum() > 500}
    LOG.info("macro from Yahoo: %s", list(cols))
    return cols


# -----------------------------------------------------------------------------
# S&P 500 changes
# -----------------------------------------------------------------------------
def load_sp500_changes(root: str | Path = "data", refresh: bool = False) -> pd.DataFrame:
    """date, added, removed (effective dates of index changes)."""
    path = _cache(root) / "sp500_changes.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    html = _session().get(SP500_WIKI, timeout=60).text
    tables = pd.read_html(io.StringIO(html))
    def flat(t):
        cols = t.columns
        return [" ".join(str(x) for x in c).strip() if isinstance(c, tuple) else str(c) for c in cols]

    def find(cols, *words):
        return next((c for c in cols if all(w in c.lower() for w in words)), None)

    ch = None
    for t in tables:                                 # the change table: added / removed tickers by date
        cols = flat(t)
        add_col = find(cols, "add", "ticker") or find(cols, "add", "symbol")
        rem_col = find(cols, "remov", "ticker") or find(cols, "remov", "symbol")
        date_col = find(cols, "date")
        if add_col and rem_col and date_col:
            ch = t.copy()
            ch.columns = cols
            break
    if ch is None:
        raise ValueError(f"S&P 500 change table not found among {len(tables)} tables")
    out = pd.DataFrame({"date": pd.to_datetime(ch[date_col], errors="coerce"),
                        "added": ch[add_col].astype(str).str.strip().str.replace(".", "-", regex=False),
                        "removed": ch[rem_col].astype(str).str.strip().str.replace(".", "-", regex=False)})
    out = out.dropna(subset=["date"]).replace({"nan": np.nan})
    out.to_parquet(path)
    return out


# -----------------------------------------------------------------------------
# FINRA short volume
# -----------------------------------------------------------------------------
def load_short_volume(dates: pd.DatetimeIndex, tickers: list[str], root: str | Path = "data",
                      budget_min: float = 60) -> pd.DataFrame:
    """Daily short-volume ratio (short volume / total off-exchange volume) per stock."""
    from .loader import to_yahoo

    cache = _cache(root) / "regsho"
    cache.mkdir(exist_ok=True)
    s = _session()
    t0 = time.time()
    want = set(tickers)
    frames = []
    failures = 0
    for d in dates[dates >= "2018-08-01"]:
        f = cache / f"{d:%Y%m%d}.parquet"
        if not f.exists():
            if (time.time() - t0) / 60 > budget_min or failures >= 10:
                if failures >= 10:
                    LOG.warning("Reg SHO: 10 failures in a row - giving up on downloads")
                break
            try:
                r = s.get(REGSHO_URL.format(d=d), timeout=30)
                if r.status_code != 200:
                    failures += 1 if r.status_code != 404 else 0       # 404 = holiday, not a failure
                    continue
                failures = 0
                df = pd.read_csv(io.StringIO(r.text), sep="|")
                df = df[df["Symbol"].notna() & (df["TotalVolume"] > 0)]
                df["ticker"] = df["Symbol"].astype(str).map(to_yahoo)
                df = df[df["ticker"].isin(want)]
                df = df.groupby("ticker")[["ShortVolume", "TotalVolume"]].sum().reset_index()
                df["date"] = d
                df.to_parquet(f)
            except Exception as exc:
                LOG.warning("Reg SHO %s: %s", d.date(), exc)
                failures += 1
                continue
        frames.append(pd.read_parquet(f))
    if not frames:
        return pd.DataFrame(index=dates, columns=tickers, dtype=float)
    x = pd.concat(frames)
    ratio = (x["ShortVolume"] / x["TotalVolume"]).to_numpy()
    out = pd.Series(ratio, index=pd.MultiIndex.from_arrays([x["date"], x["ticker"]])).unstack()
    LOG.info("short volume: %d days", len(out))
    return out.reindex(index=dates, columns=tickers)


# -----------------------------------------------------------------------------
# SEC insider transactions
# -----------------------------------------------------------------------------
def load_insider(root: str | Path = "data", start_year: int = 2006, budget_min: float = 90) -> pd.DataFrame:
    """Open-market insider purchases (P) and sales (S): one row per transaction with
    ticker, filing date, insider id, signed dollar value."""
    cache = _cache(root) / "insider"
    cache.mkdir(exist_ok=True)
    s = _session(sec=True)
    t0 = time.time()
    now = pd.Timestamp.today()
    frames = []
    failures = 0
    for y in range(start_year, now.year + 1):
        for q in range(1, 5):
            if pd.Timestamp(year=y, month=3 * q, day=1) > now:
                continue
            f = cache / f"{y}q{q}.parquet"
            if not f.exists():
                if (time.time() - t0) / 60 > budget_min or failures >= 4:
                    break
                try:
                    r = s.get(INSIDER_URL.format(y=y, q=q), timeout=300)
                    if r.status_code != 200:
                        LOG.warning("insider %dq%d: HTTP %d", y, q, r.status_code)
                        failures += 1
                        continue
                    z = zipfile.ZipFile(io.BytesIO(r.content))
                    sub = pd.read_csv(z.open("SUBMISSION.tsv"), sep="\t", dtype=str,
                                      usecols=["ACCESSION_NUMBER", "FILING_DATE", "ISSUERTRADINGSYMBOL"])
                    tr = pd.read_csv(z.open("NONDERIV_TRANS.tsv"), sep="\t", dtype=str,
                                     usecols=["ACCESSION_NUMBER", "TRANS_CODE", "TRANS_SHARES",
                                              "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD"])
                    own = pd.read_csv(z.open("REPORTINGOWNER.tsv"), sep="\t", dtype=str,
                                      usecols=["ACCESSION_NUMBER", "RPTOWNERCIK"])
                    tr = tr[tr["TRANS_CODE"].isin(["P", "S"])]
                    df = tr.merge(sub, on="ACCESSION_NUMBER").merge(
                        own.drop_duplicates("ACCESSION_NUMBER"), on="ACCESSION_NUMBER")
                    val = pd.to_numeric(df["TRANS_SHARES"], errors="coerce") * pd.to_numeric(
                        df["TRANS_PRICEPERSHARE"], errors="coerce")
                    out = pd.DataFrame({
                        "ticker": df["ISSUERTRADINGSYMBOL"].str.upper().str.strip().str.replace(".", "-", regex=False),
                        "filed": pd.to_datetime(df["FILING_DATE"], format="%d-%b-%Y", errors="coerce"),
                        "insider": df["RPTOWNERCIK"],
                        "value": np.where(df["TRANS_CODE"] == "P", 1, -1) * val})
                    out.dropna(subset=["ticker", "filed", "value"]).to_parquet(f)
                    LOG.info("insider %dq%d: %d transactions", y, q, len(out))
                except Exception as exc:
                    LOG.warning("insider %dq%d failed: %s", y, q, exc)
                    failures += 1
                    continue
            frames.append(pd.read_parquet(f))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["ticker", "filed", "insider", "value"])


# -----------------------------------------------------------------------------
# survivorship-free universe from Alpaca (includes delisted stocks)
# -----------------------------------------------------------------------------
def load_all_stocks_daily(root: str | Path = "data", start: str = "2016-01-01",
                          budget_min: float = 120) -> dict[str, pd.DataFrame]:
    """Daily close and volume for every US equity Alpaca knows, active or not.
    Returns {'close': DataFrame, 'volume': DataFrame} (dates x symbols)."""
    import os

    from .intraday import AlpacaBars
    from .loader import to_yahoo

    cache = _cache(root) / "all_daily"
    cache.mkdir(exist_ok=True)
    if (cache / "close.parquet").exists():
        return {f: pd.read_parquet(cache / f"{f}.parquet") for f in ("close", "volume")}
    import requests

    key, sec = os.environ.get("ALPACA_API_KEY"), os.environ.get("ALPACA_SECRET_KEY")
    hdr = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec}
    syms = []
    for status in ("active", "inactive"):
        r = requests.get("https://paper-api.alpaca.markets/v2/assets", headers=hdr,
                         params={"status": status, "asset_class": "us_equity"}, timeout=120)
        r.raise_for_status()
        syms += [a["symbol"] for a in r.json() if a.get("exchange") in ("NYSE", "NASDAQ", "AMEX", "ARCA", "BATS")
                 and "/" not in a["symbol"]]
    import re

    syms = sorted({x for x in syms if re.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?", x)})   # real tickers only
    LOG.info("all stocks: %d symbols (active + delisted)", len(syms))
    client = AlpacaBars(feed="sip")
    end = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=1)).isoformat()
    closes, vols = {}, {}
    t0 = time.time()
    for i in range(0, len(syms), 100):
        if (time.time() - t0) / 60 > budget_min:
            LOG.warning("all stocks: time budget reached at %d/%d", i, len(syms))
            break
        batch = syms[i:i + 100]
        got = {}
        for _ in range(10):                     # drop symbols the API rejects and retry the rest
            try:
                got = client.bars(batch, "1Day", start, end)
                break
            except RuntimeError as exc:
                bad = re.search(r"invalid symbol: ([^\"\s]+)", str(exc))
                if not bad or bad.group(1) not in batch:
                    LOG.warning("all stocks batch %d failed: %s", i, exc)
                    break
                batch = [x for x in batch if x != bad.group(1)]
        for s_, rows in got.items():
            if not rows:
                continue
            idx = pd.to_datetime([b["t"] for b in rows]).tz_convert("America/New_York").tz_localize(None).normalize()
            closes[to_yahoo(s_)] = pd.Series([b["c"] for b in rows], index=idx)
            vols[to_yahoo(s_)] = pd.Series([b["v"] for b in rows], index=idx)
    out = {"close": pd.DataFrame(closes).sort_index(), "volume": pd.DataFrame(vols).sort_index()}
    for f, df in out.items():
        df.astype("float32").to_parquet(cache / f"{f}.parquet")
    return out
