# Backtest results

| | |
|---|---|
| Period | 2003-12-19 to 2026-10-20 (22.8 years) |
| Stocks / signals | 1000 / 44 |
| Traded model | ensemble |
| Sharpe ratio | -0.18 |
| Annual return | -0.5% |
| Annual volatility | 2.7% |
| Max drawdown | -20.0% |
| Deflated Sharpe probability | 7.7% |
| Beta / correlation to market | 0.02 / 0.14 |
| Avg gross exposure | 0.99x |
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
| ensemble     |   -0.181 |       -0.005 |     0.027 |         -0.2   |         15.68  |           0.012 |     0.009 |
| regime_ridge |   -0.235 |       -0.006 |     0.026 |         -0.2   |         15.755 |           0.012 |     0.009 |
| ridge        |   -0.289 |       -0.007 |     0.024 |         -0.236 |         13.634 |           0.01  |     0.005 |

## Portfolio-construction diagnostics (same ensemble forecast)

| variant                        |   sharpe |   sharpe_1st_half |   sharpe_2nd_half |   ann_return |   ann_vol |   pre_cost_sharpe |   avg_gross |   ann_turnover |   cost_drag |
|:-------------------------------|---------:|------------------:|------------------:|-------------:|----------:|------------------:|------------:|---------------:|------------:|
| current config                 |   -0.181 |             0.34  |            -0.636 |       -0.005 |     0.027 |             0.347 |       0.988 |         15.68  |       0.014 |
| frictionless                   |    0.861 |             1.822 |             0.246 |        0.041 |     0.047 |             0.861 |       1.828 |         94.584 |       0     |
| auction_costs (no spread)      |    0.238 |             0.811 |            -0.258 |        0.008 |     0.032 |             0.533 |       1.265 |         29.178 |       0.009 |
| quoted_spread_costs            |   -0.181 |             0.34  |            -0.636 |       -0.005 |     0.027 |             0.347 |       0.988 |         15.68  |       0.014 |
| rank_weights                   |   -0.262 |             0.184 |            -0.678 |       -0.009 |     0.033 |             0.293 |       1.112 |         20.283 |       0.018 |
| dollar_neutral_only            |   -0.086 |            -0.144 |            -0.036 |       -0.004 |     0.05  |             0.105 |       0.74  |         10.95  |       0.01  |
| regime_ic                      |   -0.146 |             0.097 |            -0.336 |       -0.005 |     0.032 |             0.378 |       1.354 |         18.182 |       0.017 |
| regime_ic + edge_scaling       |   -0.076 |             0.102 |            -0.217 |       -0.002 |     0.022 |             0.457 |       0.931 |         13.007 |       0.012 |
| edge_scaling                   |   -0.293 |             0.324 |            -0.797 |       -0.007 |     0.022 |             0.232 |       0.793 |         13.207 |       0.012 |
| halflife=0 cost_aversion=0.0   |   -3.646 |            -4.59  |            -2.997 |       -0.105 |     0.029 |             1.542 |       0.998 |        174.2   |       0.149 |
| halflife=0 cost_aversion=0.25  |   -0.823 |            -0.618 |            -1.052 |       -0.021 |     0.025 |             1.253 |       0.948 |         64.748 |       0.053 |
| halflife=0 cost_aversion=0.5   |   -0.412 |            -0.122 |            -0.851 |       -0.011 |     0.026 |             0.878 |       1.022 |         41.674 |       0.034 |
| halflife=0 cost_aversion=1.0   |   -0.374 |            -0.165 |            -0.676 |       -0.007 |     0.02  |             0.309 |       0.815 |         16.833 |       0.013 |
| halflife=3 cost_aversion=0.0   |   -0.756 |            -0.745 |            -0.769 |       -0.021 |     0.028 |             1.035 |       1.104 |         54.561 |       0.05  |
| halflife=3 cost_aversion=0.25  |   -0.275 |             0.027 |            -0.577 |       -0.009 |     0.033 |             0.783 |       1.36  |         38.415 |       0.035 |
| halflife=3 cost_aversion=0.5   |   -0.231 |             0.174 |            -0.586 |       -0.007 |     0.032 |             0.52  |       1.209 |         26.632 |       0.024 |
| halflife=3 cost_aversion=1.0   |   -0.181 |             0.34  |            -0.636 |       -0.005 |     0.027 |             0.347 |       0.988 |         15.68  |       0.014 |
| halflife=7 cost_aversion=0.0   |   -0.515 |            -0.448 |            -0.576 |       -0.013 |     0.026 |             0.691 |       1.05  |         32.452 |       0.031 |
| halflife=7 cost_aversion=0.25  |   -0.271 |             0.042 |            -0.579 |       -0.009 |     0.032 |             0.617 |       1.377 |         29.541 |       0.028 |
| halflife=7 cost_aversion=0.5   |   -0.269 |             0.084 |            -0.59  |       -0.008 |     0.031 |             0.441 |       1.285 |         23.201 |       0.022 |
| halflife=7 cost_aversion=1.0   |   -0.251 |             0.171 |            -0.633 |       -0.007 |     0.028 |             0.306 |       1.132 |         16.38  |       0.016 |
| halflife=15 cost_aversion=0.0  |   -0.578 |            -0.476 |            -0.686 |       -0.015 |     0.026 |             0.314 |       1.017 |         22.803 |       0.023 |
| halflife=15 cost_aversion=0.25 |   -0.391 |            -0.177 |            -0.642 |       -0.011 |     0.028 |             0.352 |       1.232 |         20.578 |       0.021 |
| halflife=15 cost_aversion=0.5  |   -0.352 |            -0.078 |            -0.664 |       -0.01  |     0.028 |             0.3   |       1.192 |         17.474 |       0.018 |
| halflife=15 cost_aversion=1.0  |   -0.346 |            -0.068 |            -0.65  |       -0.009 |     0.026 |             0.198 |       1.123 |         13.722 |       0.014 |
| halflife=30 cost_aversion=0.0  |   -0.611 |            -0.592 |            -0.629 |       -0.015 |     0.025 |             0.143 |       0.975 |         17.422 |       0.019 |
| halflife=30 cost_aversion=0.25 |   -0.478 |            -0.434 |            -0.524 |       -0.012 |     0.025 |             0.069 |       0.95  |         12.521 |       0.014 |
| halflife=30 cost_aversion=0.5  |   -0.413 |            -0.312 |            -0.536 |       -0.011 |     0.027 |             0.126 |       1.121 |         12.968 |       0.014 |
| halflife=30 cost_aversion=1.0  |   -0.422 |            -0.319 |            -0.54  |       -0.011 |     0.026 |             0.028 |       1.042 |         10.221 |       0.012 |

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