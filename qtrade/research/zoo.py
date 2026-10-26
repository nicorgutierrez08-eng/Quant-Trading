"""A model zoo: hundreds of forecasting models on the same data, judged out of sample.

Every combination of

  model family  (34: simple weightings, linear GLMs, trees, neural nets, kernels,
                 PLS, Bayesian ridge, SVR, time-decayed / expanding / regime ridge, stacking)
  signal set    (4: reversal only, all price signals, + fundamentals, + news)
  horizon       (1, 5, 21 and 63 days)

is refit once a year on the previous five years and forecasts the next year.
Each forecast is then traded six ways (smoothing half-life 0 / 5 / 20 days x
all stocks / the 300 most liquid) with measured trading costs. Everything is
reported for 2006-2014 and 2015-2026 separately.

The work is split into groups of families so GitHub can run them in parallel
(``python -m qtrade.research.zoo --group tree --horizon 5``); ``aggregate``
merges the pieces, ranks on the first period only, and checks what survived.
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import LOG, cs_rank_gauss, setup_logging

SPLIT = "2015-01-01"
TRAIN_YEARS = 5
HALFLIVES = (0, 5, 20)
SURVIVORSHIP_PRONE = {"size_proxy", "amihud", "cs_spread", "turnover_trend", "low_vol", "idio_vol", "bab",
                      "max_effect"}


# -----------------------------------------------------------------------------
# simple models (fit on rows with a day index, so per-day ICs can be computed)
# -----------------------------------------------------------------------------
def _daily_ic(X: np.ndarray, y: np.ndarray, day: np.ndarray) -> np.ndarray:
    order = np.argsort(day, kind="stable")
    d, Xs, ys = day[order], X[order], y[order]
    starts = np.r_[0, np.flatnonzero(np.diff(d)) + 1]
    cnt = np.diff(np.r_[starts, len(d)])
    return np.add.reduceat(Xs * ys[:, None], starts, axis=0) / cnt[:, None]


class _Weights:
    needs_day = True

    def predict(self, X):
        return X @ self.w


class SignIC(_Weights):
    """+1/-1 on every signal whose training IC has |t| > 2, 0 otherwise."""

    def fit(self, X, y, day):
        ic = _daily_ic(X, y, day)
        t = ic.mean(0) / (ic.std(0) + 1e-12) * np.sqrt(len(ic))
        self.w = np.sign(ic.mean(0)) * (np.abs(t) > 2)
        return self


class TstatIC(_Weights):
    """Weights = information ratio, shrunk to 0 when the t-stat is small (Grinold)."""

    def fit(self, X, y, day):
        ic = _daily_ic(X, y, day)
        ir = ic.mean(0) / (ic.std(0) + 1e-12)
        t = ir * np.sqrt(len(ic))
        self.w = ir * np.clip(1 - 4 / np.maximum(t ** 2, 1e-9), 0, 1)
        return self


class BestSingle(_Weights):
    """Only the signal with the highest |t| in the training window."""

    def fit(self, X, y, day):
        ic = _daily_ic(X, y, day)
        t = ic.mean(0) / (ic.std(0) + 1e-12)
        self.w = np.zeros(X.shape[1])
        j = int(np.argmax(np.abs(t)))
        self.w[j] = np.sign(t[j])
        return self


class PCARidge:
    needs_day = False

    def __init__(self, k):
        self.k = k

    def fit(self, X, y, day=None):
        from sklearn.decomposition import PCA
        from sklearn.linear_model import Ridge

        self.p = PCA(n_components=min(self.k, X.shape[1])).fit(X)
        self.r = Ridge(alpha=10.0).fit(self.p.transform(X), y)
        return self

    def predict(self, X):
        return self.r.predict(self.p.transform(X))


class RFFRidge:
    """Random Fourier features + ridge: approximate Gaussian-kernel regression."""
    needs_day = False

    def __init__(self, D=256, seed=0, scale=1.0):
        self.D, self.rng, self.scale = D, np.random.default_rng(seed), scale

    def fit(self, X, y, day=None):
        from sklearn.linear_model import Ridge

        p = X.shape[1]
        self.W = self.rng.standard_normal((p, self.D)) / (np.sqrt(p) * self.scale)
        self.b = self.rng.uniform(0, 2 * np.pi, self.D)
        self.r = Ridge(alpha=10.0).fit(self._phi(X), y)
        return self

    def _phi(self, X):
        return np.hstack([np.sqrt(2 / self.D) * np.cos(X @ self.W + self.b), X])

    def predict(self, X):
        return self.r.predict(self._phi(X))


class DecayRidge:
    """Ridge with recent days weighted more (half-life one year): adapts to change."""
    needs_day = True

    def fit(self, X, y, day):
        from sklearn.linear_model import Ridge

        w = 0.5 ** ((day.max() - day) / 252)
        self.r = Ridge(alpha=100.0).fit(X, y, sample_weight=w)
        return self

    def predict(self, X):
        return self.r.predict(X)


class StackAvg:
    """Average of three different learners' standardized forecasts."""
    needs_day = False

    def fit(self, X, y, day=None):
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
        from sklearn.neural_network import MLPRegressor

        self.ms = [Ridge(alpha=100.0).fit(X, y),
                   HistGradientBoostingRegressor(max_leaf_nodes=8, max_iter=200, learning_rate=0.05,
                                                 min_samples_leaf=500, max_bins=64, random_state=0).fit(X, y),
                   MLPRegressor(hidden_layer_sizes=(16,), alpha=1e-3, max_iter=30, early_stopping=True,
                                random_state=0).fit(X, y)]
        self.sd = [np.std(m.predict(X[:20000])) + 1e-12 for m in self.ms]
        return self

    def predict(self, X):
        return sum(m.predict(X) / s for m, s in zip(self.ms, self.sd)) / len(self.ms)


class PLS:
    needs_day = False

    def __init__(self, k):
        self.k = k

    def fit(self, X, y, day=None):
        from sklearn.cross_decomposition import PLSRegression

        self.m = PLSRegression(n_components=self.k, scale=False).fit(X, y)
        return self

    def predict(self, X):
        return self.m.predict(X).ravel()


