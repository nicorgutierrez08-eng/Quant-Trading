"""Intraday model zoo: which model forecasts 5-minute returns best, before costs?

The goal is the largest *gross* edge, for a future with direct exchange access.
Costs never shape the models, but every result is also shown net of 0.5, 1 and
2.34 bp per unit traded (2.34 bp is today's measured Alpaca cost), because even
direct access pays spreads and fees.

For each forecast horizon (next 1, 3, 6, 12 bars, or to the close):

* inputs: 20 signals per stock and bar (reversals over 1-24 bars, distance
  from VWAP, gap, volume surprises, realised volatility so far, yesterday's
  move, interactions) plus the time of day, all from bars up to the decision;
* models: the production ridge (8 signals) as the baseline, ridge on all
  signals with time-of-day weights, t-stat-weighted signals, gradient boosting,
  a neural net, and an ensemble of the last three;
* walk-forward: refit at each month start on the previous 12 months;
* book: at each decision, long the top decile and short the bottom decile of
  the forecast (equal weight, gross 1), held for the horizon, flat by the close.

2016-2020 is the period to choose on, 2021-2026 the period to check.

    python -m qtrade.research.intraday_zoo --store data/intraday/5min --symbols 500 --horizon 6
    python -m qtrade.research.intraday_zoo --synthetic --horizon 3
    python -m qtrade.research.intraday_zoo --aggregate parts_dir --out reports/intraday_zoo
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from ..intraday.bars import DayBars
from ..intraday.features import (_cs_demean, _cs_z, _ffill_bars,
                                 day_target, exec_prices, history)
from ..utils import LOG

SPLIT = "2021-01-01"
START_BAR = 3                       # first decision at the close of bar 3 (9:50)
COSTS_BP = (0.5, 1.0, 2.34)
SIGNALS = ["rev_1", "rev_2", "rev_3", "rev_6", "rev_12", "rev_24", "day_ret", "gap", "vwap_dev",
           "abn_vol", "abn_vol_1", "vol_share", "rv_ratio", "rev3_lowvol", "rev1_x_vol", "rev3_x_mkt",
           "prev_day_ret", "prev_last30", "gap_x_day", "vwap_x_vol"]
TOD = "time_of_day"
MODELS = ["baseline_ridge", "ridge_all", "tstat_ic", "gbm", "mlp", "ensemble"]


# -----------------------------------------------------------------------------
# signals
# -----------------------------------------------------------------------------
def signals(open_, close, volume, vwap, prev_close, sigma, vol_base, prev_open, prev_close_bars):
    """B x N x len(SIGNALS) cross-sectional z-scores for one session (bars up to b only)."""
    B, N = close.shape
    px = _ffill_bars(close)
    anchor = np.where(np.isfinite(open_[0]), open_[0], prev_close)
    ext = np.vstack([anchor[None], px])
    b = np.arange(B)[:, None]
    sig = np.where(sigma > 0, sigma, np.nan)[None, :]
    valid = np.isfinite(px) & np.isfinite(sig) & np.isfinite(anchor)[None]

    def ret_k(k):
        lag = np.maximum(np.arange(B) + 1 - k, 0)
        return ext[1:] / ext[lag] - 1

    with np.errstate(invalid="ignore", divide="ignore"):
        f = {}
        for k in (1, 2, 3, 6, 12, 24):
            f[f"rev_{k}"] = -_cs_demean(ret_k(k)) / (sig * np.sqrt(np.minimum(k, b + 1)))
        f["day_ret"] = _cs_demean(px / anchor - 1) / (sig * np.sqrt(b + 1))
        gap = np.broadcast_to(anchor / prev_close - 1, (B, N))
        f["gap"] = -_cs_demean(np.where(valid, gap, np.nan)) / (sig * np.sqrt(6))
        vv = np.nan_to_num(volume)
        cv = np.cumsum(vv, axis=0)
        cum_vwap = np.cumsum(np.nan_to_num(vwap) * vv, axis=0) / np.where(cv > 0, cv, np.nan)
        f["vwap_dev"] = -_cs_demean(px / cum_vwap - 1) / (sig * np.sqrt(b + 1))
        bc = np.cumsum(np.nan_to_num(vol_base), axis=0)
        v3 = cv - np.vstack([np.zeros((3, N)), cv[:-3]])
        b3 = bc - np.vstack([np.zeros((3, N)), bc[:-3]])
        f["abn_vol"] = _cs_demean(np.log((v3 + 1) / (b3 + 1)))
        f["abn_vol_1"] = _cs_demean(np.log((vv + 1) / (np.nan_to_num(vol_base) + 1)))
        f["vol_share"] = _cs_demean(np.log((cv + 1) / (bc + 1)))
        lr = np.diff(np.log(ext), axis=0)
        rv = np.sqrt(np.nancumsum(lr ** 2, axis=0) / (b + 1))
        f["rv_ratio"] = _cs_demean(np.log(rv / sig))
        mkt3 = np.nanmean(ret_k(3), axis=1, keepdims=True)
        # previous session (NaN on the first day of the data)
        if prev_open is not None:
            pp = _ffill_bars(prev_close_bars)
            pday = pp[-1] / prev_open[0] - 1
            plast = pp[-1] / pp[-7] - 1
        else:
            pday = plast = np.full(N, np.nan)
        f["prev_day_ret"] = -_cs_demean(np.broadcast_to(pday, (B, N)).copy()) / (sig * np.sqrt(B))
        f["prev_last30"] = -_cs_demean(np.broadcast_to(plast, (B, N)).copy()) / (sig * np.sqrt(6))
        z = {k: _cs_z(np.where(valid, x, np.nan)) for k, x in f.items()}
        z["rev3_lowvol"] = _cs_z(z["rev_3"] * -np.tanh(np.nan_to_num(z["abn_vol"])))
        z["rev1_x_vol"] = _cs_z(z["rev_1"] * np.tanh(np.nan_to_num(z["abn_vol_1"])))
        z["rev3_x_mkt"] = _cs_z(z["rev_3"] * np.abs(mkt3) / (np.nanmean(sig) + 1e-12))
        z["gap_x_day"] = _cs_z(z["gap"] * np.nan_to_num(z["day_ret"]))
        z["vwap_x_vol"] = _cs_z(z["vwap_dev"] * np.tanh(np.nan_to_num(z["vol_share"])))
    X = np.stack([np.nan_to_num(z[k]) for k in SIGNALS], axis=-1).astype(np.float32)
    X[~valid] = np.nan
    return X


def raw_forward(open_, close, h: int) -> np.ndarray:
    """B x N relative return from the open of bar b+1 to the open of bar b+1+h (or the close)."""
    B = open_.shape[0]
    Qf, can = exec_prices(open_, close)
    k0 = np.arange(B) + 1
    k1 = np.minimum(k0 + h, B)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = Qf[k1] / Qf[k0] - 1
        r[~can[k0]] = np.nan
        r[k0 >= B] = np.nan
    return _cs_demean(np.clip(r, -0.2, 0.2))


# -----------------------------------------------------------------------------
# models
# -----------------------------------------------------------------------------
def _tod_expand(X, tod):
    """Each signal three times: active in the open, midday or close third of the session."""
    k = np.minimum((tod * 3).astype(int), 2)
    out = np.zeros((len(X), X.shape[1] * 3), dtype=np.float32)
    for j in range(3):
        m = k == j
        out[m, j * X.shape[1]:(j + 1) * X.shape[1]] = X[m]
    return out


class Ridge:
    def __init__(self, cols=None, alpha=1e-3):
        self.cols, self.alpha = cols, alpha

    def fit(self, X, tod, y):
        Z = _tod_expand(X if self.cols is None else X[:, self.cols], tod).astype(np.float64)
        n = len(y)
        self.coef = np.linalg.solve(Z.T @ Z + self.alpha * n * np.eye(Z.shape[1]), Z.T @ y)
        return self

    def predict(self, X, tod):
        return _tod_expand(X if self.cols is None else X[:, self.cols], tod) @ self.coef


class TstatIC:
    """Each signal weighted by the t-statistic of its correlation with the target."""

    def fit(self, X, tod, y):
        n = len(y)
        c = np.array([np.corrcoef(X[:, j], y)[0, 1] for j in range(X.shape[1])])
        self.w = np.nan_to_num(c * np.sqrt(n) / np.sqrt(np.maximum(1 - c ** 2, 1e-9)))
        self.w /= np.abs(self.w).sum() + 1e-12
        return self

    def predict(self, X, tod):
        return X @ self.w


class Sk:
    def __init__(self, make, cap):
        self.make, self.cap = make, cap

    def fit(self, X, tod, y):
        Z = np.column_stack([X, tod])
        if len(y) > self.cap:
            idx = np.random.default_rng(0).choice(len(y), self.cap, replace=False)
            Z, y = Z[idx], y[idx]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.m = self.make().fit(Z, y)
        return self

    def predict(self, X, tod):
        return self.m.predict(np.column_stack([X, tod]))


def make_models(names):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.neural_network import MLPRegressor

    prod_base = [SIGNALS.index(f) for f in ("rev_1", "rev_3", "rev_12", "day_ret", "gap", "vwap_dev",
                                            "abn_vol", "rev3_lowvol")]
    out = {}
    for n in names:
        if n == "baseline_ridge":
            out[n] = lambda: Ridge(prod_base)
        elif n == "ridge_all":
            out[n] = lambda: Ridge()
        elif n == "tstat_ic":
            out[n] = TstatIC
        elif n == "gbm":
            out[n] = lambda: Sk(lambda: HistGradientBoostingRegressor(
                max_leaf_nodes=31, max_iter=150, learning_rate=0.05, min_samples_leaf=2000,
                l2_regularization=1.0, max_bins=64, random_state=0), 300_000)
        elif n == "mlp":
            out[n] = lambda: Sk(lambda: MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3, max_iter=20,
                                                     early_stopping=True, random_state=0), 200_000)
    return out


def _zcs(p):
    """Cross-sectional z-score per bar (B x N)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return (p - np.nanmean(p, axis=1, keepdims=True)) / np.nanstd(p, axis=1, keepdims=True)


