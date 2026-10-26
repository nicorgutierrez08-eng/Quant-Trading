"""Is the new-exchange result real? Stress tests of the flat-in-stress book on the 20 new exchanges.

The pre-registered test passed with a 2015-26 Sharpe of 2.1 across 20
markets, high enough to distrust. This checks the obvious ways it could be
wrong:

* data quality: stale opens (open equal to the previous close), zero-volume
  days and bad prints, per market;
* implementability: only the 14 markets where single stocks can be borrowed
  (dropping Indonesia, Vietnam, Pakistan, Saudi Arabia, Kuwait, Qatar);
* liquidity: the liquid half of each market only, and costs x3;
* timing: execution one day later than the signal allows (stale-price or
  microstructure effects die with a delay; a 12-month momentum effect should
  not);
* where the money comes from: long leg vs short leg, each against the
  equal-weighted market, in calm periods (survivor selection on today's size
  makes shorting past losers look worse, not better);
* capacity: median daily traded value (USD) of the liquid half, and a rough
  gross capacity (10% of one day's traded value per name).

    python research_international/code/new_exchanges_robust.py --prices data2/prices_new --universe data2/universe_new_markets.csv \
        --macro data2/macro.parquet --out reports/new_exchanges
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L
from intl_more import equal_risk
from new_exchanges import load

NO_BORROW = ("Indonesia", "Vietnam", "Pakistan", "Saudi Arabia", "Kuwait", "Qatar")
CCY = {"Indonesia": "IDR", "Vietnam": "VND", "Pakistan": "PKR", "Brazil": "BRL", "Mexico": "MXN", "Chile": "CLP",
       "South Africa": "ZAR", "Turkey": "TRY", "Saudi Arabia": "SAR", "Kuwait": "KWD", "Qatar": "QAR", "Poland": "PLN",
       "Greece": "EUR", "Israel": "ILS", "Norway": "NOK", "Denmark": "DKK", "Finland": "EUR", "Belgium": "EUR",
       "Austria": "EUR", "Portugal": "EUR"}
# Yahoo quotes these exchanges in sub-units (ZA cents, agorot, fils): divide traded value to get the main unit
SUBUNIT = {"South Africa": 100, "Israel": 100, "Kuwait": 1000}


def quality(m: L.Market) -> dict:
    prev_close = m.close.shift(1)
    live = m.tradable
    stale_open = ((m.open - prev_close).abs() < 1e-9) & live
    return {"market": m.name, "share_stale_open": float(stale_open.sum().sum() / live.sum().sum()),
            "share_zero_volume": float(((m.volume == 0) & m.adj.notna()).sum().sum() / m.adj.notna().sum().sum()),
            "share_zero_return": float(((m.ret.abs() < 1e-12) & live).sum().sum() / live.sum().sum()),
            "median_tradable_2015_26": int(live.sum(axis=1)["2015":].median())}


def legs(m: L.Market, comp: pd.DataFrame, mask: pd.DataFrame, flat: pd.Series) -> dict:
    """Long and short legs of the flat-in-stress book, each measured against the equal-weighted market (gross)."""
    W = L.staggered(m, comp, mask, flat)
    ew = m.r1.where(mask).mean(axis=1)
    long_w, short_w = W.clip(lower=0), W.clip(upper=0)
    lw, sw = long_w.sum(axis=1), -short_w.sum(axis=1)
    return {"long_leg_vs_ew": (long_w * m.r1).sum(axis=1) - lw * ew,
            "short_leg_vs_ew": (short_w * m.r1).sum(axis=1) + sw * ew}          # positive = shorted names lagged the market


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--macro", required=True)
    ap.add_argument("--out", default="reports/new_exchanges")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    u = pd.read_csv(args.universe)
    vix = pd.read_parquet(Path(args.prices) / "_series" / "adj_close.parquet")["vol:US"].dropna()
    macro = pd.read_parquet(args.macro)
    markets = load(Path(args.prices), u, vix, dict.fromkeys(u["market"]))
    q, per, cap = [], {}, []
    for name, m in markets.items():
        q.append(quality(m))
        sigs = m.signals()
        comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
        flat = pd.Series(np.where(m.vix > 20, 0.0, 1.0), index=m.dates)
        liquid = m.tradable & (m.adv.where(m.tradable).rank(axis=1, pct=True) > 0.5)
        b = {}
        b["flat"] = L.pnl(L.staggered(m, comp, m.tradable, flat), m)["net"]
        b["flat_liquid_half"] = L.pnl(L.staggered(m, comp, liquid, flat), m)["net"]
        # one extra day between signal and trade: shift the signal and the regime by a day
        b["flat_one_day_late"] = L.pnl(L.staggered(m, comp.shift(1), m.tradable, flat.shift(1).fillna(1.0)), m)["net"]
        saved = m.cost
        m.cost = saved * 3
        b["flat_costs_x3"] = L.pnl(L.staggered(m, comp, m.tradable, flat), m)["net"]
        b["flat_liquid_half_costs_x3"] = L.pnl(L.staggered(m, comp, liquid, flat), m)["net"]
        m.cost = saved
        b.update(legs(m, comp, m.tradable, flat))
        per[name] = b
        fx = macro.get(f"fx:{CCY[name]}")
        adv_usd = (m.adv.where(liquid) / SUBUNIT.get(name, 1) / fx.reindex(m.dates, method="ffill").to_numpy()[:, None]) if fx is not None else None
        cap.append({"market": name,
                    "median_adv_usd_m_liquid_half_2021_26": float(adv_usd["2021":].median(axis=1).median() / 1e6) if adv_usd is not None else np.nan,
                    "names_liquid_half": int(liquid.sum(axis=1)["2015":].median())})
        # rough gross capacity: hold at most 10% of one day's traded value in each liquid-half name
        cap[-1]["rough_gross_capacity_usd_m"] = 0.10 * cap[-1]["median_adv_usd_m_liquid_half_2021_26"] * cap[-1]["names_liquid_half"]
    qt = pd.DataFrame(q).merge(pd.DataFrame(cap), on="market")
    qt.to_csv(out / "robust_quality_capacity.csv", index=False)

    rows = []
    sets = (("all 20", tuple(markets)), ("14 borrowable", tuple(k for k in markets if k not in NO_BORROW)),
            ("6 not borrowable", NO_BORROW))
    for sname, members in sets:
        for k in ("flat", "flat_liquid_half", "flat_one_day_late", "flat_costs_x3", "flat_liquid_half_costs_x3",
                  "long_leg_vs_ew", "short_leg_vs_ew"):
            R = pd.DataFrame({mk: per[mk][k] for mk in members if mk in per})
            rows.append(L.period_stats(equal_risk(R), f"{sname}: {k}", {"markets": R.shape[1]}))
    # per-market liquid-half table
    pm = pd.DataFrame([{"market": k, **{f"{c}_2015_26": L._sharpe(v[c]["2015":]) for c in ("flat", "flat_liquid_half", "flat_one_day_late", "flat_costs_x3")}}
                       for k, v in per.items()])
    pm.to_csv(out / "robust_per_market.csv", index=False)
    agg = pd.DataFrame(rows)
    agg.to_csv(out / "robust_cross_market.csv", index=False)
    pd.set_option("display.width", 250)
    print(qt.round(4).to_string(index=False))
    print(pm.round(2).to_string(index=False))
    cols = ["book", "sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26", "vol_2015_26", "maxdd_2015_26", "markets"]
    print(agg[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
