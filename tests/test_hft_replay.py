"""HFT replay: the recorded stream runs through the live simulator; picks are made on train days only."""
import numpy as np
import pandas as pd

from qtrade.intraday import hft_shadow as S
from qtrade.research import hft_replay as R


def _events(seed, n=6000, syms=("AAA", "BBB")):
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp("2026-10-21 14:00", tz="UTC")
    ts = t0 + pd.to_timedelta(np.sort(rng.uniform(0, 600, n)), unit="s")
    mid = {s: 100.0 for s in syms}
    rows = []
    for i in range(n):
        s = syms[i % len(syms)]
        mid[s] += rng.choice([-0.005, 0, 0.005])
        if rng.random() < 0.8:
            rows.append((ts[i], 0, s, round(mid[s] - 0.005, 2), rng.integers(1, 1000), round(mid[s] + 0.015, 2),
                         rng.integers(1, 1000)))
        else:
            rows.append((ts[i], 1, s, round(mid[s] + rng.choice([-0.01, 0.01]), 2), 100, np.nan, np.nan))
    return pd.DataFrame(rows, columns=["t", "kind", "symbol", "a", "b", "c", "d"])


def test_replay_trades_and_flip_follows_vix():
    ev = _events(0)
    rules = S.Rules(strategies=tuple(S.ALL_STRATEGIES))
    calm = R.replay(ev, rules, 15.0, ["AAA", "BBB"])
    stress = R.replay(ev, rules, 30.0, ["AAA", "BBB"])
    assert {"imbalance_taker", "imbalance_flip", "market_maker"} <= set(calm.strategy)
    side = lambda t, k: t[t.strategy == k].side.tolist()
    assert side(calm, "imbalance_flip") == side(calm, "imbalance_taker")     # VIX <= 20: follow
    assert side(stress, "imbalance_flip") == side(stress, "imbalance_fade")  # VIX > 20: fade
    assert (calm.notional <= 10_000 / 4 / S.SLOTS + 1e-6).all()


def test_select_picks_on_train_and_reports_test():
    rules = R.variants()[:2]
    days = [pd.Timestamp(f"2026-10-{d}") for d in (12, 13, 14, 15)]
    rows = []
    for v, sign in ((0, 1.0), (1, -1.0)):
        for d in days:
            for _ in range(20):
                rows.append({"strategy": "market_maker", "variant": v, "day": d, "pnl_usd": sign * 0.1,
                             "pnl_bp": sign, "pnl_mid_bp": sign})
    tab, chosen = R.select(pd.DataFrame(rows), rules, days)
    c = chosen["market_maker"]
    assert c["variant"] == R.label(rules[0]) and c["enabled"] and c["test_days_positive"] == "2/2"
    assert np.isclose(c["train_pnl"], 4.0) and np.isclose(c["test_pnl"], 4.0)
