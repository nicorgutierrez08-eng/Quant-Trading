"""High-frequency (minute-level) trading on foreign stock exchanges: is there anything to trade?

No free source has tick-by-tick quotes for Tokyo, Hong Kong, Seoul, Taipei, Sydney, Mumbai,
London, Frankfurt or Paris, so this works on Yahoo's 5-minute bars (the last 60 days): in each
market, at the close of every bar, rank 30-40 large caps by their last ``k`` bars' return,
buy one end and sell the other at the next bar's open, hold ``h`` bars, and repeat (never held
overnight; the opening auction bar is skipped). Two families: short-term **reversal** (buy the
losers) and **momentum** (buy the winners).

There are no quotes, so the spread can't be measured: each trade pays an estimated half-spread
for the market's large caps on the way in and out (``SPREAD_BP``; Hong Kong and Taiwan have
coarse tick sizes). The sheet's own rule is 0 bp *fees*; the spread is not a fee - the US HFT paid
it through the quotes - so it is charged here too, with the 0 bp result shown alongside.

The first half of the days picks each market's best variant, the second half tests it; only a
pick that makes money on the test days passes (the same gate as the US HFT).
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, setup_logging
from .foreign import MARKETS

# estimated quoted spread (bp) of the markets' large caps, round trip = one full spread
SPREAD_BP = {"Japan": 4.0, "Hong Kong": 8.0, "Korea": 6.0, "Taiwan": 8.0, "Australia": 4.0, "India": 3.0,
             "UK": 4.0, "Germany": 3.0, "France": 3.0}
LOOKBACK = [1, 3, 6, 12]          # bars of past return in the signal
HOLD = [1, 3, 6, 12]              # bars held


def bars(tickers: list[str], period: str = "60d", interval: str = "5m") -> tuple[pd.DataFrame, pd.DataFrame]:
    import yfinance as yf

    raw = yf.download(tickers, period=period, interval=interval, group_by="ticker", auto_adjust=False,
                      progress=False, threads=True)
    have = [t for t in tickers if raw is not None and not raw.empty and t in raw.columns.get_level_values(0)]
    o = pd.DataFrame({t: raw[t]["Open"] for t in have})
    c = pd.DataFrame({t: raw[t]["Close"] for t in have})
    ok = c.notna().sum(axis=1) >= max(10, c.shape[1] // 2)
    return o[ok], c[ok]


def simulate(o: pd.DataFrame, c: pd.DataFrame, k: int, h: int, sign: float, spread_bp: float,
             frac: float = 0.2) -> pd.DataFrame:
    """Per-trade-window P&L (gross and after the spread) of the cross-sectional book, one row per window."""
    O, C = o.to_numpy(float), c.to_numpy(float)
    dates = np.array(o.index.date)
    rows = []
    starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
    ends = np.r_[starts[1:], len(dates)]
    for s0, e0 in zip(starts, ends):
        n = e0 - s0
        t = max(k, 1)                                   # first decision once k bars (after the opening bar) exist
        while t + 1 + h < n:
            i = s0 + t
            base = O[i - k + 1]
            past = sign * np.log(C[i] / base)
            r = np.log(O[i + 1 + h] / O[i + 1])
            ok = np.isfinite(past) & np.isfinite(r) & np.isfinite(O[i - k + 1:i + 1]).all(axis=0)
            m = int(ok.sum())
            if m >= 10:
                q = max(int(round(m * frac)), 2)
                ps, rs = past[ok], r[ok]
                order = np.argsort(ps, kind="stable")
                g = 0.5 * rs[order[-q:]].mean() - 0.5 * rs[order[:q]].mean()
                names = np.asarray(o.columns)[ok]
                rows.append((dates[i], o.index[i + 1], o.index[i + 1 + h], g, g - spread_bp / 1e4,   # in and out: one spread
                             " ".join(names[order[-q:]]), " ".join(names[order[:q]])))
            t += h
    return pd.DataFrame(rows, columns=["day", "time", "exit_time", "gross", "net", "longs", "shorts"])


def study(markets: dict[str, list[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid, picks = [], []
    for mkt, tickers in markets.items():
        try:
            o, c = bars(tickers)
        except Exception as exc:
            LOG.warning("%s: no 5-minute bars (%s)", mkt, exc)
            continue
        if o.shape[1] < 10 or len(o) < 200:
            continue
        days = sorted(set(o.index.date))
        half = set(days[: len(days) // 2])
        spread = SPREAD_BP.get(mkt, 5.0)
        res = []
        for (name, sign), k, h in itertools.product([("reversal", -1.0), ("momentum", 1.0)], LOOKBACK, HOLD):
            p = simulate(o, c, k, h, sign, spread)
            if p.empty:
                continue
            p["part"] = np.where(p["day"].isin(half), "train", "test")
            row = {"market": mkt, "strategy": name, "lookback_bars": k, "hold_bars": h, "stocks": o.shape[1],
                   "days": len(days), "spread_bp": spread}
            for part in ("train", "test"):
                q = p[p.part == part]
                daily = q.groupby("day")[["gross", "net"]].sum()
                row.update({f"trades_{part}": len(q), f"gross_bp_per_trade_{part}": q["gross"].mean() * 1e4,
                            f"net_bp_per_trade_{part}": q["net"].mean() * 1e4,
                            f"net_bp_per_day_{part}": daily["net"].mean() * 1e4,
                            f"net_days_positive_{part}": float((daily["net"] > 0).mean())})
            res.append(row)
        r = pd.DataFrame(res)
        grid.append(r)
        best = r.sort_values("net_bp_per_day_train", ascending=False).iloc[0]
        passed = bool(best["net_bp_per_day_test"] > 0 and best["net_days_positive_test"] >= 0.5)
        gross_best = r.sort_values("gross_bp_per_trade_train", ascending=False).iloc[0]
        picks.append({"market": mkt, "pick": f"{best['strategy']} k={best['lookback_bars']} h={best['hold_bars']}",
                      "net_bp_per_day_train": round(best["net_bp_per_day_train"], 2),
                      "net_bp_per_day_test": round(best["net_bp_per_day_test"], 2),
                      "test_days_positive": round(best["net_days_positive_test"], 2), "passes": passed,
                      "best_at_0bp": f"{gross_best['strategy']} k={gross_best['lookback_bars']} h={gross_best['hold_bars']}",
                      "gross_bp_per_trade_test_at_0bp": round(gross_best["gross_bp_per_trade_test"], 2),
                      "spread_bp": spread})
    return (pd.concat(grid, ignore_index=True) if grid else pd.DataFrame()), pd.DataFrame(picks)


def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    grid, picks = study(MARKETS)
    grid.round(3).to_csv(out / "foreign_hft_grid.csv", index=False)
    picks.to_csv(out / "foreign_hft_picks.csv", index=False)
    (out / "foreign_hft_rules.json").write_text(json.dumps(picks.to_dict(orient="records"), indent=1, default=str))
    lines = ["## Foreign exchanges, minute level: cross-sectional reversal / momentum on 5-minute bars", "",
             "Yahoo 5-minute bars, last ~60 days, 30-40 large caps per market. At each bar close: rank by the last "
             "k bars, long one fifth / short the other at the next bar's open, hold h bars, never overnight. Each "
             "trade pays one estimated spread (in and out). First half of the days picks, second half tests.", "",
             "### Picks", "", picks.to_markdown(index=False) if len(picks) else "(no data)", "",
             "### Every variant", "", grid.round(2).to_markdown(index=False) if len(grid) else "", ""]
    (out / "foreign_hft.md").write_text("\n".join(lines) + "\n")
    return {"picks": picks.to_dict(orient="records")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/foreign_hft")
    args = ap.parse_args(argv)
    setup_logging()
    print(json.dumps(run(Path(args.out)), indent=1, default=str))


if __name__ == "__main__":
    main()
