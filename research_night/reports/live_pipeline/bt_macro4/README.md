# Backtest results

| | |
|---|---|
| Period | 2003-12-19 to 2026-10-20 (22.8 years) |
| Stocks / signals | 1000 / 44 |
| Traded model | ensemble |
| Sharpe ratio | -0.14 |
| Annual return | -0.4% |
| Annual volatility | 2.7% |
| Max drawdown | -21.1% |
| Deflated Sharpe probability | 11.5% |
| Beta / correlation to market | 0.02 / 0.14 |
| Avg gross exposure | 1.04x |
| Annual turnover | 16x |
| Cost + borrow drag / yr | 1.4% |

> **Read these results with care.** The universe is today's largest companies that have traded for 15+ years, tested over the past - so it never holds a company that later failed or shrank (survivorship and look-ahead bias). Expect live results to be weaker.
>
> Everything else is out-of-sample: signals use only past data, models are refit walk-forward, trades fill at the next day's open, and spread, market impact and borrow fees are charged.
>
> The **deflated Sharpe** is the probability the true Sharpe is above zero after correcting for having tried every model on this page. Below ~95% the edge is not statistically convincing.
>

![Growth of $1](charts/equity.png)

![Drawdown](charts/drawdown.png)

![Rolling Sharpe](charts/rolling_sharpe.png)

![Annual returns](charts/annual.png)

![Exposure](charts/exposure.png)

![HMM regimes](charts/regimes.png)

![Model comparison](charts/models.png)

## Models (same portfolio rules)

| model        |   sharpe |   ann_return |   ann_vol |   max_drawdown |   ann_turnover |   ann_cost_drag |   mean_ic |
|:-------------|---------:|-------------:|----------:|---------------:|---------------:|----------------:|----------:|
| ic_weighted  |   -0.038 |       -0.001 |     0.026 |         -0.208 |         16.221 |           0.011 |     0.009 |
| ensemble     |   -0.139 |       -0.004 |     0.027 |         -0.211 |         15.901 |           0.012 |     0.009 |
| regime_ridge |   -0.195 |       -0.005 |     0.028 |         -0.215 |         17.844 |           0.014 |     0.012 |
| kernel_ridge |   -0.208 |       -0.005 |     0.024 |         -0.216 |         14.031 |           0.011 |     0.006 |
| ridge        |   -0.289 |       -0.007 |     0.024 |         -0.236 |         13.634 |           0.01  |     0.005 |

## Portfolio-construction diagnostics (same ensemble forecast)