class LassoGBM:
    """Two stages: a lasso picks the signals that matter, boosting models only those."""
    needs_day = False

    def fit(self, X, y):
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Lasso

        coef = Lasso(alpha=1e-3, max_iter=2000).fit(X, y).coef_
        keep = np.flatnonzero(coef != 0)
        if len(keep) < 5:
            keep = np.argsort(-np.abs(coef))[:5]
        self.keep = np.sort(keep)
        self.m = HistGradientBoostingRegressor(max_leaf_nodes=8, max_iter=200, learning_rate=0.05,
                                               min_samples_leaf=500, l2_regularization=1.0, max_bins=64,
                                               random_state=0).fit(X[:, self.keep], y)
        return self

    def predict(self, X):
        return self.m.predict(X[:, self.keep])


# pairs of signals that kept working together in the combos study, fed to models as products
STICKY_PAIRS = [("mom_12_1", "high_52w"), ("rev_5d", "mom_12_1"), ("rev_21d", "resid_mom"),
                ("bollinger_z", "resid_mom"), ("rev_5d", "low_volume_rev"), ("resid_rev_1d", "abn_volume"),
                ("rev_5d", "idio_vol"), ("cluster_mom", "peer_gap"), ("mom_12_1", "low_vol"),
                ("rev_1d", "close_location")]


def pair_features(sigs: dict) -> dict[str, pd.DataFrame]:
    return {f"{a}*{b}": cs_rank_gauss(sigs[a] * sigs[b]) for a, b in STICKY_PAIRS if a in sigs and b in sigs}


def families() -> dict:
    """name -> (group, factory, target, row cap[, options]). Options: train_years
    (window override), regime (add signal x HMM-stress interactions)."""
    from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import BayesianRidge, ElasticNet, HuberRegressor, Lasso, LogisticRegression, Ridge
    from sklearn.svm import LinearSVR
    from sklearn.neural_network import MLPRegressor

    hgb = lambda leaves, it, lr: (lambda: HistGradientBoostingRegressor(  # noqa: E731
        max_leaf_nodes=leaves, max_iter=it, learning_rate=lr, min_samples_leaf=500, l2_regularization=1.0,
        max_bins=64, early_stopping=False, random_state=0))
    mlp = lambda h: (lambda: MLPRegressor(hidden_layer_sizes=h, alpha=1e-3, learning_rate_init=1e-3,  # noqa: E731
                                          max_iter=30, early_stopping=True, random_state=0))
    return {
        "sign_ic": ("simple", SignIC, "rank", None),
        "tstat_ic": ("simple", TstatIC, "rank", None),
        "best_single": ("simple", BestSingle, "rank", None),
        "pca5_ridge": ("simple", lambda: PCARidge(5), "rank", None),
        "pca15_ridge": ("simple", lambda: PCARidge(15), "rank", None),
        "ridge_1": ("linear", lambda: Ridge(alpha=1.0), "rank", None),
        "ridge_100": ("linear", lambda: Ridge(alpha=100.0), "rank", None),
        "ridge_1e4": ("linear", lambda: Ridge(alpha=1e4), "rank", None),
        "ridge_1e6": ("linear", lambda: Ridge(alpha=1e6), "rank", None),
        "elastic_net": ("linear", lambda: ElasticNet(alpha=2e-3, l1_ratio=0.5, max_iter=2000), "rank", 300_000),
        "lasso": ("linear", lambda: Lasso(alpha=1e-3, max_iter=2000), "rank", 300_000),
        "logistic_weak": ("linear", lambda: LogisticRegression(C=0.01, max_iter=500), "sign", None),
        "logistic": ("linear", lambda: LogisticRegression(C=1.0, max_iter=500), "sign", None),
        "huber": ("linear", lambda: HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=200), "raw", 150_000),
        "gbm_shallow": ("tree", hgb(8, 200, 0.05), "rank", 300_000),
        "gbm_deep": ("tree", hgb(31, 300, 0.05), "rank", 300_000),
        "extra_trees": ("tree", lambda: ExtraTreesRegressor(n_estimators=60, max_depth=8, min_samples_leaf=500,
                                                            max_features=0.5, n_jobs=-1, random_state=0),
                        "rank", 150_000),
        "mlp_16": ("nn", mlp((16,)), "rank", 300_000),
        "mlp_64": ("nn", mlp((64,)), "rank", 300_000),
        "mlp_64_32": ("nn", mlp((64, 32)), "rank", 300_000),
        "kernel_rff": ("nn", lambda: RFFRidge(256), "rank", 300_000),
        # second wave
        "random_forest": ("extra", lambda: RandomForestRegressor(n_estimators=60, max_depth=8, min_samples_leaf=500,
                                                                 max_features=0.33, max_samples=0.5, n_jobs=-1,
                                                                 random_state=0), "rank", 200_000),
        "gbm_l1": ("extra", lambda: HistGradientBoostingRegressor(loss="absolute_error", max_leaf_nodes=8, max_iter=200,
                                                                  learning_rate=0.05, min_samples_leaf=500, max_bins=64,
                                                                  random_state=0), "rank", 300_000),
        "gbm_early_stop": ("extra", lambda: HistGradientBoostingRegressor(max_leaf_nodes=31, max_iter=600,
                                                                          learning_rate=0.05, min_samples_leaf=500,
                                                                          max_bins=64, early_stopping=True,
                                                                          validation_fraction=0.2, n_iter_no_change=20,
                                                                          random_state=0), "rank", 300_000),
        "pls_3": ("extra", lambda: PLS(3), "rank", None),
        "pls_8": ("extra", lambda: PLS(8), "rank", None),
        "bayesian_ridge": ("extra", lambda: BayesianRidge(), "rank", None),
        "linear_svr": ("extra", lambda: LinearSVR(C=1e-3, epsilon=0.0, max_iter=5000, dual="auto"), "rank", 300_000),
        "rff_narrow": ("extra", lambda: RFFRidge(256, scale=0.5), "rank", 300_000),
        "rff_wide": ("extra", lambda: RFFRidge(256, scale=2.0), "rank", 300_000),
        "ridge_decay": ("extra", DecayRidge, "rank", None),
        "ridge_expanding": ("extra", lambda: Ridge(alpha=100.0), "rank", None, {"train_years": 99}),
        "regime_ridge": ("extra", lambda: Ridge(alpha=100.0), "rank", None, {"regime": True}),
        "stack_avg": ("extra", StackAvg, "rank", 300_000),
        # sequence models: learn from raw return / volume histories instead of hand-made signals
        "lag_ridge": ("seq", lambda: Ridge(alpha=100.0), "rank", None),
        "ridge_engineered": ("Interactions that stuck, as explicit inputs", "Pairs were picked using the whole sample (mild look-ahead)"),
    "gbm_engineered": ("Boosting with interactions and extra ideas", "More inputs, more ways to overfit"),
    "lasso_then_gbm": ("Lasso drops the noise, boosting finds the shape", "Selection is unstable between refits"),
    "lag_gbm": ("seq", hgb(15, 300, 0.05), "rank", 300_000),
        "lag_mlp": ("seq", mlp((64, 32)), "rank", 300_000),
        # other training targets (same inputs: the price signals)
        "ridge_resid_target": ("targets", lambda: Ridge(alpha=100.0), "resid", None),
        "gbm_resid_target": ("targets", hgb(8, 200, 0.05), "resid", 300_000),
        "ridge_volscaled_target": ("targets", lambda: Ridge(alpha=100.0), "volscaled", None),
        "gbm_volscaled_target": ("targets", hgb(8, 200, 0.05), "volscaled", 300_000),
        "logistic_decile_target": ("targets", lambda: LogisticRegression(C=0.05, max_iter=500), "decile", None),
        # engineered inputs: sticky pairs as products, the best ideas; lasso selection then boosting
        "ridge_engineered": ("features", lambda: Ridge(alpha=100.0), "rank", None),
        "gbm_engineered": ("features", hgb(8, 200, 0.05), "rank", 300_000),
        "lasso_then_gbm": ("features", LassoGBM, "rank", 300_000),
    }


