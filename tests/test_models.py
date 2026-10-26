import numpy as np

from qtrade.data import make_market
from qtrade.features.context import FeatureContext
from qtrade.models.combiners import ICWeightedModel, KernelRidgeModel, RegimeRidgeModel, RidgeModel
from qtrade.models.hmm import GaussianHMM
from qtrade.models.regime import walk_forward_regimes


def test_hmm_recovers_planted_regimes(cfg):
    md, true = make_market(n_stocks=80, n_days=2500, seed=5)
    ctx = FeatureContext(md, cfg)
    probs, fits = walk_forward_regimes(ctx.market_state, n_states=3, refit_every=400, min_history=600, n_init=3)
    np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-9)
    m = probs.index > fits[0][0]
    acc = (probs.to_numpy().argmax(axis=1)[m] == true.to_numpy()[m]).mean()
    assert acc > 0.7, f"HMM regime accuracy {acc:.2f}"


def test_hmm_em_increases_likelihood():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(0, 1, (300, 2)), rng.normal(4, 0.5, (300, 2))])
    one = GaussianHMM(2, n_init=1, max_iter=1, seed=1).fit(X)
    many = GaussianHMM(2, n_init=1, max_iter=100, seed=1).fit(X)
    assert many.score(X) >= one.score(X) - 1e-6
    path = many.viterbi(X)
    assert len(set(path[:300])) == 1 and path[0] != path[-1]


def _toy(n=20000, p=8, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, p)).astype(np.float32)
    R = rng.dirichlet(np.ones(3), n)
    beta = np.zeros(p)
    beta[:3] = [0.3, -0.2, 0.1]
    y = X @ beta + rng.standard_normal(n)
    day = np.repeat(np.arange(n // 100), 100)
    return X, y, R, day, beta


def test_linear_models_find_signal():
    X, y, R, day, beta = _toy()
    for m in (RidgeModel(), ICWeightedModel(), RegimeRidgeModel(seed=0)):
        m.fit(X, y, R, day)
        pred = m.predict(X, R)
        assert np.corrcoef(pred, X @ beta)[0, 1] > 0.8, m.name


def test_kernel_ridge_captures_nonlinearity():
    rng = np.random.default_rng(1)
    n = 20000
    X = rng.standard_normal((n, 4)).astype(np.float32)
    R = np.full((n, 3), 1 / 3)
    f = np.abs(X[:, 0]) - 0.8
    y = f + 0.5 * rng.standard_normal(n)
    day = np.repeat(np.arange(n // 100), 100)
    m = KernelRidgeModel(n_features=256, seed=0).fit(X, y, R, day)
    assert np.corrcoef(m.predict(X, R), f)[0, 1] > 0.5


def test_stable_signal_selection_keeps_consistent_signals():
    from qtrade.models.walkforward import stable_signals

    rng = np.random.default_rng(0)
    days, n = 300, 200
    day = np.repeat(np.arange(days), n)
    y = rng.standard_normal(days * n)
    steady = 0.1 * y + rng.standard_normal(days * n)                 # same sign throughout
    flip = np.where(day < days // 2, 1, -1) * 0.1 * y + rng.standard_normal(days * n)  # flips half-way
    noise = rng.standard_normal(days * n)
    keep = stable_signals(np.column_stack([steady, flip, noise]), y, day, splits=3, min_t=2.0)
    assert keep.tolist() == [True, False, False]
