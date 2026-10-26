"""Daily statistics from 5-minute bars, for daily signals.

Per stock and day: realized variance, realized skewness and kurtosis
(Amaya-Christoffersen-Jacobs-Vasquez: high realized skewness predicts lower
returns), the jump share of variance (realized minus bipower variation), and
the return over the first and the last half hour. Computed once from the
intraday store and kept as a small parquet file under data/public/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

STATS = ["rv", "rskew", "rkurt", "jump_share", "first30", "last30"]


def daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    """One stock's 5-minute bars (New York time index) -> daily statistics."""
    df = df[["open", "close"]].dropna()
    if df.empty:
        return pd.DataFrame(columns=STATS)
    day = df.index.tz_localize(None).normalize() if df.index.tz is not None else df.index.normalize()
    lr = np.log(df["close"]).groupby(day).diff()
    first_bar = ~pd.Series(day, index=df.index).duplicated().to_numpy()
    lr[first_bar] = np.log(df["close"] / df["open"])[first_bar]       # first bar: open -> close of the bar
    g = pd.DataFrame({"r": lr.to_numpy(), "day": day}, index=df.index)
    g["absr"] = g["r"].abs()
    g["prod"] = g["absr"] * g.groupby("day")["absr"].shift(1)
    mins = df.index.hour * 60 + df.index.minute
    agg = g.groupby("day").agg(n=("r", "count"), rv=("r", lambda x: (x ** 2).sum()),
                               s3=("r", lambda x: (x ** 3).sum()), s4=("r", lambda x: (x ** 4).sum()),
                               bv=("prod", "sum"))
    out = pd.DataFrame(index=agg.index)
    out["rv"] = agg["rv"]
    out["rskew"] = np.sqrt(agg["n"]) * agg["s3"] / agg["rv"].where(agg["rv"] > 0) ** 1.5
    out["rkurt"] = agg["n"] * agg["s4"] / agg["rv"].where(agg["rv"] > 0) ** 2
    bv = np.pi / 2 * agg["bv"]
    out["jump_share"] = ((agg["rv"] - bv).clip(lower=0) / agg["rv"].where(agg["rv"] > 0))
    early = g[(mins >= 570) & (mins < 600)].groupby("day")["r"].sum()
    late = g[(mins >= 930) & (mins < 960)].groupby("day")["r"].sum()
    out["first30"], out["last30"] = early, late
    out = out[agg["n"] >= 40]                                       # skip half days and thin data
    return out


def build(store: str | Path, root: str | Path = "data") -> Path | None:
    store = Path(store)
    files = sorted(store.glob("*.parquet"))
    if not files:
        return None
    parts = []
    for i, f in enumerate(files):
        try:
            s = daily_stats(pd.read_parquet(f, columns=["open", "close"]))
            s.columns = pd.MultiIndex.from_product([s.columns, [f.stem]])
            parts.append(s.astype("float32"))
        except Exception as exc:
            LOG.warning("intraday stats %s: %s", f.stem, exc)
        if (i + 1) % 100 == 0:
            LOG.info("intraday stats: %d/%d symbols", i + 1, len(files))
    allst = pd.concat(parts, axis=1)
    out = Path(root) / "public" / "intraday_stats.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    allst.to_parquet(out)
    LOG.info("intraday stats: %d days x %d symbols -> %s", len(allst), len(files), out)
    return out


def load(root: str | Path = "data") -> dict[str, pd.DataFrame] | None:
    p = Path(root) / "public" / "intraday_stats.parquet"
    if not p.exists():
        return None
    x = pd.read_parquet(p)
    return {s: x[s] for s in STATS if s in x.columns.get_level_values(0)}


if __name__ == "__main__":
    import sys

    from ..utils import setup_logging

    setup_logging()
    build(sys.argv[1] if len(sys.argv) > 1 else "data/intraday/5min")