PROS_CONS = {
    "sign_ic": ("Nothing to overfit; transparent", "Ignores how strong each signal is and their overlap"),
    "tstat_ic": ("Weights by proven reliability; robust (Grinold)", "Ignores correlation between signals: double-counts"),
    "best_single": ("Simplest possible; easy to monitor", "No diversification; chases last period's winner"),
    "pca5_ridge": ("Strips redundancy between signals", "First components follow variance, not predictive power"),
    "pca15_ridge": ("Keeps more detail than PCA-5", "Same issue; more components = more noise"),
    "ridge_1": ("Handles correlated signals jointly", "Nearly unpenalised: noisy weights"),
    "ridge_100": ("Balanced shrinkage", "Linear only"),
    "ridge_1e4": ("Heavy shrinkage, stable weights", "Can shrink away real edges"),
    "ridge_1e6": ("Close to an equal-weighted blend", "Barely learns anything"),
    "elastic_net": ("Drops useless signals", "Unstable choice among correlated signals"),
    "lasso": ("Sparse, interpretable", "Arbitrary pick between near-duplicates"),
    "logistic_weak": ("Only direction matters: robust to outliers", "Throws away magnitude"),
    "logistic": ("Direction model, less shrinkage", "Same; more overfitting"),
    "huber": ("Downweights extreme returns", "Slow; similar to ridge in practice"),
    "gbm_shallow": ("Finds interactions (e.g. reversal x low volume); robust", "Slower; harder to explain"),
    "gbm_deep": ("Captures complex interactions", "Overfits easily; slow"),
    "extra_trees": ("Averages many random trees: low variance", "Coarse; slow on big data"),
    "mlp_16": ("Smooth nonlinearity", "Random initialisation adds noise between refits"),
    "mlp_64": ("More capacity", "More noise and overfitting risk"),
    "mlp_64_32": ("Deepest network", "Least stable; needs more data than a few years give"),
    "kernel_rff": ("Nonlinear at linear cost", "Bandwidth chosen by rule of thumb, not tuned"),
    "random_forest": ("Bagging: low variance, hard to overfit", "Coarse step functions; slow"),
    "gbm_l1": ("Boosting that ignores outsized moves", "Loses information in large moves"),
    "gbm_early_stop": ("Picks its own complexity on held-out data", "Random validation split leaks across days"),
    "pls_3": ("Components chosen for predictive power, not variance", "Few components may miss edges"),
    "pls_8": ("More detail than PLS-3", "Closer to plain regression; more noise"),
    "bayesian_ridge": ("Learns its own penalty from the data", "Assumes Gaussian noise; linear"),
    "linear_svr": ("Margin-based loss: robust", "Sensitive to its C setting; linear"),
    "rff_narrow": ("Captures sharp nonlinear effects", "Overfits noise easily"),
    "rff_wide": ("Smooth nonlinearity, close to linear", "Little gain over ridge"),
    "ridge_decay": ("Adapts as signals strengthen or fade", "Noisier: effectively less data"),
    "ridge_expanding": ("Uses all history: most stable weights", "Slow to adapt to decaying signals"),
    "regime_ridge": ("Different weights in calm vs stressed markets", "Doubles parameters; HMM noise feeds in"),
    "stack_avg": ("Diversifies across model types", "Three times the cost; inherits each model's flaws"),
    "lag_ridge": ("Learns its own reversal/momentum weights from raw lags", "Linear in past returns"),
    "ridge_resid_target": ("Learns only the stock-specific part of returns (factor moves removed)", "Residuals are estimated, so noisier labels"),
    "gbm_resid_target": ("Nonlinear, on factor-neutral returns", "Same; slower"),
    "ridge_volscaled_target": ("Every stock's return in units of its own risk", "Down-weights big movers that may carry the edge"),
    "gbm_volscaled_target": ("Nonlinear, risk-scaled target", "Same"),
    "logistic_decile_target": ("Only learns what separates the extremes (top vs bottom 10%)", "Ignores the middle 80% of stocks"),
    "lag_gbm": ("Finds nonlinear patterns in raw histories", "Needs lots of data; easy to overfit"),
    "lag_mlp": ("Sequence model: no hand-made features at all", "Noisiest; random initialisation"),
    "online_weighted": ("Shifts weight to whichever model works lately", "Chases noise if ICs are noisy"),
    "equal_ensemble": ("Simple, robust blend of three model types", "Keeps weight on models that stopped working"),
    "disagreement_sized": ("Bets less when models disagree", "Disagreement may not mean lower accuracy"),
}


def signal_sets(core: list[str], families_of: dict, alt: dict) -> dict[str, list[str]]:
    rev = [n for n in core if families_of.get(n) == "mean_reversion"] + [n for n in ("peer_gap",) if n in core]
    fund = [k for k, v in alt.items() if v == "fundamental"]
    news = [k for k, v in alt.items() if v == "news"]
    sets = {"reversal": rev, "price": core}
    if fund:
        sets["price+fund"] = core + fund
    if news:
        sets["all"] = core + fund + news
    return sets


