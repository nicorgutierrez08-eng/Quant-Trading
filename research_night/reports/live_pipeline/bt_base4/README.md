# Backtest results

| | |
|---|---|
| Period | 2003-12-19 to 2026-10-20 (22.8 years) |
| Stocks / signals | 1000 / 44 |
| Traded model | ensemble |
| Sharpe ratio | -0.13 |
| Annual return | -0.4% |
| Annual volatility | 2.7% |
| Max drawdown | -20.4% |
| Deflated Sharpe probability | 11.6% |
| Beta / correlation to market | 0.02 / 0.13 |
| Avg gross exposure | 1.01x |
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
| ensemble     |   -0.133 |       -0.004 |     0.027 |         -0.204 |         15.747 |           0.012 |     0.008 |
| kernel_ridge |   -0.167 |       -0.004 |     0.025 |         -0.217 |         15.097 |           0.011 |     0.006 |
| regime_ridge |   -0.235 |       -0.006 |     0.026 |         -0.2   |         15.755 |           0.012 |     0.009 |
| ridge        |   -0.289 |       -0.007 |     0.024 |         -0.236 |         13.634 |           0.01  |     0.005 |

## Portfolio-construction diagnostics (same ensemble forecast)

| variant                        |   sharpe |   sharpe_1st_half |   sharpe_2nd_half |   ann_return |   ann_vol |   pre_cost_sharpe |   avg_gross |   ann_turnover |   cost_drag |
|:-------------------------------|---------:|------------------:|------------------:|-------------:|----------:|------------------:|------------:|---------------:|------------:|
| current config                 |   -0.133 |             0.458 |            -0.659 |       -0.004 |     0.027 |             0.403 |       1.006 |         15.747 |       0.014 |
| frictionless                   |    0.833 |             1.784 |             0.234 |        0.039 |     0.047 |             0.833 |       1.788 |         88.871 |       0     |
| auction_costs (no spread)      |    0.272 |             0.887 |            -0.255 |        0.009 |     0.032 |             0.564 |       1.26  |         28.519 |       0.009 |
| quoted_spread_costs            |   -0.133 |             0.458 |            -0.659 |       -0.004 |     0.027 |             0.403 |       1.006 |         15.747 |       0.014 |
| rank_weights                   |   -0.233 |             0.251 |            -0.673 |       -0.008 |     0.034 |             0.319 |       1.125 |         20.253 |       0.019 |
| dollar_neutral_only            |   -0.1   |            -0.118 |            -0.084 |       -0.005 |     0.052 |             0.088 |       0.759 |         11.147 |       0.01  |
| regime_ic                      |   -0.083 |             0.151 |            -0.319 |       -0.002 |     0.027 |             0.475 |       1.241 |         16.373 |       0.015 |
| regime_ic + edge_scaling       |   -0.066 |             0.21  |            -0.304 |       -0.001 |     0.022 |             0.508 |       0.974 |         13.63  |       0.012 |
| edge_scaling                   |   -0.249 |             0.43  |            -0.897 |       -0.005 |     0.021 |             0.299 |       0.793 |         12.901 |       0.012 |
| halflife=0 cost_aversion=0.0   |   -3.471 |            -4.496 |            -2.791 |       -0.1   |     0.029 |             1.59  |       0.992 |        170.376 |       0.146 |
| halflife=0 cost_aversion=0.25  |   -0.69  |            -0.475 |            -0.986 |       -0.02  |     0.029 |             1.246 |       0.974 |         67.913 |       0.056 |
| halflife=0 cost_aversion=0.5   |   -0.331 |            -0.026 |            -0.776 |       -0.009 |     0.026 |             0.966 |       1.026 |         42.092 |       0.034 |
| halflife=0 cost_aversion=1.0   |   -0.307 |            -0     |            -0.696 |       -0.006 |     0.021 |             0.397 |       0.865 |         18.294 |       0.015 |
| halflife=3 cost_aversion=0.0   |   -0.669 |            -0.611 |            -0.724 |       -0.019 |     0.028 |             1.024 |       1.094 |         52.006 |       0.048 |
| halflife=3 cost_aversion=0.25  |   -0.232 |             0.077 |            -0.544 |       -0.007 |     0.032 |             0.822 |       1.344 |         37.23  |       0.034 |
| halflife=3 cost_aversion=0.5   |   -0.186 |             0.279 |            -0.591 |       -0.006 |     0.032 |             0.557 |       1.209 |         26.187 |       0.024 |
| halflife=3 cost_aversion=1.0   |   -0.133 |             0.458 |            -0.659 |       -0.004 |     0.027 |             0.403 |       1.006 |         15.747 |       0.014 |
| halflife=7 cost_aversion=0.0   |   -0.418 |            -0.273 |            -0.6   |       -0.013 |     0.03  |             0.844 |       1.269 |         39.15  |       0.038 |
| halflife=7 cost_aversion=0.25  |   -0.26  |             0.058 |            -0.606 |       -0.008 |     0.03  |             0.614 |       1.295 |         27.138 |       0.026 |
| halflife=7 cost_aversion=0.5   |   -0.226 |             0.132 |            -0.583 |       -0.007 |     0.03  |             0.51  |       1.271 |         22.623 |       0.022 |
| halflife=7 cost_aversion=1.0   |   -0.221 |             0.23  |            -0.651 |       -0.006 |     0.028 |             0.35  |       1.133 |         16.196 |       0.016 |
| halflife=15 cost_aversion=0.0  |   -0.456 |            -0.344 |            -0.578 |       -0.012 |     0.026 |             0.398 |       1.018 |         21.828 |       0.022 |
| halflife=15 cost_aversion=0.25 |   -0.361 |            -0.128 |            -0.632 |       -0.01  |     0.028 |             0.364 |       1.226 |         19.702 |       0.02  |
| halflife=15 cost_aversion=0.5  |   -0.338 |            -0.065 |            -0.65  |       -0.009 |     0.027 |             0.298 |       1.18  |         16.665 |       0.017 |
| halflife=15 cost_aversion=1.0  |   -0.324 |            -0.052 |            -0.626 |       -0.008 |     0.026 |             0.205 |       1.093 |         12.99  |       0.014 |
| halflife=30 cost_aversion=0.0  |   -0.447 |            -0.35  |            -0.576 |       -0.013 |     0.029 |             0.34  |       1.189 |         20.89  |       0.022 |
| halflife=30 cost_aversion=0.25 |   -0.361 |            -0.174 |            -0.581 |       -0.01  |     0.028 |             0.24  |       1.195 |         15.275 |       0.017 |
| halflife=30 cost_aversion=0.5  |   -0.347 |            -0.137 |            -0.589 |       -0.01  |     0.027 |             0.181 |       1.147 |         12.826 |       0.014 |
| halflife=30 cost_aversion=1.0  |   -0.363 |            -0.132 |            -0.625 |       -0.009 |     0.026 |             0.081 |       1.061 |         10.099 |       0.012 |

