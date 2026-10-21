# Book lab: regime-aware capital allocation across strategies

Baseline: inverse-volatility weights (the research's rule). Regime rules multiply those weights by the predicted Sharpe relative to each strategy's trailing Sharpe (0-2x), where the prediction is the regime probabilities times the strategy's Sharpe in each regime on the training block. ``vol_tercile`` / ``vix_tercile`` use terciles of trailing market volatility / VIX instead of an HMM, to show what a plain volatility filter achieves. All weights decided at t, held over t+2, scaled to 10% volatility.

| book_set                                    | rule                     |   sharpe_2006_14 |   sharpe_2015_26 |   return_2015_26 |   max_dd_2015_26 |
|:--------------------------------------------|:-------------------------|-----------------:|-----------------:|-----------------:|-----------------:|
| 8 ETF sleeves                               | inverse_vol              |            1.012 |            0.906 |            0.096 |           -0.171 |
| 8 ETF sleeves                               | macro_gauss_K2_s0.0_t1.0 |            0.748 |            0.786 |            0.085 |           -0.233 |
| 8 ETF sleeves                               | vol_tercile              |            0.987 |            0.952 |            0.102 |           -0.178 |
| 8 ETF sleeves                               | vix_tercile              |            0.751 |            1.074 |            0.115 |           -0.189 |
| sleeves + stock book                        | inverse_vol              |            1.003 |            0.909 |            0.095 |           -0.151 |
| sleeves + stock book                        | macro_gauss_K2_s0.0_t1.0 |            0.699 |            0.683 |            0.074 |           -0.291 |
| sleeves + stock book                        | vol_tercile              |            0.994 |            0.913 |            0.098 |           -0.219 |
| sleeves + stock book                        | vix_tercile              |            0.66  |            1.077 |            0.116 |           -0.211 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | inverse_vol              |            0.791 |            0.884 |            0.067 |           -0.132 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | macro_gauss_K2_s0.0_t1.0 |            0.762 |            0.775 |            0.055 |           -0.162 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | vol_tercile              |            0.589 |            0.817 |            0.077 |           -0.161 |
| all 18 strategies with 2006-14 Sharpe > 0.3 | vix_tercile              |            0.325 |            0.768 |            0.069 |           -0.166 |
| sleeves + regime switch                     | inverse_vol              |            0.895 |            1.071 |            0.109 |           -0.167 |
| sleeves + regime switch                     | macro_gauss_K2_s0.0_t1.0 |            0.857 |            1.001 |            0.108 |           -0.206 |
| sleeves + regime switch                     | vol_tercile              |            0.851 |            1.11  |            0.117 |           -0.155 |
| sleeves + regime switch                     | vix_tercile              |            0.565 |            1.229 |            0.129 |           -0.15  |
| sleeves + stock book + regime switch        | inverse_vol              |            0.895 |            1.069 |            0.106 |           -0.138 |
| sleeves + stock book + regime switch        | macro_gauss_K2_s0.0_t1.0 |            0.821 |            1.027 |            0.109 |           -0.195 |
| sleeves + stock book + regime switch        | vol_tercile              |            0.894 |            1.114 |            0.116 |           -0.157 |
| sleeves + stock book + regime switch        | vix_tercile              |            0.512 |            1.253 |            0.131 |           -0.158 |

## Each strategy's Sharpe by regime, 2015-2026 (macro_gauss_K2_s0.0_t1.0)

|                                             |    sharpe_0 |   sharpe_1 | share_of_days   |
|:--------------------------------------------|------------:|-----------:|:----------------|
| mom_12_1                                    |  0.0869312  |  0.010943  | [0.58, 0.42]    |
| low_vol                                     | -0.0994718  | -0.924927  | [0.58, 0.42]    |
| high_52w                                    | -0.139023   | -0.631555  | [0.58, 0.42]    |
| multi_factor                                | -0.0638932  | -0.618794  | [0.58, 0.42]    |
| factor_momentum                             |  0.0130227  | -0.16325   | [0.58, 0.42]    |
| spy_buy_hold                                |  1.85146    |  0.37683   | [0.58, 0.42]    |
| spy_tsmom_12m                               |  1.7298     |  0.0193364 | [0.58, 0.42]    |
| spy_ma200                                   |  1.69362    |  0.0305769 | [0.58, 0.42]    |
| spy_vol_managed                             |  1.83842    | -0.101572  | [0.58, 0.42]    |
| spy_hmm_timing                              |  1.79837    | -0.951879  | [0.58, 0.42]    |
| spy_overnight                               |  1.00438    |  0.0907208 | [0.58, 0.42]    |
| spy_intraday                                |  0.238332   | -0.131225  | [0.58, 0.42]    |
| spy_turn_of_month                           |  0.839175   |  0.313339  | [0.58, 0.42]    |
| spy_after_vix_spike                         |  0.4286     |  0.382121  | [0.58, 0.42]    |
| multi_asset_trend                           |  1.2046     | -0.347474  | [0.58, 0.42]    |
| risk_parity                                 |  1.24736    |  0.305309  | [0.58, 0.42]    |
| cross_asset_mom                             |  1.44752    |  0.220079  | [0.58, 0.42]    |
| sector_momentum                             | -0.322459   | -0.141862  | [0.58, 0.42]    |
| broad_trend_3m                              |  0.696434   | -0.351895  | [0.58, 0.42]    |
| broad_trend_12m                             |  1.36564    | -0.230327  | [0.58, 0.42]    |
| broad_trend_blend                           |  0.875426   | -0.293024  | [0.58, 0.42]    |
| broad_xs_momentum                           |  0.638234   | -0.359257  | [0.58, 0.42]    |
| short_vol_contango                          |  1.36444    | -0.483084  | [0.58, 0.42]    |
| short_vol_always                            |  1.50436    | -0.494254  | [0.58, 0.42]    |
| long_vol_backwardation                      | -0.948613   | -0.174772  | [0.58, 0.42]    |
| sector_seasonality                          | -0.45033    | -0.687517  | [0.58, 0.42]    |
| spy_macro_timing                            |  1.40419    |  0.121263  | [0.58, 0.42]    |
| momentum_macro_timed                        |  0.330578   |  0.0531833 | [0.58, 0.42]    |
| momentum_vol_scaled                         |  0.263855   |  0.146111  | [0.58, 0.42]    |
| pairs                                       |  0.290535   |  1.08876   | [0.58, 0.42]    |
| etf_pairs                                   |  0.00681884 | -0.170672  | [0.58, 0.42]    |
| mom_12_1_sector_neutral                     |  0.0648836  | -0.110853  | [0.58, 0.42]    |
| mom_12_1_beta_neutral                       |  0.131917   |  0.243391  | [0.58, 0.42]    |
| low_vol_sector_neutral                      | -0.0365389  | -1.05418   | [0.58, 0.42]    |
| low_vol_beta_neutral                        |  0.138157   | -0.177611  | [0.58, 0.42]    |
| low_vol_vol_scaled                          | -0.0372583  | -0.637439  | [0.58, 0.42]    |
| high_52w_sector_neutral                     |  0.0707324  | -0.735717  | [0.58, 0.42]    |
| high_52w_beta_neutral                       |  0.00265183 | -0.182201  | [0.58, 0.42]    |
| high_52w_vol_scaled                         |  0.0274136  | -0.41779   | [0.58, 0.42]    |
| earnings_premium                            | -0.534262   | -0.37656   | [0.58, 0.42]    |
| REVERSAL BOOK (current system)              |  0.233976   |  0.0825546 | [0.58, 0.42]    |
| risk_parity(mom_12_1 + reversal)            |  0.258218   |  0.176284  | [0.58, 0.42]    |
| risk_parity(momentum_vol_scaled + reversal) |  0.302191   |  0.252355  | [0.58, 0.42]    |
| switch_hmm                                  | -0.135572   |  0.817736  | [0.58, 0.42]    |
| switch_voltercile                           |  0.154402   |  0.950719  | [0.58, 0.42]    |
| stock_book                                  |  0.233976   |  0.0825546 | [0.58, 0.42]    |