| variant                        |   sharpe |   sharpe_1st_half |   sharpe_2nd_half |   ann_return |   ann_vol |   pre_cost_sharpe |   avg_gross |   ann_turnover |   cost_drag |
|:-------------------------------|---------:|------------------:|------------------:|-------------:|----------:|------------------:|------------:|---------------:|------------:|
| current config                 |   -0.139 |             0.455 |            -0.692 |       -0.004 |     0.027 |             0.4   |       1.04  |         15.901 |       0.014 |
| frictionless                   |    0.908 |             2.062 |             0.155 |        0.043 |     0.048 |             0.908 |       1.857 |         92.281 |       0     |
| auction_costs (no spread)      |    0.161 |             0.887 |            -0.362 |        0.006 |     0.037 |             0.449 |       1.462 |         32.599 |       0.011 |
| quoted_spread_costs            |   -0.139 |             0.455 |            -0.692 |       -0.004 |     0.027 |             0.4   |       1.04  |         15.901 |       0.014 |
| rank_weights                   |   -0.235 |             0.285 |            -0.772 |       -0.008 |     0.033 |             0.341 |       1.167 |         20.438 |       0.019 |
| dollar_neutral_only            |   -0.07  |            -0.155 |             0.021 |       -0.004 |     0.057 |             0.102 |       0.783 |         11.182 |       0.01  |
| regime_ic                      |   -0.036 |             0.522 |            -0.392 |       -0.001 |     0.034 |             0.473 |       1.361 |         18.996 |       0.017 |
| regime_ic + edge_scaling       |   -0.171 |             0.499 |            -0.543 |       -0.004 |     0.026 |             0.359 |       0.946 |         16.602 |       0.014 |
| edge_scaling                   |   -0.287 |             0.406 |            -0.975 |       -0.006 |     0.021 |             0.254 |       0.79  |         12.667 |       0.011 |
| halflife=0 cost_aversion=0.0   |   -3.369 |            -4.623 |            -2.59  |       -0.1   |     0.03  |             1.604 |       1.008 |        172.262 |       0.148 |
| halflife=0 cost_aversion=0.25  |   -0.668 |            -0.428 |            -0.992 |       -0.02  |     0.03  |             1.274 |       1     |         68.926 |       0.057 |
| halflife=0 cost_aversion=0.5   |   -0.283 |             0.03  |            -0.725 |       -0.008 |     0.027 |             1.024 |       1.078 |         43.178 |       0.035 |
| halflife=0 cost_aversion=1.0   |   -0.229 |             0.061 |            -0.579 |       -0.005 |     0.021 |             0.473 |       0.901 |         18.466 |       0.015 |
| halflife=3 cost_aversion=0.0   |   -0.592 |            -0.425 |            -0.777 |       -0.019 |     0.032 |             1.048 |       1.159 |         55.598 |       0.052 |
| halflife=3 cost_aversion=0.25  |   -0.184 |             0.218 |            -0.619 |       -0.006 |     0.033 |             0.89  |       1.41  |         38.314 |       0.035 |
| halflife=3 cost_aversion=0.5   |   -0.174 |             0.29  |            -0.648 |       -0.005 |     0.03  |             0.623 |       1.265 |         26.751 |       0.024 |
| halflife=3 cost_aversion=1.0   |   -0.139 |             0.455 |            -0.692 |       -0.004 |     0.027 |             0.4   |       1.04  |         15.901 |       0.014 |
| halflife=7 cost_aversion=0.0   |   -0.469 |            -0.224 |            -0.779 |       -0.014 |     0.031 |             0.851 |       1.327 |         41.577 |       0.041 |
| halflife=7 cost_aversion=0.25  |   -0.22  |             0.22  |            -0.723 |       -0.007 |     0.03  |             0.659 |       1.299 |         27.098 |       0.026 |
| halflife=7 cost_aversion=0.5   |   -0.175 |             0.296 |            -0.676 |       -0.005 |     0.03  |             0.585 |       1.308 |         23.182 |       0.022 |
| halflife=7 cost_aversion=1.0   |   -0.135 |             0.447 |            -0.735 |       -0.004 |     0.027 |             0.458 |       1.166 |         16.522 |       0.016 |
| halflife=15 cost_aversion=0.0  |   -0.43  |            -0.08  |            -0.855 |       -0.013 |     0.03  |             0.601 |       1.327 |         30.222 |       0.031 |
| halflife=15 cost_aversion=0.25 |   -0.324 |             0.127 |            -0.856 |       -0.009 |     0.029 |             0.423 |       1.268 |         20.911 |       0.022 |
| halflife=15 cost_aversion=0.5  |   -0.316 |             0.147 |            -0.85  |       -0.009 |     0.028 |             0.333 |       1.214 |         17.474 |       0.018 |
| halflife=15 cost_aversion=1.0  |   -0.324 |             0.16  |            -0.856 |       -0.009 |     0.027 |             0.222 |       1.137 |         13.904 |       0.015 |
| halflife=30 cost_aversion=0.0  |   -0.454 |            -0.198 |            -0.764 |       -0.013 |     0.029 |             0.375 |       1.257 |         22.681 |       0.024 |
| halflife=30 cost_aversion=0.25 |   -0.348 |            -0.013 |            -0.738 |       -0.01  |     0.029 |             0.257 |       1.214 |         15.747 |       0.017 |
| halflife=30 cost_aversion=0.5  |   -0.327 |            -0.002 |            -0.701 |       -0.009 |     0.028 |             0.199 |       1.169 |         13.165 |       0.015 |
| halflife=30 cost_aversion=1.0  |   -0.303 |            -0.006 |            -0.639 |       -0.008 |     0.027 |             0.138 |       1.092 |         10.36  |       0.012 |

## Signals (descriptive, full-sample rank IC)

