"""Intraday strategies on daily slices of the trading day.

The day is cut into overnight (previous close -> open), the first half hour
(open -> 10:00), the middle (10:00 -> 15:30) and the last half hour
(15:30 -> close). The half-hour returns come from 5-minute bars (built by
``intraday_stats``, Alpaca data since 2016); the middle is what is left of the
open-to-close return. Each strategy decides with what is known at its entry
time and holds one slice:

  market_intraday_momentum  the market's overnight + first-half-hour return
                            predicts its last half hour (Gao-Han-Li-Zhou):
                            long/short the equal-weight market 15:30 -> close
  opening_drive             stocks ranked on their first half hour, held
                            10:00 -> close (positive = continuation)
  late_momentum             stocks ranked on overnight + first half hour,
                            held over the last half hour
  gap_reversal_open         ranked on the overnight gap, short gappers-up and
                            long gappers-down from the open to the close
  gap_reversal_10am         the same, entered at 10:00 once the open's wide
                            spreads have settled
  overnight_persistence     ranked on the past month's overnight returns, held
                            overnight (Lou-Polk-Skouras "tug of war")
  intraday_persistence      ranked on the past month's open-to-close returns,
                            held open -> close
  last30_next_overnight     ranked on the last half hour, held to the next open

Books are long the top fifth and short the bottom fifth, equal-weighted, fully
rebuilt every day. Costs: the tiered half-spread + 1 bp per side, tripled for
trades at the open, where measured spreads are 5-8x wider in the first minutes.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

SPLIT = "2021-01-01"
OPEN_COST_MULT = 3.0


def _ls(sig: pd.DataFrame, ok: pd.DataFrame) -> pd.DataFrame:
    rk = sig.where(ok).rank(axis=1, pct=True)
    w = (rk > 0.8).astype(float) - (rk <= 0.2).astype(float)
    return w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def _stats(gross: pd.Series, net: pd.Series, turnover: pd.Series) -> dict:
    out = {}
    for tag, m in (("1st", gross.index < SPLIT), ("2nd", gross.index >= SPLIT)):
        g, n, t = gross[m], net[m], turnover[m]
        live = t > 0
        g, n, t = g[live], n[live], t[live]
        out[f"days_{tag}"] = int(live.sum())
        out[f"gross_bp_day_{tag}"] = g.mean() * 1e4 if len(g) else np.nan
        out[f"gross_sharpe_{tag}"] = g.mean() / g.std() * np.sqrt(252) if g.std() > 0 else np.nan
        out[f"net_sharpe_{tag}"] = n.mean() / n.std() * np.sqrt(252) if n.std() > 0 else np.nan
        out[f"breakeven_bp_{tag}"] = g.mean() / t.mean() * 1e4 if t.mean() > 0 else np.nan
    return out


def slices(md, ctx, st: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Log returns of each slice of the day, aligned to the price panel."""
    f30 = st["first30"].reindex(index=md.dates, columns=md.tickers)
    l30 = st["last30"].reindex(index=md.dates, columns=md.tickers)
    on = np.log1p(ctx.overnight.clip(-0.5, 1.0))
    oc = np.log1p(ctx.intraday.clip(-0.5, 1.0))
    have = f30.notna() & l30.notna() & oc.notna()
    mid = (oc - f30 - l30).where(have)
    return {"overnight": on, "first30": f30.where(have), "mid": mid, "last30": l30.where(have), "oc": oc.where(have)}


