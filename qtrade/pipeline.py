"""End-to-end research pipeline shared by the backtest and the live trader.

    market data -> features -> 45 signals -> HMM regimes -> walk-forward models
                -> forecasts -> portfolio -> backtest / orders
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Config
from .data.market import MarketData
from .features.context import FeatureContext
from .models.regime import walk_forward_regimes
from .models.walkforward import WalkForwardResult, walk_forward
from .signals import REGISTRY, signal_array
from .utils import LOG, cs_rank_gauss, rank_ic


@dataclass
class Research:
    ctx: FeatureContext
    signal_names: list[str]
    feats: np.ndarray            # T x N x F
    fwd_ret: np.ndarray          # T x N raw forward return (open t+1 -> open t+1+h)
    target: np.ndarray           # T x N rank-Gaussian target used for training
    regimes: pd.DataFrame        # T x K filtered regime probabilities
    regime_fits: list
    wf: WalkForwardResult

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.ctx.md.dates

    def prediction(self, model: str) -> np.ndarray:
        return self.wf.predictions[model]

    def signal_ic_table(self) -> pd.DataFrame:
        """Univariate rank IC of every signal, overall and by regime (in-sample, descriptive)."""
        reg = self.regimes.to_numpy().argmax(axis=1)
        rows = []
        for k, name in enumerate(self.signal_names):
            ic = rank_ic(self.feats[:, :, k], self.fwd_ret)
            s = pd.Series(ic, index=self.dates).dropna()
            row = {"signal": name, "family": REGISTRY[name].family,
                   "mean_ic": s.mean(), "ic_ir": s.mean() / s.std() * np.sqrt(252) if s.std() > 0 else np.nan,
                   "t_stat": s.mean() / s.std() * np.sqrt(len(s)) if s.std() > 0 else np.nan,
                   "hit_rate": (s > 0).mean()}
            for r in range(self.regimes.shape[1]):
                m = pd.Series(reg == r, index=self.dates).reindex(s.index)
                row[f"ic_regime_{r}"] = s[m].mean()
            rows.append(row)
        return pd.DataFrame(rows).sort_values("ic_ir", ascending=False).reset_index(drop=True)


def forward_returns(md: MarketData, horizon: int) -> pd.DataFrame:
    """Return from the open of t+1 to the open of t+1+horizon (stored at row t)."""
    o = md.open
    return o.shift(-(1 + horizon)) / o.shift(-1) - 1


def build_research(md: MarketData, cfg: Config, final_refit: bool = False,
                   models: list[str] | None = None) -> Research:
    ctx = FeatureContext(md, cfg)
    names = cfg.model.signals or list(REGISTRY)
    feats, names = signal_array(ctx, names)

    fwd = forward_returns(md, cfg.model.horizon).where(ctx.tradable)
    target = cs_rank_gauss(fwd.clip(-0.5, 0.5)).to_numpy(dtype=np.float32)

    rc = cfg.regime
    regimes, fits = walk_forward_regimes(
        ctx.market_state, n_states=rc.n_states, refit_every=rc.refit_every,
        min_history=rc.min_history, n_init=rc.n_init, max_iter=rc.max_iter, seed=cfg.model.seed,
        temper=rc.temper, align=rc.align,
    )
    ctx.regimes = regimes          # the portfolio can size by regime (portfolio.regime_ic)
    wf = walk_forward(feats, target, regimes.to_numpy(), md.dates, cfg,
                      model_names=models, final_refit=final_refit)
    LOG.info("research pipeline complete")
    return Research(ctx, names, feats, fwd.to_numpy(dtype=np.float32), target, regimes, fits, wf)