# -----------------------------------------------------------------------------
# evaluation of one day
# -----------------------------------------------------------------------------
def _day_ic(pred, r):
    """Mean over bars of the cross-sectional correlation between forecast and outcome."""
    ok = np.isfinite(pred) & np.isfinite(r)
    ics = []
    for b in range(pred.shape[0]):
        m = ok[b]
        if m.sum() > 20:
            ics.append(np.corrcoef(pred[b, m], r[b, m])[0, 1])
    return float(np.nanmean(ics)) if ics else np.nan


def _day_book(pred, open_, close, h, frac=0.1):
    """Gross return and turnover of the decile long/short book for one session."""
    B, N = pred.shape
    Qf, can = exec_prices(open_, close)
    w = np.zeros(N)
    gross = turn = 0.0
    hh = B if h >= B else h
    decisions = [START_BAR] if h >= B else list(range(START_BAR, B - 1, hh))
    for b in decisions:
        p = pred[b]
        ok = np.isfinite(p) & can[b + 1]
        new = np.zeros(N)
        if ok.sum() >= 20:
            k = max(int(ok.sum() * frac), 1)
            order = np.argsort(np.where(ok, p, np.nan))
            valid_idx = order[: ok.sum()]
            new[valid_idx[-k:]] = 0.5 / k
            new[valid_idx[:k]] = -0.5 / k
        turn += np.abs(new - w).sum()
        k1 = min(b + 1 + hh, B)
        with np.errstate(invalid="ignore", divide="ignore"):
            r = Qf[k1] / Qf[b + 1] - 1
        gross += float(np.nansum(new * np.clip(np.nan_to_num(r), -0.2, 0.2)))
        w = new
    turn += np.abs(w).sum()                        # flat by the close
    return gross, turn


