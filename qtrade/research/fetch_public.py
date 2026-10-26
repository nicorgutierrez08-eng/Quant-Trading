"""Download the free public datasets once (run in a workflow's prep step):
    python -m qtrade.research.fetch_public
"""
from __future__ import annotations

import warnings

from ..config import Config
from ..utils import LOG, setup_logging


def main():
    warnings.filterwarnings("ignore")
    setup_logging()
    from ..cli import _market
    from ..data.public import load_fred, load_insider, load_short_volume, load_sp500_changes

    cfg = Config()
    root = cfg.data.cache_dir
    for name, fn in (("FRED", lambda: load_fred(root, refresh=True)),
                     ("S&P 500 changes", lambda: load_sp500_changes(root, refresh=True)),
                     ("insider trades", lambda: load_insider(root, budget_min=120))):
        try:
            out = fn()
            LOG.info("%s: %d rows", name, len(out))
        except Exception as exc:
            LOG.warning("%s failed: %s", name, exc)
    try:
        md = _market(cfg)
        sv = load_short_volume(md.dates, md.tickers, root, budget_min=90)
        LOG.info("short volume: %d days with data", int(sv.notna().any(axis=1).sum()))
    except Exception as exc:
        LOG.warning("short volume failed: %s", exc)


if __name__ == "__main__":
    main()
