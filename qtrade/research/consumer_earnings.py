"""Consumer companies around earnings: do free consumer signals predict the reaction?

Events: every 8-K item 2.02 (earnings release) of the price universe since
2016, with the second it was filed. A release after the close of day d is
traded with a market-on-close order on d and a market-on-open exit on d+1; a
release before the open of day d with a market-on-close order on d-1 and the
open of d. (Companies announce their earnings dates weeks ahead, so the date
is treated as known; the result is not.) Releases during the session are left
out.

Signals, all known at the entry close:

  wiki_attention   page views in the 7 days before entry vs the 60 days before that
  wiki_yoy         page views over the last 90 days vs the same 90 days a year earlier
  trends_yoy       Google search interest, last 4 weeks vs a year earlier (when available)
  runup_20d        the stock's return over the 20 days before entry (market-relative)
  last_reaction    the previous release's announcement return

Outcomes (market-relative): the announcement return (entry close -> exit open),
and the drift from that open to the close 5 and 20 days later.

Each signal's direction comes from 2016-2020 only; 2021-2026 is the check.
Trading: equal dollars per event, long or short by the signal (or the composite),
IBKR Lite costs (no commission; SEC fee and FINRA TAF on sales; auction legs at
0 bp, 1 bp as a stress case). Consumer companies (by SIC code) and the whole
universe side by side.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

SPLIT = "2021-01-01"
SIGNALS = ["wiki_attention", "wiki_yoy", "trends_yoy", "runup_20d", "last_reaction"]
SEC_FEE = 27.80e-6                    # per dollar sold
TAF = 0.000166                        # per share sold (approximated per dollar below)


def build_events(md, events: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """One row per tradable release: entry day index, exit (next open) day index, consumer flag."""
    dates = md.dates
    tick = {t: i for i, t in enumerate(md.tickers)}
    cons = dict(zip(profiles["ticker"], profiles["consumer"])) if len(profiles) else {}
    rows = []
    for _, e in events.iterrows():
        if e["ticker"] not in tick or e["session"] == "during":
            continue
        day = e["accepted"].tz_localize(None).normalize()
        pos = dates.searchsorted(day)
        if pos >= len(dates):
            continue
        if e["session"] == "after_close":
            if dates[pos] != day:                       # filed on a non-trading day: treat as before the next open
                entry = pos - 1
            else:
                entry = pos
        else:                                           # before the open of day `pos`
            entry = pos - 1
        if entry < 1 or entry + 1 >= len(dates):
            continue
        rows.append({"ticker": e["ticker"], "col": tick[e["ticker"]], "entry": entry, "exit": entry + 1,
                     "date": dates[entry + 1], "session": e["session"], "consumer": bool(cons.get(e["ticker"], False))})
    ev = pd.DataFrame(rows).drop_duplicates(["ticker", "entry"])
    return ev[ev["date"] >= "2016-01-01"].reset_index(drop=True)


def outcomes(md, ev: pd.DataFrame) -> pd.DataFrame:
    o, c = md.open.to_numpy(), md.close.to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        ann = o[1:] / c[:-1] - 1                                    # close t -> open t+1, indexed by t
        mkt_ann = np.nanmean(np.clip(ann, -0.5, 0.5), axis=1)
    out = ev.copy()
    e, x, j = ev["entry"].to_numpy(), ev["exit"].to_numpy(), ev["col"].to_numpy()
    out["ann_ret"] = np.clip(ann[e, j], -0.5, 0.5) - mkt_ann[e]
    for h in (5, 20):
        end = np.minimum(x + h, len(c) - 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            r = c[end, j] / o[x, j] - 1
            m = np.nanmean(np.clip(c[end] / o[x] - 1, -0.5, 0.5), axis=1)
        out[f"drift_{h}d"] = np.clip(r, -0.5, 0.5) - m
    out["entry_price"] = c[e, j]
    return out


def features(md, ev: pd.DataFrame, views: pd.DataFrame | None, trends: pd.DataFrame | None) -> pd.DataFrame:
    out = ev.copy()
    dates = md.dates
    c = md.close
    lr = np.log(c / c.shift(1))
    mkt = lr.mean(axis=1)
    run = (lr.sub(mkt, axis=0)).rolling(20, min_periods=15).sum()
    out["runup_20d"] = [run.iat[e, j] for e, j in zip(ev["entry"], ev["col"])]
    # previous release's announcement return for the same ticker (known: it happened earlier)
    out = out.sort_values(["ticker", "entry"])
    out["last_reaction"] = out.groupby("ticker")["ann_ret"].shift(1) if "ann_ret" in out else np.nan
    out = out.sort_index()
    wa, wy, ty = [], [], []
    for _, r in out.iterrows():
        d = dates[r["entry"]]
        a = wy_ = t_ = np.nan
        if views is not None and r["ticker"] in views:
            v = views[r["ticker"]]
            known = v[v.index < d]                  # day d's views are published on d+1
            if len(known) > 400:
                last7, prior60 = known.iloc[-7:].mean(), known.iloc[-67:-7].mean()
                a = np.log((last7 + 1) / (prior60 + 1))
                l90 = known.iloc[-90:].mean()
                ya = known[(known.index >= d - pd.Timedelta(days=455)) & (known.index < d - pd.Timedelta(days=365))]
                if len(ya) > 60:
                    wy_ = np.log((l90 + 1) / (ya.mean() + 1))
        if trends is not None and r["ticker"] in trends:
            g = trends[r["ticker"]]
            known = g[g.index <= d]
            if len(known) > 60:
                ya = known[(known.index > d - pd.Timedelta(days=393)) & (known.index <= d - pd.Timedelta(days=365))]
                if len(ya):
                    t_ = np.log((known.iloc[-4:].mean() + 1) / (ya.mean() + 1))
        wa.append(a)
        wy.append(wy_)
        ty.append(t_)
    out["wiki_attention"], out["wiki_yoy"], out["trends_yoy"] = wa, wy, ty
    return out


def _ic(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    ok = x.notna() & y.notna()
    if ok.sum() < 30:
        return np.nan, int(ok.sum())
    return float(x[ok].rank().corr(y[ok].rank())), int(ok.sum())


def ic_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for uni, part in (("consumer", df[df["consumer"]]), ("all companies", df)):
        for s in SIGNALS:
            for y in ("ann_ret", "drift_5d", "drift_20d"):
                row = {"universe": uni, "signal": s, "outcome": y}
                for tag, m in (("2016_20", part["date"] < SPLIT), ("2021_26", part["date"] >= SPLIT)):
                    row[f"ic_{tag}"], row[f"n_{tag}"] = _ic(part.loc[m, s], part.loc[m, y])
                rows.append(row)
    return pd.DataFrame(rows)


def _zq(df: pd.DataFrame, col: str) -> pd.Series:
    """Rank within each calendar quarter, mapped to [-1, 1] (comparable across seasons)."""
    q = df["date"].dt.to_period("Q")
    return df.groupby(q)[col].rank(pct=True).mul(2).sub(1)


def strategies(df: pd.DataFrame, tab: pd.DataFrame, slip_bp: float = 0.0, per_event: float = 0.02) -> pd.DataFrame:
    """Daily returns of trading the announcement (MOC in, MOO out) on each signal and the composite,
    sign from 2016-2020; ``per_event`` of capital per event (long or short)."""
    rows = []
    for uni, part in (("consumer", df[df["consumer"]].copy()), ("all companies", df.copy())):
        signs = {}
        for s in SIGNALS:
            r = tab[(tab["universe"] == uni) & (tab["signal"] == s) & (tab["outcome"] == "ann_ret")]
            ic = r["ic_2016_20"].iloc[0] if len(r) else np.nan
            signs[s] = 0.0 if not np.isfinite(ic) else float(np.sign(ic))
        for s in SIGNALS:
            part[f"z_{s}"] = _zq(part, s)
        used = [s for s in SIGNALS if signs[s] != 0 and part[s].notna().mean() > 0.3]
        part["z_composite"] = sum(signs[s] * part[f"z_{s}"].fillna(0) for s in used) / max(len(used), 1)
        for name in used + ["composite"]:
            sgn = 1.0 if name == "composite" else signs[name]
            pos = np.sign(sgn * part[f"z_{name}"]).fillna(0)
            gross = pos * part["ann_ret"]
            # costs per event, as a fraction of the position: auction slippage both legs + fees on the sell leg
            cost = (2 * slip_bp / 1e4 + SEC_FEE + TAF / part["entry_price"].clip(lower=1)) * (pos != 0)
            pnl = (gross - cost) * per_event
            daily = pnl.groupby(part["date"]).sum()
            idx = pd.bdate_range(daily.index.min(), daily.index.max())
            daily = daily.reindex(idx, fill_value=0.0)
            row = {"universe": uni, "strategy": name, "direction": "+" if sgn > 0 else "-", "events": int((pos != 0).sum()),
                   "auction_slippage_bp": slip_bp}
            for tag, m in (("2016_20", daily.index < SPLIT), ("2021_26", daily.index >= SPLIT)):
                d = daily[m]
                row[f"sharpe_{tag}"] = d.mean() / d.std() * np.sqrt(252) if d.std() > 0 else np.nan
                row[f"annual_return_{tag}"] = d.mean() * 252
                ev_m = (part["date"] < SPLIT) if tag == "2016_20" else (part["date"] >= SPLIT)
                row[f"avg_event_bp_{tag}"] = float((gross[ev_m & (pos != 0)]).mean() * 1e4)
            rows.append(row)
        # post-earnings drift: follow the announcement move for 5 / 20 days (enter at the open, exit at a close)
        for h in (5, 20):
            pos = np.sign(part["ann_ret"]).fillna(0)
            gross = pos * part[f"drift_{h}d"]
            row = {"universe": uni, "strategy": f"post-earnings drift {h}d", "direction": "+", "events": int((pos != 0).sum()),
                   "auction_slippage_bp": slip_bp}
            for tag, m in (("2016_20", part["date"] < SPLIT), ("2021_26", part["date"] >= SPLIT)):
                g = gross[m & (pos != 0)]
                row[f"avg_event_bp_{tag}"] = float(g.mean() * 1e4)
                row[f"t_{tag}"] = float(g.mean() / g.std() * np.sqrt(len(g))) if len(g) > 30 else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def intraday_reaction(md, ctx, df: pd.DataFrame, root: str) -> pd.DataFrame:
    """Reaction day (the session after the release): does the first half hour's move continue
    from 10:00 to the close, or reverse? Entry at 10:00 pays the half-spread (x1 and x2: spreads
    are wider on earnings days), exit in the closing auction."""
    from ..research.edge import cost_panel
    from .intraday_stats import load

    st = load(root)
    if st is None:
        return pd.DataFrame()
    f30 = st["first30"].reindex(index=md.dates, columns=md.tickers).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        oc = np.log(md.close / md.open).to_numpy()
    hs = (cost_panel(ctx) - 1e-4).to_numpy()                 # half-spread by liquidity tier (without slippage)
    x, j = df["exit"].to_numpy(), df["col"].to_numpy()
    d = df.assign(first30=f30[x, j], rest=oc[x, j] - f30[x, j], half_spread=hs[x, j]).dropna(subset=["first30", "rest"])
    rows = []
    for uni, part in (("consumer", d[d["consumer"]]), ("all companies", d)):
        for tag, m in (("2016_20", part["date"] < SPLIT), ("2021_26", part["date"] >= SPLIT)):
            p = part[m]
            if len(p) < 30:
                continue
            ic = p["first30"].rank().corr(p["rest"].rank())
            for name, sgn in (("follow the first 30 min", 1.0), ("fade the first 30 min", -1.0)):
                g = sgn * np.sign(p["first30"]) * p["rest"]
                rows.append({"universe": uni, "period": tag, "strategy": name, "events": len(p),
                             "ic_first30_vs_rest": ic, "gross_bp": g.mean() * 1e4,
                             "net_bp_spread_x1": (g - p["half_spread"] - 0.5e-4).mean() * 1e4,
                             "net_bp_spread_x2": (g - 2 * p["half_spread"] - 0.5e-4).mean() * 1e4,
                             "t_gross": g.mean() / g.std() * np.sqrt(len(g)) if g.std() > 0 else np.nan})
    return pd.DataFrame(rows)


def run(md, ctx, out: Path, cfg) -> dict:
    from ..data.consumer import company_search_terms, google_trends, sec_profiles_and_earnings, wiki_pageviews

    root = cfg.data.cache_dir
    profiles, events = sec_profiles_and_earnings(list(md.tickers), root)
    if events.empty:
        (out / "consumer_earnings.md").write_text("## Consumer earnings\n\n(no SEC earnings events)\n")
        return {"error": "no events"}
    views = None
    try:
        views = wiki_pageviews(list(md.tickers), root)
    except Exception as exc:
        LOG.warning("Wikipedia page views unavailable: %s", exc)
    trends = None
    try:
        names = company_search_terms(list(profiles.loc[profiles["consumer"], "ticker"]), root)
        trends = google_trends(names, root, budget_min=float(os.environ.get("TRENDS_BUDGET_MIN", "0")))
        trends = trends if len(trends) else None
    except Exception as exc:
        LOG.warning("Google Trends unavailable: %s", exc)
    ev = build_events(md, events, profiles)
    df = outcomes(md, ev)
    df = features(md, df, views, trends)
    df.to_csv(out / "consumer_earnings_events.csv", index=False)
    tab = ic_table(df)
    tab.to_csv(out / "consumer_earnings_ic.csv", index=False)
    strat = pd.concat([strategies(df, tab, 0.0), strategies(df, tab, 1.0)], ignore_index=True)
    strat.to_csv(out / "consumer_earnings_strategies.csv", index=False)
    hft = pd.DataFrame()
    try:
        hft = intraday_reaction(md, ctx, df, root)
        hft.to_csv(out / "consumer_earnings_intraday.csv", index=False)
    except Exception as exc:
        LOG.warning("intraday reaction study failed: %s", exc)
    cov = {s: float(df[s].notna().mean()) for s in SIGNALS}
    lines = ["## Consumer companies around earnings", "",
             f"{len(df)} earnings releases since 2016 ({int(df['consumer'].sum())} from consumer companies by SIC "
             "code), traded with a market-on-close order before the release and a market-on-open exit after it. "
             "Signal directions from 2016-2020; 2021-2026 is the check. Coverage of each signal: "
             + ", ".join(f"{k} {v:.0%}" for k, v in cov.items()) + ".", "",
             "### Rank correlation of each signal with the outcome", "",
             tab.round(3).to_markdown(index=False), "",
             "### Trading it (IBKR Lite: no commission; SEC/FINRA fees on sales; auction legs at 0 bp and 1 bp)", "",
             "2% of capital per event; announcement trades are overnight (close -> next open). The post-earnings "
             "drift rows show the average event return and its t-statistic (entered at the open after the release).",
             "", strat.round(3).to_markdown(index=False), "",
             "### High frequency: the reaction day, from 10:00 to the close", "",
             "Does the first half hour's move after a release continue or reverse? Entry at 10:00 pays the half-spread "
             "(x1, and x2 because spreads widen on earnings days) plus 0.5 bp; exit in the closing auction.", "",
             hft.round(3).to_markdown(index=False) if len(hft) else "(no 5-minute statistics)", ""]
    (out / "consumer_earnings.md").write_text("\n".join(lines) + "\n")
    LOG.info("consumer earnings: %d events", len(df))
    return {"events": len(df), "consumer_events": int(df["consumer"].sum()), "coverage": cov}