# -----------------------------------------------------------------------------
# the walk-forward run for one horizon
# -----------------------------------------------------------------------------
def run_horizon(bars: DayBars, h: int, models: list[str], train_months: int = 12, min_months: int = 6,
                rows_per_day: int = 2500, vol_days: int = 20) -> pd.DataFrame:
    D, B, N = bars.close.shape
    hist = history(bars, vol_days)
    months = bars.days.to_period("M")
    uniq = list(months.unique())
    rng = np.random.default_rng(0)
    store: dict = {}                                # month -> (X, tod, y) training samples
    factories = make_models([m for m in models if m != "ensemble"])
    fitted: dict = {}
    rows = []
    tod_grid = (np.arange(B)[:, None] / B * np.ones((1, N))).astype(np.float32)
    cur_month = None
    for d in range(D):
        m = months[d]
        if m != cur_month:                           # month start: refit on the trailing months
            cur_month = m
            j = uniq.index(m)
            train = [store[p] for p in uniq[max(0, j - train_months):j] if p in store]
            fitted = {}
            if len(train) >= min_months:
                Xt = np.concatenate([t[0] for t in train])
                tt = np.concatenate([t[1] for t in train])
                yt = np.concatenate([t[2] for t in train])
                for name, make in factories.items():
                    try:
                        fitted[name] = make().fit(Xt, tt, yt)
                    except Exception as exc:
                        LOG.warning("%s fit failed in %s: %s", name, m, exc)
                LOG.info("h=%d %s: refit %d models on %d rows", h, m, len(fitted), len(yt))
        prev = (bars.open[d - 1], bars.close[d - 1]) if d > 0 else (None, None)
        X = signals(bars.open[d], bars.close[d], bars.volume[d], bars.vwap[d], hist.prev_close[d],
                    hist.sigma[d], hist.vol_base[d], prev[0], prev[1])
        y = day_target(bars.open[d], bars.close[d], hist.sigma[d], h)
        r = raw_forward(bars.open[d], bars.close[d], h)
        # training sample for later months
        sl = slice(START_BAR, B - 1)
        Xs = X[sl].reshape(-1, X.shape[-1])
        ys = y[sl].reshape(-1)
        ts = tod_grid[sl].reshape(-1)
        ok = np.flatnonzero(np.isfinite(Xs[:, 0]) & np.isfinite(ys))
        if len(ok):
            pick = rng.choice(ok, min(rows_per_day, len(ok)), replace=False)
            prev_s = store.get(m)
            new = (Xs[pick], ts[pick], ys[pick].astype(np.float32))
            store[m] = new if prev_s is None else tuple(np.concatenate([a, b]) for a, b in zip(prev_s, new))
        if not fitted:
            continue
        flat = X.reshape(-1, X.shape[-1])
        okf = np.isfinite(flat[:, 0])
        preds = {}
        for name, mdl in fitted.items():
            p = np.full(len(flat), np.nan)
            if okf.any():
                p[okf] = mdl.predict(flat[okf], tod_grid.reshape(-1)[okf])
            preds[name] = p.reshape(B, N)
        ens = [preds[k] for k in ("ridge_all", "gbm", "mlp") if k in preds]
        if "ensemble" in models and ens:
            preds["ensemble"] = np.nanmean(np.stack([_zcs(p) for p in ens]), axis=0)
        for name, p in preds.items():
            g, t = _day_book(p, bars.open[d], bars.close[d], h)
            rows.append({"date": bars.days[d], "model": name, "horizon": h, "ic": _day_ic(p, r),
                         "gross": g, "turnover": t})
    # free the samples
    store.clear()
    return pd.DataFrame(rows)


