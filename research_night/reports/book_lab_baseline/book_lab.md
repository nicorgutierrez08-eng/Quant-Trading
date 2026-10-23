# Book lab: regime-aware capital allocation across strategies

Baseline: inverse-volatility weights (the research's rule). Regime rules multiply those weights by the predicted Sharpe relative to each strategy's trailing Sharpe (0-2x), where the prediction is the regime probabilities times the strategy's Sharpe in each regime on the training block. ``vol_tercile`` / ``vix_tercile`` use terciles of trailing market volatility / VIX instead of an HMM, to show what a plain volatility filter achieves. All weights decided at t, held over t+2, scaled to 10% volatility.

| book_set                                    | rule        |   sharpe_2006_14 |   sharpe_2015_26 |   return_2015_26 |   max_dd_2015_26 |
|:--------------------------------------------|:------------|-----------------:|-----------------:|-----------------:|-----------------:|
| 8 ETF sleeves                               | inverse_vol |            1.012 |            0.906 |            0.096 |           -0.171 |
| 8 ETF sleeves                               | vol_tercile |            0.987 |            0.952 |            0.102 |           -0.178 |
| 8 ETF sleeves                               | vix_tercile |            0.751 |            1.074 |            0.115 |           -0.189 |
| sleeves + stock book                        | inverse_vol |            1.003 |            0.909 |            0.095 |           -0.151 |
| sleeves + stock book                        | vol_tercile |            0.994 |            0.913 |            0.098 |           -0.219 |
| sleeves + stock book                        | vix_tercile |            0.66  |            1.077 |            0.116 |           -0.211 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | inverse_vol |            0.791 |            0.884 |            0.067 |           -0.132 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | vol_tercile |            0.589 |            0.817 |            0.077 |           -0.161 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | vix_tercile |            0.325 |            0.768 |            0.069 |           -0.166 |

## Each strategy's Sharpe by regime, 2015-2026 (vol_tercile)

|                                             |    sharpe_0 |   sharpe_1 |   sharpe_2 | share_of_days      |
|:--------------------------------------------|------------:|-----------:|-----------:|:-------------------|
| mom_12_1                                    |  0.152893   |  0.30338   | -0.27177   | [0.36, 0.35, 0.29] |
| low_vol                                     | -0.3902     | -0.661885  | -0.587887  | [0.36, 0.35, 0.29] |
| high_52w                                    | -0.0344355  | -0.265839  | -0.752705  | [0.36, 0.35, 0.29] |
| multi_factor                                | -0.129743   | -0.298236  | -0.606733  | [0.36, 0.35, 0.29] |
| factor_momentum                             |  0.257942   |  0.369895  | -0.575487  | [0.36, 0.35, 0.29] |
| spy_buy_hold                                |  2.06277    |  0.444285  |  0.765601  | [0.36, 0.35, 0.29] |
| spy_tsmom_12m                               |  2.05534    |  0.428364  |  0.286444  | [0.36, 0.35, 0.29] |
| spy_ma200                                   |  2.06277    |  0.330337  |  0.404628  | [0.36, 0.35, 0.29] |
| spy_vol_managed                             |  1.97351    |  0.153155  |  0.538626  | [0.36, 0.35, 0.29] |
| spy_hmm_timing                              |  1.95673    | -0.254633  | -0.279846  | [0.36, 0.35, 0.29] |
| spy_overnight                               |  0.721127   |  0.393454  |  0.326727  | [0.36, 0.35, 0.29] |
| spy_intraday                                |  0.502774   | -0.669542  |  0.24475   | [0.36, 0.35, 0.29] |
| spy_turn_of_month                           |  0.572726   |  0.46989   |  0.521357  | [0.36, 0.35, 0.29] |
| spy_after_vix_spike                         |  0.119594   |  0.323084  |  0.535264  | [0.36, 0.35, 0.29] |
| multi_asset_trend                           |  0.600245   |  1.12106   | -0.497628  | [0.36, 0.35, 0.29] |
| risk_parity                                 |  0.61912    |  0.753793  |  0.7601    | [0.36, 0.35, 0.29] |
| cross_asset_mom                             |  1.18664    |  0.645967  |  0.623223  | [0.36, 0.35, 0.29] |
| sector_momentum                             | -0.141274   | -0.599246  |  0.0373663 | [0.36, 0.35, 0.29] |
| broad_trend_3m                              |  0.814753   |  0.213834  | -0.481739  | [0.36, 0.35, 0.29] |
| broad_trend_12m                             |  1.06846    |  1.07327   | -0.503935  | [0.36, 0.35, 0.29] |
| broad_trend_blend                           |  0.707074   |  0.713155  | -0.499835  | [0.36, 0.35, 0.29] |
| broad_xs_momentum                           |  0.519977   |  0.0449666 | -0.094967  | [0.36, 0.35, 0.29] |
| short_vol_contango                          |  1.14529    |  0.137098  |  0.312169  | [0.36, 0.35, 0.29] |
| short_vol_always                            |  1.28559    |  0.219653  | -0.0500263 | [0.36, 0.35, 0.29] |
| long_vol_backwardation                      | -0.93831    | -0.345669  | -0.13429   | [0.36, 0.35, 0.29] |
| sector_seasonality                          | -0.426851   | -0.762223  | -0.480442  | [0.36, 0.35, 0.29] |
| spy_macro_timing                            |  1.19323    |  0.857358  |  0.289189  | [0.36, 0.35, 0.29] |
| momentum_macro_timed                        |  0.0873898  | -0.0178673 |  0.449801  | [0.36, 0.35, 0.29] |
| momentum_vol_scaled                         |  0.251102   |  0.441674  | -0.073464  | [0.36, 0.35, 0.29] |
| pairs                                       | -0.351752   |  0.75664   |  1.35585   | [0.36, 0.35, 0.29] |
| etf_pairs                                   | -0.460407   |  0.570698  | -0.342953  | [0.36, 0.35, 0.29] |
| mom_12_1_sector_neutral                     | -0.151905   |  0.504186  | -0.445776  | [0.36, 0.35, 0.29] |
| mom_12_1_beta_neutral                       |  0.173721   |  0.364061  |  0.038651  | [0.36, 0.35, 0.29] |
| low_vol_sector_neutral                      | -0.475908   | -0.560867  | -0.741112  | [0.36, 0.35, 0.29] |
| low_vol_beta_neutral                        | -0.163784   | -0.0550978 |  0.0432192 | [0.36, 0.35, 0.29] |
| low_vol_vol_scaled                          | -0.297444   | -0.363257  | -0.351523  | [0.36, 0.35, 0.29] |
| high_52w_sector_neutral                     | -0.14267    |  0.0318428 | -0.841297  | [0.36, 0.35, 0.29] |
| high_52w_beta_neutral                       | -0.0500917  |  0.16326   | -0.314685  | [0.36, 0.35, 0.29] |
| high_52w_vol_scaled                         | -0.00142381 |  0.0163111 | -0.537174  | [0.36, 0.35, 0.29] |
| earnings_premium                            | -0.36677    | -0.883632  | -0.104998  | [0.36, 0.35, 0.29] |
| REVERSAL BOOK (current system)              |  0.0213719  |  0.303562  |  0.139986  | [0.36, 0.35, 0.29] |
| risk_parity(mom_12_1 + reversal)            |  0.264284   |  0.494548  | -0.0860519 | [0.36, 0.35, 0.29] |
| risk_parity(momentum_vol_scaled + reversal) |  0.246654   |  0.520816  |  0.0693719 | [0.36, 0.35, 0.29] |
| stock_book                                  |  0.0213719  |  0.303562  |  0.139986  | [0.36, 0.35, 0.29] |

