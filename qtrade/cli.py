"""Command line interface.

    python -m qtrade universe            # pick the top-1000, 15-year-history universe
    python -m qtrade download            # download / refresh daily prices
    python -m qtrade backtest            # full walk-forward backtest + HTML report
    python -m qtrade demo                # same pipeline on a synthetic market (offline)
    python -m qtrade paper               # paper-trading dry run (prints orders)
    python -m qtrade paper --send        # actually place orders on Alpaca paper
    python -m qtrade intraday            # download 5-minute bars from Alpaca
    python -m qtrade news                # download news headlines from Alpaca
    python -m qtrade fundamentals        # download SEC fundamentals
    python -m qtrade intraday-backtest   # intraday reversal strategy on 5-minute bars
    python -m qtrade intraday-paper      # trade it on Alpaca paper every 5 minutes
    python -m qtrade auction-paper --phase close|open   # auction trader (market-on-close / -open)
    python -m qtrade signals             # list every signal in the library
"""
from __future__ import annotations

import argparse
import os
import sys
import warnings

import pandas as pd

from .config import Config
from .utils import LOG, setup_logging


def _cfg(args) -> Config:
    overrides: dict = {}
    if getattr(args, "size", None):
        overrides.setdefault("universe", {})["size"] = args.size
    if getattr(args, "years", None):
        overrides.setdefault("universe", {})["min_history_years"] = args.years
    if getattr(args, "start", None):
        overrides.setdefault("data", {})["start"] = args.start
    if getattr(args, "end", None):
        overrides.setdefault("data", {})["end"] = args.end
    if getattr(args, "models", None):
        ms = args.models.split(",")
        overrides["model"] = {"models": ms, "ensemble": [m for m in ms if m != "elastic_net"] or ms}
    if getattr(args, "horizon", None):
        overrides.setdefault("model", {})["horizon"] = args.horizon
    return Config.load(args.config, overrides)


def cmd_universe(args):
    from .data import build_universe, save_universe

    cfg = _cfg(args)
    u = cfg.universe
    uni = build_universe(u.size, u.min_history_years, u.candidate_source, u.universe_file,
                         start=cfg.data.start, batch_size=cfg.data.batch_size)
    path = save_universe(uni, cfg.data.cache_dir)
    print(f"Saved {len(uni)} companies to {path}")
    print(uni.head(15).to_string(index=False))


def _market(cfg):
    from .data import build_universe, get_market_data, load_universe, save_universe

    uni = load_universe(cfg.data.cache_dir)
    if uni is None:
        u = cfg.universe
        uni = build_universe(u.size, u.min_history_years, u.candidate_source, u.universe_file,
                             start=cfg.data.start, batch_size=cfg.data.batch_size)
        save_universe(uni, cfg.data.cache_dir)
    tickers = uni["ticker"].head(cfg.universe.size).tolist()
    return get_market_data(tickers, cfg.data.start, cfg.data.end, cfg.data.cache_dir, cfg.data.batch_size)


def cmd_download(args):
    cfg = _cfg(args)
    md = _market(cfg)
    print(f"{len(md.tickers)} tickers, {md.dates[0].date()} -> {md.dates[-1].date()}")


def cmd_backtest(args):
    from .backtest.runner import run

    cfg = _cfg(args)
    md = _market(cfg)
    out = run(md, cfg, args.out)
    _print_result(out)


def cmd_demo(args):
    from .backtest.runner import run
    from .data import make_market

    cfg = _cfg(args)
    cfg.universe.min_dollar_volume = 0
    md, _ = make_market(n_stocks=args.stocks, n_days=args.days, seed=args.seed)
    out = run(md, cfg, args.out or "reports/demo", synthetic=True)
    _print_result(out)


def cmd_paper(args):
    from .live.alpaca_trader import run_paper

    cfg = _cfg(args)
    run_paper(cfg, dry_run=not args.send, once_per_day=args.once_per_day)


