"""Find vendor errors in the price cache: the biggest single-stock moves, and
the bars the bad-print filter removes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..data.loader import cache_paths
from ..data.market import bad_prints
from ..utils import load_frame


def run(md, ctx, out: Path, cache_dir: str) -> dict:
    raw = {f: load_frame(p) for f, p in cache_paths(cache_dir).items()}
    lines = ["## Data quality", ""]
    res = {}
    if raw.get("open") is not None and raw.get("close") is not None:
        bp = bad_prints(raw["open"], raw["close"])
        hits = bp.stack()
        hits = hits[hits]
        res["bad_prints_masked"] = int(len(hits))
        tab = pd.DataFrame([{"date": d.date(), "ticker": t,
                             "prev_close": raw["close"].shift(1).at[d, t], "open": raw["open"].at[d, t],
                             "close": raw["close"].at[d, t], "next_close": raw["close"].shift(-1).at[d, t]}
                            for d, t in hits.index[:200]])
        tab.to_csv(out / "bad_prints.csv", index=False)
        lines += [f"Bars removed as bad prints: {len(hits)}", "", tab.head(30).round(3).to_markdown(index=False)
                  if len(tab) else "(none)", ""]
    for name, panel in (("close-to-close", ctx.ret), ("overnight", ctx.overnight), ("intraday", ctx.intraday)):
        s = panel.stack()
        top = s.abs().sort_values(ascending=False).head(15)
        t = pd.DataFrame({"date": [d.date() for d, _ in top.index], "ticker": [k for _, k in top.index],
                          "return": s[top.index].to_numpy()})
        lines += [f"Largest {name} moves after cleaning:", "", t.round(3).to_markdown(index=False), ""]
        res[f"max_abs_{name}"] = float(top.iloc[0]) if len(top) else np.nan
    (out / "data_quality.md").write_text("\n".join(lines) + "\n")
    return res