def summarize(daily: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (model, h), g in daily.groupby(["model", "horizon"]):
        row = {"model": model, "horizon_bars": "close" if h >= 78 else h}
        for tag, m in (("2016_20", g["date"] < SPLIT), ("2021_26", g["date"] >= SPLIT)):
            x = g[m]
            if len(x) < 20:
                continue
            row[f"ic_{tag}"] = x["ic"].mean()
            row[f"ic_t_{tag}"] = x["ic"].mean() / x["ic"].std() * np.sqrt(len(x))
            row[f"gross_bp_day_{tag}"] = x["gross"].mean() * 1e4
            row[f"gross_sharpe_{tag}"] = x["gross"].mean() / x["gross"].std() * np.sqrt(252)
            row[f"turnover_day_{tag}"] = x["turnover"].mean()
            row[f"breakeven_bp_{tag}"] = x["gross"].mean() / x["turnover"].mean() * 1e4
            for c in COSTS_BP:
                net = x["gross"] - x["turnover"] * c / 1e4
                row[f"net_sharpe_{c}bp_{tag}"] = net.mean() / net.std() * np.sqrt(252)
        out.append(row)
    tab = pd.DataFrame(out)
    if "gross_sharpe_2016_20" in tab:
        tab = tab.sort_values("gross_sharpe_2016_20", ascending=False)
    return tab


def aggregate(parts: Path, out: Path) -> pd.DataFrame:
    daily = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in sorted(parts.rglob("intraday_zoo_h*.csv"))])
    out.mkdir(parents=True, exist_ok=True)
    tab = summarize(daily)
    tab.to_csv(out / "intraday_zoo.csv", index=False)
    daily.to_csv(out / "intraday_zoo_daily.csv.gz", index=False)
    best = tab.iloc[0] if len(tab) else None
    cols = ["model", "horizon_bars", "ic_2016_20", "ic_2021_26", "gross_bp_day_2016_20", "gross_bp_day_2021_26",
            "gross_sharpe_2016_20", "gross_sharpe_2021_26", "breakeven_bp_2016_20", "breakeven_bp_2021_26",
            "turnover_day_2021_26", "net_sharpe_0.5bp_2021_26", "net_sharpe_1.0bp_2021_26",
            "net_sharpe_2.34bp_2021_26"]
    cols = [c for c in cols if c in tab]
    lines = ["# Intraday model zoo: the best gross edge", "",
             "Ranked by gross Sharpe in 2016-2020 (the period to choose on); 2021-2026 is the check. "
             "Decile long/short book, gross 1, flat by the close. Net columns subtract 0.5 / 1 / 2.34 bp "
             "per unit traded (2.34 bp = today's Alpaca cost).", "",
             tab[cols].round(3).to_markdown(index=False), ""]
    if best is not None:
        lines += [f"**Chosen on 2016-2020: {best['model']} at horizon {best['horizon_bars']}** - gross Sharpe "
                  f"{best.get('gross_sharpe_2016_20', np.nan):.2f} -> {best.get('gross_sharpe_2021_26', np.nan):.2f} "
                  f"in 2021-2026, break-even {best.get('breakeven_bp_2021_26', np.nan):.2f} bp.", ""]
    (out / "README.md").write_text("\n".join(lines) + "\n")
    return tab


def main(argv=None):
    from ..utils import setup_logging

    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="data/intraday/5min")
    ap.add_argument("--symbols", type=int, default=500)
    ap.add_argument("--start")
    ap.add_argument("--horizon", default="6", help="bars ahead, or 'close'")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--out", default="reports/intraday_zoo")
    ap.add_argument("--aggregate")
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    out = Path(args.out)
    if args.aggregate:
        print(aggregate(Path(args.aggregate), out).head(20).to_string())
        return
    if args.synthetic:
        from ..intraday.synthetic import make_intraday

        bars = make_intraday(n_stocks=80, n_days=520, seed=1)
        bars.days = pd.bdate_range("2019-06-03", periods=len(bars.days))
    else:
        from ..intraday.bars import load_store

        bars = load_store(args.store, args.symbols, args.start)
    h = bars.n_bars if args.horizon == "close" else int(args.horizon)
    daily = run_horizon(bars, h, args.models.split(","),
                        min_months=2 if args.synthetic else 6)
    out.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out / f"intraday_zoo_h{args.horizon}.csv", index=False)
    print(summarize(daily).round(3).to_string())


if __name__ == "__main__":
    main()
