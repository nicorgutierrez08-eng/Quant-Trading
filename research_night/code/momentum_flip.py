"""The momentum flip: hold the momentum book, hold it short when the VIX is above 20.

The end point of the overnight regime work (docs/night_lab_log.md). Every
regime model tried - 88 HMM variants, vol terciles, VIX terciles, a learned
reversal/momentum switch - was beaten by this one-threshold rule, which fits
nothing: in calm markets momentum continues, once the VIX is above 20 the
momentum book unwinds and the losers rebound.

Reproduces the robustness table (threshold, universe, rebalance, delay, costs,
single signals) and the beta-hedged line, net of measured costs.

    python -m qtrade.research.momentum_flip --lab data/lab --out reports/momentum_flip
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, setup_logging
from .edge import cost_panel, portfolio_stats
from .switch_lab import MOM, composite, monthly_weights

PERIODS = (("2006_14", "2006", "2014"), ("2015_20", "2015", "2020"), ("2021_26", "2021", "2026"), ("2015_26", "2015", "2026"))


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 20 and x.std() > 0 else np.nan


def _dd(x: pd.Series) -> float:
    eq = (1 + x.fillna(0)).cumprod()
    return float((eq / eq.cummax() - 1).min())


def flip_returns(md, ctx, X, names, vix: pd.Series, mask, threshold: float = 20.0, rebalance_days: int = 21,
                 delay: int = 0, members: list[str] | None = None, cost_mult: float = 1.0) -> pd.DataFrame:
    """Daily gross/net/turnover of the flipped momentum book (unit gross)."""
    dates = md.dates
    reb = np.zeros(len(dates), bool)
    reb[::rebalance_days] = True
    z = composite(X, names, members or MOM, dates, md.tickers, mask)
    w = monthly_weights(z, mask, reb)
    sign = pd.Series(np.where(vix > threshold, -1.0, 1.0), index=dates).where(pd.Series(reb, index=dates), np.nan).ffill().fillna(1.0)
    W = w.mul(sign, axis=0)
    if delay:
        W = W.shift(delay).fillna(0.0)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5)
    return portfolio_stats(W, r1, cost_panel(ctx) * cost_mult)


def stats(net: pd.Series, label: str) -> dict:
    out = {"variant": label}
    for tag, a, b in PERIODS:
        out[f"sharpe_{tag}"] = _sharpe(net[a:b])
    out["return_2015_26"] = float(net["2015":].mean() * 252)
    out["max_dd_2015_26"] = _dd(net["2015":])
    return out


def today(lab: str, top_frac: float | None, liquid_only: bool, threshold: float = 20.0) -> pd.DataFrame:
    """Target weights for the flip book as of the last cached day: a separate
    model that can be run next to the existing system without touching it."""
    from . import switch_lab as SL
    from .lab_prep import load

    md, ctx, X, names = load(lab)
    fred = pd.read_parquet(Path(lab) / "fred.parquet")
    vix = fred["vix"].reindex(md.dates).ffill()
    mask = ctx.tradable
    if liquid_only:
        mask = mask & (ctx.adv.where(mask).rank(axis=1, ascending=False) <= 300)
    SL.TOP_FRAC = top_frac
    z = composite(X, names, MOM, md.dates, md.tickers, mask)
    reb = np.zeros(len(md.dates), bool)
    reb[-1] = True                                   # rebalance as of the last day in the cache
    w = monthly_weights(z, mask, reb).iloc[-1]
    SL.TOP_FRAC = None
    stressed = bool(vix.iloc[-1] > threshold)
    w = -w if stressed else w
    w = w[w != 0].sort_values()
    out = pd.DataFrame({"weight": w, "side": np.where(w > 0, "long", "short")})
    out.attrs["as_of"] = md.dates[-1]
    out.attrs["vix"] = float(vix.iloc[-1])
    out.attrs["stance"] = "short momentum (VIX above %.0f)" % threshold if stressed else "long momentum (VIX at or below %.0f)" % threshold
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/lab")
    ap.add_argument("--out", default="reports/momentum_flip")
    ap.add_argument("--today", action="store_true", help="print today's target book instead of the backtest")
    ap.add_argument("--top-frac", type=float, default=None, help="with --today: trade only the top/bottom fraction")
    ap.add_argument("--liquid", action="store_true", help="with --today: 300 most liquid names only")
    args = ap.parse_args(argv)
    setup_logging()
    if args.today:
        book = today(args.lab, args.top_frac, args.liquid)
        print(f"as of {book.attrs['as_of'].date()}  VIX {book.attrs['vix']:.1f}  ->  {book.attrs['stance']}")
        print(f"{(book.side == 'long').sum()} longs, {(book.side == 'short').sum()} shorts, gross {book.weight.abs().sum():.2f}")
        print(book.round(4).to_string())
        Path(args.out).mkdir(parents=True, exist_ok=True)
        book.to_csv(Path(args.out) / f"book_{book.attrs['as_of'].date()}.csv")
        return
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from .lab_prep import load

    md, ctx, X, names = load(args.lab)
    fred = pd.read_parquet(Path(args.lab) / "fred.parquet")
    vix = fred["vix"].reindex(md.dates).ffill()
    tr = ctx.tradable
    liquid = tr & (ctx.adv.where(tr).rank(axis=1, ascending=False) <= 300)
    o = md.open
    ew = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5).where(tr).mean(axis=1)

    rows, daily = [], {}
    base = flip_returns(md, ctx, X, names, vix, tr)
    rows.append(stats(base["net"], "momentum flip, VIX 20, all names, 21 days"))
    daily["flip"] = base["net"]
    beta = (base["net"].rolling(252).cov(ew) / ew.rolling(252).var()).shift(1)
    hedged = (base["net"] - beta * ew).dropna()
    rows.append(stats(hedged, "  beta-hedged (trailing 252-day beta)"))
    daily["flip_hedged"] = hedged
    rows.append(stats(flip_returns(md, ctx, X, names, vix, tr, threshold=1e9)["net"], "  plain momentum, never flipped"))
    for thr in (16, 18, 22, 25):
        rows.append(stats(flip_returns(md, ctx, X, names, vix, tr, threshold=thr)["net"], f"  threshold {thr}"))
    rows.append(stats(flip_returns(md, ctx, X, names, vix, liquid)["net"], "  top 300 names"))
    for h in (10, 42):
        rows.append(stats(flip_returns(md, ctx, X, names, vix, tr, rebalance_days=h)["net"], f"  {h}-day rebalance"))
    rows.append(stats(flip_returns(md, ctx, X, names, vix, tr, delay=1)["net"], "  one-day execution delay"))
    rows.append(stats(flip_returns(md, ctx, X, names, vix, tr, cost_mult=2.0)["net"], "  costs x2"))
    for m in MOM:
        rows.append(stats(flip_returns(md, ctx, X, names, vix, tr, members=[m])["net"], f"  {m} alone"))
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "momentum_flip.csv", index=False)
    pd.DataFrame(daily).to_csv(out / "momentum_flip_daily.csv")
    yearly = (base["net"].groupby(base["net"].index.year).sum() * 100).loc[2006:].round(1)
    lines = ["# The momentum flip", "",
             "Momentum composite (mom_12_1 + resid_mom + high_52w), rebalanced every 21 days, held short whenever the "
             "VIX is above 20 at the rebalance. Net of measured spreads + 1 bp, unit gross.", "",
             tab.round(3).to_markdown(index=False), "",
             f"Turnover {base['turnover']['2015':].mean():.3f}/day; break-even "
             f"{base['gross']['2015':].sum() / base['turnover']['2015':].sum() * 1e4:.0f} bp (2015-26).", "",
             "## Net return by year (%)", "", yearly.to_frame("return_%").to_markdown(), ""]
    (out / "momentum_flip.md").write_text("\n".join(lines) + "\n")
    LOG.info("momentum flip done")
    print(tab.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
