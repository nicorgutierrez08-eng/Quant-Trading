"""Macro symptoms for the regime HMM: the set that won the regime lab.

Two states on these symptoms were the only HMM in 88 variants whose
reversal/momentum switch paid in both 2004-2014 and 2015-2026 (see
docs/night_lab_log.md). Columns, all known at the close of day t:

    z_mkt           market return / GARCH(1,1) predicted vol (parameters fitted on the first 3 years only)
    log_sigma       log of that predicted vol (the column regimes are sorted by)
    log_dispersion  log cross-sectional std of stock returns that day
    corr_1d         share of that day's average squared return explained by the market
    breadth         share of tradable stocks up that day, minus 1/2
    log_vix         log VIX close, lagged a day (FRED, or the Yahoo stand-in)
    term            10y-3m Treasury spread, lagged a day
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils import LOG

GARCH_FIT_DAYS = 756


def garch_sigma(mkt: pd.Series, fit_days: int = GARCH_FIT_DAYS) -> pd.Series:
    from ..research.garch import fit_garch, garch_filter

    x = mkt.to_numpy(dtype=float)
    first = int(np.argmax(np.isfinite(x)))
    p = fit_garch(x[first:first + fit_days])
    s2 = np.full(len(x), np.nan)
    s2[first:] = garch_filter(x[first:], p["w"], p["a"], p["b"], p["g"], p["s0"])
    return pd.Series(np.sqrt(s2), index=mkt.index)


def macro_state(ctx, cache_dir: str = "data") -> pd.DataFrame:
    from ..data.public import load_fred

    r = ctx.ret.clip(-0.5, 0.5)
    mkt = ctx.market_ret
    sig = garch_sigma(mkt)
    disp = r.std(axis=1)
    breadth = (r.where(ctx.tradable) > 0).sum(axis=1) / ctx.tradable.sum(axis=1).clip(lower=1) - 0.5
    out = pd.DataFrame({
        "z_mkt": mkt / sig,
        "log_sigma": np.log(sig),
        "log_dispersion": np.log(disp.clip(lower=1e-5)),
        "corr_1d": (mkt ** 2 / (r.pow(2).mean(axis=1) + 1e-10)).clip(0, 1),
        "breadth": breadth,
    })
    fred = load_fred(cache_dir).reindex(mkt.index).ffill()
    out["log_vix"] = np.log(fred["vix"])
    out["term"] = fred["term_spread_10y3m"]
    LOG.info("macro regime symptoms: %d days, VIX from %s", out["log_vix"].notna().sum(),
             out["log_vix"].first_valid_index().date() if out["log_vix"].notna().any() else "n/a")
    return out
