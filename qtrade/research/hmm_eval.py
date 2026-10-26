"""Which HMM is accurate? Out-of-sample tests on real market data.

There is no "true regime" to check against, so a variant is judged on what it
predicts, always walk-forward (refit once a year on data up to that day):

1. one-step predictive log-likelihood of tomorrow's market symptoms - the
   standard score for a probabilistic model (higher is better; only
   comparable between variants on the same features);
2. calibration: from the regime probabilities, the probability that the
   market falls more than 3% over the next 5 days, compared with how often
   it actually did (Brier score vs. always predicting the base rate);
3. usefulness: R^2 for next month's realized volatility, and how much the
   5-day reversal signal's IC differs between the calmest and most stressed
   regime out of sample;
4. confidence: share of days where one regime gets > 90%.

Variants: number of regimes, tempering, rolling vs. daily (non-overlapping)
symptoms. Selection uses 2004-2014; 2015-2026 is reported as the check.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..models.regime import walk_forward_regimes
from ..signals import compute_signals
from ..utils import LOG, rank_ic

SPLIT = "2015-01-01"


def daily_state(ctx) -> pd.DataFrame:
    """Non-overlapping daily symptoms: each day's numbers use that day only."""
    r = ctx.ret.clip(-0.5, 0.5)
    mkt = ctx.market_ret
    disp = r.std(axis=1)
    return pd.DataFrame({
        "mkt_ret": mkt,
        "log_abs_mkt": np.log(mkt.abs() + 0.002),
        "log_dispersion": np.log(disp.clip(lower=1e-5)),
        "corr_1d": (mkt ** 2 / (r.pow(2).mean(axis=1) + 1e-10)).clip(0, 1),
    })


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    ok = np.isfinite(p) & np.isfinite(y)
    return float(np.mean((p[ok] - y[ok]) ** 2))


def evaluate(probs: pd.DataFrame, fits, event: pd.Series, fwd_vol: pd.Series, trail_vol: pd.Series,
             rev_ic: pd.Series) -> dict:
    """Walk-forward economic and calibration tests for one variant."""
    P = probs.to_numpy()
    idx = probs.index
    pred_event = pd.Series(np.nan, index=idx)
    base = pd.Series(np.nan, index=idx)
    vol_pred = pd.Series(np.nan, index=idx)
    refit_dates = [d for d, _ in fits] + [idx[-1] + pd.Timedelta(days=1)]
    for a, b in zip(refit_dates[:-1], refit_dates[1:]):
        train = idx <= a - pd.Timedelta(days=35)        # 5- and 21-day labels already known at the refit
        test = (idx > a) & (idx < b)
        ev = event[train].to_numpy()
        ok = np.isfinite(ev)
        Ptr = P[train][ok]
        f_k = (Ptr * ev[ok, None]).sum(axis=0) / (Ptr.sum(axis=0) + 1e-9)   # event frequency per regime
        pred_event[test] = P[test] @ f_k
        base[test] = ev[ok].mean()
        y, x1 = fwd_vol[train].to_numpy(), trail_vol[train].to_numpy()
        X = np.column_stack([P[train], x1])
        okv = np.isfinite(y) & np.isfinite(X).all(axis=1)
        if okv.sum() > 100:
            coef = np.linalg.lstsq(X[okv], y[okv], rcond=None)[0]
            vol_pred[test] = np.column_stack([P[test], trail_vol[test].to_numpy()]) @ coef
    res = {}
    sd_order = None
    for name, m in (("1st", idx < SPLIT), ("2nd", idx >= SPLIT)):
        m = m & np.isfinite(pred_event.to_numpy())
        y = event[m].to_numpy()
        res[f"brier_skill_{name}"] = 1 - _brier(pred_event[m].to_numpy(), y) / _brier(base[m].to_numpy(), y)
        yv, pv, tv = fwd_vol[m], vol_pred[m], trail_vol[m]
        okv = yv.notna() & pv.notna() & tv.notna()
        # R^2 gain over trailing volatility alone (fit in-sample on the same days, for reference)
        naive = np.polyfit(tv[okv], yv[okv], 1)
        sse_n = ((yv[okv] - np.polyval(naive, tv[okv])) ** 2).sum()
        res[f"vol_r2_{name}"] = 1 - ((yv[okv] - pv[okv]) ** 2).sum() / ((yv[okv] - yv[okv].mean()) ** 2).sum()
        res[f"vol_r2_vs_trailing_{name}"] = 1 - ((yv[okv] - pv[okv]) ** 2).sum() / sse_n
        res[f"confident_share_{name}"] = float((P[m].max(axis=1) > 0.9).mean())
        # reversal IC: most volatile regime minus least volatile, out of sample
        ric = rev_ic[m]
        if sd_order is None:
            last = fits[-1][1]
            sd_order = np.argsort([np.trace(c) for c in last.covars_])
        hi, lo = sd_order[-1], sd_order[0]
        ok = ric.notna().to_numpy()
        for tag, k in (("stressed", hi), ("calm", lo)):
            wk = P[m][ok, k]
            res[f"rev_ic_{tag}_{name}"] = float((wk * ric[ok]).sum() / wk.sum()) if wk.sum() > 1 else np.nan
    pll = probs.attrs.get("predictive_ll")
    if pll is not None:
        res["pred_ll_1st"] = float(pll[pll.index < SPLIT].mean())
        res["pred_ll_2nd"] = float(pll[pll.index >= SPLIT].mean())
    return res