# -----------------------------------------------------------------------------
# running one group
# -----------------------------------------------------------------------------
def _load(cfg):
    from ..cli import _market
    from ..features.context import FeatureContext
    from ..signals import REGISTRY, compute_signals, normalize_signal
    from .alt_signals import load_alt

    md = _market(cfg)
    ctx = FeatureContext(md, cfg)
    sigs = compute_signals(ctx)
    fam = {n: REGISTRY[n].family for n in sigs}
    raw, afam = load_alt(md, ctx, cfg.data.cache_dir)
    for k, v in raw.items():
        sigs[k] = normalize_signal(v, ctx.tradable)
    return md, ctx, sigs, fam, afam


def _daily_corr(z, y):
    from .combos import _daily_corr as dc

    return dc(z, y)


def run_ideas(cfg, horizon: int, out: Path, synthetic: bool = False) -> pd.DataFrame:
    """Score every idea in qtrade/research/ideas.py at one horizon."""
    from ..features.context import FeatureContext
    from .edge import Bench
    from .ideas import compute_ideas

    if synthetic:
        from ..data import make_market

        md, _ = make_market(n_stocks=100, n_days=5800, seed=1, start="2003-01-02")
        cfg.universe.min_dollar_volume = 0
    else:
        from ..cli import _market

        md = _market(cfg)
    ctx = FeatureContext(md, cfg)
    sigs, themes = compute_ideas(md, ctx, cfg.data.cache_dir)
    o = md.open
    y = cs_rank_gauss((o.shift(-(1 + horizon)) / o.shift(-1) - 1).where(ctx.tradable)).to_numpy()
    first = np.asarray((md.dates >= "2006-01-01") & (md.dates < SPLIT))
    years = np.asarray(md.dates.year)
    bench = Bench(md, ctx)
    rows = []
    for n, z in sigs.items():
        ic = _daily_corr(z.to_numpy(dtype=np.float32), y)
        a, b = ic[first & np.isfinite(ic)], ic[~first & np.isfinite(ic)]
        row = {"kind": "signal", "name": n, "family": themes[n], "set": "", "horizon": horizon,
               "ic_1st": a.mean() if len(a) else np.nan, "ic_2nd": b.mean() if len(b) else np.nan,
               "t_1st": a.mean() / a.std() * np.sqrt(len(a) / horizon) if len(a) > 50 else np.nan,
               "t_2nd": b.mean() / b.std() * np.sqrt(len(b) / horizon) if len(b) > 50 else np.nan,
               "years_positive": float((pd.Series(ic).groupby(years).mean().dropna() > 0).mean())}
        # a split inside 2015-2026, for signals that only exist from 2015 (news)
        for lab, m in (("2015_20", (years >= 2015) & (years <= 2020)), ("2021_26", years >= 2021)):
            x = ic[m & np.isfinite(ic)]
            row[f"ic_{lab}"] = x.mean() if len(x) > 50 else np.nan
        # trade it in its own best direction as judged on 2006-2014 only
        sgn = np.sign(row["ic_1st"]) if np.isfinite(row["ic_1st"]) and row["ic_1st"] != 0 else 1.0
        best = None
        for hl in HALFLIVES:
            st = bench.score(z * sgn, hl, "all")
            if best is None or st["breakeven_bp_1st"] > best[1]["breakeven_bp_1st"]:
                best = (hl, st)
        row |= {"best_halflife_1st": best[0], "breakeven_bp_1st": best[1]["breakeven_bp_1st"],
                "breakeven_bp_2nd": best[1]["breakeven_bp_2nd"], "net_sharpe_1st": best[1]["net_sharpe_1st"],
                "net_sharpe_2nd": best[1]["net_sharpe_2nd"]}
        rows.append(row)
        LOG.info("idea %-18s h=%d IC %.4f / %.4f", n, horizon, row["ic_1st"], row["ic_2nd"])
    df = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"zoo_ideas_h{horizon}.csv", index=False)
    return df


def lag_features(ctx, md) -> dict[str, pd.DataFrame]:
    """Raw histories, each scaled cross-sectionally: the last 20 daily factor-residual
    returns (in units of the stock's vol), the last 10 daily volume changes, and the
    last 12 monthly returns."""
    from ..signals import normalize_signal

    e = ctx.resid
    sd = e.rolling(63, min_periods=40).std()
    z = e / sd
    lv = np.log(md.volume.replace(0, np.nan)).diff()
    m = ctx.log_ret.rolling(21, min_periods=15).sum()
    out = {}
    for k in range(20):
        out[f"lag_resid_{k + 1}d"] = normalize_signal(z.shift(k), ctx.tradable)
    for k in range(10):
        out[f"lag_volchg_{k + 1}d"] = normalize_signal(lv.shift(k), ctx.tradable)
    for k in range(12):
        out[f"lag_month_{k + 1}"] = normalize_signal(m.shift(21 * k), ctx.tradable)
    return out


