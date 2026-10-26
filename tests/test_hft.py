"""Tick-level HFT study on synthetic quotes and trades."""
import numpy as np
import pandas as pd

from qtrade.research import hft as H


def _ticks(seed=0, minutes=15, start="2026-03-02 15:00"):
    """Quotes every 200 ms; buy pressure (bid size > ask size) precedes the mid ticking up."""
    rng = np.random.default_rng(seed)
    n = minutes * 60 * 5
    t0 = pd.Timestamp(start, tz="UTC")
    idx = t0 + pd.to_timedelta(np.arange(n) * 200, unit="ms")
    imb = np.zeros(n)
    mid = np.empty(n)
    m = 100.0
    for i in range(n):
        imb[i] = 0.9 * imb[i - 1] + rng.normal(0, 0.3) if i else 0.0
        if i >= 25:
            m += 0.01 * np.sign(imb[i - 25]) * (rng.random() < 0.3)    # imbalance leads by 5 s
        mid[i] = m
    bid, ask = mid - 0.005, mid + 0.005
    bs = 500 * (1 + np.clip(imb, -0.9, 0.9))
    as_ = 500 * (1 - np.clip(imb, -0.9, 0.9))
    q = pd.DataFrame({"bid": bid, "ask": ask, "bsize": bs, "asize": as_}, index=idx)
    tt = idx[::7]
    side = rng.choice([-1, 1], size=len(tt))
    tr = pd.DataFrame({"price": np.where(side > 0, ask[::7] + 0.001, bid[::7] - 0.001), "size": 100.0}, index=tt)
    return q, tr, t0, t0 + pd.Timedelta(minutes=minutes)


def test_features_and_ofi_sign():
    q = pd.DataFrame({"bid": [10.0, 10.0, 10.01], "ask": [10.02, 10.02, 10.03], "bsize": [100, 300, 50.0],
                      "asize": [100, 100, 100.0]}, index=pd.date_range("2026-03-02", periods=3, freq="1s", tz="UTC"))
    e = H.ofi_events(q)
    assert e.iloc[1] == 200 and e.iloc[2] > 0          # more bid size, then a higher bid: buying pressure
    qq, tr, a, b = _ticks()
    f = H.window_features(qq, tr, a, b)
    assert set(H.FEATURES) <= set(f.columns) and {"fwd_1s", "fwd_60s"} <= set(f.columns)
    assert f["spread_bp"].median() > 0 and f["quote_imbalance"].abs().max() <= 1


def test_imbalance_predicts_and_analysis_runs():
    frames, maker = [], []
    for k, day in enumerate(pd.bdate_range("2026-03-02", periods=4)):
        q, tr, a, b = _ticks(seed=k, start=f"{day.date()} 15:00")
        f = H.window_features(q, tr, a, b).assign(symbol="X", day=day, window="10:00")
        frames.append(f)
        m = H.maker_fills(f, tr, strict=False)
        maker.append(m.assign(symbol="X", day=day, window="10:00", strict=False))
    feats = pd.concat(frames).reset_index(names="time")
    res = H.analyse(feats, pd.concat(maker, ignore_index=True))
    ic = res["ic"].set_index(["feature", "horizon_s"])
    assert ic.loc[("quote_imbalance", 5), "ic_test"] > 0.1
    assert len(res["taker"]) == 12 and len(res["maker"]) == 2
    assert len(res["model"]["beta"].iloc[0]) == len(H.FEATURES) + 1
