"""Which combinations of signals stick?

Every pair of signals is combined two ways:

  sum       z_a + s * z_b   (s = sign that made b useful alongside a in 2004-2014)
  product   z_a * z_b       (an interaction: e.g. reversal that is stronger on light volume)

and scored on how well it *sticks*:

  ic5_1st / ic5_2nd   5-day IC in 2004-2014 (where pairs are chosen) and 2015-2026
  years_positive      share of calendar years with a positive 5-day IC
  persistence         21-day IC / 1-day IC: near 1 = the edge lasts, near 0 = it fades fast
  gain                how much better the pair is than its better half alone (2nd period)

Pairs are ranked on 2004-2014 only. The report shows how the top-ranked pairs
did in 2015-2026 and how well first-period rank predicts second-period rank -
with ~2,000 pairs, many will look good in-sample by luck, and this shows how
much of the ranking survives. The top pairs are then scored on break-even cost.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, cs_rank_gauss
from .edge import SPLIT, Bench


def _daily_corr(z: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Cross-sectional Pearson correlation per day (rows), ignoring NaNs."""
    ok = np.isfinite(z) & np.isfinite(y)
    n = ok.sum(axis=1)
    zz = np.where(ok, z, 0.0)
    yy = np.where(ok, y, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        zm = zz.sum(axis=1, keepdims=True) / n[:, None]
        ym = yy.sum(axis=1, keepdims=True) / n[:, None]
        zc = np.where(ok, zz - zm, 0.0)
        yc = np.where(ok, yy - ym, 0.0)
        r = (zc * yc).sum(axis=1) / np.sqrt((zc ** 2).sum(axis=1) * (yc ** 2).sum(axis=1))
    r[n < 30] = np.nan
    return r


def _zs(x: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.nanmean(x, axis=1, keepdims=True)
        sd = np.nanstd(x, axis=1, keepdims=True)
        return np.clip((x - mu) / np.where(sd > 0, sd, np.nan), -4, 4)


def run(md, ctx, out: Path, sigs: dict[str, pd.DataFrame], families: dict[str, str], top: int = 25) -> dict:
    dates = md.dates
    o = md.open
    tr = ctx.tradable
    y = {h: cs_rank_gauss((o.shift(-(1 + h)) / o.shift(-1) - 1).where(tr)).to_numpy() for h in (1, 5, 21)}
    first = np.asarray((dates >= "2006-01-01") & (dates < SPLIT))
    years = np.asarray(dates.year)
    names = list(sigs)
    Z = {n: sigs[n].to_numpy(dtype=np.float32) for n in names}

    def stats(z: np.ndarray) -> dict:
        ic = {h: _daily_corr(z, y[h]) for h in (1, 5, 21)}
        i5 = ic[5]
        yr = pd.Series(i5).groupby(years).mean()
        res = {"ic5_1st": np.nanmean(i5[first]), "ic5_2nd": np.nanmean(i5[~first]),
               "years_positive": float((yr > 0).mean()),
               "persistence": np.nanmean(ic[21]) / np.nanmean(ic[1]) if np.nanmean(ic[1]) != 0 else np.nan}
        a = i5[first & np.isfinite(i5)]
        res["t5_1st"] = a.mean() / a.std() * np.sqrt(len(a) / 5) if len(a) > 50 else np.nan
        return res

    single = {}
    stab_rows = []
    parts_1st = np.array_split(np.nonzero(first)[0], 3)           # 2004-14 in three chunks
    for n in names:
        single[n] = stats(Z[n])
        i5 = _daily_corr(Z[n], y[5])
        means = [np.nanmean(i5[p]) for p in parts_1st]
        a = i5[first & np.isfinite(i5)]
        t1 = a.mean() / a.std() * np.sqrt(len(a) / 5) if len(a) > 50 else np.nan
        stable = len(set(np.sign(means))) == 1 and abs(t1) >= 2
        stab_rows.append({"signal": n, "family": families.get(n, ""), "ic5_part1": means[0], "ic5_part2": means[1],
                          "ic5_part3": means[2], "t_2004_14": t1, "kept_by_2004_14_rule": stable,
                          "ic5_2015_26": np.nanmean(i5[~first]),
                          "same_sign_2015_26": bool(np.sign(np.nanmean(i5[~first])) == np.sign(means[0]))})
    LOG.info("combos: %d single signals scored", len(names))
    stab = pd.DataFrame(stab_rows)
    stab.to_csv(out / "stability.csv", index=False)
    rows = []
    pairs = list(combinations(names, 2))
    for k, (a, b) in enumerate(pairs):
        sa = np.sign(single[a]["ic5_1st"]) or 1.0
        sb = np.sign(single[b]["ic5_1st"]) or 1.0
        for kind in ("sum", "product"):
            if kind == "sum":
                z = _zs(sa * Z[a] + sb * Z[b])
            else:
                z = _zs(Z[a] * Z[b])
                z = z * (np.sign(stats_sign(z, y[5], first)) or 1.0)
            st = stats(z)
            best_half = max(abs(single[a]["ic5_2nd"]), abs(single[b]["ic5_2nd"]))
            rows.append({"a": a, "b": b, "kind": kind, "family_a": families.get(a, ""),
                         "family_b": families.get(b, ""), **st, "gain_2nd": abs(st["ic5_2nd"]) - best_half})
        if (k + 1) % 100 == 0:
            LOG.info("combos: %d/%d pairs", k + 1, len(pairs))
    tab = pd.DataFrame(rows)
    sing = pd.DataFrame([{"signal": n, "family": families.get(n, ""), **v} for n, v in single.items()])
    tab.to_csv(out / "combos.csv", index=False)
    sing.to_csv(out / "combos_single.csv", index=False)

    # rank on the first period only; then see what survives
    tab["score_1st"] = tab["t5_1st"].abs()
    ranked = tab.sort_values("score_1st", ascending=False)
    rank_corr = ranked[["ic5_1st", "ic5_2nd"]].abs().corr(method="spearman").iloc[0, 1]
    sticky = tab[(np.sign(tab["ic5_1st"]) == np.sign(tab["ic5_2nd"])) & (tab["years_positive"] >= 0.8)
                 & (tab["gain_2nd"] > 0)].sort_values("ic5_2nd", key=np.abs, ascending=False)

    bench = Bench(md, ctx)
    scored = []
    for _, r in pd.concat([ranked.head(top), sticky.head(top)]).drop_duplicates(["a", "b", "kind"]).iterrows():
        sa = np.sign(single[r.a]["ic5_1st"]) or 1.0
        sb = np.sign(single[r.b]["ic5_1st"]) or 1.0
        if r.kind == "sum":
            z = _zs(sa * Z[r.a] + sb * Z[r.b])
        else:
            z = _zs(Z[r.a] * Z[r.b])
            z = z * (np.sign(r.ic5_1st) or 1.0)
        zf = pd.DataFrame(z, index=dates, columns=md.tickers)
        for hl in (0, 5, 20):
            st = bench.score(zf, hl, "all")
            scored.append({"a": r.a, "b": r.b, "kind": r.kind, "halflife": hl,
                           **{k: v for k, v in st.items() if k.startswith(("breakeven", "net_sharpe"))}})
    sc = pd.DataFrame(scored)
    sc.to_csv(out / "combos_costs.csv", index=False)

    cols = ["a", "b", "kind", "ic5_1st", "ic5_2nd", "years_positive", "persistence", "gain_2nd"]
    lines = ["## Signal combinations: which stick?", "",
             f"{len(pairs)} pairs x 2 ways (sum, product) = {len(tab)} combinations of {len(names)} signals.", "",
             f"How well does the 2004-2014 ranking predict 2015-2026? Rank correlation of |IC| between the "
             f"periods: **{rank_corr:.2f}** (1 = the ranking fully survives, 0 = it was luck).", "",
             "### Top pairs chosen on 2004-2014, and how they did afterwards", "",
             ranked.head(top)[cols].round(4).to_markdown(index=False), "",
             "### Pairs that stuck: same sign in both periods, positive IC in >= 80% of years, and better "
             "than either signal alone in 2015-2026", "",
             sticky.head(top)[cols].round(4).to_markdown(index=False) if len(sticky) else "(none)", "",
             "### Does consistency up to 2014 predict consistency after?", "",
             "Rule, using 2004-2014 only: IC of the same sign in each third of 2004-2014 and |t| >= 2. "
             "The model's `select_stable` option applies the same rule at every refit on its own training "
             "window.", "",
             f"Kept by the rule: {int(stab['kept_by_2004_14_rule'].sum())} of {len(stab)}. Of those, "
             f"{int(stab.loc[stab['kept_by_2004_14_rule'], 'same_sign_2015_26'].sum())} kept the same sign in "
             f"2015-2026; of the dropped ones, "
             f"{int(stab.loc[~stab['kept_by_2004_14_rule'], 'same_sign_2015_26'].sum())} of "
             f"{int((~stab['kept_by_2004_14_rule']).sum())} did.", "",
             stab.sort_values(["kept_by_2004_14_rule", "t_2004_14"], key=lambda c: c.abs() if c.dtype != bool else c,
                              ascending=False).round(4).to_markdown(index=False), "",
             "### Single signals for reference", "",
             sing.sort_values("ic5_1st", key=np.abs, ascending=False)[["signal", "family", "ic5_1st", "ic5_2nd",
                                                                       "years_positive", "persistence"]]
             .round(4).to_markdown(index=False), "",
             "### Break-even cost of the top and sticky pairs (bp per dollar traded)", "",
             sc.round(2).to_markdown(index=False) if len(sc) else "(none)", ""]
    (out / "combos.md").write_text("\n".join(lines) + "\n")
    return {"pairs": len(pairs), "rank_corr_1st_2nd": float(rank_corr), "sticky": int(len(sticky))}


def stats_sign(z: np.ndarray, y5: np.ndarray, first: np.ndarray) -> float:
    """Sign of a combination's first-period IC (chosen without looking at the second period)."""
    return float(np.nanmean(_daily_corr(z[first], y5[first])))
