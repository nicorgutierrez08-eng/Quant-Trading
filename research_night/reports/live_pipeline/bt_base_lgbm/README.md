# Backtest results

| | |
|---|---|
| Period | 2003-12-19 to 2026-10-20 (22.8 years) |
| Stocks / signals | 1000 / 44 |
| Traded model | ensemble |
| Sharpe ratio | -0.02 |
| Annual return | -0.1% |
| Annual volatility | 2.6% |
| Max drawdown | -18.2% |
| Deflated Sharpe probability | 25.3% |
| Beta / correlation to market | 0.02 / 0.13 |
| Avg gross exposure | 1.00x |
| Annual turnover | 15x |
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
| ensemble     |   -0.021 |       -0.001 |     0.026 |         -0.182 |         15.451 |           0.012 |     0.009 |
| gbm          |   -0.043 |       -0.001 |     0.019 |         -0.175 |         13.861 |           0.011 |     0.008 |
| kernel_ridge |   -0.066 |       -0.002 |     0.025 |         -0.214 |         14.347 |           0.011 |     0.006 |
| ic_weighted  |   -0.082 |       -0.002 |     0.027 |         -0.22  |         16.282 |           0.011 |     0.007 |
| regime_ridge |   -0.195 |       -0.005 |     0.027 |         -0.172 |         15.087 |           0.011 |     0.008 |
| ridge        |   -0.248 |       -0.006 |     0.023 |         -0.235 |         13.496 |           0.01  |     0.006 |

## Portfolio-construction diagnostics (same ensemble forecast)

| variant                        |   sharpe |   sharpe_1st_half |   sharpe_2nd_half |   ann_return |   ann_vol |   pre_cost_sharpe |   avg_gross |   ann_turnover |   cost_drag |
|:-------------------------------|---------:|------------------:|------------------:|-------------:|----------:|------------------:|------------:|---------------:|------------:|
| current config                 |   -0.021 |             0.619 |            -0.587 |       -0.001 |     0.026 |             0.517 |       1.004 |         15.451 |       0.014 |
| frictionless                   |    0.91  |             1.937 |             0.232 |        0.042 |     0.046 |             0.91  |       1.763 |         87.348 |       0     |
| auction_costs (no spread)      |    0.268 |             1.121 |            -0.297 |        0.01  |     0.037 |             0.555 |       1.431 |         32.665 |       0.011 |
| quoted_spread_costs            |   -0.021 |             0.619 |            -0.587 |       -0.001 |     0.026 |             0.517 |       1.004 |         15.451 |       0.014 |
| rank_weights                   |   -0.078 |             0.41  |            -0.505 |       -0.003 |     0.033 |             0.467 |       1.112 |         19.73  |       0.018 |
| dollar_neutral_only            |    0.063 |            -0.014 |             0.139 |        0.003 |     0.055 |             0.246 |       0.774 |         11.386 |       0.01  |
| regime_ic                      |   -0.092 |             0.229 |            -0.433 |       -0.002 |     0.025 |             0.514 |       1.186 |         15.992 |       0.015 |
| regime_ic + edge_scaling       |   -0.029 |             0.372 |            -0.431 |       -0.001 |     0.019 |             0.65  |       0.94  |         13.653 |       0.013 |
| edge_scaling                   |   -0.15  |             0.567 |            -0.764 |       -0.003 |     0.021 |             0.399 |       0.788 |         12.695 |       0.011 |
| halflife=0 cost_aversion=0.0   |   -3.613 |            -4.469 |            -3.022 |       -0.1   |     0.028 |             1.562 |       0.984 |        167.82  |       0.144 |
| halflife=0 cost_aversion=0.25  |   -0.741 |            -0.442 |            -1.17  |       -0.021 |     0.029 |             1.268 |       0.977 |         69.307 |       0.057 |
| halflife=0 cost_aversion=0.5   |   -0.303 |             0.059 |            -0.838 |       -0.008 |     0.025 |             1.096 |       1.026 |         43.928 |       0.036 |
| halflife=0 cost_aversion=1.0   |   -0.195 |             0.131 |            -0.623 |       -0.004 |     0.02  |             0.562 |       0.856 |         19.183 |       0.015 |
| halflife=3 cost_aversion=0.0   |   -0.566 |            -0.384 |            -0.74  |       -0.016 |     0.028 |             1.085 |       1.082 |         50.799 |       0.047 |
| halflife=3 cost_aversion=0.25  |   -0.133 |             0.327 |            -0.603 |       -0.004 |     0.032 |             0.901 |       1.328 |         36.493 |       0.033 |
| halflife=3 cost_aversion=0.5   |   -0.026 |             0.53  |            -0.551 |       -0.001 |     0.03  |             0.746 |       1.197 |         25.647 |       0.023 |
| halflife=3 cost_aversion=1.0   |   -0.021 |             0.619 |            -0.587 |       -0.001 |     0.026 |             0.517 |       1.004 |         15.451 |       0.014 |
| halflife=7 cost_aversion=0.0   |   -0.395 |            -0.233 |            -0.571 |       -0.011 |     0.027 |             0.724 |       1.044 |         31.346 |       0.03  |
| halflife=7 cost_aversion=0.25  |   -0.172 |             0.219 |            -0.598 |       -0.005 |     0.029 |             0.712 |       1.276 |         26.333 |       0.026 |
| halflife=7 cost_aversion=0.5   |   -0.134 |             0.314 |            -0.565 |       -0.004 |     0.029 |             0.614 |       1.258 |         22.159 |       0.021 |
| halflife=7 cost_aversion=1.0   |   -0.142 |             0.356 |            -0.577 |       -0.004 |     0.027 |             0.429 |       1.128 |         15.971 |       0.016 |
| halflife=15 cost_aversion=0.0  |   -0.35  |            -0.209 |            -0.5   |       -0.009 |     0.025 |             0.515 |       1.011 |         21.234 |       0.022 |
| halflife=15 cost_aversion=0.25 |   -0.227 |             0.075 |            -0.566 |       -0.006 |     0.027 |             0.531 |       1.209 |         19.596 |       0.02  |
| halflife=15 cost_aversion=0.5  |   -0.184 |             0.173 |            -0.569 |       -0.005 |     0.027 |             0.486 |       1.198 |         17     |       0.018 |
| halflife=15 cost_aversion=1.0  |   -0.164 |             0.28  |            -0.578 |       -0.004 |     0.027 |             0.394 |       1.186 |         14.257 |       0.015 |
| halflife=30 cost_aversion=0.0  |   -0.496 |            -0.467 |            -0.524 |       -0.012 |     0.024 |             0.28  |       0.985 |         17.083 |       0.018 |
| halflife=30 cost_aversion=0.25 |   -0.334 |            -0.257 |            -0.417 |       -0.008 |     0.024 |             0.227 |       0.962 |         12.309 |       0.014 |
| halflife=30 cost_aversion=0.5  |   -0.257 |            -0.062 |            -0.485 |       -0.007 |     0.026 |             0.305 |       1.139 |         13.002 |       0.015 |
| halflife=30 cost_aversion=1.0  |   -0.25  |             0.004 |            -0.53  |       -0.006 |     0.025 |             0.23  |       1.086 |         10.474 |       0.012 |

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