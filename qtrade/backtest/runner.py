"""Full backtest: research pipeline -> every model through the same portfolio
rules -> overfitting-aware statistics -> HTML report and data files."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data.market import MarketData
from ..pipeline import build_research
from ..utils import LOG
from .engine import run_backtest
from .metrics import deflated_sharpe, sharpe, summarize
from .report import charts, write_markdown, write_report

BIAS_NOTES = [
    "<b>Read these results with care.</b> The universe is today's largest companies that have "
    "traded for 15+ years, tested over the past - so it never holds a company that later failed "
    "or shrank (survivorship and look-ahead bias). Expect live results to be weaker.",
    "Everything else is out-of-sample: signals use only past data, models are refit walk-forward, "
    "trades fill at the next day's open, and spread, market impact and borrow fees are charged.",
    "The <b>deflated Sharpe</b> is the probability the true Sharpe is above zero after "
    "correcting for having tried every model on this page. Below ~95% the edge is not "
    "statistically convincing.",
]


def run(md: MarketData, cfg: Config, out_dir: str | Path | None = None, synthetic: bool = False) -> dict:
    out_dir = Path(out_dir or cfg.report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    research = build_research(md, cfg)

    results, comparison, rows = {}, {}, []
    for name in research.wf.predictions:
        bt = run_backtest(research.ctx, research.prediction(name), research.fwd_ret, cfg,
                          name=name, record_weights=(name == cfg.model.trade_model))
        results[name] = bt
        comparison[name] = bt.returns
        s = summarize(bt.returns, bt.daily)
        rows.append({"model": name, "sharpe": s["sharpe"], "ann_return": s["ann_return"],
                     "ann_vol": s["ann_vol"], "max_drawdown": s["max_drawdown"],
                     "ann_turnover": s["ann_turnover"], "ann_cost_drag": s["ann_cost_drag"],
                     "mean_ic": float(np.nanmean(bt.ic.reindex(bt.daily.index)))})
    cmp_tbl = pd.DataFrame(rows).set_index("model").sort_values("sharpe", ascending=False)

    main = results[cfg.model.trade_model]
    bench = research.ctx.market_ret
    summary = summarize(main.returns, main.daily, benchmark=bench)
    summary["deflated_sharpe_prob"] = deflated_sharpe(main.returns, cmp_tbl["sharpe"].tolist())
    summary["n_models_tried"] = len(cmp_tbl)
    summary["n_signals"] = len(research.signal_names)
    summary["n_stocks"] = len(md.tickers)
    summary["model"] = main.name

    diag = run_diagnostics(research, cfg) if cfg.diagnostics else None
    if diag is not None:
        diag.to_csv(out_dir / "diagnostics.csv")
        LOG.info("portfolio diagnostics:\n%s", diag.round(3).to_string())

    ic_table = research.signal_ic_table()
    imgs = charts(main, bench, research.regimes, comparison, ic_table,
                  research.wf.weights.get("ridge", []), research.signal_names)
    notes = list(BIAS_NOTES)
    if synthetic:
        notes = ["<b>Synthetic data.</b> This run used a simulated market with planted "
                 "patterns, to check that the machinery works. It says nothing about real markets."]
    path = write_report(main, summary, cmp_tbl, ic_table, imgs, cfg, out_dir, notes)
    write_markdown(summary, cmp_tbl, ic_table, imgs, out_dir, notes, cfg, diag)

    if research.wf.selected:
        sel = pd.DataFrame(research.wf.selected, index=research.signal_names).T.astype(int)
        sel.to_csv(out_dir / "selected_signals.csv")
        LOG.info("stable-signal selection: kept on average %.1f of %d signals; most often kept:\n%s",
                 sel.sum(axis=1).mean(), sel.shape[1], sel.mean().sort_values(ascending=False).head(15).round(2))
    main.daily.to_csv(out_dir / "daily.csv")
    cmp_tbl.to_csv(out_dir / "model_comparison.csv")
    ic_table.to_csv(out_dir / "signal_ic.csv", index=False)
    research.regimes.to_csv(out_dir / "regimes.csv")
    if main.weights is not None:
        last = main.weights.iloc[-1]
        last[last.abs() > 1e-6].sort_values().to_csv(out_dir / "latest_weights.csv", header=["weight"])
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    LOG.info("report written to %s", path)
    LOG.info("Sharpe %.2f | ann. return %.1f%% | max DD %.1f%% | deflated Sharpe prob %.1f%%",
             summary["sharpe"], summary["ann_return"] * 100, summary["max_drawdown"] * 100,
             summary["deflated_sharpe_prob"] * 100)
    return {"summary": summary, "comparison": cmp_tbl, "report": str(path), "research": research,
            "results": results}


DIAGNOSTIC_VARIANTS = {
    "frictionless": {"costs": {"slippage_bps": 0.0, "spread_tiers": [[0.0, 0.0]], "impact_coef": 0.0,
                               "borrow_bps_annual": 0.0}, "portfolio": {"cost_aversion": 0.0}},
    "auction_costs (no spread)": {"costs": {"spread_tiers": [[0.0, 0.0]]}},
    "quoted_spread_costs": {"costs": {"spread_tiers": [[500e6, 1.5], [100e6, 3.0], [20e6, 6.0], [0.0, 12.0]]}},
    "rank_weights": {"portfolio": {"weighting": "rank"}},
    "dollar_neutral_only": {"portfolio": {"factor_neutral": False}},
    "regime_ic": {"portfolio": {"regime_ic": True}},
    # exposure follows the expected IC: full size at IC 0.015 (about twice the typical level)
    "regime_ic + edge_scaling": {"portfolio": {"regime_ic": True, "edge_scaling": 0.015}},
    "edge_scaling": {"portfolio": {"edge_scaling": 0.015}},
}
SWEEP_HALFLIFE = [0, 3, 7, 15, 30]
SWEEP_COST_AVERSION = [0.0, 0.25, 0.5, 1.0]


def run_diagnostics(research, cfg: Config) -> pd.DataFrame:
    """Same forecasts, different portfolio rules: shows where the edge is lost.

    Also sweeps forecast smoothing x cost aversion. Sharpe is reported for the
    first and second half of the sample separately: choose settings on the
    first half only and judge them on the second, so the choice is not fitted
    to the period it is evaluated on.
    """
    import copy

    from ..config import _merge

    variants = {"current config": {}}
    variants.update(DIAGNOSTIC_VARIANTS)
    for hl in SWEEP_HALFLIFE:
        for ca in SWEEP_COST_AVERSION:
            variants[f"halflife={hl} cost_aversion={ca}"] = {
                "portfolio": {"forecast_halflife": float(hl), "cost_aversion": ca}}
    rows = []
    pred = research.prediction(cfg.model.trade_model)
    for name, ov in variants.items():
        c = copy.deepcopy(cfg)
        _merge(c, ov)
        bt = run_backtest(research.ctx, pred, research.fwd_ret, c, name=name, record_weights=False)
        r = bt.returns
        mid = r.index[len(r) // 2]
        s = summarize(r, bt.daily)
        gross_ret = s["ann_return"] + s["ann_cost_drag"] + s["ann_borrow_drag"]
        rows.append({"variant": name, "sharpe": s["sharpe"],
                     "sharpe_1st_half": sharpe(r[r.index < mid]), "sharpe_2nd_half": sharpe(r[r.index >= mid]),
                     "ann_return": s["ann_return"], "ann_vol": s["ann_vol"],
                     "pre_cost_sharpe": gross_ret / s["ann_vol"] if s["ann_vol"] > 0 else np.nan,
                     "avg_gross": s["avg_gross"], "ann_turnover": s["ann_turnover"],
                     "cost_drag": s["ann_cost_drag"] + s["ann_borrow_drag"]})
    out = pd.DataFrame(rows).set_index("variant")
    out.attrs["split_date"] = str(mid.date())
    return out
