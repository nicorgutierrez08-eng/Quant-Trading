"""When is the reversal edge biggest - and does trading only then pay?

Every condition is known at the close when the trade is decided:

  stressed    the HMM's probability of its most volatile regime is in the top
              third of its own trailing 3-year range (market-wide)
  dispersed   cross-sectional dispersion of yesterday's returns in its top third
              (market-wide: many stocks moving apart = more to revert)
  low_volume  the stock's last-5-day volume is in the bottom third vs. its
              63-day average (moves on light volume are more often noise)
  no_news     no article about the stock in the last 5 days (if news data exists)

For each signal and condition: the IC inside vs. outside the condition, and a
portfolio that only trades inside it (gated), scored on break-even cost and
net Sharpe in 2004-2014 and 2015-2026. A market-wide gate holds no positions
on other days; a stock-level gate only holds stocks that qualify.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..models.regime import walk_forward_regimes
from ..utils import LOG, rank_ic
from .edge import SPLIT, Bench


def _trailing_tercile(x: pd.Series, top: bool = True, window: int = 756) -> pd.Series:
    q = x.rolling(window, min_periods=252).quantile(2 / 3 if top else 1 / 3).shift(1)
    return (x > q) if top else (x < q)


def market_conditions(ctx, cfg) -> dict[str, pd.Series]:
    rc = cfg.regime
    probs, fits = walk_forward_regimes(ctx.market_state, rc.n_states, rc.refit_every, rc.min_history, rc.n_init,
                                       rc.max_iter, cfg.model.seed, temper=rc.temper, align=rc.align)
    # the most volatile regime, judged by each day's own model would be ideal; the last fit's
    # ordering is used here, which is fine with aligned labels
    last = fits[-1][1]
    hi = int(np.argmax([np.trace(c) for c in last.covars_]))
    p_stress = probs.iloc[:, hi]
    disp = ctx.ret.clip(-0.5, 0.5).std(axis=1)
    return {"stressed": _trailing_tercile(p_stress), "dispersed": _trailing_tercile(disp),
            "_p_stress": p_stress}


def run(md, ctx, out: Path, cfg, sigs: dict[str, pd.DataFrame], news_counts: pd.DataFrame | None = None) -> dict:
    bench = Bench(md, ctx)
    mk = market_conditions(ctx, cfg)
    vol_ratio = md.volume.rolling(5).mean() / md.volume.rolling(63).mean()
    low_vol = vol_ratio.le(vol_ratio.where(ctx.tradable).quantile(1 / 3, axis=1), axis=0)
    conds = {"stressed": mk["stressed"], "dispersed": mk["dispersed"], "low_volume": low_vol}
    if news_counts is not None:
        conds["no_news"] = news_counts.reindex_like(low_vol).fillna(0).rolling(5).sum() == 0
    rows = []
    for sname, z in sigs.items():
        zn = z.to_numpy()
        for cname, c in conds.items():
            cm = (c.reindex(z.index).fillna(False).to_numpy()[:, None] if isinstance(c, pd.Series)
                  else c.reindex_like(z).fillna(False).to_numpy())
            cm = np.broadcast_to(cm, zn.shape)
            fwd = bench.fwd[5]
            ic_in = pd.Series(rank_ic(np.where(cm, zn, np.nan), fwd), index=z.index)
            ic_out = pd.Series(rank_ic(np.where(~cm, zn, np.nan), fwd), index=z.index)
            mask = pd.DataFrame(cm, index=z.index, columns=z.columns)
            row = {"signal": sname, "condition": cname, "share_in": float(cm.mean())}
            for per, sel in (("1st", (z.index >= "2006-01-01") & (z.index < SPLIT)), ("2nd", z.index >= SPLIT)):
                row[f"ic5_in_{per}"] = ic_in[sel].mean()
                row[f"ic5_out_{per}"] = ic_out[sel].mean()
            for hl in (0, 5):
                st = bench.score(z, hl, "all", mask)
                row |= {f"hl{hl}_{k}": v for k, v in st.items()
                        if k.startswith(("breakeven", "net_sharpe", "gross_sharpe"))}
            rows.append(row)
        base = {"signal": sname, "condition": "always", "share_in": 1.0}
        for hl in (0, 5):
            st = bench.score(z, hl, "all")
            base |= {f"hl{hl}_{k}": v for k, v in st.items() if k.startswith(("breakeven", "net_sharpe", "gross_sharpe"))}
        rows.append(base)
        LOG.info("conditional: %s done", sname)
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "conditional.csv", index=False)
    cols = ["signal", "condition", "share_in", "ic5_in_1st", "ic5_out_1st", "ic5_in_2nd", "ic5_out_2nd",
            "hl0_breakeven_bp_1st", "hl0_breakeven_bp_2nd", "hl5_breakeven_bp_1st", "hl5_breakeven_bp_2nd",
            "hl5_net_sharpe_1st", "hl5_net_sharpe_2nd"]
    lines = ["## Trading only when the edge is biggest", "",
             "IC over the next 5 days inside vs. outside each condition, and a portfolio that only trades "
             "inside it (hl = smoothing half-life in days). Break-even in bp per dollar traded.", "",
             tab[[c for c in cols if c in tab]].round(4).to_markdown(index=False), ""]
    (out / "conditional.md").write_text("\n".join(lines) + "\n")
    return {"rows": len(tab)}
