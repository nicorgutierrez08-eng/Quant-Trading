"""IBKR fee arithmetic for the intraday simulation."""
import numpy as np

from qtrade.intraday.ibkr_sim import IBKR, order_fees


def test_commission_min_max_and_sell_only_fees():
    shares = np.array([10.0, 1000.0, 1.0])
    price = np.array([50.0, 20.0, 5.0])
    sell = np.array([False, True, True])
    f = order_fees(shares, price, sell)
    assert np.isclose(f["commission"][0], IBKR["commission_min"])          # 10 x 0.0035 < $0.35
    assert np.isclose(f["commission"][1], 1000 * IBKR["commission_per_share"])
    assert np.isclose(f["commission"][2], IBKR["commission_min"])          # 1% of $5 < $0.35 -> the minimum
    assert f["sec_fee"][0] == 0 and f["finra_taf"][0] == 0                # buys pay no SEC fee or TAF
    assert np.isclose(f["sec_fee"][1], 20_000 * IBKR["sec_fee_per_dollar_sold"])
    assert np.isclose(f["finra_taf"][1], 1000 * IBKR["finra_taf_per_share_sold"])
    assert np.isclose(f["fixed_commission"][1], 5.0)                      # fixed plan: $0.005 x 1000
