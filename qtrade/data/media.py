"""News and media data for the news-correlation study (``qtrade.research.news_zoo``).

Every source here is free and answers from a GitHub runner (checked by the
``data-probe`` workflow on 2026-10-22):

* **GDELT DOC 2.0** - worldwide online news, machine-read in 65 languages:
  daily article counts and average tone for each company name and for ~90
  market-wide themes ("recession", "tariff", "layoffs" ...), since 2017;
* **GDELT TV 2.0** - share of national US TV news airtime mentioning a
  company or theme (CNN, Fox News, MSNBC, Bloomberg, CNBC ...), daily;
* **Hacker News** (Algolia API) - every story with 10+ points since 2016:
  title, link domain, points and comments (tech attention);
* **SEC EDGAR full-text search** - 8-K filings containing phrases such as
  "going concern", "material weakness", "cybersecurity incident", since 2016;
* **SEC EDGAR submissions** - every filing of every company (form, 8-K items,
  acceptance time): insider Form 4s, 13D activist stakes, offerings, late
  filings (NT 10-K) and so on;
* **Wikipedia** - articles found by search for companies Wikidata misses, and
  their daily page views (adds to ``consumer.wiki_pageviews``).

Not usable from a runner: Reddit (403), the Guardian's test key (401), Yahoo
(429); StockTwits answers but keeps only the latest messages (no history).

Collection is slow on purpose (GDELT allows one request every 5 seconds) and
incremental: every dataset is saved as it grows and finished keys are
remembered, so ``python -m qtrade.data.media --budget 300`` can be run again
and again (the ``media-collect`` workflow chains itself) until everything is in.
Data lives under ``media_data/`` (its own GitHub Actions cache).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import pandas as pd

from ..utils import LOG, setup_logging

GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TV = "https://api.gdeltproject.org/api/v2/tv/tv"
HN_URL = "https://hn.algolia.com/api/v1/search_by_date"
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
WIKI_API = "https://en.wikipedia.org/w/api.php"
START = "2017-01-01"                     # GDELT DOC's timelines begin here
HN_START = "2016-01-01"

THEMES = [
    "recession", "inflation", "layoffs", "bankruptcy", "tariff", "trade war", "war", "missile strike",
    "terrorist attack", "earthquake", "hurricane", "wildfire", "flooding", "pandemic", "coronavirus", "vaccine",
    "lockdown", "election", "impeachment", "government shutdown", "debt ceiling", "Federal Reserve",
    "rate hike", "rate cut", "quantitative easing", "bank failure", "bank run", "credit crunch", "housing market",
    "mortgage rates", "oil prices", "OPEC", "gas prices", "supply chain", "shortage", "labor strike",
    "unemployment", "jobs report", "stock market crash", "sell-off", "stock rally", "bull market", "bear market",
    "bubble", "cryptocurrency", "bitcoin", "artificial intelligence", "ChatGPT", "semiconductor",
    "chip shortage", "antitrust", "regulation", "cyberattack", "data breach", "ransomware", "China", "Russia",
    "Ukraine", "Israel", "Iran", "North Korea", "Taiwan", "Brexit", "sanctions", "stimulus", "tax cut",
    "consumer confidence", "retail sales", "Black Friday", "holiday shopping", "product recall", "short seller",
    "meme stock", "IPO", "merger", "acquisition", "stock buyback", "dividend cut", "default", "downgrade",
    "credit rating", "volatility", "panic", "fear", "optimism", "boom", "crisis", "drought", "heat wave",
    "travel", "airline", "electric vehicle", "climate change",
]

PHRASES = [
    "going concern", "material weakness", "restatement", "non-reliance", "cybersecurity incident",
    "data breach", "class action", "subpoena", "Department of Justice", "FDA approval",
    "complete response letter", "clinical hold", "product recall", "work stoppage", "tariffs",
    "reduction in force", "restructuring plan", "goodwill impairment", "share repurchase program",
    "special dividend", "strategic alternatives", "interim chief executive officer", "covenant waiver",
    "delisting", "reverse stock split", "at-the-market offering", "preliminary results",
    "merger agreement", "tender offer", "Chapter 11", "record revenue", "raises guidance",
    "lowers guidance", "cooperation agreement",
]

_LEGAL = {"inc", "inc.", "corp", "corp.", "corporation", "co", "co.", "company", "ltd", "ltd.", "plc", "holdings",
          "holding", "group", "n.v.", "nv", "s.a.", "sa", "lp", "l.p.", "llc", "the", "&", "incorporated", "limited",
          "cos", "cos.", "companies", "class", "a", "b"}


def media_root(root: str | Path | None = None) -> Path:
    p = Path(root or os.environ.get("QTRADE_MEDIA_DIR", "media_data"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def short_name(name: str) -> str:
    """'Apple Inc.' -> 'Apple', 'The Home Depot, Inc.' -> 'Home Depot' (how the news names a company)."""
    words = [w for w in re.split(r"[\s,]+", str(name).split(" (")[0]) if w]
    while words and words[0].lower() in {"the"}:
        words = words[1:]
    while len(words) > 1 and words[-1].lower() in _LEGAL:
        words = words[:-1]
    return " ".join(words)


class Paced:
    """requests session with a minimum gap between calls and back-off on 429 / 5xx."""

    def __init__(self, gap: float, ua: str | None = None):
        import requests

        self.s = requests.Session()
        self.s.headers.update({"User-Agent": ua or os.environ.get("SEC_USER_AGENT") or
                               "qtrade-research (github.com/ASCoding11/Quant-Trading)"})
        self.gap, self.last, self.calls = gap, 0.0, 0

    def get(self, url: str, params: dict | None = None, tries: int = 5, timeout: int = 60):
        for k in range(tries):
            wait = self.gap * random.uniform(1.0, 1.3) - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            self.calls += 1
            try:
                r = self.s.get(url, params=params, timeout=timeout)
            except Exception as exc:
                LOG.debug("request failed (%s), retrying", exc.__class__.__name__)
                time.sleep(10 * (k + 1))
                continue
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(20 * (k + 1), 120))
                continue
            return r
        return None


class Store:
    """A wide (date x key) parquet that grows key by key, plus the keys found to have no data."""

    def __init__(self, path: Path):
        self.path, self.done_path = path, path.with_suffix(".done.json")
        self.df = pd.read_parquet(path) if path.exists() else pd.DataFrame()
        self.empty = set(json.loads(self.done_path.read_text())) if self.done_path.exists() else set()
        self._new, self._saved = {}, time.time()

    def has(self, key: str) -> bool:
        return key in self.empty or key in self.df.columns or key in self._new

    def add(self, key: str, s: pd.Series | None) -> None:
        if s is None or not len(s):
            self.empty.add(key)
        else:
            self._new[key] = s
        if time.time() - self._saved > 120 or len(self._new) >= 25:
            self.save()

    def save(self) -> None:
        if self._new:
            self.df = pd.concat([self.df, pd.DataFrame(self._new)], axis=1).sort_index()
            self._new = {}
            self.df.to_parquet(self.path)
        self.done_path.write_text(json.dumps(sorted(self.empty)))
        self._saved = time.time()


# -----------------------------------------------------------------------------
# GDELT
# -----------------------------------------------------------------------------
def parse_gdelt(payload: dict, field: str = "value", total: bool = False) -> pd.Series | None:
    """Daily series from a GDELT timeline (several series, e.g. TV stations, are summed)."""
    tl = (payload or {}).get("timeline") or []
    parts = []
    for ser in tl:
        d = ser.get("data") or []
        if d:
            idx = pd.to_datetime([x["date"] for x in d], format="%Y%m%dT%H%M%SZ").normalize()
            parts.append(pd.Series([float(x.get("norm" if total else field, np.nan)) for x in d], index=idx))
    if not parts:
        return None
    s = pd.concat(parts, axis=1).sum(axis=1, min_count=1) if len(parts) > 1 else parts[0]
    return s.groupby(level=0).sum(min_count=1)


FAILED = "failed"     # a request GDELT refused or that timed out: try the key again later


def _gdelt(api: Paced, url: str, query: str, mode: str, start: str = START, end: str | None = None):
    """The parsed timeline; None when GDELT answers but won't run the query (its error text,
    e.g. a name too short to search); FAILED when it throttles or the request fails."""
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    params = {"query": query, "mode": mode, "format": "json",
              "startdatetime": pd.Timestamp(start).strftime("%Y%m%d000000"),
              "enddatetime": pd.Timestamp(end).strftime("%Y%m%d235959")}
    r = api.get(url, params, tries=2)
    if r is None or r.status_code != 200:
        return FAILED
    if not r.text.strip().startswith("{"):
        return None
    try:
        return r.json()
    except ValueError:
        return None


def _gdelt_daily(api: Paced, url: str, query: str, mode: str):
    """(daily values, daily total articles for volraw), or (FAILED, None). Falls back to yearly
    windows only when the whole span comes back coarser than daily - never after a refusal, which
    turned one throttled key into ten throttled requests."""
    p = _gdelt(api, url, query, mode)
    if p is FAILED:
        return FAILED, None
    if p is None:
        return None, None
    if (p.get("query_details") or {}).get("date_resolution", "day") == "day":
        return parse_gdelt(p), (parse_gdelt(p, total=True) if mode == "timelinevolraw" else None)
    vals, tots = [], []
    for y in range(pd.Timestamp(START).year, pd.Timestamp.today().year + 1):
        q = _gdelt(api, url, query, mode, f"{y}-01-01", f"{y}-12-31")
        if q is FAILED:
            return FAILED, None
        v = parse_gdelt(q) if q else None
        if v is not None:
            vals.append(v)
            if mode == "timelinevolraw":
                tots.append(parse_gdelt(q, total=True))
    if not vals:
        return None, None
    return pd.concat(vals).groupby(level=0).sum(), (pd.concat(tots).groupby(level=0).max() if tots else None)


def collect_gdelt(keys: dict[str, str], name: str, url: str, modes: tuple[str, ...], root, deadline: float,
                  api: Paced) -> int:
    """{key: GDELT query} -> ``<name>_<mode>.parquet`` per mode; returns keys still to fetch.
    A refused request leaves the key to fetch later (it is never recorded as having no data); after
    three refusals in a row the collector pauses, longer each time, since GDELT is throttling."""
    left = 0
    for mode in modes:
        st = Store(media_root(root) / f"{name}_{mode}.parquet")
        tot = Store(media_root(root) / "gdelt_total_articles.parquet") if mode == "timelinevolraw" else None
        fails, got = 0, 0
        for k, q in keys.items():
            if st.has(k):
                continue
            if time.time() > deadline:
                left += 1
                continue
            v, t = _gdelt_daily(api, url, q, mode)
            if v is FAILED:
                fails += 1
                left += 1
                if fails >= 3:
                    pause = min(120 * (fails - 2), 900)
                    LOG.warning("GDELT is refusing requests (%d in a row) - pausing %d s", fails, pause)
                    time.sleep(max(0.0, min(pause, deadline - time.time())))
                continue
            fails = 0
            got += 1
            st.add(k, v if v is not None and v.abs().sum() > 0 else None)
            if tot is not None and t is not None and not tot.has("all"):
                tot.add("all", t)
                tot.save()
            if got % 25 == 0:
                LOG.info("GDELT %s %s: %d fetched this run", name, mode, got)
        st.save()
        LOG.info("GDELT %s %s: %d keys with data, %d without", name, mode, st.df.shape[1], len(st.empty))
    return left


# -----------------------------------------------------------------------------
# Hacker News
# -----------------------------------------------------------------------------
def collect_hn(root, deadline: float, min_points: int = 10, days: int = 3) -> int:
    path = media_root(root) / "hn_stories.parquet"
    done_path = media_root(root) / "hn_windows.json"
    have = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    api = Paced(0.4)
    rows, today = [], pd.Timestamp.today().normalize()
    wins = pd.date_range(HN_START, today - pd.Timedelta(days=1), freq=f"{days}D")
    left = 0

    def fetch(a: int, b: int) -> list[dict]:
        r = api.get(HN_URL, {"tags": "story", "hitsPerPage": 1000,
                             "numericFilters": f"created_at_i>={a},created_at_i<{b},points>={min_points}"})
        if r is None or r.status_code != 200:
            raise RuntimeError("HN request failed")
        j = r.json()
        if j.get("nbHits", 0) > 1000 and b - a > 3600:                 # too many: split the window
            m = (a + b) // 2
            return fetch(a, m) + fetch(m, b)
        return j.get("hits", [])

    for w in wins:
        key = w.strftime("%Y-%m-%d")
        if key in done:
            continue
        if time.time() > deadline:
            left += 1
            continue
        a = int(w.tz_localize("UTC").timestamp())
        b = int(min(w + pd.Timedelta(days=days), today).tz_localize("UTC").timestamp())
        try:
            hits = fetch(a, b)
        except Exception as exc:
            LOG.warning("Hacker News %s: %s", key, exc)
            continue
        for h in hits:
            url = h.get("url") or ""
            rows.append({"id": int(h["objectID"]), "created_at": pd.Timestamp(h["created_at"]),
                         "title": h.get("title") or "", "domain": re.sub(r"^https?://(www\.)?([^/]+).*", r"\2", url),
                         "points": h.get("points") or 0, "comments": h.get("num_comments") or 0})
        if w + pd.Timedelta(days=days) < today - pd.Timedelta(days=7):   # recent windows are re-fetched later
            done.add(key)
        if len(rows) > 20000:
            have = _save_rows(have, rows, path, "id")
            rows = []
            done_path.write_text(json.dumps(sorted(done)))
    have = _save_rows(have, rows, path, "id")
    done_path.write_text(json.dumps(sorted(done)))
    LOG.info("Hacker News: %d stories, %d windows left", len(have), left)
    return left


def _save_rows(have: pd.DataFrame, rows: list[dict], path: Path, key: str) -> pd.DataFrame:
    if rows:
        have = pd.concat([have, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(key, keep="last")
        have.to_parquet(path)
    return have


# -----------------------------------------------------------------------------
# SEC
# -----------------------------------------------------------------------------
def collect_sec_phrases(root, deadline: float, start: str = "2016-01-01") -> int:
    """8-K filings containing each phrase (EDGAR full-text search), month by month."""
    from .fundamentals import SecClient

    path = media_root(root) / "sec_phrase_hits.parquet"
    done_path = media_root(root) / "sec_phrase_done.json"
    have = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    sec = SecClient(per_second=5)
    months = pd.period_range(start, pd.Timestamp.today(), freq="M")
    rows, left = [], 0
    for ph in PHRASES:
        for m in months:
            key = f"{ph}|{m}"
            if key in done:
                continue
            if time.time() > deadline:
                left += 1
                continue
            a, b = m.start_time.strftime("%Y-%m-%d"), m.end_time.strftime("%Y-%m-%d")
            try:
                for off in range(0, 10000, 100):
                    q = {"q": f'"{ph}"', "forms": "8-K", "dateRange": "custom", "startdt": a, "enddt": b, "from": off}
                    j = sec.get_json(f"{EFTS_URL}?{urlencode(q)}") or {}
                    hits = (j.get("hits") or {}).get("hits") or []
                    for h in hits:
                        src = h.get("_source") or {}
                        for cik in src.get("ciks") or []:
                            rows.append({"phrase": ph, "cik": int(cik), "file_date": src.get("file_date"),
                                         "form": src.get("form"), "adsh": src.get("adsh"),
                                         "items": ",".join(src.get("items") or [])})
                    total = ((j.get("hits") or {}).get("total") or {}).get("value", 0)
                    if off + 100 >= total or not hits:
                        break
            except Exception as exc:
                LOG.warning("SEC full-text %s: %s", key, exc)
                continue
            if m < pd.Period(pd.Timestamp.today(), "M") - 1:
                done.add(key)
            if len(rows) > 20000:
                have = _append(have, rows, path)
                rows = []
                done_path.write_text(json.dumps(sorted(done)))
    have = _append(have, rows, path)
    done_path.write_text(json.dumps(sorted(done)))
    LOG.info("SEC full-text: %d phrase hits, %d phrase-months left", len(have), left)
    return left


def _append(have: pd.DataFrame, rows: list[dict], path: Path) -> pd.DataFrame:
    if rows:
        have = pd.concat([have, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(["phrase", "cik", "adsh"])
        have.to_parquet(path)
    return have


def collect_sec_filings(tickers: list[str], root, deadline: float) -> int:
    """Every filing (form, 8-K items, acceptance time) of each company since 2014."""
    from .consumer import SUBMISSIONS_FILE_URL, SUBMISSIONS_URL
    from .fundamentals import SecClient, ticker_to_cik

    path = media_root(root) / "sec_filings.parquet"
    done_path = media_root(root) / "sec_filings_done.json"
    have = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    sec = SecClient()
    ciks = ticker_to_cik(sec)
    rows, left = [], 0

    def take(t: str, block: dict) -> None:
        for f, it, a in zip(block.get("form", []), block.get("items", []), block.get("acceptanceDateTime", [])):
            if a and a >= "2014":
                rows.append({"ticker": t, "form": f, "items": it or "", "accepted": a})

    for t in tickers:
        if t in done or t not in ciks:
            continue
        if time.time() > deadline:
            left += 1
            continue
        try:
            sub = sec.get_json(SUBMISSIONS_URL.format(cik=ciks[t])) or {}
            take(t, sub.get("filings", {}).get("recent", {}))
            for extra in sub.get("filings", {}).get("files", []):
                if str(extra.get("filingTo", "9999")) >= "2014-01-01":
                    page = sec.get_json(SUBMISSIONS_FILE_URL.format(name=extra["name"]))
                    if page:
                        take(t, page)
            done.add(t)
        except Exception as exc:
            LOG.warning("SEC filings %s: %s", t, exc)
        if len(rows) > 50000:
            have = _append_f(have, rows, path)
            rows = []
            done_path.write_text(json.dumps(sorted(done)))
    have = _append_f(have, rows, path)
    done_path.write_text(json.dumps(sorted(done)))
    LOG.info("SEC filings: %d filings of %d companies, %d left", len(have), len(done), left)
    return left


def _append_f(have: pd.DataFrame, rows: list[dict], path: Path) -> pd.DataFrame:
    if rows:
        have = pd.concat([have, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(["ticker", "form", "accepted"])
        have.to_parquet(path)
    return have


# -----------------------------------------------------------------------------
# Wikipedia (search for the companies Wikidata misses)
# -----------------------------------------------------------------------------
def collect_wiki_extra(names: dict[str, str], known: set[str], root, deadline: float) -> int:
    from urllib.parse import quote

    from .consumer import PAGEVIEWS_URL

    tpath = media_root(root) / "wiki_extra_titles.json"
    titles = json.loads(tpath.read_text()) if tpath.exists() else {}
    api = Paced(0.1)
    left = 0
    for t, n in names.items():
        if t in known or t in titles:
            continue
        if time.time() > deadline:
            left += 1
            continue
        r = api.get(WIKI_API, {"action": "query", "list": "search", "srsearch": f"{n} company",
                               "format": "json", "srlimit": 1})
        hit = ((r.json().get("query") or {}).get("search") or [{}])[0] if r is not None and r.status_code == 200 else {}
        titles[t] = hit.get("title")
    tpath.write_text(json.dumps(titles))
    st = Store(media_root(root) / "wiki_extra_pageviews.parquet")
    end = (pd.Timestamp.today() - pd.Timedelta(days=1)).strftime("%Y%m%d")
    for t, title in titles.items():
        if not title or st.has(t):
            continue
        if time.time() > deadline:
            left += 1
            continue
        r = api.get(PAGEVIEWS_URL.format(title=quote(title.replace(" ", "_"), safe=""), start="20150701", end=end))
        items = r.json().get("items", []) if r is not None and r.status_code == 200 else []
        st.add(t, pd.Series({pd.Timestamp(it["timestamp"][:8]): it["views"] for it in items}, dtype=float))
    st.save()
    LOG.info("Wikipedia (search): %d titles, %d with page views", sum(1 for v in titles.values() if v), st.df.shape[1])
    return left


# -----------------------------------------------------------------------------
def company_names(tickers: list[str], data_root: str = "data") -> dict[str, str]:
    from .consumer import company_search_terms

    return {t: short_name(n) for t, n in company_search_terms(tickers, data_root).items() if short_name(n)}


def collect_all(tickers: list[str], budget_min: float, root=None, data_root: str = "data",
                n_tv: int = 150) -> dict:
    """Run every collector until the time budget is used; returns what is left per source."""
    deadline = time.time() + budget_min * 60
    names = company_names(tickers, data_root)
    LOG.info("media collection: %d companies with names, budget %.0f min", len(names), budget_min)
    left = {}
    # fast sources first, then GDELT (5 s per request) until the budget runs out
    for label, fn in (("hn", lambda: collect_hn(root, deadline)),
                      ("sec_filings", lambda: collect_sec_filings(tickers, root, deadline)),
                      ("sec_phrases", lambda: collect_sec_phrases(root, deadline)),
                      ("wiki_extra", lambda: collect_wiki_extra(names, _wikidata_known(data_root), root, deadline))):
        try:
            left[label] = fn()
        except Exception as exc:
            LOG.warning("%s collection failed: %s", label, exc)
            left[label] = -1
    api = Paced(8.0)                                          # GDELT: one request per 5 s at most
    themes = {t: (f'"{t}"' if " " in t else t) for t in THEMES}
    comp = {t: f'"{n}"' for t, n in names.items()}
    tv_comp = dict(list(comp.items())[:n_tv])                  # tickers come most liquid first
    for label, keys, name, url, modes in (
            ("gdelt_themes", themes, "gdelt_theme", GDELT_DOC, ("timelinevolraw", "timelinetone")),
            ("tv_themes", {k: f"{q} market:\"National\"" for k, q in themes.items()}, "tv_theme", GDELT_TV,
             ("timelinevol",)),
            ("gdelt_companies", comp, "gdelt_company", GDELT_DOC, ("timelinevolraw", "timelinetone")),
            ("tv_companies", {k: f"{q} market:\"National\"" for k, q in tv_comp.items()}, "tv_company", GDELT_TV,
             ("timelinevol",))):
        try:
            left[label] = collect_gdelt(keys, name, url, modes, root, deadline, api)
        except Exception as exc:
            LOG.warning("%s collection failed: %s", label, exc)
            left[label] = -1
    LOG.info("media collection: still to fetch %s", left)
    return left


def _wikidata_known(data_root: str) -> set[str]:
    try:
        from .consumer import wiki_titles

        return set(wiki_titles(data_root)["ticker"])
    except Exception:
        return set()


def inventory(root=None) -> pd.DataFrame:
    """One row per collected dataset: rows, columns, first and last date."""
    rows = []
    for p in sorted(media_root(root).glob("*.parquet")):
        df = pd.read_parquet(p)
        idx = df.index if isinstance(df.index, pd.DatetimeIndex) else None
        rows.append({"dataset": p.stem, "rows": len(df), "columns": df.shape[1],
                     "first": str(idx.min().date()) if idx is not None and len(idx) else "",
                     "last": str(idx.max().date()) if idx is not None and len(idx) else "",
                     "megabytes": round(p.stat().st_size / 1e6, 1)})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="collect news / media data (incremental)")
    ap.add_argument("--budget", type=float, default=60, help="minutes")
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--status-file", default=None, help="write 'more' or 'done' here")
    args = ap.parse_args(argv)
    setup_logging()
    u = pd.read_csv(args.universe)
    col = "ticker" if "ticker" in u else u.columns[0]
    tickers = [str(t) for t in u[col]]
    left = collect_all(tickers, args.budget)
    inv = inventory()
    LOG.info("media data:\n%s", inv.to_string(index=False))
    if args.status_file:
        Path(args.status_file).write_text("more" if any(v != 0 for v in left.values()) else "done")


if __name__ == "__main__":
    main()
