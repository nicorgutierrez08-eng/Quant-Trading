"""How much does survivorship bias flatter each signal?

The main universe is *today's* 1,000 largest long-lived companies, tested on
the past: it never holds a company that later failed, shrank or was bought.
Alpaca keeps daily bars for delisted stocks since 2016, so here a proper
point-in-time universe is rebuilt: at every month end, the 1,000 most-traded
US stocks *at that time* (63-day median dollar volume, price >= $5, a year of
history), dead or alive today.

The same close-to-close signals are scored on both universes over the same
dates. A signal whose IC drops sharply on the point-in-time universe was being
flattered by survivorship.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, cs_rank_gauss

SIGNALS = {
    "rev_1d": lambda lr, dv: -lr,
    "rev_5d": lambda lr, dv: -lr.rolling(5, min_periods=4).sum(),
    "rev_21d": lambda lr, dv: -lr.rolling(21, min_periods=15).sum(),
    "mom_12_1": lambda lr, dv: lr.rolling(231, min_periods=200).sum().shift(21),
    "low_vol": lambda lr, dv: -lr.rolling(63, min_periods=40).std(),
    "max_effect": lambda lr, dv: -lr.rolling(21, min_periods=15).max(),
    "size_proxy (illiquid)": lambda lr, dv: -np.log(dv.rolling(63, min_periods=40).median()),
    "amihud": lambda lr, dv: np.log((lr.abs() / dv.where(dv > 0)).rolling(21, min_periods=15).mean() * 1e9 + 1e-12),
}


def point_in_time_universe(close: pd.DataFrame, volume: pd.DataFrame, n: int = 1000) -> pd.DataFrame:
    """True where a stock was in the top-n by dollar volume at the latest month end."""
    dv = (close * volume).rolling(63, min_periods=40).median()
    hist = close.notna().rolling(252, min_periods=1).sum() >= 240
    ok = (close >= 5) & hist
    rank = dv.where(ok).rank(axis=1, ascending=False)
    month_end = pd.Series(close.index, index=close.index).groupby([close.index.year, close.index.month]).transform("max")
    is_me = close.index.to_series().eq(month_end).to_numpy()
    member = (rank <= n).astype(float)
    member[~is_me] = np.nan                                   # membership is set at month ends only
    return member.ffill().fillna(0).astype(bool) & close.notna()


def run(md, out: Path, cfg) -> dict:
    from ..data.public import load_all_stocks_daily

    data = load_all_stocks_daily(cfg.data.cache_dir)
    close, vol = data["close"], data["volume"]
    if close.empty:
        return {"error": "no bars"}
    pit = point_in_time_universe(close, vol)
    survivors = [t for t in md.tickers if t in close.columns]
    surv = pd.DataFrame(False, index=close.index, columns=close.columns)
    surv[survivors] = True
    surv &= close.notna() & (close >= 5)
    lr = np.log(close / close.shift(1)).clip(-0.7, 0.7)
    dv = close * vol
    rows = []
    for h in (5, 21):
        fwd = np.log(close.shift(-h) / close).clip(-1, 1)
        for uname, mask in (("survivors (current method)", surv), ("point-in-time (incl. delisted)", pit)):
            y = cs_rank_gauss(fwd.where(mask)).to_numpy()
            for sname, fn in SIGNALS.items():
                z = fn(lr, dv).where(mask)
                zr = cs_rank_gauss(z).to_numpy()
                ok = np.isfinite(zr) & np.isfinite(y)
                num = np.nansum(np.where(ok, zr * y, 0), axis=1)
                den = np.sqrt(np.nansum(np.where(ok, zr ** 2, 0), axis=1) * np.nansum(np.where(ok, y ** 2, 0), axis=1))
                ic = pd.Series(num / np.where(den > 0, den, np.nan), index=close.index)
                ic = ic[(ic.index >= "2017-06-01") & (ok.sum(axis=1) > 100)]
                rows.append({"signal": sname, "horizon": h, "universe": uname, "ic": ic.mean(),
                             "t": ic.mean() / ic.std() * np.sqrt(len(ic) / h), "days": len(ic),
                             "avg_names": float(mask.sum(axis=1).loc["2017-06-01":].mean())})
        LOG.info("survivorship: horizon %d done", h)
    tab = pd.DataFrame(rows)
    piv = tab.pivot_table(index=["signal", "horizon"], columns="universe", values="ic")
    piv["bias (survivor - pit)"] = piv["survivors (current method)"] - piv["point-in-time (incl. delisted)"]
    piv.index = [f"{a} ({b}d)" for a, b in piv.index]
    dead = len([c for c in close.columns if close[c].last_valid_index() is not None
                and close[c].last_valid_index() < close.index[-1] - pd.Timedelta(days=30)])
    tab.to_csv(out / "survivorship.csv", index=False)
    lines = ["## Survivorship bias, signal by signal", "",
             f"{close.shape[1]} US stocks from Alpaca since 2016, {dead} of them no longer trading. Point-in-time "
             "universe: top 1,000 by dollar volume at each month end. Same signals, same dates (mid-2017 on), "
             "close-to-close.", "",
             piv.round(4).to_markdown(), "",
             "A large positive bias means the signal looks better on today's survivors than it would have "
             "been in real time.", ""]
    (out / "survivorship.md").write_text("\n".join(lines) + "\n")
    return {"stocks": int(close.shape[1]), "delisted": dead,
            "bias": {f"{k[0]}@{k[1]}d": v for k, v in piv["bias (survivor - pit)"].round(4).items()}}
