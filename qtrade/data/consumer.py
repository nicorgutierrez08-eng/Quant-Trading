"""Free consumer and earnings data for the consumer-earnings study.

What is free and usable (company-level satellite data - parking-lot car
counts, foot traffic - is sold by commercial vendors and is not here):

* SEC EDGAR submissions: each company's SIC industry code (to pick consumer
  companies) and its **earnings announcements** - 8-K filings with item 2.02
  "Results of Operations", stamped to the second (``accepted``), so a release
  after the close is known to have come out after the close;
* Wikipedia page views per company, daily since July 2015 (a proxy for
  consumer attention), the article found through Wikidata's ticker symbols;
* Google search interest, weekly, when Google allows it (best effort: the
  unofficial endpoint throttles automated use);
* consumer macro series from FRED (retail sales, sentiment, spending, saving
  rate), each shifted by its publication lag;
* TSA airport checkpoint throughput, daily since 2019.

Everything is cached under ``data/public/consumer/`` and every loader gives up
after repeated failures instead of hanging.
"""
from __future__ import annotations

import io
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

NY = "America/New_York"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SUBMISSIONS_FILE_URL = "https://data.sec.gov/submissions/{name}"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
PAGEVIEWS_URL = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
                 "{title}/daily/{start}/{end}")
TSA_URL = "https://www.tsa.gov/travel/passenger-volumes/{year}"
# FRED consumer series: (id, days until a value is public)
CONSUMER_FRED = {
    "retail_sales_ex_food": ("RSXFS", 45),
    "consumer_sentiment": ("UMCSENT", 35),
    "personal_spending": ("PCE", 60),
    "saving_rate": ("PSAVERT", 60),
    "card_delinquency": ("DRCCLACBS", 60),
}

# SIC codes counted as consumer companies (discretionary and staples)
CONSUMER_SIC = [(2000, 2099), (2100, 2199), (2300, 2399), (2840, 2844), (3140, 3149), (3630, 3652),
                (3711, 3716), (3940, 3949), (4512, 4513), (5200, 5999), (7011, 7011), (7812, 7832),
                (7900, 7999)]


def _cache(root) -> Path:
    p = Path(root) / "public" / "consumer"
    p.mkdir(parents=True, exist_ok=True)
    return p


def is_consumer(sic) -> bool:
    try:
        s = int(sic)
    except (TypeError, ValueError):
        return False
    return any(a <= s <= b for a, b in CONSUMER_SIC)


# -----------------------------------------------------------------------------
# SEC: industry codes and earnings announcements
# -----------------------------------------------------------------------------
def _earnings_rows(ticker: str, block: dict) -> list[dict]:
    rows = []
    forms, items = block.get("form", []), block.get("items", [])
    acc, filed = block.get("acceptanceDateTime", []), block.get("filingDate", [])
    for f, it, a, d in zip(forms, items, acc, filed):
        if f in ("8-K", "8-K/A") and "2.02" in str(it):
            rows.append({"ticker": ticker, "form": f, "items": it, "accepted": a, "filed": d})
    return rows


