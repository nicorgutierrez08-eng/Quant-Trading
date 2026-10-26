"""Events: what happens to a stock after specific kinds of news and index changes.

1. News event types, classified from headlines with keyword rules (merger,
   FDA, guidance raised/cut, earnings beat/miss, analyst upgrade/downgrade,
   price-target raise/cut, share offering, lawsuit/probe, buyback, dividend
   raise, CEO change). For each type: average market-relative return over the
   next 1, 5 and 21 trading days, starting the first trading day after the
   article (so the reaction on the news day itself is excluded - what is left
   is what a trader could still capture).
2. Novelty: a headline that shares few words with the stock's headlines over
   the previous week is "novel". Does a day's move continue after novel news
   and reverse after stale news?
3. S&P 500 additions and removals: average market-relative return path from
   20 days before to 20 days after the effective date.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

EVENT_RULES = {
    "merger / acquisition": r"\b(acquir\w*|merger|takeover|buyout|to buy|agrees to buy|deal to buy)\b",
    "FDA / trial": r"\b(fda|clinical trial|phase (1|2|3|i|ii|iii)|approval)\b",
    "guidance raised": r"\b(raises|boosts|lifts|ups) (its |fy|full-year |annual )?(guidance|outlook|forecast)",
    "guidance cut": r"\b(lowers|cuts|slashes|reduces) (its |fy|full-year |annual )?(guidance|outlook|forecast)",
    "earnings beat": r"\bbeats?\b",
    "earnings miss": r"\bmiss(es)?\b",
    "analyst upgrade": r"\bupgrade[sd]?\b",
    "analyst downgrade": r"\bdowngrade[sd]?\b",
    "price target raised": r"(raises|boosts|lifts) .{0,20}price target",
    "price target cut": r"(lowers|cuts) .{0,20}price target",
    "share offering": r"\b(offering|secondary|prices? .{0,30}shares|at-the-market)\b",
    "lawsuit / probe": r"\b(lawsuit|sues|sued|probe|investigation|subpoena|class action)\b",
    "buyback": r"\b(buyback|repurchase)\b",
    "dividend raise": r"\b(raises|boosts|hikes|increases) (quarterly )?dividend",
    "CEO change": r"\bceo\b.{0,30}\b(steps down|resign\w*|depart\w*|to retire|named|appoint\w*)",
}


def _usable_day(dates: pd.DatetimeIndex, ts: pd.Series) -> np.ndarray:
    """Index of the first trading day whose *open* comes after the article."""
    ny = ts.dt.tz_convert("America/New_York")
    day = ny.dt.tz_localize(None).dt.normalize()
    before_open = (ny.dt.hour * 60 + ny.dt.minute) < 9 * 60 + 30
    pos = np.where(before_open, dates.searchsorted(day, side="left"), dates.searchsorted(day, side="right"))
    return pos


def _car(ar: np.ndarray, rows: np.ndarray, cols: np.ndarray, h: int, first: np.ndarray | None = None) -> np.ndarray:
    """Cumulative abnormal return over days [row, row + h) for each event.

    ``first``: the abnormal return to use for the first day instead of ``ar``
    (e.g. open-to-close, so a gap at the open - which happened before anyone
    could trade on the news - is not counted)."""
    cs = np.vstack([np.zeros((1, ar.shape[1])), np.nancumsum(np.nan_to_num(ar), axis=0)])
    end = np.minimum(rows + h, len(ar))
    ok = rows < len(ar)
    out = np.full(len(rows), np.nan)
    if first is None:
        out[ok] = cs[end[ok], cols[ok]] - cs[rows[ok], cols[ok]]
    else:
        nxt = np.minimum(rows[ok] + 1, len(ar))
        out[ok] = np.nan_to_num(first[rows[ok], cols[ok]]) + cs[end[ok], cols[ok]] - cs[nxt, cols[ok]]
    return out


def _date_clustered(values: np.ndarray, rows: np.ndarray) -> tuple[float, float, int]:
    """Mean and t-stat with events on the same day averaged first (they're correlated)."""
    s = pd.Series(values).groupby(rows).mean().dropna()
    if len(s) < 10:
        return np.nan, np.nan, len(s)
    return float(s.mean()), float(s.mean() / s.std() * np.sqrt(len(s))), len(s)


def news_events(md, ctx, news: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tick = {t: i for i, t in enumerate(md.tickers)}
    x = news[["created_at", "headline", "symbols"]].copy()
    x["ticker"] = x["symbols"].str.split(",")
    x = x.explode("ticker")
    x = x[x["ticker"].isin(tick)]
    x["row"] = _usable_day(md.dates, x["created_at"])
    x = x[x["row"] < len(md.dates)]
    x["col"] = x["ticker"].map(tick)
    hl = x["headline"].fillna("").str.lower()
    ar = ctx.ret.sub(ctx.market_ret, axis=0).clip(-0.5, 0.5).to_numpy()
    intra = ctx.intraday.clip(-0.5, 0.5)
    ar_open = intra.sub(intra.mean(axis=1), axis=0).to_numpy()      # day 1 counts from the open we can trade at
    rows = []
    for name, pat in EVENT_RULES.items():
        m = hl.str.contains(pat, regex=True)
        ev = x[m].drop_duplicates(["ticker", "row"])
        if len(ev) < 30:
            continue
        r, c = ev["row"].to_numpy(), ev["col"].to_numpy()
        row = {"event": name, "events": len(ev)}
        for h in (1, 5, 21):
            mean, t, n = _date_clustered(_car(ar, r, c, h, ar_open), r)
            row[f"car_{h}d_bp"] = mean * 1e4 if np.isfinite(mean) else np.nan
            row[f"t_{h}d"] = t
        rows.append(row)
    tab = pd.DataFrame(rows).sort_values("t_5d", key=np.abs, ascending=False)

    # novelty: word overlap with the stock's headlines over the prior 7 days
    x = x.sort_values("created_at")
    words = hl.loc[x.index].map(lambda s: set(re.findall(r"[a-z]{3,}", s)))
    nov = np.full(len(x), np.nan)
    hist: dict[str, list] = {}
    times = x["created_at"].to_numpy()
    for i, (t, w, ts) in enumerate(zip(x["ticker"].to_numpy(), words.to_numpy(), times)):
        past = [pw for pts, pw in hist.get(t, []) if ts - pts < np.timedelta64(7, "D")]
        if past and w:
            nov[i] = 1 - max(len(w & pw) / max(len(w | pw), 1) for pw in past)
        elif w:
            nov[i] = 1.0
        hist[t] = [(pts, pw) for pts, pw in hist.get(t, []) if ts - pts < np.timedelta64(7, "D")] + [(ts, w)]
    x["novelty"] = nov
    day = x.groupby(["row", "col"])["novelty"].max().reset_index()
    # the stock's move on the day the news became usable, then what follows
    r, c = day["row"].to_numpy(), day["col"].to_numpy()
    # reaction up to the open we can trade at: previous close -> this open, market-relative
    gap = ctx.overnight.clip(-0.5, 0.5)
    gap = gap.sub(gap.mean(axis=1), axis=0).to_numpy()
    move = np.sign(np.nan_to_num(gap[np.minimum(r, len(gap) - 1), c]))
    nrows = []
    for label, sel in (("novel (overlap < 30%)", day["novelty"] > 0.7), ("stale (overlap > 70%)", day["novelty"] < 0.3)):
        sel = sel.to_numpy()
        for h in (1, 5, 21):
            mean, t, n = _date_clustered(move[sel] * _car(ar, r[sel], c[sel], h, ar_open), r[sel])
            nrows.append({"news": label, "horizon": h, "continuation_bp": mean * 1e4 if np.isfinite(mean) else np.nan,
                          "t": t, "days": n})
    return tab, pd.DataFrame(nrows)


def index_events(md, ctx, changes: pd.DataFrame) -> pd.DataFrame:
    ar = ctx.ret.sub(ctx.market_ret, axis=0).clip(-0.5, 0.5)
    offsets = [-20, -10, -5, -1, 0, 1, 5, 10, 20]
    rows = []
    for kind in ("added", "removed"):
        paths = []
        for _, r in changes.dropna(subset=[kind]).iterrows():
            t = r[kind]
            if t not in ar.columns:
                continue
            p = ar.index.searchsorted(r["date"])
            if p - 21 < 0 or p + 21 >= len(ar):
                continue
            seg = ar[t].iloc[p - 20:p + 21].fillna(0).cumsum()
            seg = seg - seg.iloc[19]                              # cumulative from the close before day -1
            paths.append([seg.iloc[20 + o] for o in offsets])
        if paths:
            P = np.array(paths)
            rows.append({"change": kind, "events": len(P),
                         **{f"day{o:+d}_bp": P[:, i].mean() * 1e4 for i, o in enumerate(offsets)},
                         "t_day+20": P[:, -1].mean() / (P[:, -1].std() + 1e-12) * np.sqrt(len(P))})
    return pd.DataFrame(rows)


def run(md, ctx, out: Path, cfg) -> dict:
    lines = ["## Events: news types, novelty and index changes", ""]
    res = {}
    npath = Path(cfg.data.cache_dir) / "news"
    if any(npath.glob("news_*.parquet")):
        from ..data.news import load_news

        tab, nov = news_events(md, ctx, load_news(npath))
        tab.to_csv(out / "news_events.csv", index=False)
        nov.to_csv(out / "news_novelty.csv", index=False)
        lines += ["### After each kind of news (market-relative, from the first open after the article)", "",
                  "t-stats average same-day events first, since they move together.", "",
                  tab.round(2).to_markdown(index=False), "",
                  "### Novel vs. stale news: does the move continue?", "",
                  "continuation = return in the direction of the stock's move into the open after the news "
                  "(positive = it keeps going, negative = it reverses).", "",
                  nov.round(2).to_markdown(index=False), ""]
        res["news_event_types"] = len(tab)
    try:
        from ..data.public import load_sp500_changes

        ch = load_sp500_changes(cfg.data.cache_dir)
        ie = index_events(md, ctx, ch)
        ie.to_csv(out / "index_events.csv", index=False)
        lines += ["### S&P 500 additions and removals", "",
                  "Average cumulative market-relative return around the effective date (day 0), measured from "
                  "the close before day -1. Only stocks in the price universe.", "",
                  ie.round(1).to_markdown(index=False), ""]
        res["index_events"] = ie.round(1).to_dict(orient="records")
    except Exception as exc:
        LOG.warning("index events skipped: %s", exc)
    (out / "events.md").write_text("\n".join(lines) + "\n")
    return res