def run_online(md, ctx, sigs, names, horizon, y_rank, y5, first, years, bench, cfg) -> list[dict]:
    """Three different learners, then three ways to combine them: equal weights,
    weights that follow each model's recent out-of-sample IC, and an equal blend
    whose size shrinks when the models disagree."""
    fam = families()
    members = ["ridge_100", "gbm_shallow", "mlp_16"]
    X = np.stack([sigs[n].to_numpy(dtype=np.float32) for n in names], axis=-1)
    dates = md.dates
    yrs = sorted(set(years))
    step = max(5, horizon)
    rng = np.random.default_rng(0)
    preds = {}
    for mname in members:
        _, make, target, cap = fam[mname][:4]
        P = np.full(X.shape[:2], np.nan, dtype=np.float32)
        for yr in [y for y in yrs if y >= yrs[0] + TRAIN_YEARS + 1]:
            first_day = int(np.argmax(years == yr))
            lo = int(np.argmax(years >= yr - TRAIN_YEARS))
            tr_days = np.arange(lo, first_day - horizon - 2, step)
            te_days = np.flatnonzero(years == yr)
            Xt = X[tr_days].reshape(-1, len(names))
            yt = y_rank[tr_days].ravel()
            ok = np.flatnonzero(np.isfinite(Xt).all(axis=1) & np.isfinite(yt))
            if len(ok) < 1000:
                continue
            if cap and len(ok) > cap:
                ok = np.sort(rng.choice(ok, cap, replace=False))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = make().fit(Xt[ok], yt[ok])
            Xe = X[te_days].reshape(-1, len(names))
            oke = np.isfinite(Xe).all(axis=1)
            p = np.full(len(Xe), np.nan)
            p[oke] = m.predict(Xe[oke])
            P[te_days] = p.reshape(len(te_days), -1)
        with np.errstate(invalid="ignore", divide="ignore"):
            P = (P - np.nanmean(P, axis=1, keepdims=True)) / np.nanstd(P, axis=1, keepdims=True)
        preds[mname] = P
        LOG.info("online: member %s done", mname)
    Z = np.stack([preds[m] for m in members])                               # M x T x N
    ics = np.stack([_daily_corr(preds[m], y_rank) for m in members])        # M x T
    # weights at day t use ICs whose labels were known: up to t - horizon - 1, trailing 63 days
    ic_df = pd.DataFrame(ics.T).shift(horizon + 1).rolling(63, min_periods=20).mean()
    w = ic_df.clip(lower=0).to_numpy()
    w = np.where(w.sum(axis=1, keepdims=True) > 0, w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12), 1 / len(members))
    combos = {
        "equal_ensemble": np.nanmean(Z, axis=0),
        "online_weighted": np.nansum(Z * w.T[:, :, None], axis=0),
    }
    disagree = np.nanstd(Z, axis=0)
    combos["disagreement_sized"] = combos["equal_ensemble"] / (1.0 + disagree)
    rows = []
    for name, P in combos.items():
        P = P.astype(np.float32)
        ic_h, ic5 = _daily_corr(P, y_rank), _daily_corr(P, y5)
        base = {"kind": "model", "name": name, "family": "online", "set": "price", "horizon": horizon}
        stats = {}
        for tag, ic in (("", ic_h), ("5d_", ic5)):
            a, b = ic[first & np.isfinite(ic)], ic[~first & np.isfinite(ic)]
            hh = horizon if tag == "" else 5
            stats |= {f"{tag}ic_1st": a.mean() if len(a) else np.nan, f"{tag}ic_2nd": b.mean() if len(b) else np.nan,
                      f"{tag}t_1st": a.mean() / a.std() * np.sqrt(len(a) / hh) if len(a) > 50 else np.nan,
                      f"{tag}t_2nd": b.mean() / b.std() * np.sqrt(len(b) / hh) if len(b) > 50 else np.nan}
        stats["years_positive"] = float((pd.Series(ic_h).groupby(years).mean().dropna() > 0).mean())
        Pz = pd.DataFrame(P, index=dates, columns=md.tickers)
        for hl in HALFLIVES:
            for uni in ("all", "top300"):
                rows.append(base | stats | {"halflife": hl, "universe": uni, **bench.score(Pz, hl, uni)})
        LOG.info("online %s h=%d: IC %.4f / %.4f", name, horizon, stats["ic_1st"], stats["ic_2nd"])
    return rows