## Signals (descriptive, full-sample rank IC)

| signal              | family         |   mean_ic |   ic_ir |   t_stat |   hit_rate |   ic_regime_0 |   ic_regime_1 |   ic_regime_2 |
|:--------------------|:---------------|----------:|--------:|---------:|-----------:|--------------:|--------------:|--------------:|
| resid_rev_1d        | mean_reversion |    0.0097 |  2.6842 |  13.583  |     0.5664 |        0.0083 |        0.0117 |        0.0109 |
| peer_gap            | structure      |    0.0132 |  2.3039 |  11.6858 |     0.5564 |        0.0091 |        0.0142 |        0.0182 |
| resid_rev_5d        | mean_reversion |    0.0097 |  2.2161 |  11.2141 |     0.557  |        0.0056 |        0.0111 |        0.0144 |
| low_volume_rev      | mean_reversion |    0.0181 |  1.9425 |   9.8615 |     0.5396 |        0.0121 |        0.0156 |        0.0262 |
| rev_5d              | mean_reversion |    0.0181 |  1.9411 |   9.8547 |     0.538  |        0.0122 |        0.0157 |        0.0263 |
| ou_sscore           | mean_reversion |    0.0072 |  1.9009 |   9.6051 |     0.5418 |        0.0039 |        0.0036 |        0.0122 |
| bollinger_z         | mean_reversion |    0.0138 |  1.6418 |   8.3353 |     0.5329 |        0.0072 |        0.0063 |        0.0242 |
| rev_1d              | mean_reversion |    0.0145 |  1.5924 |   8.0845 |     0.538  |        0.0119 |        0.013  |        0.0182 |
| close_location      | microstructure |    0.0103 |  1.5727 |   7.9842 |     0.5336 |        0.0055 |        0.0136 |        0.0155 |
| intraday_rev        | mean_reversion |    0.0118 |  1.4185 |   7.2014 |     0.5332 |        0.0104 |        0.0108 |        0.014  |
| rsi_14              | mean_reversion |    0.0129 |  1.4131 |   7.1739 |     0.5238 |        0.0067 |        0.0033 |        0.0232 |
| vol_price_corr      | volume         |    0.007  |  1.3295 |   6.7494 |     0.5326 |        0.0053 |        0.0105 |        0.0081 |
| rev_21d             | mean_reversion |    0.0128 |  1.3092 |   6.6464 |     0.5289 |        0.0078 |        0.0028 |        0.0218 |
| resid_mom           | momentum       |    0.0093 |  1.226  |   6.1361 |     0.5513 |        0.0117 |        0.0181 |        0.0042 |
| intraday_rev_21     | momentum       |    0.0107 |  1.1638 |   5.9083 |     0.5298 |        0.0056 |        0.0056 |        0.0185 |
| same_month          | seasonality    |    0.0073 |  1.0913 |   5.4261 |     0.5457 |        0.0066 |        0.0217 |        0.0043 |
| mom_12_1            | momentum       |    0.0106 |  0.8631 |   4.3776 |     0.5373 |        0.014  |        0.0237 |        0.0027 |
| overnight_rev       | mean_reversion |    0.0065 |  0.7245 |   3.6781 |     0.5206 |        0.0032 |        0.006  |        0.0108 |
| weekday_seasonality | seasonality    |    0.0028 |  0.6635 |   3.3314 |     0.5246 |        0.0033 |        0.0057 |        0.0013 |
| size_proxy          | volume         |    0.005  |  0.6366 |   3.2318 |     0.521  |        0.0051 |        0.0006 |        0.006  |
| neg_skew            | volatility     |    0.0028 |  0.5367 |   2.7245 |     0.5004 |        0.0043 |        0.0022 |        0.0011 |
| amihud              | volume         |    0.0049 |  0.5299 |   2.6903 |     0.5147 |        0.0021 |        0.0001 |        0.0098 |
| autocorr_signal     | structure      |    0.0019 |  0.4324 |   2.1954 |     0.505  |       -0      |       -0.002  |        0.0055 |
| turn_of_month       | seasonality    |    0.006  |  0.3354 |   1.7029 |     0.5067 |        0.0101 |       -0.0023 |        0.003  |
| mom_6_1             | momentum       |    0.0036 |  0.3214 |   1.6318 |     0.5324 |        0.0015 |        0.0217 |        0.0014 |
| turnover_trend      | volume         |    0.0022 |  0.3205 |   1.6273 |     0.491  |       -0.001  |       -0.0106 |        0.0098 |
| gk_ratio            | microstructure |    0.0016 |  0.2684 |   1.3624 |     0.4952 |       -0.0027 |        0.0056 |        0.006  |
| range_vol_ratio     | microstructure |    0.0013 |  0.2248 |   1.1411 |     0.5204 |        0.0023 |        0.0026 |       -0.0004 |
| max_effect          | volatility     |    0.0019 |  0.1561 |   0.7925 |     0.5018 |        0.0074 |        0.0049 |       -0.0059 |
| market_corr         | structure      |    0.0016 |  0.1419 |   0.7206 |     0.5038 |        0.0123 |        0.0034 |       -0.0124 |
| bab                 | volatility     |   -0.0001 | -0.0055 |  -0.0278 |     0.4936 |        0.0138 |        0.0019 |       -0.0182 |
| idio_vol            | volatility     |   -0.001  | -0.0861 |  -0.4354 |     0.4923 |        0.0035 |        0.004  |       -0.008  |
| low_vol             | volatility     |   -0.0013 | -0.0861 |  -0.4372 |     0.4916 |        0.0088 |       -0.0039 |       -0.0134 |
| cs_spread           | microstructure |   -0.0018 | -0.1663 |  -0.8445 |     0.5019 |       -0.007  |       -0.0058 |        0.0058 |
| high_52w            | momentum       |   -0.0047 | -0.3579 |  -1.8171 |     0.5048 |        0.0043 |        0.0121 |       -0.0207 |
| vol_of_vol          | volatility     |   -0.0023 | -0.4437 |  -2.2526 |     0.4893 |       -0.0029 |        0.0024 |       -0.0028 |
| abn_volume          | volume         |   -0.0021 | -0.5018 |  -2.5474 |     0.4931 |       -0.0025 |        0.0001 |       -0.0023 |
| trend_quality       | momentum       |   -0.007  | -0.6839 |  -3.4721 |     0.497  |       -0.0039 |        0.008  |       -0.015  |
| overnight_mom       | momentum       |   -0.0049 | -0.6984 |  -3.5455 |     0.4952 |       -0.0032 |        0.0051 |       -0.0098 |
| cluster_mom         | momentum       |   -0.0082 | -0.7765 |  -3.9387 |     0.4848 |       -0.0048 |       -0.0007 |       -0.0145 |
| peer_lead           | structure      |   -0.0085 | -0.8242 |  -4.1805 |     0.4857 |       -0.0061 |       -0.0047 |       -0.0124 |
| kalman_trend        | structure      |   -0.0092 | -0.9724 |  -4.9366 |     0.4856 |       -0.0062 |        0.0033 |       -0.0165 |
| mom_accel           | momentum       |   -0.0094 | -1.0292 |  -5.2252 |     0.4862 |       -0.0053 |       -0.0039 |       -0.016  |
| downside_beta       | volatility     |   -0.0205 | -1.1989 |  -2.4669 |     0.478  |       -0.0227 |       -0.0368 |       -0.0152 |

![signals](charts/signals.png)

![weights](charts/weights.png)

Full interactive-free report with monthly table and config: `report.html` (download and open).