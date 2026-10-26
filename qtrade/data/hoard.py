"""Data hoard: snapshots of many free data sources, collected every 30 minutes to analyse later.

``python -m qtrade.data.hoard --out hoard_run [--daily]`` writes one gzipped JSON file per source:

* open data, stored in the clear (``<day>/<source>/<HHMM>.json.gz``): Hacker News front page, SEC EDGAR's
  latest filings, USGS earthquakes, weather in the financial centres (Open-Meteo), GDELT's latest
  15-minute event file summarised by country and event type, the crypto fear & greed index; daily: Wikipedia's most-viewed articles, US Treasury yields, NY Fed reference rates
  (SOFR etc.), ECB euro reference rates;
* end of day (``--eod``): the session's consolidated 1-minute bars for the largest ~1,000 US stocks,
  encrypted, straight to the monthly release (too big for git);
* market prices, which are licensed and so never published in the clear: Alpaca (IEX) snapshots of
  ~150 US stocks and ETFs, Yahoo 1-minute bars of indices, futures, FX, commodities, Asian stocks,
  Coinbase crypto tickers, Polymarket prediction-market prices, Google's trending searches (Google's
  content); daily: FRED series. These go into one
  tar per run (``<day>/market/<HHMM>.tar``), encrypted with ``--public-key`` like the trade ledger.

Every source is independent: one that fails is logged and skipped, the others still save.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import tarfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from ..utils import LOG, setup_logging

UA = "qtrade-hoard (research)"
STOCKS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
          "SMH", "KRE", "XBI", "GLD", "SLV", "USO", "UNG", "TLT", "IEF", "HYG", "LQD", "UUP", "FXI", "EWJ", "EWY",
          "INDA", "EWT", "EEM", "VXX", "ARKK", "BITO",
          "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK.B", "JPM", "V", "MA", "UNH", "XOM",
          "LLY", "JNJ", "PG", "HD", "COST", "WMT", "NFLX", "AMD", "INTC", "CRM", "ORCL", "ADBE", "CSCO", "QCOM",
          "BAC", "WFC", "GS", "MS", "C", "KO", "PEP", "MCD", "NKE", "DIS", "BA", "CAT", "DE", "GE", "F", "GM", "UBER",
          "ABNB", "PLTR", "COIN", "MSTR", "SHOP", "PYPL", "SBUX", "TGT", "LOW", "CVX", "COP", "PFE", "MRK", "ABBV",
          "T", "VZ", "TMUS", "SNOW", "MU", "ARM", "SMCI", "RIVN", "LCID", "GME", "AMC", "HOOD", "SOFI", "DKNG",
          "RBLX", "SPOT", "DAL", "UAL", "CCL"]
YAHOO = ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^TNX", "^FVX", "^TYX", "ES=F", "NQ=F", "YM=F", "RTY=F", "CL=F",
         "BZ=F", "NG=F", "GC=F", "SI=F", "HG=F", "ZC=F", "ZW=F", "ZS=F", "DX-Y.NYB", "EURUSD=X", "JPY=X", "GBPUSD=X",
         "CNY=X", "HKD=X", "KRW=X", "INR=X", "TWD=X", "AUDUSD=X", "BTC-USD", "ETH-USD", "^N225", "^HSI", "^KS11",
         "^NSEI", "^TWII", "^AXJO", "000001.SS", "^FTSE", "^GDAXI", "^FCHI", "^STOXX50E"]
COINBASE = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD", "LTC-USD"]
FRED = ["DFF", "SOFR", "DGS2", "DGS10", "T10Y2Y", "T10YIE", "BAMLH0A0HYM2", "VIXCLS", "DCOILWTICO", "DTWEXBGS",
        "ICSA", "CCSA", "UMCSENT", "WALCL", "RRPONTSYD", "M2SL", "CPIAUCSL", "UNRATE", "PAYEMS", "RSAFS"]
CITIES = {"New York": (40.71, -74.01), "Chicago": (41.88, -87.63), "London": (51.51, -0.13),
          "Frankfurt": (50.11, 8.68), "Tokyo": (35.68, 139.69), "Hong Kong": (22.32, 114.17),
          "Shanghai": (31.23, 121.47), "Seoul": (37.57, 126.98), "Mumbai": (19.08, 72.88),
          "Singapore": (1.35, 103.82), "Sydney": (-33.87, 151.21), "Houston": (29.76, -95.37),
          "Des Moines": (41.59, -93.62), "Sao Paulo": (-23.55, -46.63)}
GDELT_COLS = {1: "day", 26: "event_code", 28: "root_code", 29: "quad_class", 30: "goldstein", 31: "mentions",
              33: "articles", 34: "tone", 53: "country"}


def _session():
    import requests

    s = requests.Session()
    s.headers["User-Agent"] = os.environ.get("SEC_USER_AGENT") or UA
    return s


def _json(s, url, **kw):
    r = s.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def _text(s, url, **kw):
    r = s.get(url, timeout=30, **kw)
    r.raise_for_status()
    return r.text


# --- open data ----------------------------------------------------------------------------------
def hackernews(s, now):
    return _json(s, "https://hn.algolia.com/api/v1/search", params={"tags": "front_page", "hitsPerPage": 100})


def sec_filings(s, now):
    return {"atom": _text(s, "https://www.sec.gov/cgi-bin/browse-edgar",
                          params={"action": "getcurrent", "count": 100, "output": "atom"})}


def earthquakes(s, now):
    return _json(s, "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson")


def weather(s, now):
    lat = ",".join(str(v[0]) for v in CITIES.values())
    lon = ",".join(str(v[1]) for v in CITIES.values())
    data = _json(s, "https://api.open-meteo.com/v1/forecast",
                 params={"latitude": lat, "longitude": lon,
                         "current": "temperature_2m,precipitation,wind_speed_10m,cloud_cover,pressure_msl,"
                                    "relative_humidity_2m,weather_code"})
    return dict(zip(CITIES, data if isinstance(data, list) else [data]))


def gdelt_summary(table: pd.DataFrame) -> list[dict]:
    """Event counts, mentions, mean tone and Goldstein score per (country, event root code)."""
    t = table.rename(columns=GDELT_COLS)[list(GDELT_COLS.values())]
    t["country"] = t["country"].fillna("")
    g = t.groupby(["country", "root_code"]).agg(events=("day", "size"), mentions=("mentions", "sum"),
                                                 articles=("articles", "sum"), tone=("tone", "mean"),
                                                 goldstein=("goldstein", "mean")).reset_index()
    return g.round(3).to_dict("records")


def gdelt(s, now):
    last = _text(s, "http://data.gdeltproject.org/gdeltv2/lastupdate.txt")
    url = next(line.split()[-1] for line in last.splitlines() if line.endswith(".export.CSV.zip"))
    r = s.get(url, timeout=60)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        table = pd.read_csv(z.open(z.namelist()[0]), sep="\t", header=None, low_memory=False)
    return {"file": url.rsplit("/", 1)[-1], "rows": len(table), "by_country_root": gdelt_summary(table)}


def google_trending(s, now):
    return {geo: _text(s, "https://trends.google.com/trending/rss", params={"geo": geo})
            for geo in ("US", "GB", "JP", "KR", "IN", "HK")}


def fear_greed_crypto(s, now):
    return _json(s, "https://api.alternative.me/fng/", params={"limit": 1})


def wiki_top(s, now):
    d = now - timedelta(days=1)
    return _json(s, f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/"
                    f"{d:%Y}/{d:%m}/{d:%d}")


def treasury_yields(s, now):
    return {"csv": _text(s, f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                            f"daily-treasury-rates.csv/{now:%Y}/all",
                         params={"type": "daily_treasury_yield_curve", "field_tdr_date_value": now.year,
                                 "_format": "csv"})}


def nyfed_rates(s, now):
    return _json(s, "https://markets.newyorkfed.org/api/rates/all/latest.json")


def ecb_fx(s, now):
    return {"xml": _text(s, "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml")}


# --- licensed market data (encrypted) -------------------------------------------------------------
def alpaca_snapshots(s, now):
    key, secret = os.environ.get("ALPACA_API_KEY"), os.environ.get("ALPACA_SECRET_KEY")
    if not key:
        raise RuntimeError("no Alpaca keys")
    h = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    out = {}
    for i in range(0, len(STOCKS), 100):
        out.update(_json(s, "https://data.alpaca.markets/v2/stocks/snapshots", headers=h,
                         params={"symbols": ",".join(STOCKS[i:i + 100]), "feed": "iex"}))
    return out


def yahoo_bars(s, now):
    import yfinance as yf

    raw = yf.download(YAHOO, period="1d", interval="1m", group_by="ticker", progress=False, threads=True,
                      auto_adjust=False)
    if raw is None or raw.empty:
        return {}
    cut = pd.Timestamp(now) - pd.Timedelta(minutes=35)
    out = {}
    for t in YAHOO:
        if t not in raw.columns.get_level_values(0):
            continue
        d = raw[t].dropna(how="all")
        d = d[d.index.tz_convert("UTC") >= cut] if d.index.tz is not None else d.tail(35)
        if len(d):
            out[t] = {str(k): v for k, v in d.round(6).to_dict("index").items()}
    return out


def coinbase(s, now):
    return {p: _json(s, f"https://api.exchange.coinbase.com/products/{p}/ticker") for p in COINBASE}


def polymarket(s, now):
    keep = ["id", "question", "slug", "endDate", "outcomes", "outcomePrices", "lastTradePrice", "bestBid", "bestAsk",
            "volume24hr", "volume", "liquidity"]
    rows = _json(s, "https://gamma-api.polymarket.com/markets",
                 params={"active": "true", "closed": "false", "limit": 500, "order": "volume24hr",
                         "ascending": "false"})
    return [{k: m.get(k) for k in keep} for m in rows]


def fred(s, now):
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError("no FRED key")
    out = {}
    for sid in FRED:
        try:
            d = _json(s, "https://api.stlouisfed.org/fred/series/observations",
                      params={"series_id": sid, "api_key": key, "file_type": "json", "sort_order": "desc",
                              "limit": 10})
            out[sid] = d.get("observations", [])
        except Exception as e:                      # the message would contain the URL with the key
            out[sid] = {"error": type(e).__name__}
    return out


def coinbase_books(s, now):
    """Top 50 levels of the order book for the biggest crypto pairs."""
    return {p: _json(s, f"https://api.exchange.coinbase.com/products/{p}/book", params={"level": 2})
            for p in COINBASE[:4]}


def cftc_cot(s, now):
    """CFTC Commitments of Traders, financial futures (weekly; public domain)."""
    return {"txt": _text(s, "https://www.cftc.gov/dea/newcot/FinFutWk.txt")}


def finra_short_volume(s, now):
    """FINRA Reg SHO daily short volume (consolidated), the latest file published."""
    for k in range(0, 6):
        d = now - timedelta(days=k)
        r = s.get(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt", timeout=30)
        if r.status_code == 200 and r.text.strip():
            return {"date": f"{d:%Y-%m-%d}", "txt": r.text}
    raise RuntimeError("no Reg SHO file in the last 6 days")


OPEN = {"hackernews": hackernews, "sec_filings": sec_filings, "earthquakes": earthquakes, "weather": weather,
        "gdelt": gdelt, "fear_greed_crypto": fear_greed_crypto}
OPEN_DAILY = {"wiki_top": wiki_top, "treasury_yields": treasury_yields, "nyfed_rates": nyfed_rates, "ecb_fx": ecb_fx,
              "cftc_cot": cftc_cot}
MARKET = {"google_trending": google_trending, "alpaca_snapshots": alpaca_snapshots, "yahoo_bars": yahoo_bars, "coinbase": coinbase,
          "polymarket": polymarket, "coinbase_books": coinbase_books}
MARKET_DAILY = {"fred": fred, "finra_short_volume": finra_short_volume}


def _gz(obj, now) -> bytes:
    return gzip.compress(json.dumps({"collected": now.isoformat(), "data": obj}, default=str).encode())


def collect(out: Path, daily: bool = False, public_key: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    day, stamp = f"{now:%Y-%m-%d}", f"{now:%H%M}"
    s = _session()
    status = {}

    def run(name, fn):
        try:
            data = fn(s, now)
            status[name] = "ok"
            return data
        except Exception as e:
            msg = str(e) if name != "fred" else type(e).__name__
            LOG.warning("hoard: %s failed: %s", name, msg[:200])
            status[name] = f"failed: {msg[:120]}"
            return None

    for name, fn in {**OPEN, **(OPEN_DAILY if daily else {})}.items():
        data = run(name, fn)
        if data is not None:
            p = out / day / name / f"{stamp}.json.gz"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(_gz(data, now))

    market = {}
    for name, fn in {**MARKET, **(MARKET_DAILY if daily else {})}.items():
        data = run(name, fn)
        if data is not None:
            market[name] = _gz(data, now)
    if market:
        p = out / day / "market" / f"{stamp}.tar"
        p.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(p, "w") as tar:
            for name, blob in market.items():
                info = tarfile.TarInfo(f"{name}.json.gz")
                info.size = len(blob)
                tar.addfile(info, io.BytesIO(blob))
        if public_key:
            from ..live.ledger import encrypt
            encrypt(p, public_key)
        elif os.environ.get("GITHUB_ACTIONS"):
            raise RuntimeError("refusing to store market data unencrypted in CI")
    LOG.info("hoard %s %s: %s", day, stamp, status)
    return status


def eod(out: Path, public_key: str | None, day: pd.Timestamp | None = None, n: int = 1000) -> dict:
    """End of day: the session's consolidated 1-minute bars for the ``n`` largest US stocks plus the
    ETFs above, one encrypted parquet (``<day>/eod_1min_bars.parquet.enc``; too big for git - it goes
    to the monthly release)."""
    from ..data.intraday import AlpacaBars, bars_to_frame

    day = (day or pd.Timestamp.now(tz="America/New_York")).normalize()
    try:
        from ..intraday.flip_sleeve import universe

        names = [t.replace("-", ".") for t in universe()][:n]
    except Exception as exc:
        LOG.warning("universe unavailable (%s) - the hoard's own list", exc)
        names = []
    syms = list(dict.fromkeys(STOCKS + names))
    data = AlpacaBars(feed="sip")
    start, end = day + pd.Timedelta(hours=4), day + pd.Timedelta(hours=20)
    frames = []
    for i in range(0, len(syms), 200):
        got = data.bars(syms[i:i + 200], "1Min", start.isoformat(), end.isoformat())
        for sym, rows in got.items():
            if rows:
                f = bars_to_frame(rows, regular_hours=False)
                f["symbol"] = sym
                frames.append(f.reset_index())
    if not frames:
        return {"eod": "no bars (holiday?)"}
    bars = pd.concat(frames, ignore_index=True)
    status = {}
    try:                                                 # foreign markets: Yahoo keeps 1-minute bars for 7 days only
        status["foreign"] = foreign_minutes(out / f"{day:%Y-%m-%d}" / "foreign_1min_bars.parquet", public_key)
    except Exception as exc:
        LOG.warning("foreign 1-minute bars failed: %s", exc)
        status["foreign"] = f"failed: {exc}"
    p = out / f"{day:%Y-%m-%d}" / "eod_1min_bars.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(p, compression="zstd")
    if public_key:
        from ..live.ledger import encrypt
        encrypt(p, public_key)
    elif os.environ.get("GITHUB_ACTIONS"):
        raise RuntimeError("refusing to store market data unencrypted in CI")
    LOG.info("eod: %d bars for %d symbols", len(bars), bars["symbol"].nunique())
    return {"eod": f"{len(bars)} bars, {bars['symbol'].nunique()} symbols", **status}


def foreign_minutes(path: Path, public_key: str | None) -> str:
    """The latest session's 1-minute bars of the foreign sleeve's markets (Yahoo), encrypted."""
    import yfinance as yf

    from ..research.foreign import MARKETS

    frames = []
    for mkt, tickers in MARKETS.items():
        raw = yf.download(tickers, period="5d", interval="1m", group_by="ticker", auto_adjust=False,
                          progress=False, threads=True)
        for t in tickers:
            if raw is None or raw.empty or t not in raw.columns.get_level_values(0):
                continue
            f = raw[t].dropna(how="all")
            if f.empty:
                continue
            f = f[pd.DatetimeIndex(f.index.date) == pd.Timestamp(max(f.index.date))]   # the latest session
            f = f.rename(columns=str.lower).reset_index().rename(columns={f.index.name or "index": "time"})
            f["time"] = f["time"].astype(str)
            f["symbol"], f["market"] = t, mkt
            frames.append(f)
    if not frames:
        return "no bars"
    df = pd.concat(frames, ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression="zstd")
    if public_key:
        from ..live.ledger import encrypt
        encrypt(path, public_key)
    elif os.environ.get("GITHUB_ACTIONS"):
        raise RuntimeError("refusing to store market data unencrypted in CI")
    return f"{len(df)} bars, {df['symbol'].nunique()} symbols"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--eod", action="store_true", help="end-of-day 1-minute bars instead of the snapshot")
    ap.add_argument("--out", default="hoard_run")
    ap.add_argument("--daily", action="store_true", help="also collect the once-a-day sources")
    ap.add_argument("--public-key", default=None, help="encrypt the market-data tar to this RSA public key")
    args = ap.parse_args(argv)
    setup_logging()
    status = eod(Path(args.out), args.public_key) if args.eod else collect(Path(args.out), args.daily, args.public_key)
    print(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
