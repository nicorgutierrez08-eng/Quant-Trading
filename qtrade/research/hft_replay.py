"""Replay the shadow HFT on recorded IEX quotes and trades, for many rule variants at once.

``python -m qtrade.research.hft_replay --days 10 --out reports/hft_replay`` downloads Alpaca's
free IEX quotes and trades for the shadow trader's symbols over the last ``days`` sessions
(the core names plus a fixed sample of 50 of the top 1,000; three 40-minute windows a day:
10:00, 12:30 and 14:30 New York), replays them in time order
through ``qtrade.intraday.hft_shadow.ShadowHFT`` exactly as the live loop does (quotes and
trades as they arrive, a clock tick every second, the same latency and fill rules) and records
every simulated trade.

Each variant of the rules runs on every day. The first half of the days picks, per strategy,
the variant with the best net P&L; the second half tests it. ``imbalance_flip`` is Nico's
regime flip brought to the order book: follow the imbalance when yesterday's VIX close is
at or below 20, fade it above.

Outputs (aggregates only, no prices): ``hft_replay.md``, ``hft_replay_variants.csv`` and
``hft_rules.json``, the chosen rules per strategy, with ``enabled`` false for any strategy
whose pick lost money on the test days.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
from dataclasses import asdict, replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from ..intraday import hft_shadow as S
from ..utils import LOG, setup_logging

NY = "America/New_York"
WINDOWS = ["10:00", "12:30", "14:30"]
WINDOW_MIN = 40
GRID = {"taker_target": [0.0, 0.5, 1.0], "exit_timeout_s": [30.0, 120.0, 600.0], "stop_bp": [None, 10.0],
        "mm_min_ticks": [1, 3]}
SAMPLE = 50                      # the live book trades the top 1,000; the replay uses the core names + 50 of the rest
MIN_TRAIN_TRADES = 30


def variants() -> list[S.Rules]:
    keys = list(GRID)
    return [replace(S.Rules(strategies=tuple(S.ALL_STRATEGIES)), **dict(zip(keys, combo)))
            for combo in itertools.product(*GRID.values())]


def label(r: S.Rules) -> str:
    return f"tgt{r.taker_target}_to{int(r.exit_timeout_s)}_stop{r.stop_bp}_ticks{r.mm_min_ticks}"


def replay_symbols(seed: int = 0) -> list[str]:
    """The core symbols plus a fixed random sample of the rest of the top 1,000."""
    wide = S.universe_symbols(1000)
    rest = [t for t in wide if t not in S.SYMBOLS]
    rng = np.random.default_rng(seed)
    pick = list(rng.choice(rest, size=min(SAMPLE, len(rest)), replace=False)) if rest else []
    return list(S.SYMBOLS) + sorted(pick)


# --- data ---------------------------------------------------------------------------------------
def _fetch(client, url: str, key: str, symbols: list[str], start: pd.Timestamp, end: pd.Timestamp) -> dict:
    params = {"symbols": ",".join(symbols), "start": start.isoformat(), "end": end.isoformat(),
              "limit": 10000, "feed": "iex", "sort": "asc"}
    out: dict[str, list] = {}
    for _ in range(500):
        data = client._get(params, url)
        for sym, rows in (data.get(key) or {}).items():
            out.setdefault(sym, []).extend(rows)
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return out


def window_events(client, day: pd.Timestamp, hhmm: str, symbols: list[str], cache: Path) -> pd.DataFrame:
    """All quotes and trades of one window, one row per event, sorted (cached as parquet)."""
    import hashlib

    tag = hashlib.md5(",".join(symbols).encode()).hexdigest()[:8]
    path = cache / f"{day:%Y%m%d}_{hhmm.replace(':', '')}_{tag}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    start = pd.Timestamp(f"{day:%Y-%m-%d} {hhmm}", tz=NY).tz_convert("UTC")
    end = start + pd.Timedelta(minutes=WINDOW_MIN)
    rows = []
    for sym, qs in _fetch(client, S.QUOTES_URL, "quotes", [s.replace("-", ".") for s in symbols], start, end).items():
        rows += [(q["t"], 0, sym, q.get("bp", 0), q.get("bs", 0), q.get("ap", 0), q.get("as", 0)) for q in qs]
    for sym, ts in _fetch(client, S.TRADES_URL, "trades", [s.replace("-", ".") for s in symbols], start, end).items():
        rows += [(r["t"], 1, sym, r.get("p", 0), r.get("s", 0), np.nan, np.nan) for r in ts]
    ev = pd.DataFrame(rows, columns=["t", "kind", "symbol", "a", "b", "c", "d"])
    ev["symbol"] = ev["symbol"].str.replace(".", "-", regex=False)
    if len(ev):
        ev["t"] = pd.to_datetime(ev["t"], utc=True, format="ISO8601")
        ev = ev.sort_values(["t", "kind"], kind="stable").reset_index(drop=True)
    cache.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(path)
    return ev


def recent_days(n: int, today: pd.Timestamp | None = None) -> list[pd.Timestamp]:
    today = (today or pd.Timestamp.now(tz=NY)).normalize().tz_localize(None)
    return list(pd.bdate_range(end=today - pd.Timedelta(days=1), periods=n + 4))


def vix_closes(days: list[pd.Timestamp]) -> dict[pd.Timestamp, float]:
    """Previous session's VIX close for each day (Nico's rule used a one-day lag)."""
    import yfinance as yf

    v = yf.download("^VIX", start=(days[0] - pd.Timedelta(days=10)).strftime("%Y-%m-%d"), progress=False,
                    auto_adjust=False)["Close"].squeeze().dropna()
    v.index = pd.to_datetime(v.index).tz_localize(None)
    return {d: float(v[v.index < d].iloc[-1]) for d in days if (v.index < d).any()}


# --- replay -------------------------------------------------------------------------------------
_EVENTS: dict = {}


def replay(ev: pd.DataFrame, rules: S.Rules, vix: float | None, symbols: list[str]) -> pd.DataFrame:
    """Run one window through a fresh simulator; returns its closed trades."""
    h = S.ShadowHFT(symbols, seed=1, rules=rules, vix=vix)
    if ev.empty:
        return h.take_closed()
    ns = ev["t"].astype("int64").to_numpy()
    tick = (ns[0] // 1_000_000_000 + 1) * 1_000_000_000
    kinds, syms = ev["kind"].to_numpy(), ev["symbol"].to_numpy()
    a, b, c, d = (ev[k].to_numpy() for k in "abcd")
    out = []
    for i in range(len(ev)):
        while ns[i] >= tick:                           # the live loop ticks about once a second
            h.step(pd.Timestamp(tick, tz="UTC"))
            tick += 1_000_000_000
        t = pd.Timestamp(int(ns[i]), tz="UTC")
        if kinds[i] == 0:
            h.on_quote(syms[i], t, a[i], b[i], c[i], d[i])
        else:
            h.on_trade(syms[i], t, a[i], b[i])
        if len(h.closed) > 500:
            out.append(h.take_closed())
    end = pd.Timestamp(int(ns[-1]), tz="UTC")
    for k in range(1, int(max(r for r in [rules.exit_timeout_s, rules.mm_wait_s])) + 60):
        h.step(end + pd.Timedelta(seconds=k))          # let the last positions run out on the final book
    out.append(h.take_closed())
    return pd.concat(out, ignore_index=True)


def _job(args):
    vi, rules, key = args
    ev, vix, symbols = _EVENTS[key]
    t = replay(ev, rules, vix, symbols)
    t["variant"], t["day"] = vi, key[0]
    return t


def select(trades: pd.DataFrame, rules: list[S.Rules], days: list) -> tuple[pd.DataFrame, dict]:
    half = len(days) // 2
    train, test = set(days[:half]), set(days[half:])
    trades = trades.assign(part=np.where(trades["day"].isin(train), "train", "test"))
    g = trades.groupby(["strategy", "variant", "part"]).agg(n=("pnl_usd", "size"), pnl=("pnl_usd", "sum"),
                                                              bp=("pnl_bp", "mean"), mid_bp=("pnl_mid_bp", "mean"))
    tab = g.unstack("part")
    tab.columns = [f"{a}_{b}" for a, b in tab.columns]
    tab = tab.reset_index()
    daily = trades.groupby(["strategy", "variant", "day"])["pnl_usd"].sum()
    chosen = {}
    for strat, gs in tab.groupby("strategy"):
        gs = gs[gs.get("n_train", 0) >= MIN_TRAIN_TRADES]
        if gs.empty:
            chosen[strat] = {"enabled": False, "reason": "too few trades"}
            continue
        best = gs.sort_values("pnl_train", ascending=False).iloc[0]
        v = int(best["variant"])
        d = daily.loc[strat, v]
        test_days = d[d.index.isin(test)]
        ok = bool(best.get("pnl_test", np.nan) > 0 and (test_days > 0).mean() >= 0.5)
        chosen[strat] = {"enabled": ok, "variant": label(rules[v]), "rules": asdict(rules[v]),
                         "train_pnl": round(float(best["pnl_train"]), 2), "test_pnl": round(float(best.get("pnl_test", 0)), 2),
                         "test_trades": int(best.get("n_test", 0) or 0), "test_bp": round(float(best.get("bp_test", 0)), 3),
                         "test_days_positive": f"{int((test_days > 0).sum())}/{len(test_days)}"}
    tab["variant"] = tab["variant"].map(lambda v: label(rules[int(v)]))
    return tab, chosen


def run(days_n: int, out: Path, cache: Path, symbols: list[str] | None = None, procs: int | None = None) -> dict:
    from ..data.intraday import AlpacaBars

    symbols = symbols or replay_symbols()
    client = AlpacaBars(feed="iex")
    days, got = [], []
    for day in reversed(recent_days(days_n)):          # most recent first, until enough days have data
        evs = [window_events(client, day, w, symbols, cache) for w in WINDOWS]
        if sum(len(e) for e in evs) > 1000:
            days.append(day)
            got.append(evs)
        if len(days) == days_n:
            break
    days, got = days[::-1], got[::-1]
    vix = vix_closes(days)
    LOG.info("replay: %d days, %s events, VIX %s", len(days), f"{sum(len(e) for g in got for e in g):,}",
             {f"{d:%m-%d}": round(v, 1) for d, v in vix.items()})
    for day, evs in zip(days, got):
        for w, e in zip(WINDOWS, evs):
            _EVENTS[(day, w)] = (e, vix.get(day), symbols)
    rules = variants()
    jobs = [(vi, r, key) for vi, r in enumerate(rules) for key in _EVENTS]
    with Pool(procs or os.cpu_count()) as pool:
        parts = pool.map(_job, jobs, chunksize=1)
    trades = pd.concat(parts, ignore_index=True)
    tab, chosen = select(trades, rules, days)
    out.mkdir(parents=True, exist_ok=True)
    tab.round(3).to_csv(out / "hft_replay_variants.csv", index=False)
    (out / "hft_rules.json").write_text(json.dumps(chosen, indent=1, default=str))
    lines = ["## Shadow HFT replay: rule variants on recorded IEX data", "",
             f"{len(days)} days ({days[0]:%Y-%m-%d} to {days[-1]:%Y-%m-%d}), windows {', '.join(WINDOWS)} "
             f"({WINDOW_MIN} min each), {len(rules)} variants, {len(symbols)} symbols. Train = first "
             f"{len(days) // 2} days, test = the rest. Position size = 1/50 of the strategy's equity.", "",
             "VIX (previous close): " + ", ".join(f"{d:%m-%d} {v:.1f}" for d, v in vix.items()), "",
             "### Chosen per strategy (best on train, judged on test)", "",
             pd.DataFrame([{"strategy": k, **{x: y for x, y in v.items() if x != "rules"}}
                           for k, v in chosen.items()]).to_markdown(index=False), ""]
    for strat, gs in tab.groupby("strategy"):
        top = gs.sort_values("pnl_train", ascending=False).head(8)
        lines += [f"### {strat}: top variants on train", "", top.drop(columns="strategy").round(3).to_markdown(index=False), ""]
    (out / "hft_replay.md").write_text("\n".join(lines) + "\n")
    return chosen


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--out", default="reports/hft_replay")
    ap.add_argument("--cache", default="data/hft_replay")
    ap.add_argument("--procs", type=int, default=None)
    args = ap.parse_args(argv)
    setup_logging()
    print(json.dumps(run(args.days, Path(args.out), Path(args.cache), procs=args.procs), indent=1, default=str))


if __name__ == "__main__":
    main()