def run(md, ctx, out: Path, cfg) -> dict:
    rc = cfg.regime
    mkt = ctx.market_ret
    fwd5 = mkt[::-1].rolling(5).sum()[::-1].shift(-1)
    event = (fwd5 < -0.03).astype(float).where(fwd5.notna())
    fwd_vol = np.log(mkt[::-1].rolling(21).std()[::-1].shift(-1))
    trail_vol = np.log(mkt.rolling(21).std())
    rev = compute_signals(ctx, ["rev_5d"])["rev_5d"].to_numpy()
    o = md.open
    fwd = (o.shift(-6) / o.shift(-1) - 1).where(ctx.tradable).to_numpy()
    rev_ic = pd.Series(rank_ic(rev, fwd), index=md.dates)

    states = {"rolling": ctx.market_state, "daily": daily_state(ctx)}
    variants = [("rolling", k, t) for k in (1, 2, 3, 4) for t in (1.0, 0.5, 0.2, 0.1)
                if not (k == 1 and t != 1.0)]
    variants += [("daily", k, t) for k in (1, 3) for t in (1.0, 0.5, 0.2) if not (k == 1 and t != 1.0)]
    rows = []
    for feats, k, temper in variants:
        st = states[feats]
        vol_col = "log_rvol" if feats == "rolling" else "log_abs_mkt"
        probs, fits = walk_forward_regimes(st, n_states=k, refit_every=rc.refit_every, min_history=rc.min_history,
                                           n_init=rc.n_init, max_iter=rc.max_iter, seed=cfg.model.seed,
                                           vol_column=vol_col, temper=temper, align=True)
        res = evaluate(probs, fits, event, fwd_vol, trail_vol, rev_ic)
        rows.append({"features": feats, "states": k, "temper": temper, **res})
        LOG.info("hmm %s K=%d temper=%.2f: pred_ll %.3f / %.3f, brier skill %.3f / %.3f", feats, k, temper,
                 res.get("pred_ll_1st", np.nan), res.get("pred_ll_2nd", np.nan),
                 res["brier_skill_1st"], res["brier_skill_2nd"])
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "hmm_variants.csv", index=False)
    cols = ["features", "states", "temper", "pred_ll_1st", "pred_ll_2nd", "brier_skill_1st", "brier_skill_2nd",
            "vol_r2_vs_trailing_1st", "vol_r2_vs_trailing_2nd", "confident_share_2nd",
            "rev_ic_calm_2nd", "rev_ic_stressed_2nd"]
    lines = ["## HMM variants, walk-forward on real data", "",
             "pred_ll: average log-likelihood of tomorrow's symptoms given today's regime beliefs (higher is "
             "better; compare within a feature set). brier_skill: calibration of P(market falls > 3% in 5 days) "
             "vs. always predicting the base rate (> 0 = useful). vol_r2_vs_trailing: improvement in "
             "forecasting next month's volatility over using last month's alone (> 0 = useful). "
             "confident_share: days with one regime > 90%. rev_ic: 5-day reversal IC in the calmest and "
             "most stressed regime, weighted by the regime probabilities.", "",
             tab[cols].round(4).to_markdown(index=False), ""]
    (out / "hmm.md").write_text("\n".join(lines) + "\n")
    return {"variants": len(tab)}
