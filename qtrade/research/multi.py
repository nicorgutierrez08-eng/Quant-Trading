"""The multi-strategy book on real data: ETF sleeves + the stock book.

Backtests ``qtrade.portfolio.sleeves.combine`` exactly as it will trade (GARCH
fitted on 2004-2014 only, sleeve weights from trailing volatility, 10% vol
target), alone and blended with the stock book at several capital splits.

Caveat: the sleeves were chosen from strategies with a 2006-2014 Sharpe above
0.3, but a few practical exclusions (short volatility, stock pairs, the 3-month
trend that faded) were made after seeing 2015-2026, so 2015-2026 is not fully
out of sample here.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG

SPLIT = "2015-01-01"


def _stats(r: pd.Series) -> dict:
    out = {}
    for tag, m in (("2006_14", (r.index >= "2006-01-01") & (r.index < SPLIT)), ("2015_26", r.index >= SPLIT)):
        x = r[m]
        out[f"sharpe_{tag}"] = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
        out[f"return_{tag}"] = x.mean() * 252
        out[f"vol_{tag}"] = x.std() * np.sqrt(252)
        eq = (1 + x).cumprod()
        out[f"max_dd_{tag}"] = (eq / eq.cummax() - 1).min() if len(x) else np.nan
    return out


def run(md, ctx, out: Path, cfg, reversal: pd.Series | None = None) -> dict:
    from ..portfolio import sleeves as S
    from .strategies import _etfs

    etf = _etfs("2003-01-01")
    rows, books = [], {}
    for label, names in (("all 8 sleeves", S.DEFAULT_SLEEVES),
                         ("small account (no 30-ETF trend)", [n for n in S.DEFAULT_SLEEVES if n != "broad_trend_12m"])):
        res = S.combine(etf.close, names, fit_end=SPLIT)
        books[label] = res["returns"]
        rows.append({"book": f"ETF sleeves: {label}", **_stats(res["returns"])})
        if label == "all 8 sleeves":
            sleeve_tab = pd.DataFrame({n: _stats(res["sleeve_returns"][n]) for n in names}).T
            avg_w = res["sleeve_weights"].loc[SPLIT:].mean().round(3)
            turnover = res["weights"].diff().abs().sum(axis=1).loc["2006":].mean() * 252
    etf_book = books["all 8 sleeves"]
    blend_rows = []
    if reversal is not None:
        rev = reversal.reindex(etf_book.index).fillna(0.0)
        rows.append({"book": "stock book (reversal, as backtested)", **_stats(rev)})
        corr = etf_book.loc["2006":].corr(rev.loc["2006":])
        for f in (0.3, 0.5, 0.7):
            b = f * etf_book + (1 - f) * rev
            blend_rows.append({"etf_fraction": f, **_stats(b)})
    else:
        corr = np.nan
    tab = pd.DataFrame(rows)
    blends = pd.DataFrame(blend_rows)
    tab.to_csv(out / "multi_books.csv", index=False)
    pd.DataFrame(books).to_csv(out / "multi_daily.csv")
    lines = ["## Multi-strategy book (ETF sleeves + stock book)", "",
             "The ETF book exactly as it trades: GARCH fitted on 2004-2014, sleeves weighted by 1 / trailing "
             "volatility, scaled to 10% volatility, gross capped at 1.5x, 1 bp per unit traded. Some sleeve "
             "exclusions were made after seeing 2015-2026, so that period is not fully out of sample.", "",
             tab.round(3).to_markdown(index=False), "",
             f"ETF book turnover: {turnover:.1f}x a year. Correlation with the stock book: {corr:.2f}.", "",
             "### Capital split between the two books", "",
             blends.round(3).to_markdown(index=False) if len(blends) else "(no stock-book returns available)", "",
             "### Each sleeve", "", sleeve_tab.round(3).to_markdown(), "",
             "Average sleeve weights since 2015: " + ", ".join(f"{k} {v:.0%}" for k, v in avg_w.items()), ""]
    (out / "multi.md").write_text("\n".join(lines) + "\n")
    LOG.info("multi book done")
    return {"books": tab.round(3).to_dict(orient="records"), "blends": blends.round(3).to_dict(orient="records"),
            "corr_with_stock_book": None if not np.isfinite(corr) else round(float(corr), 3)}
