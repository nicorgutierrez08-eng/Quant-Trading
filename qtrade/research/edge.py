"""Is there an edge after costs? Signal by signal, the honest arithmetic.

For every signal, a dollar-neutral portfolio with weights proportional to the
(optionally smoothed) z-score, gross exposure 1, decided at the close and
traded at the next open, held one day:

    gross return per day        g_t = sum_i w_it * r_i(open t+1 -> open t+2)
    turnover per day            u_t = sum_i |w_it - w_i,t-1|
    break-even cost             c*  = sum g / sum u      (bp per dollar traded)

A signal is worth trading only if c* exceeds the one-way cost of trading it
(half-spread + slippage, from the spreads study). Smoothing the signal cuts
turnover, which raises c*, but also dilutes the edge; the table shows the
trade-off. Everything is reported for 2004-2014 and 2015-2026 separately, and
for all tradable stocks vs. only the 300 most liquid each day. A composite is
built from the first period only (signs and weights by first-period t-stat)
and judged on the second, so it is not fitted to what it is graded on.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..signals import REGISTRY, compute_signals
from ..utils import LOG, rank_ic

SPLIT = "2015-01-01"
START_1ST = "2006-01-01"     # period 1 = 2006-2014 (data from 2000 only warms up signals and models)
HALFLIVES = [0, 5, 20]
HORIZONS = [1, 5, 21]


def _weights(z: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    x = z.where(mask)
    x = x.sub(x.mean(axis=1), axis=0)
    return x.div(x.abs().sum(axis=1), axis=0).fillna(0.0)


def portfolio_stats(w: pd.DataFrame, r1: pd.DataFrame, cost: pd.DataFrame | None = None) -> pd.DataFrame:
    g = (w * r1).sum(axis=1)
    dw = w.diff().abs()
    u = dw.sum(axis=1)
    out = pd.DataFrame({"gross": g, "turnover": u})
    if cost is not None:
        out["net"] = g - (dw * cost).sum(axis=1)
    return out


def summarize(daily: pd.DataFrame) -> dict:
    res = {}
    for name, part in (("1st", daily[(daily.index >= START_1ST) & (daily.index < SPLIT)]),
                       ("2nd", daily[daily.index >= SPLIT])):
        g, u = part["gross"], part["turnover"]
        res[f"gross_ret_{name}"] = g.mean() * 252
        res[f"gross_sharpe_{name}"] = g.mean() / g.std() * np.sqrt(252) if g.std() > 0 else np.nan
        res[f"turnover_{name}"] = u.mean()
        res[f"breakeven_bp_{name}"] = g.sum() / max(u.sum(), 1e-12) * 1e4
        if "net" in part:
            n = part["net"]
            res[f"net_sharpe_{name}"] = n.mean() / n.std() * np.sqrt(252) if n.std() > 0 else np.nan
    return res


def cost_panel(ctx, half_spread_bp: dict | None = None) -> pd.DataFrame:
    """One-way cost per dollar traded for every (day, stock): half-spread by
    liquidity tier + 1 bp slippage."""
    tiers = half_spread_bp or {500e6: 1.5, 100e6: 3.0, 20e6: 6.0, 0.0: 12.0}
    adv = ctx.adv
    hs = pd.DataFrame(np.nan, index=adv.index, columns=adv.columns)
    for thr, bp in sorted(tiers.items(), key=lambda x: -x[0]):
        hs = hs.where(hs.notna() | ~(adv >= thr), bp / 1e4)
    return hs.fillna(max(tiers.values()) / 1e4) + 1e-4


class Bench:
    """Shared inputs for scoring signal panels the same way everywhere."""

    def __init__(self, md, ctx, half_spread_bp: dict | None = None):
        self.cost = cost_panel(ctx, half_spread_bp)
        o = md.open
        self.r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5)
        self.tradable = ctx.tradable
        adv = ctx.adv
        self.liquid = self.tradable & (adv.where(self.tradable).rank(axis=1, ascending=False) <= 300)
        self.fwd = {h: (o.shift(-(1 + h)) / o.shift(-1) - 1).where(self.tradable).to_numpy() for h in HORIZONS}

    def decay(self, name: str, z: pd.DataFrame) -> list[dict]:
        rows = []
        for h in HORIZONS:
            ic = pd.Series(rank_ic(z.to_numpy(), self.fwd[h]), index=z.index).dropna()
            a, b = ic[(ic.index >= START_1ST) & (ic.index < SPLIT)], ic[ic.index >= SPLIT]
            rows.append({"signal": name, "horizon": h, "ic_1st": a.mean(), "ic_2nd": b.mean(),
                         "t_1st": a.mean() / a.std() * np.sqrt(len(a) / h) if len(a) > 10 else np.nan,
                         "t_2nd": b.mean() / b.std() * np.sqrt(len(b) / h) if len(b) > 10 else np.nan})
        return rows

    def score(self, z: pd.DataFrame, halflife: float = 0, universe: str = "all",
              mask: pd.DataFrame | None = None) -> dict:
        zz = z.ewm(halflife=halflife, ignore_na=True).mean() if halflife else z
        m = self.tradable if universe == "all" else self.liquid
        if mask is not None:
            m = m & mask
        return summarize(portfolio_stats(_weights(zz, m), self.r1, self.cost))

    def table(self, sigs: dict, families: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        rows, decay = [], []
        for name, z in sigs.items():
            decay += self.decay(name, z)
            for hl in HALFLIVES:
                for uni in ("all", "top300"):
                    rows.append({"signal": name, "family": (families or {}).get(name, ""), "halflife": hl,
                                 "universe": uni, **self.score(z, hl, uni)})
            LOG.info("edge: %s done", name)
        return pd.DataFrame(rows), pd.DataFrame(decay)


def first_period_composite(sigs: dict, dec: pd.DataFrame | None = None, bench: "Bench | None" = None) -> pd.DataFrame:
    """Signals weighted by their 2004-2014 one-day IC t-stat, keeping |t| > 2 -
    chosen without looking at 2015-2026."""
    if dec is None:
        dec = pd.DataFrame([r for n, z in sigs.items() for r in bench.decay(n, z) if r["horizon"] == 1])
    first = dec[dec["horizon"] == 1].set_index("signal")["t_1st"]
    w_sig = first.where(first.abs() > 2, 0.0)
    return sum(sigs[s] * w for s, w in w_sig.items() if w != 0)


def run(md, ctx, out: Path, half_spread_bp: dict | None = None) -> dict:
    """``half_spread_bp``: measured half-spread by liquidity tier (from the
    spreads study); defaults to the cost model's quoted tiers."""
    bench = Bench(md, ctx, half_spread_bp)
    sigs = compute_signals(ctx)
    tab, dec = bench.table(sigs, {n: REGISTRY[n].family for n in sigs})

    composite = first_period_composite(sigs, dec)
    comp = pd.DataFrame([{"halflife": hl, "universe": uni, **bench.score(composite, hl, uni)}
                         for hl in HALFLIVES for uni in ("all", "top300")])
    _write(tab, dec, comp, out)
    survivors = tab[(tab["breakeven_bp_1st"] > 5) & (tab["breakeven_bp_2nd"] > 5)]
    return {"n_signals": len(sigs), "n_survivors_5bp": int(len(survivors)),
            "composite": comp.round(3).to_dict(orient="records"), "_composite": composite}


