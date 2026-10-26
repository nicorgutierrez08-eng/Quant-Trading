"""Independent check of the momentum flip (Nico's research_night, 21 Oct 2026).

The rule: a cross-sectional momentum book (12-1 month momentum, residual
momentum, nearness to the 52-week high), rebalanced every 21 days, held
*short* whenever the VIX is above 20 at the rebalance. Reported: net Sharpe
about 0.67 / 0.74 / 0.22 in 2006-14 / 2015-20 / 2021-26 (staggered).

Two checks, written from scratch on this repository's own pipeline:

1. **Replication**: same rule, our signals, our measured costs, VIX from FRED
   (lagged a day, as the data loader publishes it), weights decided at the
   close and traded from the next open; staggered = the average of the 21
   books that rebalance on different days. Plus the plain (never flipped)
   book and other VIX thresholds.
2. **Survivorship**: the same rule on a point-in-time universe of all US
   stocks including those later delisted (Alpaca daily bars since 2016, top
   1,000 by dollar volume each month end) against today's survivors over the
   same dates, with close-only signals (12-1 momentum and 52-week high) on
   both, so the only difference is the universe. In stress the book buys
   last year's losers, exactly the names a survivor universe flatters.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

PERIODS = (("2006-14", "2006", "2014"), ("2015-20", "2015", "2020"), ("2021-26", "2021", "2026"),
           ("2017-26", "2017", "2026"))


def _sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 60 and x.std() > 0 else np.nan


def _weights(z: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    """Unit-gross, dollar-neutral weights proportional to the demeaned score."""
    s = z.where(mask)
    s = s.sub(s.mean(axis=1), axis=0)
    return s.div(s.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def staggered_flip(z: pd.DataFrame, mask: pd.DataFrame, vix: pd.Series, r1: pd.DataFrame,
                   cost: pd.DataFrame | None, threshold: float = 20.0, every: int = 21) -> pd.Series:
    """Daily net return of the flip, averaged over the ``every`` possible rebalance days.

    ``r1`` at date t is the return earned by weights decided at the close of t."""
    w_all = _weights(z, mask)
    sign_daily = pd.Series(np.where(vix.reindex(z.index) > threshold, -1.0, 1.0), index=z.index)
    nets = []
    for k in range(every):
        reb = pd.Series(False, index=z.index)
        reb.iloc[k::every] = True
        w = w_all.where(reb, np.nan).ffill().fillna(0.0)
        sgn = sign_daily.where(reb, np.nan).ffill().fillna(1.0)
        W = w.mul(sgn, axis=0)
        g = (W * r1).sum(axis=1)
        if cost is not None:
            g = g - (W.diff().abs() * cost).sum(axis=1)
        nets.append(g)
    return pd.concat(nets, axis=1).mean(axis=1)


def _row(label: str, net: pd.Series) -> dict:
    out = {"variant": label}
    for tag, a, b in PERIODS:
        out[f"sharpe_{tag}"] = _sharpe(net[a:b])
    out["return_2015_26"] = float(net["2015":].mean() * 252)
    eq = (1 + net["2015":].fillna(0)).cumprod()
    out["max_dd_2015_26"] = float((eq / eq.cummax() - 1).min())
    return out


def replication(md, ctx, vix: pd.Series) -> pd.DataFrame:
    from ..signals import compute_signals
    from .edge import cost_panel

    sig = compute_signals(ctx, ["mom_12_1", "resid_mom", "high_52w"])
    z = sum(sig.values()) / len(sig)
    o = md.open
    r1 = (o.shift(-2) / o.shift(-1) - 1).clip(-0.5, 0.5)
    cost = cost_panel(ctx)
    rows = [_row("momentum flip, VIX 20 (staggered, net)", staggered_flip(z, ctx.tradable, vix, r1, cost)),
            _row("  gross (no costs)", staggered_flip(z, ctx.tradable, vix, r1, None)),
            _row("  plain momentum, never flipped", staggered_flip(z, ctx.tradable, vix, r1, cost, threshold=1e9)),
            _row("  always short momentum", staggered_flip(z, ctx.tradable, vix, r1, cost, threshold=-1.0))]
    for thr in (16, 18, 22, 25, 30):
        rows.append(_row(f"  threshold {thr}", staggered_flip(z, ctx.tradable, vix, r1, cost, threshold=thr)))
    share = (vix.reindex(md.dates) > 20)
    LOG.info("VIX above 20 on %.0f%% of days", 100 * share.mean())
    return pd.DataFrame(rows)


def survivorship(md, vix: pd.Series, cache_dir: str) -> pd.DataFrame:
    from ..data.public import load_all_stocks_daily
    from .survivorship import point_in_time_universe

    data = load_all_stocks_daily(cache_dir)
    close, vol = data["close"], data["volume"]
    if close.empty:
        return pd.DataFrame()
    pit = point_in_time_universe(close, vol)
    survivors = [t for t in md.tickers if t in close.columns]
    keep = sorted(set(survivors) | set(pit.columns[pit.any()]))       # names that ever enter either universe
    close, pit = close[keep], pit[keep]
    surv = pd.DataFrame(False, index=close.index, columns=close.columns)
    surv[survivors] = True
    surv &= close.notna() & (close >= 5)
    lr = np.log(close / close.shift(1)).clip(-0.7, 0.7)
    mom = lr.rolling(231, min_periods=200).sum().shift(21)
    high = np.log(close / close.rolling(252, min_periods=200).max())
    # trade at the next close (close-only data). Alpaca has no delisting returns: a stock's last
    # bar is its last price, so a bankruptcy's final drop to zero is missed in both universes
    r1 = (close.shift(-2) / close.shift(-1) - 1).clip(-0.9, 1.0)
    rows = []
    for uname, mask in (("survivors (today's universe)", surv), ("point-in-time incl. delisted", pit)):
        z = (mom.where(mask).rank(axis=1, pct=True) + high.where(mask).rank(axis=1, pct=True)) / 2
        for thr, lab in ((20.0, "flip VIX 20"), (1e9, "plain momentum")):
            net = staggered_flip(z, mask, vix, r1, None, threshold=thr)
            net = net[net.index >= "2017-06-01"]
            rows.append({"universe": uname, "book": lab, "gross_sharpe_2017_26": _sharpe(net),
                         "gross_return_2017_26": float(net.mean() * 252),
                         "gross_sharpe_2017_20": _sharpe(net[:"2020"]), "gross_sharpe_2021_26": _sharpe(net["2021":])})
    return pd.DataFrame(rows)


def run(md, ctx, out: Path, cfg) -> dict:
    from ..data.public import load_fred

    fred = load_fred(cfg.data.cache_dir)
    if fred is None or fred.empty or "vix" not in fred:
        (out / "flip_check.md").write_text("## Momentum flip check\n\n(no VIX data)\n")
        return {"error": "no VIX"}
    vix = fred["vix"].reindex(pd.date_range(fred.index.min(), md.dates[-1], freq="D")).ffill()
    rep = replication(md, ctx, vix.reindex(md.dates).ffill())
    rep.to_csv(out / "flip_check_replication.csv", index=False)
    surv = pd.DataFrame()
    try:
        surv = survivorship(md, vix, cfg.data.cache_dir)
        surv.to_csv(out / "flip_check_survivorship.csv", index=False)
    except Exception as exc:
        LOG.warning("survivorship check failed: %s", exc)
    lines = ["## Momentum flip (Nico's research_night): independent check", "",
             "Same rule rebuilt on this repository's pipeline: momentum composite (mom_12_1, resid_mom, high_52w), "
             "21-day rebalance staggered over all start days, short when the VIX (FRED, one-day publication lag) "
             "is above 20 at the rebalance, measured costs. Nico reported net Sharpe 0.67 / 0.74 / 0.22 "
             "(2006-14 / 2015-20 / 2021-26).", "",
             rep.round(3).to_markdown(index=False), "",
             "### Survivorship: point-in-time universe with delisted stocks (2017-26, before costs)", "",
             "Close-only signals (12-1 momentum + 52-week high) on both universes, same dates, so only the "
             "universe differs.", "",
             surv.round(3).to_markdown(index=False) if len(surv) else "(no all-stocks data)", ""]
    (out / "flip_check.md").write_text("\n".join(lines) + "\n")
    return {"replication": rep.round(3).to_dict(orient="records"),
            "survivorship": surv.round(3).to_dict(orient="records")}