def strategies(md, ctx, st: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    from .edge import cost_panel

    s = slices(md, ctx, st)
    ok = ctx.tradable & s["first30"].notna()
    cost = cost_panel(ctx).shift(1)                     # tier known from yesterday's volume
    rows, series = [], {}

    def book(name, sig, hold, entry_mult=1.0, exit_mult=1.0, ok_=ok):
        w = _ls(sig, ok_)
        ret = np.expm1(hold).fillna(0)
        gross = (w * ret).sum(axis=1)
        turn = w.abs().sum(axis=1)                       # opened and closed the same day
        c = (w.abs() * cost * (entry_mult + exit_mult)).sum(axis=1)
        net = gross - c
        series[name] = net
        rows.append({"strategy": name, **_stats(gross, net, 2 * turn)})

    # market timing over the last half hour
    mkt_sig = (s["overnight"] + s["first30"]).where(ok).mean(axis=1)
    mkt_l30 = np.expm1(s["last30"]).where(ok).mean(axis=1)
    pos = np.sign(mkt_sig).where(ok.sum(axis=1) > 50, 0).fillna(0)
    gross = pos * mkt_l30.fillna(0)
    net = gross - pos.abs() * 2e-4                       # SPY: ~1 bp per side
    series["market_intraday_momentum"] = net
    rows.append({"strategy": "market_intraday_momentum (equal-weight market, 15:30 -> close)",
                 **_stats(gross, net, 2 * pos.abs())})

    book("opening_drive (first 30 min -> rest of day)", s["first30"], s["mid"] + s["last30"])
    book("late_momentum (overnight + first 30 -> last 30)", s["overnight"] + s["first30"], s["last30"])
    book("gap_reversal_open (gap -> open to close, short gappers)", -s["overnight"], s["oc"],
         entry_mult=OPEN_COST_MULT)
    book("gap_reversal_10am (gap -> 10:00 to close)", -s["overnight"], s["mid"] + s["last30"])
    on21 = s["overnight"].rolling(21, min_periods=15).sum()
    oc21 = s["oc"].rolling(21, min_periods=15).sum()
    nxt_on = s["overnight"].shift(-1)                    # tonight: today's close -> tomorrow's open
    ok_close = ctx.tradable & nxt_on.notna()
    book("overnight_persistence (past month's overnight -> tonight)", on21, nxt_on,
         entry_mult=1.0, exit_mult=OPEN_COST_MULT, ok_=ok_close)
    # intraday persistence: ranked on yesterday's 21-day open-to-close, held open -> close today
    book("intraday_persistence (past month's open-to-close -> today's)", oc21.shift(1), s["oc"],
         entry_mult=OPEN_COST_MULT)
    book("last30_next_overnight (last 30 min -> tonight)", s["last30"], nxt_on,
         entry_mult=1.0, exit_mult=OPEN_COST_MULT, ok_=ok_close & s["last30"].notna())
    tab = pd.DataFrame(rows)
    return tab, pd.DataFrame(series)


def run(md, ctx, out: Path, cfg) -> dict:
    from .intraday_stats import load

    st = load(cfg.data.cache_dir)
    if st is None:
        (out / "intraday.md").write_text("## Intraday strategies\n\n(no 5-minute statistics available)\n")
        return {"error": "no intraday stats"}
    tab, R = strategies(md, ctx, st)
    tab.to_csv(out / "intraday_strategies.csv", index=False)
    R.to_csv(out / "intraday_strategy_returns.csv")
    cols = ["strategy", "gross_bp_day_1st", "gross_bp_day_2nd", "breakeven_bp_1st", "breakeven_bp_2nd",
            "gross_sharpe_1st", "gross_sharpe_2nd", "net_sharpe_1st", "net_sharpe_2nd", "days_1st", "days_2nd"]
    lines = ["## Intraday strategies (5-minute data, 2016-2026)", "",
             f"Periods: 2016-2020 (1st) and {SPLIT[:4]}-2026 (2nd). Long top / short bottom fifth, rebuilt "
             "daily. gross_bp_day = average daily return before costs; breakeven = gross return per unit "
             "traded, to compare with the one-way cost (about 2.5-4 bp in liquid names, 3x at the open).", "",
             tab[cols].round(2).to_markdown(index=False), ""]
    (out / "intraday.md").write_text("\n".join(lines) + "\n")
    LOG.info("intraday strategies: %d", len(tab))
    return {"strategies": tab[["strategy", "net_sharpe_1st", "net_sharpe_2nd", "breakeven_bp_2nd"]]
            .round(2).to_dict(orient="records")}