def cmd_status(args):
    """Report the paper account's P&L and positions."""
    import json

    from .live.status import run_status, summary_line

    cfg = _cfg(args)
    st = run_status(cfg, args.out)
    line = summary_line(st)
    print(line)
    print(json.dumps({k: st[k] for k in ("best_today", "worst_today")}, indent=1))
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice title=Paper account::{line}")


def cmd_intraday(args):
    """Download / refresh intraday bars from Alpaca for the most liquid stocks."""
    from pathlib import Path

    from .data import load_universe
    from .data.intraday import AlpacaBars, download, most_liquid, write_manifest

    cfg = _cfg(args)
    store = Path(args.store or f"data/intraday/{args.timeframe.lower()}")
    store.mkdir(parents=True, exist_ok=True)
    sym_file = store / "symbols.csv"
    client = AlpacaBars()
    if sym_file.exists() and not args.reselect:
        symbols = pd.read_csv(sym_file)["ticker"].tolist()
        print(f"Using the {len(symbols)} symbols already in the store")
    else:
        uni = load_universe(cfg.data.cache_dir)
        if uni is None:
            raise SystemExit("No universe found. Run `python -m qtrade universe` first.")
        ranked = most_liquid(client, uni["ticker"].tolist(), args.symbols)
        ranked.to_csv(sym_file, index=False)
        symbols = ranked["ticker"].tolist()
        print(f"Selected the {len(symbols)} most liquid stocks (median daily $ volume)")
    m = download(symbols, store, args.timeframe, args.start, client, args.budget)
    path = write_manifest(m, store, {"api_calls": client.calls, "start_requested": args.start})
    done = int((m["rows"] > 0).sum())
    print(f"{done}/{len(symbols)} symbols stored, {int(m['rows'].sum()):,} bars. Manifest: {path}")


def cmd_intraday_backtest(args):
    """Walk-forward backtest of the intraday reversal strategy."""
    from .intraday.runner import run

    cfg = _cfg(args)
    icfg = cfg.intraday
    if args.symbols:
        icfg.n_symbols = args.symbols
    if args.every:
        icfg.rebalance_every = args.every
    if args.synthetic:
        from .intraday.synthetic import make_intraday

        bars = make_intraday(n_stocks=100, n_days=300, seed=1)
        icfg.min_train_months = 2
    else:
        from .intraday.bars import load_store

        bars = load_store(args.store or icfg.store, icfg.n_symbols, args.start or icfg.start, icfg.bar_minutes)
    out = run(bars, cfg, args.out)
    s = out["summary"]
    print(f"\n{s['variant']}: Sharpe {s['sharpe']:.2f} after costs ({s['sharpe_pre_cost']:.2f} before), "
          f"{s['ann_return'] * 100:.1f}%/yr, max DD {s['max_drawdown'] * 100:.1f}%")
    print(out["variants"][["sharpe", "sharpe_pre_cost", "sharpe_2nd_half", "ann_return", "turnover_per_day"]]
          .round(2).to_string())
    print(f"\nReport: {args.out}/README.md")


def cmd_auction_paper(args):
    """The auction trader: market-on-close book in the evening, market-on-open exit in the morning."""
    from .intraday import auction_live as A

    cfg = _cfg(args)
    dry = not args.send
    if args.phase == "keeper":
        tickers, signs = A.load_inputs(args.tickers, args.signs)
        res = A.run_keeper(cfg, tickers, signs, hours=args.hours, dry_run=dry, out_dir=args.out)
        print(f"auction keeper: {res['status']}, {len(res['actions'])} actions")
        return
    try:
        A.fill_report(days=4, out_dir=args.out)
    except Exception as exc:          # the report must never block trading
        A.LOG.warning("fill report failed: %s", exc)
    if args.phase == "close":
        tickers, signs = A.load_inputs(args.tickers, args.signs)
        res = A.run_close(cfg, tickers, signs, dry_run=dry, out_dir=args.out)
    elif args.phase == "open":
        res = A.run_open(cfg, dry_run=dry, out_dir=args.out)
    else:
        res = {"status": "report only"}
    print(f"auction {args.phase}: {res}")