def sec_profiles_and_earnings(tickers: list[str], root: str | Path = "data", refresh: bool = False,
                              budget_min: float = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(profiles: ticker, cik, sic, sic_description, consumer) and
    (events: ticker, accepted [New York time], session, filed) for 8-K item 2.02 filings."""
    from .fundamentals import SecClient, ticker_to_cik

    c = _cache(root)
    pf, ef = c / "sec_profiles.parquet", c / "earnings_events.parquet"
    if pf.exists() and ef.exists() and not refresh:
        return pd.read_parquet(pf), pd.read_parquet(ef)
    client = SecClient()
    ciks = ticker_to_cik(client)
    prof, ev, t0, fails = [], [], time.time(), 0
    for i, t in enumerate(tickers):
        if time.time() - t0 > budget_min * 60 or fails >= 10:
            LOG.warning("SEC submissions: stopped after %d tickers (%s)", i,
                        "time budget" if fails < 10 else "repeated failures")
            break
        cik = ciks.get(t)
        if cik is None:
            continue
        try:
            sub = client.get_json(SUBMISSIONS_URL.format(cik=cik))
        except Exception as exc:
            fails += 1
            LOG.warning("SEC submissions %s: %s", t, exc)
            continue
        if not sub:
            continue
        prof.append({"ticker": t, "cik": cik, "sic": sub.get("sic"), "sic_description": sub.get("sicDescription"),
                     "consumer": is_consumer(sub.get("sic"))})
        ev += _earnings_rows(t, sub.get("filings", {}).get("recent", {}))
        for extra in sub.get("filings", {}).get("files", []):        # older filings, page by page
            if str(extra.get("filingTo", "9999")) < "2014-01-01":
                continue
            try:
                page = client.get_json(SUBMISSIONS_FILE_URL.format(name=extra["name"]))
            except Exception:
                continue
            if page:
                ev += _earnings_rows(t, page)
        if (i + 1) % 100 == 0:
            LOG.info("SEC submissions: %d/%d tickers, %d earnings filings", i + 1, len(tickers), len(ev))
    profiles = pd.DataFrame(prof)
    events = pd.DataFrame(ev)
    if len(events):
        acc = pd.to_datetime(events["accepted"], utc=True, errors="coerce").dt.tz_convert(NY)
        events["accepted"] = acc
        mins = acc.dt.hour * 60 + acc.dt.minute
        events["session"] = np.where(mins < 9 * 60 + 30, "before_open", np.where(mins >= 16 * 60, "after_close",
                                                                                 "during"))
        events = events.dropna(subset=["accepted"]).drop_duplicates(["ticker", "accepted"]).sort_values("accepted")
    profiles.to_parquet(pf)
    events.to_parquet(ef)
    LOG.info("SEC: %d profiles (%d consumer), %d earnings filings", len(profiles),
             int(profiles["consumer"].sum()) if len(profiles) else 0, len(events))
    return profiles, events


# -----------------------------------------------------------------------------
# Wikipedia page views
# -----------------------------------------------------------------------------
def _session():
    import requests

    s = requests.Session()
    s.headers.update({"User-Agent": os.environ.get("SEC_USER_AGENT") or
                      "qtrade-research (github.com/ASCoding11/Quant-Trading)"})
    return s


def wiki_titles(root: str | Path = "data", refresh: bool = False) -> pd.DataFrame:
    """ticker -> English Wikipedia article, from Wikidata's NYSE / Nasdaq ticker symbols."""
    path = _cache(root) / "wiki_titles.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    q = """SELECT ?ticker ?article WHERE {
      VALUES ?ex { wd:Q13677 wd:Q82059 }
      ?item p:P414 ?st . ?st ps:P414 ?ex ; pq:P249 ?ticker .
      ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> .
    }"""
    r = _session().get(WIKIDATA_SPARQL, params={"query": q, "format": "json"}, timeout=120)
    r.raise_for_status()
    rows = [{"ticker": b["ticker"]["value"].upper().replace(".", "-"),
             "title": b["article"]["value"].rsplit("/", 1)[-1]} for b in r.json()["results"]["bindings"]]
    df = pd.DataFrame(rows).drop_duplicates("ticker")
    df.to_parquet(path)
    LOG.info("Wikidata: %d tickers with an English Wikipedia article", len(df))
    return df


def wiki_pageviews(tickers: list[str], root: str | Path = "data", start: str = "2015-07-01",
                   refresh: bool = False, budget_min: float = 30) -> pd.DataFrame:
    """Daily page views (date x ticker); a value for day d is published early on day d+1."""
    path = _cache(root) / "wiki_pageviews.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    titles = wiki_titles(root).set_index("ticker")["title"]
    s = _session()
    end = (pd.Timestamp.today() - pd.Timedelta(days=1)).strftime("%Y%m%d")
    cols, t0, fails = {}, time.time(), 0
    from urllib.parse import quote

    for i, t in enumerate(tickers):
        if t not in titles.index:
            continue
        if time.time() - t0 > budget_min * 60 or fails >= 20:
            LOG.warning("Wikipedia: stopped after %d tickers", i)
            break
        url = PAGEVIEWS_URL.format(title=quote(titles[t], safe=""), start=start.replace("-", ""), end=end)
        try:
            r = s.get(url, timeout=60)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            items = r.json().get("items", [])
            cols[t] = pd.Series({pd.Timestamp(it["timestamp"][:8]): it["views"] for it in items}, dtype=float)
        except Exception as exc:
            fails += 1
            LOG.warning("Wikipedia %s: %s", t, exc)
        time.sleep(0.05)
    df = pd.DataFrame(cols).sort_index()
    df.to_parquet(path)
    LOG.info("Wikipedia page views: %d days x %d tickers", *df.shape)
    return df


# -----------------------------------------------------------------------------
# Google search interest (best effort)
# -----------------------------------------------------------------------------
_SUFFIXES = {"inc", "corp", "corporation", "co", "company", "ltd", "plc", "holdings", "holding", "group",
             "sa", "nv", "lp", "llc", "intl", "cos", "companies"}


def company_search_terms(tickers: list[str], root: str | Path = "data") -> dict[str, str]:
    """{ticker: search term}: the Wikipedia article title when there is one, otherwise the company's
    SEC name without legal suffixes ("COSTCO WHOLESALE CORP /NEW" -> "Costco Wholesale")."""
    names = {}
    try:
        titles = wiki_titles(root).set_index("ticker")["title"]
        names = {t: titles[t].replace("_", " ").split(" (")[0] for t in tickers if t in titles.index}
    except Exception as exc:
        LOG.warning("Wikipedia titles unavailable: %s", exc)
    missing = [t for t in tickers if t not in names]
    if missing:
        try:
            from .fundamentals import TICKERS_URL, SecClient, to_yahoo

            data = SecClient().get_json(TICKERS_URL)
            sec = {to_yahoo(v["ticker"]): v["title"] for v in data.values()}
            for t in missing:
                if t in sec:
                    words = [w for w in sec[t].replace(",", " ").replace(".", " ").split()
                             if w.lower() not in _SUFFIXES and not w.startswith("/")]      # "/DE/", "/NEW"
                    if words:
                        names[t] = " ".join(w if any(c.islower() for c in w) else w.capitalize() for w in words)
        except Exception as exc:
            LOG.warning("SEC company names unavailable: %s", exc)
    return names


# Google returns weekly points only for windows under five years (monthly beyond), so the history is
# fetched in overlapping windows and stitched: each window is rescaled to the previous one on their
# overlap year.
TRENDS_WINDOWS = (("2015-06-01", "2020-05-31"), ("2019-06-01", "2024-05-31"), ("2023-06-01", None))


def _stitch(parts: list[pd.Series]) -> pd.Series:
    out = parts[0]
    for p in parts[1:]:
        ov = out.index.intersection(p.index)
        if len(ov) < 8 or p[ov].mean() <= 0:
            return out                                  # can't scale the next window: keep what is consistent
        p = p * out[ov].mean() / p[ov].mean()
        out = pd.concat([out, p[p.index > out.index.max()]])
    return out


def google_trends(terms: dict[str, str], root: str | Path = "data", budget_min: float = 0,
                  pause: float = 25.0) -> pd.DataFrame:
    """Weekly search interest (0-100 scale of the first window) for {ticker: search term}.

    Incremental: each ticker is saved as soon as it is fetched (``google_trends_weekly.parquet``, plus
    ``google_trends_done.csv`` for terms Google had no data for), so throttled runs add up across runs.
    ``budget_min`` = minutes to spend fetching (0 = only read the cache). Needs ``pytrends``."""
    c = _cache(root)
    path, done_path = c / "google_trends_weekly.parquet", c / "google_trends_done.csv"
    have = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    done = set(pd.read_csv(done_path)["ticker"]) if done_path.exists() else set()
    todo = [t for t in terms if t not in done and t not in have.columns]
    if not todo or budget_min <= 0:
        return have
    try:
        from pytrends.request import TrendReq
    except ImportError:
        LOG.warning("pytrends not installed - skipping Google Trends")
        return have
    import random

    py = TrendReq(hl="en-US", tz=300, timeout=(10, 30))
    t0, fails, got = time.time(), 0, 0
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    for t in todo:
        if time.time() - t0 > budget_min * 60:
            LOG.info("Google Trends: time budget used")
            break
        if fails >= 6:
            LOG.warning("Google Trends: throttled - stopping")
            break
        term, parts, ok = terms[t], [], True
        for a, b in TRENDS_WINDOWS:
            try:
                py.build_payload([term], timeframe=f"{a} {b or today}", geo="US")
                d = py.interest_over_time()
                fails = 0
            except Exception as exc:
                fails += 1
                LOG.warning("Google Trends %s: %s - backing off", t, exc.__class__.__name__)
                time.sleep(min(60 * 2 ** fails, 600))
                ok = False
                break
            if len(d) and term in d:
                parts.append(d[term].astype(float))
            time.sleep(pause * random.uniform(0.8, 1.4))
        if not ok:
            continue                                    # retried in a later run
        s = _stitch(parts) if parts else pd.Series(dtype=float)
        if len(s) and s.max() > 0:
            s.index = pd.to_datetime(s.index) + pd.Timedelta(days=7)   # a week's value is known once it ends
            have = pd.concat([have, s.rename(t)], axis=1).sort_index()
            have.to_parquet(path)
            got += 1
        else:
            done.add(t)
            pd.DataFrame({"ticker": sorted(done)}).to_csv(done_path, index=False)
    LOG.info("Google Trends: +%d terms this run, %d in the cache, %d still to fetch", got, have.shape[1],
             len([t for t in terms if t not in done and t not in have.columns]))
    return have


# -----------------------------------------------------------------------------
# consumer macro: FRED and TSA
# -----------------------------------------------------------------------------
def consumer_macro(root: str | Path = "data", refresh: bool = False) -> pd.DataFrame:
    """Daily frame of FRED consumer series, each dated when it became public (needs FRED_API_KEY)."""
    path = _cache(root) / "consumer_macro.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    key = os.environ.get("FRED_API_KEY")
    if not key:
        LOG.warning("no FRED_API_KEY - skipping consumer macro series")
        return pd.DataFrame()
    s, cols = _session(), {}
    for name, (sid, lag) in CONSUMER_FRED.items():
        try:
            r = s.get("https://api.stlouisfed.org/fred/series/observations",
                      params={"series_id": sid, "api_key": key, "file_type": "json"}, timeout=30)
            r.raise_for_status()
            obs = pd.DataFrame(r.json()["observations"])
            x = pd.Series(pd.to_numeric(obs["value"], errors="coerce").to_numpy(),
                          index=pd.to_datetime(obs["date"]) + pd.Timedelta(days=lag)).dropna()
            cols[name] = x
        except Exception as exc:
            LOG.warning("FRED %s failed: %s", sid, exc.__class__.__name__)       # never log the key
    if not cols:
        return pd.DataFrame()
    df = pd.DataFrame(cols).sort_index().resample("D").last().ffill()
    df.to_parquet(path)
    return df


def tsa_throughput(root: str | Path = "data", refresh: bool = False) -> pd.Series:
    """Daily TSA checkpoint travel numbers since 2019 (published the next morning)."""
    path = _cache(root) / "tsa.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)["travelers"]
    s, parts = _session(), []
    for year in range(2019, pd.Timestamp.today().year + 1):
        url = TSA_URL.format(year=year) if year < pd.Timestamp.today().year else TSA_URL.rsplit("/", 1)[0]
        try:
            r = s.get(url, timeout=60)
            r.raise_for_status()
            for tab in pd.read_html(io.StringIO(r.text)):
                cols = [str(c).lower() for c in tab.columns]
                if any("date" in c for c in cols) and len(tab.columns) >= 2:
                    tab.columns = cols
                    dcol = next(c for c in cols if "date" in c)
                    vcol = next(c for c in cols if c != dcol)
                    parts.append(pd.Series(pd.to_numeric(tab[vcol].astype(str).str.replace(",", ""), errors="coerce").to_numpy(),
                                           index=pd.to_datetime(tab[dcol], errors="coerce")))
                    break
        except Exception as exc:
            LOG.warning("TSA %d: %s", year, exc)
    if not parts:
        return pd.Series(dtype=float)
    ser = pd.concat(parts).dropna()
    ser = ser[~ser.index.duplicated()].sort_index()
    ser.index = ser.index + pd.Timedelta(days=1)
    ser.to_frame("travelers").to_parquet(path)
    return ser