def _write(tab, dec, comp, out: Path) -> None:
    tab.to_csv(out / "edge_signals.csv", index=False)
    dec.to_csv(out / "edge_decay.csv", index=False)
    comp.to_csv(out / "edge_composite.csv", index=False)
    best = tab.sort_values("breakeven_bp_1st", ascending=False)
    survivors = tab[(tab["breakeven_bp_1st"] > 5) & (tab["breakeven_bp_2nd"] > 5)]
    lines = ["## Edge vs. cost, signal by signal", "",
             "Break-even cost = gross profit per dollar traded (bp). A one-way trade costs about "
             "half-spread + 1 bp slippage: ~2.5 bp for the most liquid names, 4-13 bp for the rest.", "",
             "### Composite (signals and weights chosen on 2004-2014 only)", "",
             comp.round(3).to_markdown(index=False), "",
             "### Top 15 signal/smoothing/universe by 2004-2014 break-even", "",
             best.head(15)[["signal", "halflife", "universe", "breakeven_bp_1st", "breakeven_bp_2nd",
                            "gross_sharpe_1st", "gross_sharpe_2nd", "net_sharpe_1st", "net_sharpe_2nd",
                            "turnover_1st"]].round(2).to_markdown(index=False), "",
             f"Signals whose break-even is above 5 bp in **both** periods: {len(survivors)}", "",
             survivors[["signal", "halflife", "universe", "breakeven_bp_1st", "breakeven_bp_2nd",
                        "net_sharpe_1st", "net_sharpe_2nd"]].round(2).to_markdown(index=False)
             if len(survivors) else "(none)", ""]
    (out / "edge.md").write_text("\n".join(lines) + "\n")