def cmd_intraday_paper(args):
    """Trade the intraday strategy on Alpaca paper, every bar until the close."""
    from .intraday.live import run_intraday_paper

    cfg = _cfg(args)
    if args.every:
        cfg.intraday.rebalance_every = args.every
    res = run_intraday_paper(cfg, args.model, dry_run=not args.send, minutes=args.minutes)
    if args.status_file:
        Path_ = __import__("pathlib").Path
        Path_(args.status_file).write_text(res["status"])
    print(f"intraday session: {res['status']} after {len(res.get('cycles', []))} cycles")


def _universe_tickers(cfg) -> list[str]:
    from .data import load_universe

    uni = load_universe(cfg.data.cache_dir)
    if uni is None:
        raise SystemExit("No universe found. Run `python -m qtrade universe` first.")
    return uni["ticker"].head(cfg.universe.size).tolist()


def cmd_news(args):
    """Download / refresh news headlines from Alpaca for the universe."""
    from .data.intraday import AlpacaBars
    from .data.news import download_news, write_news_manifest

    cfg = _cfg(args)
    tickers = _universe_tickers(cfg)[: args.symbols]
    client = AlpacaBars()
    m = download_news(tickers, args.store, args.start, client, args.budget)
    path = write_news_manifest(m, args.store, {"symbols_requested": len(tickers), "api_calls": client.calls})
    print(f"{len(m)} months, {int(m['articles'].sum()) if len(m) else 0:,} articles. Manifest: {path}")


def cmd_fundamentals(args):
    """Download fundamentals for the universe from SEC EDGAR."""
    from .data.fundamentals import download_fundamentals

    cfg = _cfg(args)
    man = download_fundamentals(_universe_tickers(cfg), args.store)
    print(f"{int((man['facts'] > 0).sum())} companies, {int(man['facts'].sum()):,} facts in {args.store}")


def cmd_signals(args):
    from .signals import list_signals

    with pd.option_context("display.max_colwidth", 90, "display.width", 160):
        print(list_signals().to_string(index=False))


def _print_result(out):
    s = out["summary"]
    print("\n" + "=" * 64)
    print(f" {s['start']} -> {s['end']}   model: {s['model']}   stocks: {s['n_stocks']}")
    print(f" Sharpe {s['sharpe']:.2f} | return {s['ann_return']*100:.1f}%/yr | vol {s['ann_vol']*100:.1f}% "
          f"| max DD {s['max_drawdown']*100:.1f}%")
    print(f" deflated-Sharpe probability {s['deflated_sharpe_prob']*100:.0f}% over {s['n_models_tried']} models")
    print("=" * 64)
    print(out["comparison"].round(3).to_string())
    print(f"\nReport: {out['report']}")