def run_group(cfg, group: str, horizon: int, out: Path, synthetic: bool = False) -> pd.DataFrame:
    from .edge import Bench

    if group == "ideas":
        return run_ideas(cfg, horizon, out, synthetic)

    if synthetic:
        from ..data import make_market
        from ..features.context import FeatureContext
        from ..signals import REGISTRY, compute_signals

        md, _ = make_market(n_stocks=100, n_days=5800, seed=1, start="2003-01-02")
        cfg.universe.min_dollar_volume = 0
        ctx = FeatureContext(md, cfg)
        sigs = compute_signals(ctx)
        fam, afam = {n: REGISTRY[n].family for n in sigs}, {}
    else:
        md, ctx, sigs, fam, afam = _load(cfg)
    dates = md.dates
    o = md.open
    tr = ctx.tradable
    fwd = (o.shift(-(1 + horizon)) / o.shift(-1) - 1).where(tr).clip(-0.5, 0.5)
    y_rank = cs_rank_gauss(fwd).to_numpy()
    y_raw = fwd.sub(fwd.mean(axis=1), axis=0).to_numpy()
    y_sign = np.where(np.isfinite(y_rank), (y_rank > 0).astype(float), np.nan)
    y_extra = {}
    if group == "targets":
        # factor-residual forward return: sum of the next h days' PCA residuals
        res = ctx.resid
        y_extra["resid"] = cs_rank_gauss(res[::-1].rolling(horizon, min_periods=1).sum()[::-1]
                                         .shift(-2).where(tr)).to_numpy()
        vol = ctx.vol_63.where(ctx.vol_63 > 0)
        y_extra["volscaled"] = (fwd / vol).sub((fwd / vol).mean(axis=1), axis=0).clip(-10, 10).to_numpy()
        pct = fwd.rank(axis=1, pct=True)
        dec = np.where(pct >= 0.9, 1.0, np.where(pct <= 0.1, 0.0, np.nan))
        y_extra["decile"] = np.where(fwd.notna().to_numpy(), dec, np.nan)
    y5 = cs_rank_gauss((o.shift(-6) / o.shift(-1) - 1).where(tr)).to_numpy() if horizon != 5 else y_rank
    first = np.asarray((dates >= "2006-01-01") & (dates < SPLIT))
    years = np.asarray(dates.year)
    bench = Bench(md, ctx)
    core = [n for n in sigs if n in fam]
    sets = signal_sets(core, fam, afam)
    if group in ("seq", "online"):
        lags = lag_features(ctx, md)
        sigs = {**sigs, **lags}
        sets = {"lags": list(lags), "lags+price": list(lags) + core} if group == "seq" else {"price": core}
    if group == "features":
        pf = pair_features(sigs)
        from .ideas import compute_ideas

        ideas, _ = compute_ideas(md, ctx, cfg.data.cache_dir)
        # the 20 ideas with the strongest 2006-2014 IC at this horizon (period 2 never used)
        t1 = {}
        for n, z in ideas.items():
            ic = _daily_corr(z.to_numpy(dtype=np.float32), y_rank)[first]
            ic = ic[np.isfinite(ic)]
            if len(ic) > 250:
                t1[n] = abs(ic.mean() / ic.std())
        top = sorted(t1, key=t1.get, reverse=True)[:20]
        sigs = {**sigs, **pf, **{f"idea:{n}": ideas[n] for n in top}}
        sets = {"price+pairs": core + list(pf), "price+pairs+ideas": core + list(pf) + [f"idea:{n}" for n in top]}
        LOG.info("features: %d pair products, ideas %s", len(pf), top)
    if group == "online":
        rows = run_online(md, ctx, sigs, sets["price"], horizon, y_rank, y5, first, years, bench, cfg)
        df = pd.DataFrame(rows)
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / f"zoo_{group}_h{horizon}.csv", index=False)
        return df
    fams = {k: v for k, v in families().items() if v[0] == group}
    p_stress = None
    if any(len(v) > 4 and v[4].get("regime") for v in fams.values()):
        from ..models.regime import walk_forward_regimes

        probs, fits = walk_forward_regimes(ctx.market_state, 3, 252, 756, 3, 200, 0, temper=0.5, align=True)
        hi = int(np.argmax([np.trace(c) for c in fits[-1][1].covars_]))
        p_stress = probs.iloc[:, hi].reindex(dates).fillna(1 / 3).to_numpy(dtype=np.float32)
    step = max(5, horizon)
    rows, samples = [], {}
    rng = np.random.default_rng(0)
    yrs = sorted(set(years))
    start_year = yrs[0] + TRAIN_YEARS + 1

    if group == "simple":                          # single signals at this horizon, for the correlations file
        for n, z in sigs.items():
            ic = _daily_corr(z.to_numpy(dtype=np.float32), y_rank)
            a, b = ic[first & np.isfinite(ic)], ic[~first & np.isfinite(ic)]
            rows.append({"kind": "signal", "name": n, "family": fam.get(n, afam.get(n, "")), "set": "",
                         "horizon": horizon, "ic_1st": a.mean(), "ic_2nd": b.mean(),
                         "t_1st": a.mean() / a.std() * np.sqrt(len(a) / horizon) if len(a) > 50 else np.nan,
                         "t_2nd": b.mean() / b.std() * np.sqrt(len(b) / horizon) if len(b) > 50 else np.nan,
                         "years_positive": float((pd.Series(ic).groupby(years).mean().dropna() > 0).mean())})

    for sname, names in sets.items():
        X = np.stack([sigs[n].to_numpy(dtype=np.float32) for n in names], axis=-1)
        for fname, spec in fams.items():
            _, make, target, cap = spec[:4]
            opts = spec[4] if len(spec) > 4 else {}
            Xf = np.concatenate([X, X * p_stress[:, None, None]], axis=-1) if opts.get("regime") else X
            nf = Xf.shape[-1]
            P = np.full(X.shape[:2], np.nan, dtype=np.float32)
            for yr in [y for y in yrs if y >= start_year]:
                first_day = int(np.argmax(years == yr))
                lo = int(np.argmax(years >= yr - opts.get("train_years", TRAIN_YEARS)))
                tr_days = np.arange(lo, first_day - horizon - 2, step)
                te_days = np.flatnonzero(years == yr)
                Xt = Xf[tr_days].reshape(-1, nf)
                yt = ({"rank": y_rank, "raw": y_raw, "sign": y_sign} | y_extra)[target][tr_days].ravel()
                dt = np.repeat(tr_days, X.shape[1])
                ok = np.flatnonzero(np.isfinite(Xt).all(axis=1) & np.isfinite(yt))
                if len(ok) < 1000:
                    continue
                if cap and len(ok) > cap:
                    ok = np.sort(rng.choice(ok, cap, replace=False))
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = make()
                    m = m.fit(Xt[ok], yt[ok], dt[ok]) if getattr(m, "needs_day", False) else m.fit(Xt[ok], yt[ok])
                Xe = Xf[te_days].reshape(-1, nf)
                oke = np.isfinite(Xe).all(axis=1)
                p = np.full(len(Xe), np.nan)
                if oke.any():
                    p[oke] = (m.predict_proba(Xe[oke])[:, 1] if target in ("sign", "decile")
                              else m.predict(Xe[oke]))
                P[te_days] = p.reshape(len(te_days), -1)
            ic_h = _daily_corr(P, y_rank)
            ic5 = _daily_corr(P, y5)
            base = {"kind": "model", "name": fname, "family": group, "set": sname, "horizon": horizon}
            stats = {}
            for tag, ic in (("", ic_h), ("5d_", ic5)):
                a, b = ic[first & np.isfinite(ic)], ic[~first & np.isfinite(ic)]
                hh = horizon if tag == "" else 5
                stats |= {f"{tag}ic_1st": a.mean() if len(a) else np.nan, f"{tag}ic_2nd": b.mean() if len(b) else np.nan,
                          f"{tag}t_1st": a.mean() / a.std() * np.sqrt(len(a) / hh) if len(a) > 50 else np.nan,
                          f"{tag}t_2nd": b.mean() / b.std() * np.sqrt(len(b) / hh) if len(b) > 50 else np.nan}
            stats["years_positive"] = float((pd.Series(ic_h).groupby(years).mean().dropna() > 0).mean())
            Pz = pd.DataFrame(P, index=dates, columns=md.tickers)
            for hl in HALFLIVES:
                for uni in ("all", "top300"):
                    st = bench.score(Pz, hl, uni)
                    rows.append(base | stats | {"halflife": hl, "universe": uni, **st})
            samples[f"{fname}|{sname}|h{horizon}"] = P[::21].ravel()
            LOG.info("zoo %s/%s h=%d: IC %.4f / %.4f", fname, sname, horizon, stats["ic_1st"], stats["ic_2nd"])
    df = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"zoo_{group}_h{horizon}.csv", index=False)
    pd.DataFrame(samples).to_parquet(out / f"zoo_preds_{group}_h{horizon}.parquet")
    # the targets at the same sampled days, for ensembles in the aggregate step
    pd.DataFrame({"y": y_rank[::21].ravel(), "day": np.repeat(np.arange(0, len(dates), 21), y_rank.shape[1]),
                  "first": np.repeat(first[::21], y_rank.shape[1])}).to_parquet(out / f"zoo_target_h{horizon}.parquet")
    return df


# -----------------------------------------------------------------------------
# aggregation
# -----------------------------------------------------------------------------
def _expected_max_sharpe(sharpes: np.ndarray) -> float:
    """Expected best Sharpe among N strategies with no skill (Bailey & Lopez de Prado)."""
    from scipy.stats import norm

    s = sharpes[np.isfinite(sharpes)]
    n = len(s)
    if n < 2:
        return np.nan
    g = 0.5772156649
    return float(np.std(s) * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * np.e))))