| signal              | family         |   mean_ic |   ic_ir |   t_stat |   hit_rate |   ic_regime_0 |   ic_regime_1 |
|:--------------------|:---------------|----------:|--------:|---------:|-----------:|--------------:|--------------:|
| resid_rev_1d        | mean_reversion |    0.0097 |  2.6842 |  13.583  |     0.5664 |        0.0097 |        0.0096 |
| peer_gap            | structure      |    0.0132 |  2.3039 |  11.6858 |     0.5564 |        0.0119 |        0.0164 |
| resid_rev_5d        | mean_reversion |    0.0097 |  2.2161 |  11.2141 |     0.557  |        0.0097 |        0.0098 |
| low_volume_rev      | mean_reversion |    0.0181 |  1.9425 |   9.8615 |     0.5396 |        0.0152 |        0.025  |
| rev_5d              | mean_reversion |    0.0181 |  1.9411 |   9.8547 |     0.538  |        0.0151 |        0.0253 |
| ou_sscore           | mean_reversion |    0.0072 |  1.9009 |   9.6051 |     0.5418 |        0.0073 |        0.0069 |
| bollinger_z         | mean_reversion |    0.0138 |  1.6418 |   8.3353 |     0.5329 |        0.0115 |        0.0194 |
| rev_1d              | mean_reversion |    0.0145 |  1.5924 |   8.0845 |     0.538  |        0.0126 |        0.0189 |
| close_location      | microstructure |    0.0103 |  1.5727 |   7.9842 |     0.5336 |        0.0087 |        0.0142 |
| intraday_rev        | mean_reversion |    0.0118 |  1.4185 |   7.2014 |     0.5332 |        0.0106 |        0.0147 |
| rsi_14              | mean_reversion |    0.0129 |  1.4131 |   7.1739 |     0.5238 |        0.0093 |        0.0214 |
| vol_price_corr      | volume         |    0.007  |  1.3295 |   6.7494 |     0.5326 |        0.0073 |        0.0061 |
| rev_21d             | mean_reversion |    0.0128 |  1.3092 |   6.6464 |     0.5289 |        0.0101 |        0.0192 |
| resid_mom           | momentum       |    0.0093 |  1.226  |   6.1361 |     0.5513 |        0.014  |       -0.0013 |
| intraday_rev_21     | momentum       |    0.0107 |  1.1638 |   5.9083 |     0.5298 |        0.0076 |        0.0183 |
| same_month          | seasonality    |    0.0073 |  1.0913 |   5.4261 |     0.5457 |        0.0063 |        0.0096 |
| mom_12_1            | momentum       |    0.0106 |  0.8631 |   4.3776 |     0.5373 |        0.0167 |       -0.0041 |
| overnight_rev       | mean_reversion |    0.0065 |  0.7245 |   3.6781 |     0.5206 |        0.0044 |        0.0114 |
| weekday_seasonality | seasonality    |    0.0028 |  0.6635 |   3.3314 |     0.5246 |        0.0045 |       -0.0012 |
| size_proxy          | volume         |    0.005  |  0.6366 |   3.2318 |     0.521  |        0.004  |        0.0073 |
| neg_skew            | volatility     |    0.0028 |  0.5367 |   2.7245 |     0.5004 |        0.0035 |        0.0012 |
| amihud              | volume         |    0.0049 |  0.5299 |   2.6903 |     0.5147 |        0.0016 |        0.0128 |
| autocorr_signal     | structure      |    0.0019 |  0.4324 |   2.1954 |     0.505  |        0.0004 |        0.0056 |
| turn_of_month       | seasonality    |    0.006  |  0.3354 |   1.7029 |     0.5067 |        0.0065 |        0.0047 |
| mom_6_1             | momentum       |    0.0036 |  0.3214 |   1.6318 |     0.5324 |        0.0062 |       -0.0026 |
| turnover_trend      | volume         |    0.0022 |  0.3205 |   1.6273 |     0.491  |       -0.0013 |        0.0108 |
| gk_ratio            | microstructure |    0.0016 |  0.2684 |   1.3624 |     0.4952 |       -0.0023 |        0.0111 |
| range_vol_ratio     | microstructure |    0.0013 |  0.2248 |   1.1411 |     0.5204 |        0.0014 |        0.0009 |
| max_effect          | volatility     |    0.0019 |  0.1561 |   0.7925 |     0.5018 |        0.0076 |       -0.0118 |
| market_corr         | structure      |    0.0016 |  0.1419 |   0.7206 |     0.5038 |        0.0081 |       -0.014  |
| bab                 | volatility     |   -0.0001 | -0.0055 |  -0.0278 |     0.4936 |        0.008  |       -0.0196 |
| idio_vol            | volatility     |   -0.001  | -0.0861 |  -0.4354 |     0.4923 |        0.0035 |       -0.0118 |
| low_vol             | volatility     |   -0.0013 | -0.0861 |  -0.4372 |     0.4916 |        0.0069 |       -0.0212 |
| cs_spread           | microstructure |   -0.0018 | -0.1663 |  -0.8445 |     0.5019 |       -0.0065 |        0.0095 |
| high_52w            | momentum       |   -0.0047 | -0.3579 |  -1.8171 |     0.5048 |        0.0038 |       -0.0252 |
| vol_of_vol          | volatility     |   -0.0023 | -0.4437 |  -2.2526 |     0.4893 |       -0.0025 |       -0.002  |
| abn_volume          | volume         |   -0.0021 | -0.5018 |  -2.5474 |     0.4931 |       -0.0003 |       -0.0064 |
| trend_quality       | momentum       |   -0.007  | -0.6839 |  -3.4721 |     0.497  |       -0.0005 |       -0.0226 |
| overnight_mom       | momentum       |   -0.0049 | -0.6984 |  -3.5455 |     0.4952 |       -0.0057 |       -0.003  |
| cluster_mom         | momentum       |   -0.0082 | -0.7765 |  -3.9387 |     0.4848 |       -0.0041 |       -0.018  |
| peer_lead           | structure      |   -0.0085 | -0.8242 |  -4.1805 |     0.4857 |       -0.0061 |       -0.0142 |
| kalman_trend        | structure      |   -0.0092 | -0.9724 |  -4.9366 |     0.4856 |       -0.0054 |       -0.0183 |
| mom_accel           | momentum       |   -0.0094 | -1.0292 |  -5.2252 |     0.4862 |       -0.0043 |       -0.0215 |
| downside_beta       | volatility     |   -0.0205 | -1.1989 |  -2.4669 |     0.478  |       -0.0064 |       -0.0393 |

![signals](charts/signals.png)

![weights](charts/weights.png)

Full interactive-free report with monthly table and config: `report.html` (download and open).