def main(argv=None):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser(prog="qtrade", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="YAML config file (default: built-in defaults)")
    ap.add_argument("--log", default="INFO")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--size", type=int, help="number of companies (default 1000)")
        p.add_argument("--years", type=float, help="minimum years of history (default 15)")
        p.add_argument("--start", help="first date of data, e.g. 2000-01-01")
        p.add_argument("--end", help="last date of data")
        p.add_argument("--models", help="comma list: ridge,elastic_net,regime_ridge,kernel_ridge,gbm,ic_weighted")
        p.add_argument("--horizon", type=int, help="forecast horizon in days (default 5)")
        return p

    common(sub.add_parser("universe", help="select the trading universe")).set_defaults(fn=cmd_universe)
    common(sub.add_parser("download", help="download daily prices")).set_defaults(fn=cmd_download)
    p = common(sub.add_parser("backtest", help="run the full backtest"))
    p.add_argument("--out", help="report directory (default reports/)")
    p.set_defaults(fn=cmd_backtest)
    p = common(sub.add_parser("demo", help="run on a synthetic market (no internet needed)"))
    p.add_argument("--stocks", type=int, default=200)
    p.add_argument("--days", type=int, default=2520)
    p.add_argument("--seed", type=int, default=3)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_demo)
    p = common(sub.add_parser("paper", help="paper trade on Alpaca"))
    p.add_argument("--send", action="store_true", help="really submit orders (paper account)")
    p.add_argument("--once-per-day", action="store_true",
                   help="skip if orders were already sent today (for back-up scheduled runs)")
    p.set_defaults(fn=cmd_paper)
    p = sub.add_parser("status", help="paper account P&L and positions")
    p.add_argument("--out", default="logs/status")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("intraday", help="download intraday bars from Alpaca")
    p.add_argument("--symbols", type=int, default=200, help="how many of the most liquid stocks")
    p.add_argument("--timeframe", default="5Min", help="bar size, e.g. 1Min, 5Min, 15Min")
    p.add_argument("--start", default="2016-01-01", help="first date (Alpaca history begins 2016)")
    p.add_argument("--store", help="where per-symbol files are kept (default data/intraday/<timeframe>)")
    p.add_argument("--budget", type=float, help="stop after this many minutes (resume later)")
    p.add_argument("--reselect", action="store_true", help="re-pick the most liquid stocks")
    p.set_defaults(fn=cmd_intraday)
    p = sub.add_parser("intraday-backtest", help="backtest the intraday reversal strategy")
    p.add_argument("--store", help="intraday bar store (default data/intraday/5min)")
    p.add_argument("--symbols", type=int, help="most liquid N names (default 500)")
    p.add_argument("--start", help="first day, e.g. 2018-01-01")
    p.add_argument("--every", type=int, help="rebalance every N bars (default 1)")
    p.add_argument("--out", default="reports/intraday")
    p.add_argument("--synthetic", action="store_true", help="use a simulated market (offline check)")
    p.set_defaults(fn=cmd_intraday_backtest)
    p = sub.add_parser("intraday-paper", help="trade the intraday strategy on Alpaca paper")
    p.add_argument("--model", default="data/intraday_model.json", help="model.json from intraday-backtest")
    p.add_argument("--send", action="store_true", help="really submit orders (paper account)")
    p.add_argument("--every", type=int, help="rebalance every N bars (default 1)")
    p.add_argument("--minutes", type=float, help="stop after this many minutes (GitHub's 6-hour job limit)")
    p.add_argument("--status-file", help="write done / continue / closed here")
    p.set_defaults(fn=cmd_intraday_paper)
    p = sub.add_parser("auction-paper", help="trade the auction strategies on Alpaca paper")
    p.add_argument("--phase", choices=["keeper", "close", "open", "report"], required=True,
                   help="keeper: stay up and act at the right moments; close: market-on-close book (~15:45); "
                        "open: market-on-open exit (before 9:28)")
    p.add_argument("--hours", type=float, default=5.4, help="keeper: how long to stay up")
    p.add_argument("--tickers", default="data/auction_tickers.json", help="JSON list (or {'tickers': [...]})")
    p.add_argument("--signs", default="data/auction_signs.json", help="strategy directions from the backtest")
    p.add_argument("--send", action="store_true", help="really submit orders (paper account)")
    p.add_argument("--out", default="logs")
    p.set_defaults(fn=cmd_auction_paper)
    p = sub.add_parser("news", help="download news headlines from Alpaca")
    p.add_argument("--symbols", type=int, default=1000, help="first N stocks of the universe")
    p.add_argument("--start", default="2015-01-01")
    p.add_argument("--store", default="data/news")
    p.add_argument("--budget", type=float, help="stop after this many minutes (resume later)")
    p.set_defaults(fn=cmd_news)
    p = sub.add_parser("fundamentals", help="download company fundamentals from SEC EDGAR")
    p.add_argument("--store", default="data/fundamentals")
    p.set_defaults(fn=cmd_fundamentals)
    sub.add_parser("signals", help="list the signal library").set_defaults(fn=cmd_signals)

    args = ap.parse_args(argv)
    setup_logging(args.log)
    LOG.debug("args: %s", args)
    try:
        args.fn(args)
    except (Exception, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code in (0, None):
            raise
        if os.environ.get("GITHUB_ACTIONS"):
            # surfaces as an annotation on the run page, readable without opening logs
            msg = str(exc).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::error title=qtrade {args.cmd} failed::{type(exc).__name__}: {msg}", flush=True)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
