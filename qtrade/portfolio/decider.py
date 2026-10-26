"""The daily trading decision, shared verbatim by the backtest and live trading."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..backtest.costs import unit_cost
from ..features.context import FeatureContext
from ..utils import rank_ic
from .optimizer import SizingInfo, construct, realized_ic


@dataclass
class Decision:
    weights: np.ndarray       # target weights for every ticker (0 for untraded)
    info: SizingInfo
    ic_hat: float
    holding_periods: float
    n_candidates: int


def smooth_forecast(pred: np.ndarray, halflife: float) -> np.ndarray:
    """Exponentially smooth each stock's daily cross-sectional z-score over time.

    A raw short-horizon forecast flips quickly, so trading it fully costs more
    than it earns. Smoothing keeps the persistent part of the signal and
    filters the noisy day-to-day flips (Garleanu-Pedersen: "aim" toward a
    weighted average of current and expected future forecasts). Uses only
    past forecasts, so it adds no look-ahead.
    """
    lam = 1.0 - 0.5 ** (1.0 / halflife)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.nanmean(pred, axis=1, keepdims=True)
        sd = np.nanstd(pred, axis=1, keepdims=True)
        z = (pred - mu) / np.where(sd > 0, sd, np.nan)
    out = np.full(pred.shape, np.nan, dtype=np.float32)
    ema = np.zeros(pred.shape[1])
    seen = np.zeros(pred.shape[1], dtype=bool)
    for t in range(len(pred)):
        ok = np.isfinite(z[t])
        ema = np.where(ok, np.where(seen, (1 - lam) * ema + lam * z[t], z[t]), ema)
        seen |= ok
        out[t] = np.where(ok, ema, np.nan)
    return out


class Decider:
    """Turns the forecast for day t into target weights using only data <= t."""

    def __init__(self, ctx: FeatureContext, pred: np.ndarray, fwd_ret: np.ndarray, cfg):
        hl = cfg.portfolio.forecast_halflife
        pred = smooth_forecast(pred, hl) if hl and hl > 0 else pred
        self.ctx, self.pred, self.cfg = ctx, pred, cfg
        self.h = cfg.model.horizon
        sigma_idio = ctx.resid.rolling(63, min_periods=40).std().to_numpy()
        sigma_tot = ctx.vol_63.to_numpy()
        self.sigma = np.where(np.isfinite(sigma_idio), sigma_idio, sigma_tot)
        self.adv = ctx.adv.to_numpy()
        self.tradable = ctx.tradable.to_numpy()
        self.fm = ctx.factor_model
        self.tickers = ctx.md.tickers
        self.dates = ctx.md.dates
        # realised IC of the forecast (known h+1 days later)
        self.ic = rank_ic(pred, fwd_ret)
        # forecast persistence: rank autocorrelation with the forecast h days earlier
        self.persist = np.full(len(pred), np.nan)
        if len(pred) > self.h:
            self.persist[self.h:] = rank_ic(pred[self.h:], pred[: -self.h])
        self._load_cache: dict = {}
        reg = getattr(ctx, "regimes", None)
        self.regimes = reg.to_numpy() if reg is not None else None

    def _loadings(self, t: int, idx: np.ndarray):
        snap = self.fm.snapshot_at(self.dates[t])
        if snap is None or not len(idx):
            return None
        if snap.date not in self._load_cache:
            self._load_cache.clear()
            pos = {tk: j for j, tk in enumerate(snap.tickers)}
            col_to_row = np.array([pos.get(tk, -1) for tk in self.tickers])
            L = np.vstack([snap.loadings, np.zeros((1, snap.loadings.shape[1]))])  # row -1 = zeros
            self._load_cache[snap.date] = (col_to_row, L)
        col_to_row, L = self._load_cache[snap.date]
        nf = self.cfg.portfolio.n_neutral_factors
        return L[col_to_row[idx]][:, :nf] if nf is not None else L[col_to_row[idx]]

    def ic_estimate(self, t: int) -> float:
        p = self.cfg.portfolio
        hist_end = t - self.h - 1          # last day whose label is complete at t
        if hist_end <= 0:
            return p.ic_prior
        if p.regime_ic and self.regimes is not None:
            return self._regime_ic(t, hist_end)
        return realized_ic(self.ic[max(0, hist_end - p.ic_lookback + 1) : hist_end + 1],
                           p.ic_prior, p.ic_prior_days)

    def _regime_ic(self, t: int, hist_end: int) -> float:
        """IC expected today = sum_k P(regime k today) x IC realised in regime k.

        Each regime's IC is the probability-weighted average of past daily ICs
        (all history up to the last complete label), shrunk toward the prior
        with ``ic_prior_days`` pseudo-days, so a rarely visited regime is not
        trusted on a handful of days."""
        p = self.cfg.portfolio
        ic = self.ic[: hist_end + 1]
        P = self.regimes[: hist_end + 1]
        ok = np.isfinite(ic) & np.isfinite(P).all(axis=1)
        w = P[ok]
        ic_k = (w * ic[ok, None]).sum(axis=0) + p.ic_prior * p.ic_prior_days
        ic_k /= w.sum(axis=0) + p.ic_prior_days
        now = self.regimes[t]
        return float(max(np.nansum(now * ic_k) if np.isfinite(now).all() else p.ic_prior, 0.0))

    def holding_periods(self, t: int) -> float:
        win = self.persist[max(0, t - 62) : t + 1]
        rho = float(np.nanmean(win)) if np.isfinite(win).any() else 0.0
        return float(np.clip(1.0 / (1.0 - np.clip(rho, 0.0, 0.95)), 1.0, 20.0))

    def decide(self, t: int, w_cur: np.ndarray, equity: float, risk_scale: float = 1.0,
               allowed: np.ndarray | None = None, no_short: np.ndarray | None = None) -> Decision:
        """``allowed``: names that may be held at all. ``no_short``: names that may
        only be held long (the broker can't borrow them); they are kept out of the
        short side here, so the book stays balanced instead of losing its shorts
        after the fact."""
        z = self.pred[t]
        ok = np.isfinite(z) & self.tradable[t] & np.isfinite(self.sigma[t])
        if allowed is not None:
            ok &= allowed
        if no_short is not None:
            # a stock we can't short is only a candidate if the model likes it
            zc = np.where(np.isfinite(z), z - np.nanmean(z[ok]) if ok.any() else z, np.nan)
            ok &= ~(no_short & (zc < 0))
        idx = np.nonzero(ok)[0]
        N = len(z)
        ic_hat = self.ic_estimate(t)
        hold_L = self.holding_periods(t)
        ref = self.cfg.portfolio.edge_scaling
        if ref:
            # bet more when the expected edge is bigger: exposure follows IC_hat
            risk_scale = risk_scale * float(np.clip(ic_hat / ref, 0.0, 1.0))
        if len(idx) < 10:
            return Decision(np.zeros(N), SizingInfo(0.0, "no_edge", 0.0, 0.0, 0.0), ic_hat, hold_L, len(idx))
        zz = z[idx]
        zz = (zz - zz.mean()) / (zz.std() + 1e-12)
        k = self.cfg.portfolio.max_names
        if k and len(idx) > k:
            # small accounts: open positions only in the k/2 strongest longs and
            # shorts; keep an existing position while it stays within the top or
            # bottom k (a rank buffer that avoids churning names in and out)
            rank = np.argsort(np.argsort(zz))           # 0 = most negative
            n = len(idx)
            new_ok = (rank < k // 2) | (rank >= n - k // 2)
            buffer_ok = (rank < k) | (rank >= n - k)
            held = w_cur[idx] != 0
            keep = new_ok | (held & buffer_ok)
            idx, zz = idx[keep], zz[keep]
        for _ in range(5):
            tc = unit_cost(self.adv[t, idx], self.sigma[t, idx], equity, self.cfg)
            w_sel, info = construct(zz, self.sigma[t, idx], self._loadings(t, idx), ic_hat, self.cfg,
                                    risk_scale, w_cur=w_cur[idx], tcost=tc, holding_periods=hold_L)
            if no_short is None:
                break
            bad = no_short[idx] & (w_sel < -1e-9)   # hedging pushed an unshortable name short
            if not bad.any():
                break
            idx, zz = idx[~bad], zz[~bad]
        w = np.zeros(N)
        w[idx] = w_sel
        return Decision(w, info, ic_hat, hold_L, len(idx))
