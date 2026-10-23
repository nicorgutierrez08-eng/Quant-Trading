# Backtest results

| | |
|---|---|
| Period | 2003-12-19 to 2026-10-20 (22.8 years) |
| Stocks / signals | 1000 / 44 |
| Traded model | ensemble |
| Sharpe ratio | -0.07 |
| Annual return | -0.2% |
| Annual volatility | 2.4% |
| Max drawdown | -20.4% |
| Deflated Sharpe probability | 8.4% |
| Beta / correlation to market | 0.02 / 0.17 |
| Avg gross exposure | 1.00x |
| Annual turnover | 15x |
| Cost + borrow drag / yr | 1.3% |

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
| gbm          |    0.228 |        0.006 |     0.024 |         -0.147 |         19.764 |           0.015 |     0.01  |
| ensemble     |   -0.069 |       -0.002 |     0.024 |         -0.204 |         14.804 |           0.011 |     0.009 |
| ic_weighted  |   -0.082 |       -0.002 |     0.027 |         -0.22  |         16.282 |           0.011 |     0.007 |
| regime_ridge |   -0.163 |       -0.004 |     0.023 |         -0.195 |         14.941 |           0.011 |     0.01  |
| kernel_ridge |   -0.186 |       -0.004 |     0.021 |         -0.228 |         12.642 |           0.01  |     0.003 |
| ridge        |   -0.248 |       -0.006 |     0.023 |         -0.235 |         13.496 |           0.01  |     0.006 |

## Portfolio-construction diagnostics (same ensemble forecast)

| variant                        |   sharpe |   sharpe_1st_half |   sharpe_2nd_half |   ann_return |   ann_vol |   pre_cost_sharpe |   avg_gross |   ann_turnover |   cost_drag |
|:-------------------------------|---------:|------------------:|------------------:|-------------:|----------:|------------------:|------------:|---------------:|------------:|
| current config                 |   -0.069 |             0.699 |            -0.692 |       -0.002 |     0.024 |             0.492 |       1     |         14.804 |       0.013 |
| frictionless                   |    0.888 |             2.119 |             0.117 |        0.041 |     0.046 |             0.888 |       1.768 |         88.31  |       0     |
| auction_costs (no spread)      |    0.285 |             1.333 |            -0.401 |        0.01  |     0.034 |             0.579 |       1.376 |         30.103 |       0.01  |
| quoted_spread_costs            |   -0.069 |             0.699 |            -0.692 |       -0.002 |     0.024 |             0.492 |       1     |         14.804 |       0.013 |
| rank_weights                   |   -0.112 |             0.512 |            -0.631 |       -0.003 |     0.03  |             0.464 |       1.112 |         19.003 |       0.017 |
| dollar_neutral_only            |    0.06  |            -0.07  |             0.178 |        0.003 |     0.052 |             0.247 |       0.77  |         11.03  |       0.01  |
| regime_ic                      |    0.018 |             0.57  |            -0.441 |        0     |     0.027 |             0.524 |       1.195 |         14.38  |       0.014 |
| regime_ic + edge_scaling       |   -0.151 |             0.46  |            -0.628 |       -0.003 |     0.019 |             0.385 |       0.754 |         11.971 |       0.01  |
| edge_scaling                   |   -0.162 |             0.777 |            -0.946 |       -0.003 |     0.018 |             0.412 |       0.758 |         11.759 |       0.011 |
| halflife=0 cost_aversion=0.0   |   -3.538 |            -4.394 |            -2.98  |       -0.098 |     0.028 |             1.584 |       0.976 |        164.923 |       0.141 |
| halflife=0 cost_aversion=0.25  |   -0.697 |            -0.36  |            -1.164 |       -0.02  |     0.028 |             1.393 |       1.006 |         70.707 |       0.059 |
| halflife=0 cost_aversion=0.5   |   -0.238 |             0.359 |            -0.937 |       -0.006 |     0.025 |             1.211 |       1.095 |         45.546 |       0.037 |
| halflife=0 cost_aversion=1.0   |   -0.034 |             0.614 |            -0.505 |       -0.001 |     0.023 |             0.707 |       0.983 |         22.239 |       0.017 |
| halflife=3 cost_aversion=0.0   |   -0.566 |            -0.341 |            -0.806 |       -0.017 |     0.031 |             1.057 |       1.108 |         53.028 |       0.05  |
| halflife=3 cost_aversion=0.25  |   -0.078 |             0.528 |            -0.684 |       -0.002 |     0.03  |             1.004 |       1.334 |         35.79  |       0.033 |
| halflife=3 cost_aversion=0.5   |   -0.019 |             0.722 |            -0.681 |       -0.001 |     0.028 |             0.785 |       1.201 |         24.897 |       0.023 |
| halflife=3 cost_aversion=1.0   |   -0.069 |             0.699 |            -0.692 |       -0.002 |     0.024 |             0.492 |       1     |         14.804 |       0.013 |
| halflife=7 cost_aversion=0.0   |   -0.441 |            -0.261 |            -0.608 |       -0.011 |     0.026 |             0.74  |       1.036 |         31.154 |       0.03  |
| halflife=7 cost_aversion=0.25  |   -0.184 |             0.284 |            -0.655 |       -0.005 |     0.027 |             0.727 |       1.237 |         25.523 |       0.025 |
| halflife=7 cost_aversion=0.5   |   -0.093 |             0.457 |            -0.595 |       -0.003 |     0.027 |             0.696 |       1.258 |         21.998 |       0.021 |
| halflife=7 cost_aversion=1.0   |   -0.044 |             0.647 |            -0.632 |       -0.001 |     0.025 |             0.56  |       1.129 |         15.711 |       0.015 |
| halflife=15 cost_aversion=0.0  |   -0.26  |             0.022 |            -0.569 |       -0.007 |     0.027 |             0.772 |       1.258 |         27.377 |       0.028 |
| halflife=15 cost_aversion=0.25 |   -0.123 |             0.31  |            -0.574 |       -0.003 |     0.026 |             0.659 |       1.227 |         19.957 |       0.021 |
| halflife=15 cost_aversion=0.5  |   -0.076 |             0.401 |            -0.557 |       -0.002 |     0.026 |             0.612 |       1.207 |         17.15  |       0.018 |
| halflife=15 cost_aversion=1.0  |   -0.061 |             0.487 |            -0.593 |       -0.002 |     0.025 |             0.512 |       1.141 |         13.534 |       0.014 |
| halflife=30 cost_aversion=0.0  |   -0.289 |            -0.01  |            -0.606 |       -0.008 |     0.028 |             0.575 |       1.27  |         22.236 |       0.024 |
| halflife=30 cost_aversion=0.25 |   -0.168 |             0.212 |            -0.58  |       -0.005 |     0.027 |             0.482 |       1.232 |         15.801 |       0.018 |
| halflife=30 cost_aversion=0.5  |   -0.138 |             0.261 |            -0.559 |       -0.004 |     0.026 |             0.437 |       1.203 |         13.465 |       0.015 |
| halflife=30 cost_aversion=1.0  |   -0.116 |             0.325 |            -0.569 |       -0.003 |     0.025 |             0.369 |       1.129 |         10.607 |       0.012 |

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