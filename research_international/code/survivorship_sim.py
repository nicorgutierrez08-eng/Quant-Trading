"""How much momentum does "today's largest survivors" manufacture? A calibration by simulation.

The new-exchange universes are the 120 largest companies listed *today*.
Selecting on the end of the sample can create or destroy momentum by itself.
This simulates markets in which momentum is zero by construction and applies
the same selection and the same books:

* 600 stocks per market, 2000-2026 business days; half listed from the
  start, half listing on random dates; initial size lognormal;
* daily return = beta x market + idiosyncratic, both Student-t (df 4), with
  market volatility following the actual US VIX path and idiosyncratic
  volatility scaled by it (so stress periods are realistic);
* a stock is delisted (dies) once it has lost 90% from its peak;
* the universe is the 120 largest stocks *alive at the end* - exactly the
  screener construction - and the books (plain, flip, flat in stress) are run
  with intl_lab on that universe, gross of costs.

Also runs the same books on *all* simulated stocks with point-in-time
availability (each stock tradable while listed, dead stocks included), which
should show no momentum at all: the difference is the selection bias.

    python research_international/code/survivorship_sim.py --vix-from data2/prices_new/_series/adj_close.parquet --sims 24 --out reports/survivorship_sim
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import intl_lab as L

N, TOP, DIE = 600, 120, 0.10


def simulate(vix: pd.Series, seed: int) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    dates = vix.index
    T = len(dates)
    sv = (vix.to_numpy() / 100 / np.sqrt(252))
    t4 = lambda size: rng.standard_t(4, size=size) / np.sqrt(2.0)            # unit variance
    mkt = 0.0003 + sv * t4(T)
    beta = rng.uniform(0.6, 1.4, N)
    idio = rng.lognormal(np.log(0.018), 0.4, N)                                  # ~1.8%/day median at VIX 20
    eps = t4((T, N)) * idio[None, :] * (sv / sv.mean())[:, None] * 0.7
    r = np.clip(beta[None, :] * mkt[:, None] + eps, -0.5, 1.0)
    start = np.where(rng.random(N) < 0.5, 0, rng.integers(0, int(T * 0.85), N))
    logp = np.cumsum(np.log1p(r), axis=0)
    price = np.exp(logp - logp[np.maximum(start, 0), np.arange(N)][None, :]) * 10
    listed = np.arange(T)[:, None] >= start[None, :]
    price = np.where(listed, price, np.nan)
    # death: first day the price is 90% below its running peak since listing
    peak = np.fmax.accumulate(np.where(listed, price, -np.inf), axis=0)
    crossed = np.cumsum(listed & (price < DIE * peak), axis=0) > 0
    dead = np.vstack([np.zeros((1, N), bool), crossed[:-1]])      # the crash day itself is recorded (a delisting return)
    price = np.where(dead, np.nan, price)
    size0 = rng.lognormal(0, 1.2, N)
    alive_end = ~np.isnan(price[-1])
    cap_end = np.where(alive_end, size0 * price[-1] / 10, -np.inf)
    top = np.argsort(-cap_end)[:TOP]
    cols = [f"S{i}" for i in range(N)]
    P = pd.DataFrame(price, index=dates, columns=cols)
    return P, pd.Series(np.isin(np.arange(N), top), index=cols)


def write_market(P: pd.DataFrame, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    vol = pd.DataFrame(1e5, index=P.index, columns=P.columns).where(P.notna())
    for f in ("open", "high", "low", "close", "adj_close"):
        P.to_parquet(path / f"{f}.parquet")
    vol.to_parquet(path / "volume.parquet")


def gross_books(m: L.Market, mask: pd.DataFrame) -> dict[str, pd.Series]:
    sigs = m.signals()
    comp = sum(sigs[s] for s in L.MOM) / len(L.MOM)
    stress = m.vix > 20
    out = {}
    for name, sign in (("plain", None), ("flip", pd.Series(np.where(stress, -1.0, 1.0), index=m.dates)),
                       ("flat in stress", pd.Series(np.where(stress, 0.0, 1.0), index=m.dates))):
        out[name] = L.pnl(L.staggered(m, comp, mask, sign), m)["gross"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vix-from", required=True)
    ap.add_argument("--sims", type=int, default=24)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--out", default="reports/survivorship_sim")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vix = pd.read_parquet(args.vix_from)["vol:US"].dropna()
    vix = vix[vix.index >= "2000-01-01"]
    vix = vix.reindex(pd.bdate_range(vix.index[0], vix.index[-1])).ffill()
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for s in range(args.seed_start, args.seed_start + args.sims):
            P, top = simulate(vix, s)
            write_market(P, Path(tmp) / f"sim{s}")
            uni = pd.DataFrame({"ticker": P.columns, "financial": False})
            m = L.Market("simulated", Path(tmp) / f"sim{s}", uni, vix)
            in_top = pd.DataFrame(np.repeat(top.reindex(m.tickers).fillna(False).to_numpy()[None, :], len(m.dates), 0),
                                  index=m.dates, columns=m.tickers)
            for uni_label, mask in (("today's 120 largest survivors", m.tradable & in_top), ("all stocks, point in time", m.tradable)):
                for rule, g in gross_books(m, mask).items():
                    rows.append({"sim": s, "universe": uni_label, "rule": rule,
                                 **{f"sharpe_{t}": L._sharpe(g[a:b]) for t, a, b in L.PERIODS},
                                 "sharpe_2015_26": L._sharpe(g["2015":]), "ret_2015_26": float(g["2015":].mean() * 252)})
            print(f"sim {s}: survivors flat {rows[-4]['sharpe_2015_26']:.2f}  point-in-time flat {rows[-1]['sharpe_2015_26']:.2f}")
    R = pd.DataFrame(rows)
    R.to_csv(out / f"sims_{args.seed_start}.csv", index=False)
    R = pd.concat([pd.read_csv(f) for f in sorted(out.glob("sims_*.csv"))])
    # paired: survivor-universe Sharpe minus point-in-time Sharpe in the same simulated market
    w = R.pivot_table(index=["sim", "rule"], columns="universe", values="sharpe_2015_26")
    d = (w["today's 120 largest survivors"] - w["all stocks, point in time"]).groupby("rule").agg(["mean", "std", "count"])
    d["se"] = d["std"] / np.sqrt(d["count"])
    d.to_csv(out / "paired_bias.csv")
    print("bias = survivors minus point-in-time, 2015-26 Sharpe, per simulated market:")
    print(d.round(3).to_string())
    summ = R.groupby(["universe", "rule"])[["sharpe_2006_14", "sharpe_2015_20", "sharpe_2021_26", "sharpe_2015_26", "ret_2015_26"]].agg(["mean", "std"])
    summ.to_csv(out / "summary.csv")
    pd.set_option("display.width", 250)
    print(summ.round(3).to_string())


if __name__ == "__main__":
    main()
