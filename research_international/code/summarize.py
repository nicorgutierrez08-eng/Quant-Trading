"""Cross-market summary tables from intl_lab output.

1. The sign pattern: for each market, the 21-day IC of the momentum signals
   and of reversal in calm (VIX <= 20) vs. stressed markets - is "momentum
   reverses in stress" a property of the US only, or of stock markets?
2. Invariants by market: which signals keep their sign in all four sub-periods.
3. The momentum books side by side, and data quality per market.

    python research_international/code/summarize.py --lab reports/intl --prices data/prices --out reports/intl
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PER = ["ic_2004_09", "ic_2010_14", "ic_2015_20", "ic_2021_26"]


def sign_pattern(ics: pd.DataFrame) -> pd.DataFrame:
    x = ics[ics["horizon"] == 21].copy()
    mom = x[x["signal"].isin(["mom_12_1", "resid_mom", "high_52w"])].groupby("market")[["ic_calm", "ic_stressed"]].mean()
    rev = x[x["signal"] == "rev_21d"].set_index("market")[["ic_calm", "ic_stressed"]]
    out = pd.DataFrame({"momentum_ic_calm": mom["ic_calm"], "momentum_ic_stressed": mom["ic_stressed"],
                        "reversal21_ic_calm": rev["ic_calm"], "reversal21_ic_stressed": rev["ic_stressed"]})
    out["momentum_turns_negative_in_stress"] = (out["momentum_ic_calm"] > 0) & (out["momentum_ic_stressed"] < 0)
    out["stress_minus_calm_momentum"] = out["momentum_ic_stressed"] - out["momentum_ic_calm"]
    return out.sort_values("stress_minus_calm_momentum")


def invariants(ics: pd.DataFrame, horizon: int) -> pd.DataFrame:
    x = ics[ics["horizon"] == horizon].copy()
    s = np.sign(x[PER])
    x["same_sign_all_4"] = (s.nunique(axis=1) == 1) & x[PER].notna().all(axis=1)
    x["robust"] = x["same_sign_all_4"] & (x["t_all"].abs() > 2)
    piv = x.pivot(index="signal", columns="market", values="robust").fillna(False)
    sign = np.sign(x.pivot(index="signal", columns="market", values="ic_all"))
    out = pd.DataFrame({"markets_robust": piv.sum(axis=1), "of": piv.shape[1],
                        "robust_positive": ((piv) & (sign > 0)).sum(axis=1), "robust_negative": ((piv) & (sign < 0)).sum(axis=1)})
    return out.sort_values("markets_robust", ascending=False)


def data_quality(prices: Path) -> pd.DataFrame:
    rows = []
    for d in sorted(p for p in prices.iterdir() if p.is_dir() and not p.name.startswith("_")):
        adj = pd.read_parquet(d / "adj_close.parquet")
        r = adj.pct_change(fill_method=None)
        rows.append({"market": d.name, "stocks": adj.shape[1], "stocks_with_10y": int((adj.notna().sum() > 2520).sum()),
                     "days_abs_ret_gt_40pct": int((r.abs() > 0.4).sum().sum()),
                     "share_zero_return_days": float((r.abs() < 1e-12).sum().sum() / r.notna().sum().sum()),
                     "names_with_data_2006": int(adj.loc["2006"].notna().any().sum()) if (adj.index.year == 2006).any() else 0})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="reports/intl")
    ap.add_argument("--prices", default="data/prices")
    ap.add_argument("--out", default="reports/intl")
    args = ap.parse_args(argv)
    lab, out = Path(args.lab), Path(args.out)
    ics = pd.read_csv(lab / "signal_ic.csv")
    books = pd.read_csv(lab / "books.csv")
    sp = sign_pattern(ics)
    inv5, inv21 = invariants(ics, 5), invariants(ics, 21)
    dq = data_quality(Path(args.prices))
    sp.to_csv(out / "sign_pattern.csv")
    inv5.to_csv(out / "invariants_h5.csv")
    inv21.to_csv(out / "invariants_h21.csv")
    dq.to_csv(out / "data_quality.csv", index=False)
    cols = ["sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26"]
    wide = {}
    for b in ("momentum, never flipped (L/S)", "momentum flip VIX>20 (L/S)", "momentum flip, local-vol regime (L/S)",
              "long-only flip, minus market (hedged)", "long-only, never flipped, minus market"):
        wide[b] = books[books["book"] == b].set_index("market")[cols]
    side = pd.concat(wide, axis=1)
    side.to_csv(out / "books_side_by_side.csv")
    pd.set_option("display.width", 250)
    print("== sign pattern (21-day IC) =="); print(sp.round(4).to_string())
    print("\n== invariants, 21-day =="); print(inv21.to_string())
    print("\n== invariants, 5-day =="); print(inv5.to_string())
    print("\n== data quality =="); print(dq.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
