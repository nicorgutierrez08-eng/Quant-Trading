"""The intraday zoo's best model, trained for live trading.

The intraday model zoo (``qtrade.research.intraday_zoo``) ranks models by gross
edge, choosing on 2016-2020. This module takes its winner (model and horizon),
fits it once more on the latest ``train_months`` of 5-minute bars, and saves it
for the live trader:

    python -m qtrade.intraday.zoo_model --store data/intraday/5min --symbols 500 \
        --zoo-table intraday_zoo.csv --out model_zoo.joblib

The saved file holds the fitted model (a pickle, so only load files this
repository's own workflows wrote), the signal list, horizon, tickers and the
out-of-sample IC the zoo measured, which the live trader uses for sizing.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..research import intraday_zoo as Z
from ..utils import LOG
from .bars import DayBars
from .features import day_target, history

FORMAT = "qtrade-intraday-zoo/1"


class Ensemble:
    """Average of cross-sectionally z-scored forecasts (what the zoo's 'ensemble' trades)."""

    def __init__(self, members):
        self.members = members

    def predict_day(self, X, tod):
        preds = [predict_day(m, X, tod) for m in self.members]
        return np.nanmean(np.stack([Z._zcs(p) for p in preds]), axis=0)


def predict_day(model, X: np.ndarray, tod: np.ndarray) -> np.ndarray:
    """B x N forecasts from B x N x F signals and the B x N time-of-day grid."""
    if isinstance(model, Ensemble):
        return model.predict_day(X, tod)
    B, N, F = X.shape
    flat = X.reshape(-1, F)
    ok = np.isfinite(flat[:, 0])
    p = np.full(len(flat), np.nan)
    if ok.any():
        p[ok] = model.predict(flat[ok], tod.reshape(-1)[ok])
    return p.reshape(B, N)


def tod_grid(B: int, N: int) -> np.ndarray:
    return (np.arange(B)[:, None] / B * np.ones((1, N))).astype(np.float32)


def day_signals(bars: DayBars, hist, d: int) -> np.ndarray:
    prev = (bars.open[d - 1], bars.close[d - 1]) if d > 0 else (None, None)
    return Z.signals(bars.open[d], bars.close[d], bars.volume[d], bars.vwap[d], hist.prev_close[d],
                     hist.sigma[d], hist.vol_base[d], prev[0], prev[1])


def training_rows(bars: DayBars, h: int, days: np.ndarray, rows_per_day: int = 2500, vol_days: int = 20,
                  seed: int = 0):
    """Sampled (X, time of day, target) rows from the given days, as in the zoo's walk-forward."""
    hist = history(bars, vol_days)
    B, N = bars.n_bars, len(bars.tickers)
    grid = tod_grid(B, N)
    rng = np.random.default_rng(seed)
    Xs, Ts, Ys = [], [], []
    sl = slice(Z.START_BAR, B - 1)
    for d in days:
        X = day_signals(bars, hist, d)
        y = day_target(bars.open[d], bars.close[d], hist.sigma[d], h)
        x2, y2, t2 = X[sl].reshape(-1, X.shape[-1]), y[sl].reshape(-1), grid[sl].reshape(-1)
        ok = np.flatnonzero(np.isfinite(x2[:, 0]) & np.isfinite(y2))
        if len(ok):
            pick = rng.choice(ok, min(rows_per_day, len(ok)), replace=False)
            Xs.append(x2[pick]); Ts.append(t2[pick]); Ys.append(y2[pick].astype(np.float32))  # noqa: E702
    return np.concatenate(Xs), np.concatenate(Ts), np.concatenate(Ys)


def pick_winner(table: pd.DataFrame) -> dict:
    """The zoo's top row by 2016-2020 gross Sharpe (never by 2021-2026)."""
    t = table.dropna(subset=["gross_sharpe_2016_20"]).sort_values("gross_sharpe_2016_20", ascending=False)
    if t.empty:
        raise SystemExit("The intraday zoo table has no 2016-2020 results.")
    r = t.iloc[0]
    return {"model": r["model"], "horizon": r["horizon_bars"],
            "ic_oos": float(r.get("ic_2021_26", np.nan)), "gross_sharpe_2016_20": float(r["gross_sharpe_2016_20"]),
            "gross_sharpe_2021_26": float(r.get("gross_sharpe_2021_26", np.nan))}


def fit_winner(bars: DayBars, winner: dict, train_months: int = 12) -> dict:
    h = bars.n_bars if str(winner["horizon"]) == "close" else int(float(winner["horizon"]))
    months = bars.days.to_period("M")
    keep = months.unique()[-train_months:]
    days = np.flatnonzero(months.isin(keep))
    X, T, y = training_rows(bars, h, days)
    name = winner["model"]
    if name == "ensemble":
        facs = Z.make_models(["ridge_all", "gbm", "mlp"])
        model = Ensemble([facs[k]().fit(X, T, y) for k in ("ridge_all", "gbm", "mlp")])
    else:
        model = Z.make_models([name])[name]().fit(X, T, y)
    for m in (model.members if isinstance(model, Ensemble) else [model]):
        if hasattr(m, "make"):
            m.make = None                          # the factory lambda can't be pickled; the fit can
    LOG.info("trained %s (horizon %s) on %d rows from %s to %s", name, winner["horizon"], len(y),
             bars.days[days[0]].date(), bars.days[days[-1]].date())
    return {"format": FORMAT, "model_name": name, "model": model, "horizon": h, "signals": Z.SIGNALS,
            "tickers": list(bars.tickers), "trained_through": str(bars.days[-1].date()),
            "ic": winner.get("ic_oos", 0.02), "zoo": winner}


def load(path: str | Path) -> dict:
    bundle = joblib.load(path)
    if bundle.get("format") != FORMAT or bundle.get("signals") != Z.SIGNALS:
        raise SystemExit(f"{path} was made by a different version of the intraday zoo; retrain it.")
    return bundle


def main(argv=None):
    from ..utils import setup_logging
    from .bars import load_store

    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="data/intraday/5min")
    ap.add_argument("--symbols", type=int, default=500)
    ap.add_argument("--zoo-table", required=True, help="intraday_zoo.csv from the intraday-zoo workflow")
    ap.add_argument("--out", default="model_zoo.joblib")
    ap.add_argument("--train-months", type=int, default=12)
    args = ap.parse_args(argv)
    setup_logging()
    winner = pick_winner(pd.read_csv(args.zoo_table))
    LOG.info("zoo winner (chosen on 2016-2020): %s", winner)
    months_back = args.train_months + 2
    start = (pd.Timestamp.today() - pd.DateOffset(months=months_back)).strftime("%Y-%m-%d")
    bars = load_store(args.store, args.symbols, start)
    bundle = fit_winner(bars, winner, args.train_months)
    joblib.dump(bundle, args.out)
    meta = {k: v for k, v in bundle.items() if k not in ("model", "tickers")}
    Path(args.out).with_suffix(".json").write_text(pd.Series(meta).to_json(indent=2, default_handler=str))
    LOG.info("saved %s", args.out)


if __name__ == "__main__":
    main()
