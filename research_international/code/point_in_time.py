"""Point-in-time membership for NIFTY 50 and DAX: how much does survivorship move the result?

Rebuilds each index's membership on every date by walking its Wikipedia change
table backwards from today's members (before a change date, the included
company is out and the excluded one is in), resolves company names to Yahoo
tickers with Yahoo's search endpoint, downloads the former members that still
have price history, and reruns the momentum books on (a) today's members only
(the survivor universe used everywhere else) and (b) the point-in-time
members. Companies that were acquired or delisted usually have no Yahoo
history; the coverage table reports how many members are missing on each date,
so the remaining bias is visible.

    python research_international/code/point_in_time.py --prices data/prices --out reports/pit
"""
from __future__ import annotations

import argparse
import io
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import intl_lab as L
from download import fetch, save_market

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (research)"


def resolve(name: str, exchange: str, suffix: str) -> str | None:
    q = re.sub(r"\(.*?\)|\[.*?\]", "", str(name)).replace("Ltd", "").replace("Limited", "").strip()
    for attempt in (q, q.split(" now ")[0], " ".join(q.split()[:2])):
        try:
            r = S.get("https://query2.finance.yahoo.com/v1/finance/search", params={"q": attempt, "quotesCount": 8, "newsCount": 0}, timeout=20)
            for x in r.json().get("quotes", []):
                if x.get("exchange") == exchange and str(x.get("symbol", "")).endswith(suffix):
                    return x["symbol"]
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.3)
    return None


def nifty_changes() -> pd.DataFrame:
    t = pd.read_html(io.StringIO(S.get("https://en.wikipedia.org/wiki/NIFTY_50", timeout=30).text))[2]
    t.columns = [c[1] if isinstance(c, tuple) else c for c in t.columns]
    t = t.rename(columns={"Constituent excluded": "out", "Constituent included": "in", "Date of replacement": "date"})
    t["date"] = pd.to_datetime(t["date"], errors="coerce", dayfirst=True)
    return t.dropna(subset=["date"])[["date", "out", "in"]]


def dax_changes() -> pd.DataFrame:
    t = [x for x in pd.read_html(io.StringIO(S.get("https://en.wikipedia.org/wiki/DAX", timeout=30).text))
         if "Component excluded" in " ".join(map(str, x.columns))][0]
    t = t.rename(columns={"Component excluded": "out", "Component included": "in", "Date": "date"})
    t["date"] = pd.to_datetime(t["date"], format="%d.%m.%Y", errors="coerce")
    return t.dropna(subset=["date"])[["date", "out", "in"]]