def aggregate(in_dir: Path, out: Path, extra_dir: Path | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    parts = [pd.read_csv(p) for p in sorted(in_dir.rglob("zoo_*_h*.csv"), key=lambda p: p.stat().st_mtime)]
    if not parts:
        raise SystemExit(f"no zoo results under {in_dir}")
    allr = pd.concat(parts, ignore_index=True)
    allr = allr.drop_duplicates([c for c in ("kind", "name", "set", "horizon", "halflife", "universe")
                                 if c in allr.columns], keep="last")
    sig = allr[allr["kind"] == "signal"].drop_duplicates(["name", "horizon"])
    mod = allr[allr["kind"] == "model"].copy()
    mod["strategy"] = (mod["name"] + " | " + mod["set"] + " | h" + mod["horizon"].astype(str) + " | hl"
                       + mod["halflife"].astype(str) + " | " + mod["universe"])
    mod.to_csv(out / "zoo_all_strategies.csv", index=False)
    n = len(mod)

    # selection on the first period only
    mod["rank_1st"] = mod["net_sharpe_1st"].rank(ascending=False)
    rank_corr = mod[["net_sharpe_1st", "net_sharpe_2nd"]].corr(method="spearman").iloc[0, 1]
    ic_corr = mod.drop_duplicates(["name", "set", "horizon"])[["ic_1st", "ic_2nd"]].corr(method="spearman").iloc[0, 1]
    top = mod.sort_values("net_sharpe_1st", ascending=False)
    sel = {}
    for k in (1, 10, 50):
        sel[k] = {"net_sharpe_1st": top.head(k)["net_sharpe_1st"].mean(),
                  "net_sharpe_2nd": top.head(k)["net_sharpe_2nd"].mean()}
    hurdle_1st = _expected_max_sharpe(mod["net_sharpe_1st"].to_numpy())

    # robust: good in both periods (still reported with the multiple-testing hurdle)
    robust = mod[(mod["net_sharpe_1st"] > 0) & (mod["net_sharpe_2nd"] > 0)].copy()
    robust["min_sharpe"] = robust[["net_sharpe_1st", "net_sharpe_2nd"]].min(axis=1)
    robust = robust.sort_values("min_sharpe", ascending=False)

    by_family = mod.groupby("name").agg(
        ic_1st=("ic_1st", "mean"), ic_2nd=("ic_2nd", "mean"), net_sharpe_2nd_best=("net_sharpe_2nd", "max"),
        net_sharpe_2nd_median=("net_sharpe_2nd", "median"), breakeven_2nd_median=("breakeven_bp_2nd", "median"),
        years_positive=("years_positive", "mean")).sort_values("ic_2nd", ascending=False)
    by_family["pros"] = [PROS_CONS.get(k, ("", ""))[0] for k in by_family.index]
    by_family["cons"] = [PROS_CONS.get(k, ("", ""))[1] for k in by_family.index]
    by_set = mod.groupby("set")[["ic_1st", "ic_2nd", "net_sharpe_2nd"]].median()
    by_h = mod.groupby("horizon")[["ic_1st", "ic_2nd", "net_sharpe_1st", "net_sharpe_2nd", "turnover_2nd"]].median()
    by_trade = mod.groupby(["halflife", "universe"])[["net_sharpe_1st", "net_sharpe_2nd", "breakeven_bp_2nd"]].median()

    # ensemble of the 10 best models chosen on the first period (IC on sampled days)
    ens = _ensemble(in_dir, mod)

    # the correlations file
    rows = []
    for _, r in sig.iterrows():
        rows.append({"what": "signal", "name": r["name"], "family": r["family"], "horizon_days": r["horizon"],
                     "ic_2006_14": r["ic_1st"], "ic_2015_26": r["ic_2nd"], "t_2006_14": r["t_1st"],
                     "t_2015_26": r["t_2nd"], "years_positive": r["years_positive"],
                     "breakeven_bp_2006_14": r.get("breakeven_bp_1st", np.nan),
                     "breakeven_bp_2015_26": r.get("breakeven_bp_2nd", np.nan),
                     "net_sharpe_2006_14": r.get("net_sharpe_1st", np.nan),
                     "net_sharpe_2015_26": r.get("net_sharpe_2nd", np.nan),
                     "ic_2015_20": r.get("ic_2015_20", np.nan), "ic_2021_26": r.get("ic_2021_26", np.nan)})
    best_trade = mod.sort_values("net_sharpe_1st", ascending=False).drop_duplicates(["name", "set", "horizon"])
    for _, r in best_trade.iterrows():
        rows.append({"what": "model", "name": f"{r['name']} on {r['set']}", "family": r["family"],
                     "horizon_days": r["horizon"], "ic_2006_14": r["ic_1st"], "ic_2015_26": r["ic_2nd"],
                     "t_2006_14": r["t_1st"], "t_2015_26": r["t_2nd"], "years_positive": r["years_positive"],
                     "breakeven_bp_2006_14": r["breakeven_bp_1st"], "breakeven_bp_2015_26": r["breakeven_bp_2nd"],
                     "net_sharpe_2006_14": r["net_sharpe_1st"], "net_sharpe_2015_26": r["net_sharpe_2nd"]})
    if extra_dir is not None and (extra_dir / "combos.csv").exists():
        cb = pd.read_csv(extra_dir / "combos.csv")
        for _, r in cb.iterrows():
            rows.append({"what": "pair", "name": f"{r['a']} {'+' if r['kind'] == 'sum' else 'x'} {r['b']}",
                         "family": f"{r.get('family_a', '')}/{r.get('family_b', '')}", "horizon_days": 5,
                         "ic_2006_14": r["ic5_1st"], "ic_2015_26": r["ic5_2nd"], "t_2006_14": r.get("t5_1st", np.nan),
                         "t_2015_26": np.nan, "years_positive": r["years_positive"]})
    cor = pd.DataFrame(rows)
    same = np.sign(cor["ic_2006_14"]) == np.sign(cor["ic_2015_26"])
    cor["same_sign_both_periods"] = same
    cor["weaker_period_ic"] = np.where(same, np.minimum(cor["ic_2006_14"].abs(), cor["ic_2015_26"].abs()), 0.0)
    if "ic_2015_20" in cor:
        # signals that only exist from 2015 (news): judge on 2015-2020 vs 2021-2026 instead
        late = cor["ic_2006_14"].isna() & cor["ic_2015_20"].notna() & cor["ic_2021_26"].notna()
        same_late = np.sign(cor["ic_2015_20"]) == np.sign(cor["ic_2021_26"])
        cor.loc[late, "same_sign_both_periods"] = same_late[late]
        cor.loc[late, "weaker_period_ic"] = np.where(
            same_late, np.minimum(cor["ic_2015_20"].abs(), cor["ic_2021_26"].abs()), 0.0)[late]
    cor["survivorship_prone"] = cor["name"].apply(lambda s: any(k in s for k in SURVIVORSHIP_PRONE))
    cor = cor.sort_values("weaker_period_ic", ascending=False)
    cor.to_csv(out / "best_correlations.csv", index=False)
    strong = cor[cor["same_sign_both_periods"] & (cor["years_positive"] >= 0.7)]

    pct = lambda x: f"{x:.2f}"  # noqa: E731
    lines = [
        "# Model zoo: what forecasts best, and does it last?", "",
        f"{mod[['name', 'set', 'horizon']].drop_duplicates().shape[0]} fitted models, {n} traded strategies "
        "(model x signal set x horizon x smoothing x universe), refit yearly on 5 years, costs from measured spreads. "
        "Period 1 = 2006-2014, period 2 = 2015-2026.", "",
        "## Does picking the best in period 1 work in period 2?", "",
        f"* Rank correlation of net Sharpe between the periods: **{rank_corr:.2f}** (IC: {ic_corr:.2f}).",
        f"* With {n} strategies tried, the best period-1 Sharpe expected from pure luck is up to "
        f"**{hurdle_1st:.2f}** (deflated-Sharpe hurdle; an upper bound, since the strategies overlap heavily).",
    ]
    for k, v in sel.items():
        lines.append(f"* Top {k} by period 1: Sharpe {v['net_sharpe_1st']:.2f} in period 1 -> "
                     f"**{v['net_sharpe_2nd']:.2f}** in period 2.")
    if ens:
        lines.append(f"* Ensemble of the 10 best period-1 models (equal weight): IC {ens['ic_1st']:.4f} -> "
                     f"**{ens['ic_2nd']:.4f}**; best single of them in period 2: {ens['best_member_2nd']:.4f}.")
    lines += ["", "## Model families: results, pros and cons", "",
              by_family.round(4).to_markdown(), "",
              "## Signal sets", "", by_set.round(4).to_markdown(), "",
              "## Forecast horizon", "", by_h.round(4).to_markdown(), "",
              "## How to trade a forecast (median over models)", "", by_trade.round(3).to_markdown(), "",
              "## Strategies positive in both periods (ranked by the weaker period)", "",
              robust.head(25)[["strategy", "ic_1st", "ic_2nd", "net_sharpe_1st", "net_sharpe_2nd", "breakeven_bp_2nd",
                               "turnover_2nd"]].round(3).to_markdown(index=False) if len(robust) else "(none)", "",
              "## Strongest and most consistent correlations with future returns", "",
              "Full list: `best_correlations.csv`. Ranked by the IC in the *weaker* of the two periods; only "
              "entries with the same sign in both periods and a positive IC in at least 70% of years. "
              "Survivorship-prone = small/illiquid tilts that a universe of today's survivors flatters.", "",
              strong.head(40)[["what", "name", "horizon_days", "ic_2006_14", "ic_2015_26", "t_2006_14", "t_2015_26",
                               "years_positive", "survivorship_prone"]].round(4).to_markdown(index=False), ""]
    (out / "README.md").write_text("\n".join(lines) + "\n")
    summary = {"strategies": n, "rank_corr_sharpe": float(rank_corr), "luck_hurdle_sharpe": hurdle_1st,
               "top10_period2_sharpe": float(sel[10]["net_sharpe_2nd"]), "robust_count": int(len(robust))}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def _ensemble(in_dir: Path, mod: pd.DataFrame) -> dict | None:
    preds = {}
    for p in sorted(in_dir.rglob("zoo_preds_*_h5.parquet")):
        preds.update(pd.read_parquet(p).to_dict(orient="series"))
    tfiles = sorted(in_dir.rglob("zoo_target_h5.parquet"))
    if not preds or not tfiles:
        return None
    t = pd.read_parquet(tfiles[0])
    m5 = mod[(mod["horizon"] == 5)].drop_duplicates(["name", "set"]).sort_values("ic_1st", ascending=False)
    keys = [f"{r['name']}|{r['set']}|h5" for _, r in m5.head(10).iterrows() if f"{r['name']}|{r['set']}|h5" in preds]
    if not keys:
        return None
    day = t["day"].to_numpy()

    def ic(p, mask):
        out = []
        for d in np.unique(day[mask]):
            sel = mask & (day == d)
            a, b = p[sel], t["y"].to_numpy()[sel]
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() > 30:
                out.append(np.corrcoef(a[ok], b[ok])[0, 1])
        return float(np.mean(out)) if out else np.nan

    Z = []
    for k in keys:
        p = preds[k].to_numpy()
        z = pd.Series(p).groupby(day).transform(lambda s: (s - s.mean()) / (s.std() + 1e-12)).to_numpy()
        Z.append(z)
    ens = np.nanmean(np.stack(Z), axis=0)
    first = t["first"].to_numpy().astype(bool)
    return {"members": keys, "ic_1st": ic(ens, first), "ic_2nd": ic(ens, ~first),
            "best_member_2nd": max(ic(z, ~first) for z in Z)}


def main(argv=None):
    from ..config import Config

    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", choices=["simple", "linear", "tree", "nn", "extra", "ideas", "seq", "online",
                                        "targets", "features"])
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--out", default="reports/zoo")
    ap.add_argument("--aggregate", help="directory with group results to merge")
    ap.add_argument("--extra", help="directory with combos.csv for the correlations file")
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args(argv)
    setup_logging()
    if args.aggregate:
        print(json.dumps(aggregate(Path(args.aggregate), Path(args.out),
                                   Path(args.extra) if args.extra else None), indent=1))
    else:
        run_group(Config(), args.group, args.horizon, Path(args.out), args.synthetic)


if __name__ == "__main__":
    main()
