"""What does trading actually cost? Real bid-ask spreads from Alpaca quotes.

Samples consolidated (SIP) quotes for ~140 stocks spread across the liquidity
ranks of the universe, on ~3 random days a year since 2016, in short windows
at fixed times of day. For each (stock, day, time) it records the median
quoted spread as a fraction of the midquote. Then it compares:

* the measured half-spread with the cost model's liquidity tiers (daily
  backtest: 1.5/3/6/12 bp; intraday: 1/2/4/8 bp);
* with the Corwin-Schultz high-low estimate the daily signals use;
* the official opening price with the midquote just after the open, which is
  what an opening-auction (market-on-open) order is really paying.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data.intraday import AlpacaBars
from ..data.loader import to_alpaca, to_yahoo
from ..utils import LOG

QUOTES_URL = "https://data.alpaca.markets/v2/stocks/quotes"
TIMES = ["09:30:05", "09:35:00", "10:00:00", "12:00:00", "15:30:00", "15:55:00"]
WINDOW_S = 10


def quotes_window(client: AlpacaBars, symbols: list[str], start: pd.Timestamp, seconds: int) -> dict[str, float]:
    """Median relative quoted spread per symbol in [start, start + seconds)."""
    params = {"symbols": ",".join(to_alpaca(s) for s in symbols), "start": start.isoformat(),
              "end": (start + pd.Timedelta(seconds=seconds)).isoformat(), "limit": 10000,
              "feed": "sip", "sort": "asc"}
    spreads: dict[str, list[float]] = {}
    for _ in range(20):                                    # page cap: ~200k quotes
        data = client._get(params, QUOTES_URL)
        for sym, rows in (data.get("quotes") or {}).items():
            bid = np.array([q.get("bp", 0) for q in rows], float)
            ask = np.array([q.get("ap", 0) for q in rows], float)
            ok = (bid > 0) & (ask > bid)
            if ok.any():
                mid = (bid[ok] + ask[ok]) / 2
                spreads.setdefault(to_yahoo(sym), []).extend(((ask[ok] - bid[ok]) / mid).tolist())
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return {s: float(np.median(v)) for s, v in spreads.items()}


def first_mid(client: AlpacaBars, symbols: list[str], day: pd.Timestamp) -> dict[str, float]:
    """Midquote in the first 10 seconds after the open (median)."""
    start = day.tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30)
    params = {"symbols": ",".join(to_alpaca(s) for s in symbols), "start": start.isoformat(),
              "end": (start + pd.Timedelta(seconds=10)).isoformat(), "limit": 10000, "feed": "sip"}
    mids: dict[str, list[float]] = {}
    for _ in range(20):
        data = client._get(params, QUOTES_URL)
        for sym, rows in (data.get("quotes") or {}).items():
            for q in rows:
                b, a = q.get("bp", 0), q.get("ap", 0)
                if b > 0 and a > b:
                    mids.setdefault(to_yahoo(sym), []).append((a + b) / 2)
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return {s: float(np.median(v)) for s, v in mids.items()}


def run(md, ctx, out: Path, n_symbols: int = 140, days_per_year: int = 3, seed: int = 0) -> dict:
    client = AlpacaBars(feed="sip")
    rng = np.random.default_rng(seed)
    tickers = md.tickers
    picks = sorted(set(np.linspace(0, len(tickers) - 1, n_symbols).astype(int)))
    symbols = [tickers[i] for i in picks]
    dates = md.dates[md.dates >= "2016-03-01"]
    days = []
    for y in sorted(set(dates.year)):
        dy = dates[dates.year == y]
        days += list(rng.choice(dy, min(days_per_year, len(dy)), replace=False))
    adv = ctx.adv.shift(1)                                  # as-traded $ volume known before the day
    cs = ctx.spread.shift(1)
    rows, auction = [], []
    for day in sorted(pd.DatetimeIndex(days)):
        for tm in TIMES:
            start = pd.Timestamp(f"{day.date()} {tm}").tz_localize("America/New_York")
            for i in range(0, len(symbols), 70):
                batch = symbols[i:i + 70]
                try:
                    got = quotes_window(client, batch, start, WINDOW_S)
                except Exception as exc:
                    LOG.warning("quotes %s %s failed: %s", day.date(), tm, exc)
                    continue
                for s, sp in got.items():
                    rows.append({"date": day, "time": tm, "ticker": s, "spread": sp,
                                 "adv": adv.at[day, s] if s in adv.columns else np.nan,
                                 "cs_spread": cs.at[day, s] if s in cs.columns else np.nan})
        try:
            mids = {}
            for i in range(0, len(symbols), 70):
                mids.update(first_mid(client, symbols[i:i + 70], day))
            opens = md.traded_close.loc[day] * (md.open.loc[day] / md.close.loc[day])
            for s, m in mids.items():
                if s in opens.index and np.isfinite(opens[s]):
                    auction.append({"date": day, "ticker": s, "open": opens[s], "mid_after_open": m,
                                    "gap_bp": (opens[s] / m - 1) * 1e4})
        except Exception as exc:
            LOG.warning("auction check %s failed: %s", day.date(), exc)
        LOG.info("spreads: %s done (%d rows)", day.date(), len(rows))

    # the quote-level samples are vendor market data: only summaries are written out
    # (results are published to a public branch)
    df = pd.DataFrame(rows)
    au = pd.DataFrame(auction)
    if df.empty:
        return {"error": "no quotes returned"}
    df["half_bp"] = df["spread"] / 2 * 1e4
    cfg = Config()
    df["tier"] = pd.cut(df["adv"], [-1, 20e6, 100e6, 500e6, np.inf],
                        labels=["< $20M", "$20-100M", "$100-500M", "> $500M"])
    model_daily = {"> $500M": 1.5, "$100-500M": 3.0, "$20-100M": 6.0, "< $20M": 12.0}
    itiers = cfg.intraday.spread_tiers
    def intraday_model(a):
        for t, b in sorted(itiers, key=lambda x: -x[0]):
            if a >= t:
                return b
        return itiers[-1][1]
    df["model_intraday_bp"] = df["adv"].map(lambda a: intraday_model(a) if np.isfinite(a) else np.nan)
    by_tier = df[df["time"].isin(["10:00:00", "12:00:00", "15:30:00"])].groupby("tier", observed=True).agg(
        obs=("half_bp", "size"), median_half_bp=("half_bp", "median"), mean_half_bp=("half_bp", "mean"),
        p90_half_bp=("half_bp", lambda x: x.quantile(0.9)), model_intraday_bp=("model_intraday_bp", "median"),
        corwin_schultz_half_bp=("cs_spread", lambda x: x.median() / 2 * 1e4))
    by_tier["model_daily_bp"] = [model_daily[t] for t in by_tier.index]
    by_time = df.groupby(["time", "tier"], observed=True)["half_bp"].median().unstack()
    by_year = df[df["time"] == "12:00:00"].groupby([df["date"].dt.year, "tier"], observed=True)["half_bp"].median().unstack()
    cs_corr = df[["spread", "cs_spread"]].corr(method="spearman").iloc[0, 1]
    by_tier.to_csv(out / "spreads_by_tier.csv")
    by_time.to_csv(out / "spreads_by_time.csv")
    by_year.to_csv(out / "spreads_by_year.csv")
    summary = {"observations": len(df), "symbols": int(df["ticker"].nunique()), "days": int(df["date"].nunique()),
               "corwin_schultz_rank_corr_with_quoted": float(cs_corr)}
    if len(au):
        summary |= {"auction_abs_gap_median_bp": float(au["gap_bp"].abs().median()),
                    "auction_gap_mean_bp": float(au["gap_bp"].mean())}
    lines = ["## Bid-ask spreads (Alpaca SIP quotes)", "",
             f"{summary['observations']} measurements: {summary['symbols']} stocks x {summary['days']} days x "
             f"{len(TIMES)} times of day, {WINDOW_S}-second windows.", "",
             "Half-spread in bp, 10:00-15:30 (what an intraday market order pays):", "",
             "| liquidity (21-day median $ volume) | obs | median | mean | 90th pct | model: daily | model: intraday | Corwin-Schultz |",
             "|---|---|---|---|---|---|---|---|"]
    for t, r in by_tier.iterrows():
        lines.append(f"| {t} | {r.obs} | {r.median_half_bp:.2f} | {r.mean_half_bp:.2f} | {r.p90_half_bp:.2f} | "
                     f"{r.model_daily_bp:.1f} | {r.model_intraday_bp:.1f} | {r.corwin_schultz_half_bp:.1f} |")
    lines += ["", "Median half-spread (bp) by time of day:", "", by_time.round(2).to_markdown(), "",
              f"Corwin-Schultz vs quoted spread, rank correlation: {cs_corr:.2f}."]
    if len(au):
        lines += ["", f"Opening auction: official open vs midquote 0-10 s after the open: median |gap| "
                  f"{summary['auction_abs_gap_median_bp']:.1f} bp (mean signed {summary['auction_gap_mean_bp']:+.1f} bp)."]
    (out / "spreads.md").write_text("\n".join(lines) + "\n")
    return summary
