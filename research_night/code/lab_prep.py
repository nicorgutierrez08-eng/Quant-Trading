"""Build the market data and feature context once and cache the heavy panels.

The research studies rebuild ``FeatureContext`` (factor model, signals) on
every run, which takes minutes. For an iterative session it is far cheaper to
compute everything once and reload it in seconds:

    python -m qtrade.research.lab_prep --out data/lab

Writes ``md.pkl`` (MarketData), ``ctx.pkl`` (FeatureContext with its cached
panels), ``signals.npz`` (all library signals, float32, T x N x F) plus
``etf_close.parquet`` and ``fred.parquet`` when those downloads succeed.
"""
from __future__ import annotations

import argparse
import pickle
import time
from pathlib import Path

import numpy as np

from ..config import Config
from ..utils import LOG, setup_logging


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/lab")
    ap.add_argument("--config")
    args = ap.parse_args(argv)
    setup_logging()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = Config.load(args.config)

    from ..cli import _market
    from ..features.context import FeatureContext
    from ..signals import compute_signals

    t0 = time.time()
    md = _market(cfg)
    LOG.info("market: %d dates x %d tickers (%.0fs)", len(md.dates), len(md.tickers), time.time() - t0)
    ctx = FeatureContext(md, cfg)
    # touch every panel the studies use so they end up in the pickle
    for name in ("ret", "log_ret", "overnight", "intraday", "dollar_volume", "adv", "vol_21", "vol_63", "spread",
                 "market_ret", "beta_252", "tradable", "factor_model", "resid", "clusters", "market_state"):
        getattr(ctx, name)
        LOG.info("ctx.%s ready (%.0fs)", name, time.time() - t0)
    with open(out / "md.pkl", "wb") as fh:
        pickle.dump(md, fh, protocol=pickle.HIGHEST_PROTOCOL)
    with open(out / "ctx.pkl", "wb") as fh:
        pickle.dump(ctx, fh, protocol=pickle.HIGHEST_PROTOCOL)
    LOG.info("pickled md and ctx (%.0fs)", time.time() - t0)

    sigs = compute_signals(ctx)
    names = list(sigs)
    X = np.stack([sigs[n].to_numpy(dtype=np.float32) for n in names], axis=-1)
    np.savez(out / "signals.npz", X=X, names=np.array(names))
    LOG.info("signals: %s (%.0fs)", X.shape, time.time() - t0)

    try:
        from .strategies import _etfs

        etf = _etfs("2003-01-01")
        etf.close.to_parquet(out / "etf_close.parquet")
        LOG.info("ETF closes: %s", etf.close.shape)
    except Exception as exc:  # noqa: BLE001 - optional input
        LOG.warning("ETF download failed: %s", exc)
    try:
        from ..data.public import load_fred

        fred = load_fred(cfg.data.cache_dir)
        fred.to_parquet(out / "fred.parquet")
        LOG.info("FRED: %s", fred.shape)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("FRED failed: %s", exc)
    LOG.info("done in %.0fs", time.time() - t0)


def load(out: str | Path = "data/lab"):
    """(md, ctx, signals X, signal names) from the cache."""
    out = Path(out)
    with open(out / "md.pkl", "rb") as fh:
        md = pickle.load(fh)
    with open(out / "ctx.pkl", "rb") as fh:
        ctx = pickle.load(fh)
    z = np.load(out / "signals.npz", allow_pickle=False)
    return md, ctx, z["X"], list(z["names"])


if __name__ == "__main__":
    main()
