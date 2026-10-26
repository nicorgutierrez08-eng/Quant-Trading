"""python -m qtrade.research --tasks quality,spreads,edge,hmm --out reports/research"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

from ..config import Config
from ..utils import LOG, setup_logging


def _news_counts(cfg, extra: dict):
    """Daily article counts per ticker (cached), or None without news data."""
    if "news_counts" not in extra:
        extra["news_counts"] = None
        npath = Path(cfg.data.cache_dir) / "news"
        if any(npath.glob("news_*.parquet")):
            from ..data.news import article_counts, load_news

            c = article_counts(load_news(npath))
            c.index = c.index.to_timestamp()
            extra["news_counts"] = c
    return extra["news_counts"]


def main(argv=None):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="quality,spreads,edge,alt,poisson,conditional,combos,garch,glm,strategies,"
                                       "events,survivorship,intraday,hmm")
    ap.add_argument("--out", default="reports/research")
    ap.add_argument("--config")
    ap.add_argument("--synthetic", action="store_true", help="offline smoke test on a simulated market")
    args = ap.parse_args(argv)
    setup_logging()
    cfg = Config.load(args.config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.synthetic:
        from ..data import make_market

        md, _ = make_market(n_stocks=150, n_days=3000, seed=1, start="2004-01-02")
        cfg.universe.min_dollar_volume = 0
    else:
        from ..cli import _market

        md = _market(cfg)
    from ..features.context import FeatureContext

    ctx = FeatureContext(md, cfg)
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    summary, extra = {}, {}
    for task in tasks:
        LOG.info("research task: %s", task)
        try:
            if task == "quality":
                from .data_quality import run
                summary[task] = run(md, ctx, out, cfg.data.cache_dir)
            elif task == "consumer":
                from .consumer_earnings import run
                summary[task] = run(md, ctx, out, cfg)
            elif task == "hft":
                from .hft import run
                summary[task] = run(md, ctx, out, cfg)
            elif task == "asia":
                from .asia import run
                summary[task] = run(md, ctx, out, cfg)
            elif task == "news":
                from .news_zoo import run
                summary[task] = run(md, ctx, out, cfg)
            elif task == "flip":
                from .flip_check import run
                summary[task] = run(md, ctx, out, cfg)
            elif task == "multi":
                import pandas as pd

                from .multi import run
                rpath = Path(cfg.data.cache_dir) / "reversal_daily.csv"
                rev = pd.read_csv(rpath, index_col=0, parse_dates=True)["ret"] if rpath.exists() else None
                summary[task] = run(md, ctx, out, cfg, rev)
            elif task == "intraday":
                from .intraday_strats import run
                summary[task] = run(md, ctx, out, cfg)
            elif task == "spreads":
                from .spreads import run
                summary[task] = run(md, ctx, out)
            elif task == "edge":
                from .edge import run
                summary[task] = run(md, ctx, out)
                extra["composite"] = summary[task].pop("_composite", None)
            elif task == "alt":
                from ..signals import normalize_signal
                from .alt_signals import load_alt
                from .edge import Bench

                raw, fam = load_alt(md, ctx, cfg.data.cache_dir)
                alt = {k: normalize_signal(v, ctx.tradable) for k, v in raw.items()}
                extra.setdefault("alt", {}).update(alt)
                extra.setdefault("alt_family", {}).update(fam)
                if alt:
                    tab, dec = Bench(md, ctx).table(alt, fam)
                    tab.to_csv(out / "alt_signals.csv", index=False)
                    dec.to_csv(out / "alt_decay.csv", index=False)
                    cols = ["signal", "family", "halflife", "universe", "breakeven_bp_1st", "breakeven_bp_2nd",
                            "gross_sharpe_1st", "gross_sharpe_2nd", "net_sharpe_1st", "net_sharpe_2nd", "turnover_1st"]
                    d5 = dec[dec["horizon"].isin([5, 21])]
                    (out / "alt.md").write_text("\n".join([
                        "## Fundamental and news signals", "",
                        "Fundamentals start in 2009 and news in 2015, so '1st' covers 2009/2015-2014 only "
                        "(empty for news) - judge news on the 2nd period.", "",
                        "IC by horizon:", "", d5.round(4).to_markdown(index=False), "",
                        tab[cols].round(3).to_markdown(index=False), ""]) + "\n")
                    summary[task] = {"signals": list(alt)}
                else:
                    summary[task] = {"error": "no fundamentals or news data found"}
            elif task == "poisson":
                from ..signals import normalize_signal
                from .edge import Bench
                from .poisson import run

                res, raw = run(md, ctx, out, _news_counts(cfg, extra))
                psig = {k: normalize_signal(v, ctx.tradable) for k, v in raw.items()}
                extra.setdefault("alt", {}).update(psig)
                extra.setdefault("alt_family", {}).update({k: "poisson" for k in psig})
                tab, dec = Bench(md, ctx).table(psig, {k: "poisson" for k in psig})
                tab.to_csv(out / "poisson_signals.csv", index=False)
                cols = ["signal", "halflife", "universe", "breakeven_bp_1st", "breakeven_bp_2nd",
                        "gross_sharpe_1st", "gross_sharpe_2nd", "net_sharpe_1st", "net_sharpe_2nd", "turnover_1st"]
                with open(out / "poisson.md", "a") as fh:
                    fh.write("\n### Jump-intensity and news-surprise signals\n\nIC by horizon:\n\n"
                             + dec.round(4).to_markdown(index=False) + "\n\n"
                             + tab[cols].round(3).to_markdown(index=False) + "\n")
                summary[task] = res
            elif task == "conditional":
                from ..signals import compute_signals
                from .conditional import run

                sigs = compute_signals(ctx, ["rev_5d", "resid_rev_1d", "low_volume_rev", "peer_gap"])
                if extra.get("composite") is not None:
                    from ..signals import normalize_signal
                    sigs["composite"] = normalize_signal(extra["composite"], ctx.tradable)
                for k in ("no_news_rev", "sue", "ear"):
                    if k in extra.get("alt", {}):
                        sigs[k] = extra["alt"][k]
                summary[task] = run(md, ctx, out, cfg, sigs, _news_counts(cfg, extra))
            elif task == "combos":
                from ..signals import REGISTRY, compute_signals
                from .combos import run

                sigs = compute_signals(ctx)
                fam = {n: REGISTRY[n].family for n in sigs}
                for k, v in extra.get("alt", {}).items():
                    sigs[k] = v
                    fam[k] = extra.get("alt_family", {}).get(k, "")
                summary[task] = run(md, ctx, out, sigs, fam)
            elif task == "garch":
                from .garch import run

                comp = extra.get("composite")
                if comp is None:
                    from ..signals import compute_signals
                    from .edge import Bench, first_period_composite

                    comp = first_period_composite(compute_signals(ctx), bench=Bench(md, ctx))
                summary[task] = run(md, ctx, out, comp)
            elif task == "glm":
                from .glm import run

                summary[task] = run(md, ctx, out)
            elif task == "strategies":
                import pandas as pd

                from .strategies import run

                alt_raw = {}
                if extra.get("alt"):
                    alt_raw = {k: v for k, v in extra["alt"].items()
                               if k in ("gross_prof", "book_to_market", "sue", "accruals")}
                rev = None
                rpath = Path(cfg.data.cache_dir) / "reversal_daily.csv"
                if rpath.exists():
                    rev = pd.read_csv(rpath, index_col=0, parse_dates=True)["ret"]
                summary[task] = run(md, ctx, out, cfg, alt_raw, rev)
            elif task == "events":
                from .events import run

                summary[task] = run(md, ctx, out, cfg)
            elif task == "survivorship":
                from .survivorship import run

                summary[task] = run(md, out, cfg)
            elif task == "hmm":
                from .hmm_eval import run
                summary[task] = run(md, ctx, out, cfg)
        except Exception as exc:          # one failing study shouldn't lose the others
            LOG.exception("task %s failed", task)
            summary[task] = {"error": f"{type(exc).__name__}: {exc}"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    parts = ["# Research results", ""]
    for name in ("data_quality", "spreads", "edge", "alt", "poisson", "conditional", "combos", "garch", "glm",
                 "strategies", "events", "survivorship", "hmm"):
        p = out / f"{name}.md"
        if p.exists():
            parts.append(p.read_text())
    (out / "README.md").write_text("\n".join(parts))
    print(json.dumps(summary, indent=1, default=str)[:3000])


if __name__ == "__main__":
    main()