def membership(current: list[str], changes: pd.DataFrame, name_to_ticker: dict, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """members(t) = today's list with every change dated after t undone.

    Undoing a change (out, in) means removing `in` and adding back `out`.
    Changes are undone newest first, so members(t) is the state after undoing
    all changes with date > t; it applies on [next older change date, this
    change date). Companies with no Yahoo ticker are kept as UNRESOLVED:<name>
    so the coverage table counts them."""
    ch = changes.sort_values("date", ascending=False).reset_index(drop=True)
    state = set(current)
    intervals = []                      # (from, to, members)
    upper = pd.Timestamp.max
    for _, row in ch.iterrows():
        intervals.append((row["date"], upper, set(state)))       # state valid from this change until the next newer one
        tin = name_to_ticker.get(row["in"]) or (f"UNRESOLVED:{row['in']}" if isinstance(row["in"], str) else None)
        tout = name_to_ticker.get(row["out"]) or (f"UNRESOLVED:{row['out']}" if isinstance(row["out"], str) else None)
        state.discard(tin)
        if tout:
            state.add(tout)
        upper = row["date"]
    intervals.append((pd.Timestamp.min, upper, set(state)))
    cols = sorted({t for _, _, s in intervals for t in s})
    M = pd.DataFrame(False, index=dates, columns=cols)
    for lo, hi, s in intervals:
        mask = (dates >= lo) & (dates < hi)
        if mask.any() and s:
            M.loc[mask, sorted(s)] = True
    return M


def run(name: str, market_dir: str, suffix: str, exchange: str, changes: pd.DataFrame, current: list[str], start_year: int,
        prices: Path, out: Path, vix: pd.Series) -> pd.DataFrame:
    names = set(changes["in"].dropna()) | set(changes["out"].dropna())
    known = {}
    for n in sorted(names):
        known[n] = resolve(n, exchange, suffix)
    resolved = {k: v for k, v in known.items() if v}
    print(f"{name}: {len(resolved)}/{len(names)} company names resolved to {exchange} tickers")
    extra = sorted(set(resolved.values()) - set(current))
    pit_dir = out / f"{market_dir}_pit"
    base = {f: pd.read_parquet(prices / market_dir / f"{f}.parquet") for f in ("open", "high", "low", "close", "adj_close", "volume")}
    if extra:
        f = fetch(extra, "2000-01-01", batch=40)
        if "Close" in f:
            # merge with the existing market files
            names_map = {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}
            fac = (f["Adj Close"] / f["Close"]).where(f["Close"] > 0)
            for k, v in f.items():
                if k in ("Open", "High", "Low"):
                    v = v * fac.reindex_like(v)
                v = v[[c for c in v.columns if c not in base[names_map[k]].columns]]   # some former members are already in the folder
                base[names_map[k]] = base[names_map[k]].join(v, how="outer")
    pit_dir.mkdir(parents=True, exist_ok=True)
    for k, v in base.items():
        v.sort_index().to_parquet(pit_dir / f"{k}.parquet")
    uni = pd.DataFrame({"ticker": base["adj_close"].columns, "financial": False})
    m = L.Market(name, pit_dir, uni, vix)
    M = membership(current, changes, resolved, m.dates)
    have = [c for c in M.columns if c in m.tickers]
    in_pit = M.reindex(columns=m.tickers, fill_value=False)
    in_today = pd.DataFrame(False, index=m.dates, columns=m.tickers)
    in_today[[c for c in current if c in m.tickers]] = True
    cov = pd.DataFrame({"members": M.sum(axis=1), "members_with_prices": M[have].sum(axis=1) if have else 0,
                        "unresolved_or_no_data": M.sum(axis=1) - (M[have].sum(axis=1) if have else 0)}).resample("YE").last()
    cov.index = cov.index.year
    sigs = m.signals()
    comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
    stress = m.vix > 20
    rows = []
    for uni_label, mask in (("today's members (survivors)", m.tradable & in_today), ("point-in-time members", m.tradable & in_pit)):
        for rule, sign in (("plain", None), ("flip", pd.Series(np.where(stress, -1.0, 1.0), index=m.dates)),
                           ("flat in stress", pd.Series(np.where(stress, 0.0, 1.0), index=m.dates))):
            W = L.staggered(m, comp, mask, sign)
            s = L.pnl(W, m)["net"][f"{start_year}":]
            rows.append(L.period_stats(s, f"{name}, {uni_label}, {rule}", {"median_names": int(mask.sum(axis=1)[f"{start_year}":].median())}))
    tab = pd.DataFrame(rows)
    tab.to_csv(out / f"pit_{market_dir}.csv", index=False)
    cov.to_csv(out / f"pit_{market_dir}_coverage.csv")
    pd.set_option("display.width", 250)
    print(cov.to_string())
    print(tab[["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "median_names"]].round(2).to_string(index=False))
    return tab


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices")
    ap.add_argument("--universe", default="data/universe.csv")
    ap.add_argument("--out", default="reports/pit")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prices = Path(args.prices)
    u = pd.read_csv(args.universe)
    vix = pd.read_parquet(prices / "_series" / "adj_close.parquet")["vol:US"].dropna()
    nifty_now = u[(u["market"] == "India") & (u["index"] == "NIFTY 50")]["ticker"].tolist()
    dax_now = u[u["market"] == "Germany"]["ticker"].tolist()
    a = run("India NIFTY 50", "India", ".NS", "NSI", nifty_changes(), nifty_now, 2006, prices, out, vix)
    b = run("Germany DAX", "Germany", ".DE", "GER", dax_changes()[lambda d: d["date"] >= "2002-01-01"], dax_now, 2006, prices, out, vix)
    pd.concat([a, b]).to_csv(out / "pit_all.csv", index=False)


if __name__ == "__main__":
    main()
