# Model zoo: what forecasts best, and does it last?

684 fitted models, 4104 traded strategies (model x signal set x horizon x smoothing x universe), refit yearly on 5 years, costs from measured spreads. Period 1 = 2006-2014, period 2 = 2015-2026.

## Does picking the best in period 1 work in period 2?

* Rank correlation of net Sharpe between the periods: **0.63** (IC: -0.15).
* With 4104 strategies tried, the best period-1 Sharpe expected from pure luck is up to **2.44** (deflated-Sharpe hurdle; an upper bound, since the strategies overlap heavily).
* Top 1 by period 1: Sharpe 0.42 in period 1 -> **0.11** in period 2.
* Top 10 by period 1: Sharpe 0.35 in period 1 -> **0.14** in period 2.
* Top 50 by period 1: Sharpe 0.24 in period 1 -> **0.04** in period 2.
* Ensemble of the 10 best period-1 models (equal weight): IC 0.0078 -> **0.0090**; best single of them in period 2: 0.0218.

## Model families: results, pros and cons

| name                   |   ic_1st |   ic_2nd |   net_sharpe_2nd_best |   net_sharpe_2nd_median |   breakeven_2nd_median |   years_positive | pros                                                                  | cons                                                   |
|:-----------------------|---------:|---------:|----------------------:|------------------------:|-----------------------:|-----------------:|:----------------------------------------------------------------------|:-------------------------------------------------------|
| regime_ridge           |  -0.0042 |   0.0143 |                0.4875 |                  0.0345 |                 5.9087 |           0.6607 | Different weights in calm vs stressed markets                         | Doubles parameters; HMM noise feeds in                 |
| gbm_engineered         |   0.0014 |   0.0135 |                0.3797 |                 -0.01   |                 4.5219 |           0.7381 |                                                                       |                                                        |
| lasso_then_gbm         |   0.0012 |   0.0128 |                0.3001 |                 -0.0286 |                 3.5965 |           0.7083 |                                                                       |                                                        |
| equal_ensemble         |  -0.0031 |   0.0114 |                0.2592 |                 -0.0242 |                 3.5529 |           0.6667 | Simple, robust blend of three model types                             | Keeps weight on models that stopped working            |
| disagreement_sized     |  -0.0033 |   0.0111 |                0.2347 |                 -0.0388 |                 3.275  |           0.6786 | Bets less when models disagree                                        | Disagreement may not mean lower accuracy               |
| gbm_shallow            |   0.0024 |   0.0105 |                0.4596 |                 -0.1281 |                 2.9248 |           0.7173 | Finds interactions (e.g. reversal x low volume); robust               | Slower; harder to explain                              |
| online_weighted        |  -0.0038 |   0.0103 |                0.2663 |                 -0.0802 |                 2.2459 |           0.6429 | Shifts weight to whichever model works lately                         | Chases noise if ICs are noisy                          |
| stack_avg              |  -0.0015 |   0.01   |                0.3107 |                 -0.1055 |                 2.5313 |           0.6726 | Diversifies across model types                                        | Three times the cost; inherits each model's flaws      |
| random_forest          |   0.0013 |   0.0099 |                0.3296 |                 -0.0692 |                 2.9689 |           0.744  | Bagging: low variance, hard to overfit                                | Coarse step functions; slow                            |
| lag_gbm                |   0.0022 |   0.0099 |                0.3161 |                 -0.2105 |                 1.5895 |           0.7083 | Finds nonlinear patterns in raw histories                             | Needs lots of data; easy to overfit                    |
| lag_ridge              |  -0.0041 |   0.0098 |                0.1107 |                 -0.202  |                 1.1768 |           0.6131 | Learns its own reversal/momentum weights from raw lags                | Linear in past returns                                 |
| extra_trees            |   0.0019 |   0.0097 |                0.2823 |                 -0.0313 |                 3.7929 |           0.7173 | Averages many random trees: low variance                              | Coarse; slow on big data                               |
| gbm_deep               |   0.0039 |   0.0094 |                0.4632 |                 -0.1797 |                 3.0899 |           0.7113 | Captures complex interactions                                         | Overfits easily; slow                                  |
| tstat_ic               |   0.0071 |   0.0092 |                0.5828 |                 -0.1626 |                 2.4314 |           0.7496 | Weights by proven reliability; robust (Grinold)                       | Ignores correlation between signals: double-counts     |
| sign_ic                |   0.0072 |   0.0088 |                0.5222 |                 -0.1234 |                 3.149  |           0.7347 | Nothing to overfit; transparent                                       | Ignores how strong each signal is and their overlap    |
| gbm_early_stop         |   0.0033 |   0.0087 |                0.394  |                 -0.1553 |                 1.8014 |           0.7024 | Picks its own complexity on held-out data                             | Random validation split leaks across days              |
| ridge_engineered       |  -0.005  |   0.0086 |                0.3442 |                 -0.0889 |                 2.4764 |           0.6726 |                                                                       |                                                        |
| gbm_l1                 |   0.0018 |   0.0083 |                0.1537 |                 -0.1785 |                 1.6582 |           0.7113 | Boosting that ignores outsized moves                                  | Loses information in large moves                       |
| kernel_rff             |  -0.0005 |   0.008  |                0.3861 |                 -0.1344 |                 2.8671 |           0.6935 | Nonlinear at linear cost                                              | Bandwidth chosen by rule of thumb, not tuned           |
| lasso                  |  -0.0053 |   0.0079 |                0.158  |                 -0.1194 |                 2.4133 |           0.6548 | Sparse, interpretable                                                 | Arbitrary pick between near-duplicates                 |
| elastic_net            |  -0.0054 |   0.0079 |                0.1583 |                 -0.1187 |                 2.4353 |           0.6548 | Drops useless signals                                                 | Unstable choice among correlated signals               |
| ridge_expanding        |   0.0018 |   0.0079 |                0.138  |                 -0.1872 |                 1.9877 |           0.6786 | Uses all history: most stable weights                                 | Slow to adapt to decaying signals                      |
| mlp_64                 |   0.0017 |   0.0078 |                0.3864 |                 -0.1878 |                 2.1606 |           0.6905 | More capacity                                                         | More noise and overfitting risk                        |
| pca15_ridge            |  -0.0008 |   0.0077 |                0.2746 |                 -0.0723 |                 2.9592 |           0.6577 | Keeps more detail than PCA-5                                          | Same issue; more components = more noise               |
| logistic               |  -0.0036 |   0.0076 |                0.1041 |                 -0.1992 |                 1.6123 |           0.6458 | Direction model, less shrinkage                                       | Same; more overfitting                                 |
| pls_3                  |  -0.0041 |   0.0075 |                0.1629 |                 -0.1755 |                 1.4084 |           0.6488 | Components chosen for predictive power, not variance                  | Few components may miss edges                          |
| ridge_100              |  -0.005  |   0.0075 |                0.2074 |                 -0.1264 |                 2.5478 |           0.6548 | Balanced shrinkage                                                    | Linear only                                            |
| logistic_decile_target |  -0.0061 |   0.0074 |                0.2089 |                 -0.1248 |                 2.5263 |           0.5833 | Only learns what separates the extremes (top vs bottom 10%)           | Ignores the middle 80% of stocks                       |
| ridge_1                |  -0.0052 |   0.0074 |                0.2109 |                 -0.1499 |                 2.5169 |           0.6548 | Handles correlated signals jointly                                    | Nearly unpenalised: noisy weights                      |
| logistic_weak          |  -0.0037 |   0.0074 |                0.0967 |                 -0.1911 |                 1.4164 |           0.6429 | Only direction matters: robust to outliers                            | Throws away magnitude                                  |
| rff_wide               |  -0.0021 |   0.0072 |                0.322  |                 -0.1697 |                 2.3939 |           0.6756 | Smooth nonlinearity, close to linear                                  | Little gain over ridge                                 |
| bayesian_ridge         |  -0.0057 |   0.0071 |                0.1537 |                 -0.1294 |                 1.8192 |           0.6518 | Learns its own penalty from the data                                  | Assumes Gaussian noise; linear                         |
| best_single            |   0.0064 |   0.007  |                0.1984 |                 -0.2206 |                 2.4197 |           0.7143 | Simplest possible; easy to monitor                                    | No diversification; chases last period's winner        |
| rff_narrow             |  -0.0017 |   0.0069 |                0.2902 |                 -0.1777 |                 2.0578 |           0.6786 | Captures sharp nonlinear effects                                      | Overfits noise easily                                  |
| pls_8                  |  -0.0055 |   0.0067 |                0.1106 |                 -0.1441 |                 1.5742 |           0.6548 | More detail than PLS-3                                                | Closer to plain regression; more noise                 |
| ridge_1e4              |  -0.0044 |   0.0066 |                0.1449 |                 -0.1475 |                 1.3995 |           0.6488 | Heavy shrinkage, stable weights                                       | Can shrink away real edges                             |
| mlp_16                 |  -0.0005 |   0.0066 |                0.4635 |                 -0.2121 |                 1.8386 |           0.6607 | Smooth nonlinearity                                                   | Random initialisation adds noise between refits        |
| lag_mlp                |  -0.0001 |   0.0065 |                0.1728 |                 -0.3571 |                 1.4819 |           0.6667 | Sequence model: no hand-made features at all                          | Noisiest; random initialisation                        |
| ridge_1e6              |  -0.0015 |   0.0063 |                0.2244 |                 -0.091  |                 2.8466 |           0.6786 | Close to an equal-weighted blend                                      | Barely learns anything                                 |
| mlp_64_32              |   0.0005 |   0.0061 |                0.3466 |                 -0.296  |                 1.4388 |           0.6786 | Deepest network                                                       | Least stable; needs more data than a few years give    |
| linear_svr             |  -0.0043 |   0.0061 |                0.1655 |                 -0.2073 |                 0.7062 |           0.6429 | Margin-based loss: robust                                             | Sensitive to its C setting; linear                     |
| huber                  |  -0.004  |   0.0058 |                0.1732 |                 -0.191  |                 1.4192 |           0.6429 | Downweights extreme returns                                           | Slow; similar to ridge in practice                     |
| ridge_decay            |  -0.0077 |   0.0054 |                0.1953 |                 -0.0916 |                 2.4602 |           0.6339 | Adapts as signals strengthen or fade                                  | Noisier: effectively less data                         |
| gbm_volscaled_target   |   0.004  |   0.0051 |                0.1736 |                 -0.2839 |                 0.2239 |           0.6607 | Nonlinear, risk-scaled target                                         | Same                                                   |
| pca5_ridge             |  -0.0025 |   0.0045 |                0.2903 |                 -0.0507 |                 3.8394 |           0.6577 | Strips redundancy between signals                                     | First components follow variance, not predictive power |
| gbm_resid_target       |   0.006  |   0.0044 |                0.1377 |                 -0.3627 |                 0.4634 |           0.6548 | Nonlinear, on factor-neutral returns                                  | Same; slower                                           |
| ridge_volscaled_target |  -0.0034 |   0.004  |                0.0933 |                 -0.3404 |                -1.0834 |           0.6161 | Every stock's return in units of its own risk                         | Down-weights big movers that may carry the edge        |
| ridge_resid_target     |   0.0015 |   0.0015 |                0.3367 |                 -0.4474 |                -0.4419 |           0.5327 | Learns only the stock-specific part of returns (factor moves removed) | Residuals are estimated, so noisier labels             |

## Signal sets

| set               |   ic_1st |   ic_2nd |   net_sharpe_2nd |
|:------------------|---------:|---------:|-----------------:|
| all               |   0.0052 |   0.0073 |          -0.1617 |
| lags              |   0.0002 |   0.0072 |          -0.2564 |
| lags+price        |   0.0037 |   0.0083 |          -0.1962 |
| price             |   0.0055 |   0.008  |          -0.1497 |
| price+fund        |   0.0051 |   0.007  |          -0.1679 |
| price+pairs       |   0.0033 |   0.0108 |          -0.0674 |
| price+pairs+ideas |   0.0028 |   0.0115 |          -0.0432 |
| reversal          |   0.0061 |   0.0066 |          -0.2015 |

## Forecast horizon

|   horizon |   ic_1st |   ic_2nd |   net_sharpe_1st |   net_sharpe_2nd |   turnover_2nd |
|----------:|---------:|---------:|-----------------:|-----------------:|---------------:|
|         1 |   0.0109 |   0.0068 |          -0.4032 |          -0.1186 |         0.158  |
|         5 |   0.0089 |   0.0062 |          -0.3822 |          -0.1415 |         0.1685 |
|        21 |  -0.0105 |   0.0088 |          -0.5855 |          -0.1928 |         0.1616 |
|        63 |  -0.0141 |   0.0079 |          -0.4932 |          -0.2129 |         0.1466 |

## How to trade a forecast (median over models)

|                  |   net_sharpe_1st |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------------|-----------------:|-----------------:|-------------------:|
| (0.0, 'all')     |           -1.434 |           -1.501 |              1.057 |
| (0.0, 'top300')  |           -0.585 |           -0.651 |              0.867 |
| (5.0, 'all')     |           -0.464 |           -0.21  |              3.142 |
| (5.0, 'top300')  |           -0.323 |           -0.08  |              2.182 |
| (20.0, 'all')    |           -0.421 |            0.02  |              7.98  |
| (20.0, 'top300') |           -0.373 |           -0.001 |              3.834 |

## Strategies positive in both periods (ranked by the weaker period)

| strategy                                                 |   ic_1st |   ic_2nd |   net_sharpe_1st |   net_sharpe_2nd |   breakeven_bp_2nd |   turnover_2nd |
|:---------------------------------------------------------|---------:|---------:|-----------------:|-----------------:|-------------------:|---------------:|
| tstat_ic | reversal | h1 | hl5.0 | top300                |    0.01  |    0.01  |            0.308 |            0.583 |             22.469 |          0.171 |
| tstat_ic | reversal | h1 | hl20.0 | all                  |    0.01  |    0.01  |            0.262 |            0.32  |             19.799 |          0.115 |
| ridge_1e6 | reversal | h1 | hl5.0 | top300               |    0.012 |    0.012 |            0.321 |            0.224 |              7.132 |          0.236 |
| sign_ic | reversal | h1 | hl5.0 | top300                 |    0.01  |    0.01  |            0.219 |            0.522 |             25.482 |          0.136 |
| ridge_1e6 | reversal | h1 | hl20.0 | all                 |    0.012 |    0.012 |            0.235 |            0.213 |             12.93  |          0.11  |
| ridge_1e6 | reversal | h1 | hl20.0 | top300              |    0.012 |    0.012 |            0.213 |            0.205 |              9.683 |          0.124 |
| best_single | price | h5 | hl20.0 | top300               |    0.007 |    0.007 |            0.232 |            0.198 |              7.486 |          0.154 |
| best_single | reversal | h5 | hl20.0 | top300            |    0.008 |    0.007 |            0.38  |            0.198 |              7.486 |          0.154 |
| best_single | reversal | h1 | hl20.0 | top300            |    0.01  |    0.008 |            0.375 |            0.18  |              5.813 |          0.239 |
| ridge_1e6 | reversal | h5 | hl20.0 | all                 |    0.015 |    0.012 |            0.267 |            0.168 |             12.381 |          0.096 |
| ridge_1e6 | reversal | h5 | hl20.0 | top300              |    0.015 |    0.012 |            0.167 |            0.169 |              9.299 |          0.11  |
| tstat_ic | reversal | h1 | hl20.0 | top300               |    0.01  |    0.01  |            0.152 |            0.537 |             33.697 |          0.097 |
| best_single | price+fund | h5 | hl20.0 | top300          |    0.007 |    0.007 |            0.232 |            0.129 |              6.631 |          0.129 |
| sign_ic | reversal | h1 | hl20.0 | all                   |    0.01  |    0.01  |            0.115 |            0.295 |             20.352 |          0.099 |
| best_single | reversal | h5 | hl5.0 | top300             |    0.008 |    0.007 |            0.416 |            0.108 |              4.691 |          0.292 |
| best_single | price | h5 | hl5.0 | top300                |    0.007 |    0.007 |            0.202 |            0.108 |              4.691 |          0.292 |
| sign_ic | reversal | h1 | hl20.0 | top300                |    0.01  |    0.01  |            0.096 |            0.508 |             37.566 |          0.082 |
| ridge_1e6 | reversal | h5 | hl5.0 | top300               |    0.015 |    0.012 |            0.327 |            0.09  |              5.251 |          0.213 |
| ridge_resid_target | reversal | h5 | hl20.0 | all        |    0.008 |    0.008 |            0.081 |            0.219 |             12.988 |          0.092 |
| ridge_expanding | reversal | h5 | hl20.0 | all           |    0.019 |    0.012 |            0.104 |            0.079 |              9.725 |          0.109 |
| best_single | price+fund | h5 | hl5.0 | top300           |    0.007 |    0.007 |            0.202 |            0.074 |              4.489 |          0.239 |
| best_single | price | h1 | hl20.0 | top300               |    0.01  |    0.004 |            0.262 |            0.074 |              4.761 |          0.191 |
| best_single | reversal | h5 | hl20.0 | all               |    0.008 |    0.007 |            0.318 |            0.071 |              8.115 |          0.14  |
| best_single | price | h5 | hl20.0 | all                  |    0.007 |    0.007 |            0.269 |            0.071 |              8.113 |          0.14  |
| ridge_volscaled_target | reversal | h5 | hl20.0 | top300 |    0.008 |    0.001 |            0.139 |            0.071 |              5.902 |          0.119 |

## Strongest and most consistent correlations with future returns

Full list: `best_correlations.csv`. Ranked by the IC in the *weaker* of the two periods; only entries with the same sign in both periods and a positive IC in at least 70% of years. Survivorship-prone = small/illiquid tilts that a universe of today's survivors flatters.

| what   | name                           |   horizon_days |   ic_2006_14 |   ic_2015_26 |   t_2006_14 |   t_2015_26 |   years_positive | survivorship_prone   |
|:-------|:-------------------------------|---------------:|-------------:|-------------:|------------:|------------:|-----------------:|:---------------------|
| signal | amihud                         |             63 |       0.0403 |       0.0218 |      2.8289 |      1.1463 |           0.7407 | True                 |
| signal | rd_intensity                   |             63 |       0.0214 |       0.0255 |      1.2998 |      2.0428 |           0.8333 | False                |
| pair   | rev_5d + downside_beta         |              5 |       0.0205 |       0.0181 |      3.7463 |    nan      |           0.8519 | False                |
| signal | size_proxy                     |             63 |       0.0409 |       0.018  |      3.2682 |      1.1384 |           0.7407 | True                 |
| pair   | low_volume_rev + downside_beta |              5 |       0.0216 |       0.0174 |      3.898  |    nan      |           0.8519 | True                 |
| signal | bollinger_plus_resid_mom       |             21 |       0.0176 |       0.0173 |      2.3364 |      1.8723 |           0.8462 | False                |
| pair   | rev_1d + rev_21d               |              5 |       0.0178 |       0.0168 |      3.4318 |    nan      |           0.8889 | False                |
| signal | bollinger_z                    |             21 |       0.0212 |       0.0164 |      2.4608 |      1.537  |           0.7778 | False                |
| pair   | rev_5d + rev_21d               |              5 |       0.0189 |       0.0161 |      3.5792 |    nan      |           0.8519 | False                |
| pair   | rev_5d + resid_mom             |              5 |       0.0199 |       0.016  |      4.2746 |    nan      |           0.8148 | False                |
| pair   | bollinger_z + resid_mom        |              5 |       0.016  |       0.016  |      3.9971 |    nan      |           0.8889 | False                |
| signal | rev5_plus_resid_mom            |              5 |       0.0189 |       0.0159 |      4.1603 |      2.6998 |           0.8846 | False                |
| pair   | rsi_14 + downside_beta         |              5 |       0.0159 |       0.0168 |      2.9933 |    nan      |           0.8148 | False                |
| pair   | rev_21d + low_volume_rev       |              5 |       0.0199 |       0.0159 |      3.7147 |    nan      |           0.8519 | True                 |
| signal | rev_21d                        |             21 |       0.0158 |       0.0174 |      1.4932 |      1.4738 |           0.7037 | False                |
| pair   | mom_12_1 + high_52w            |              5 |       0.0171 |       0.0158 |      2.6971 |    nan      |           0.8519 | False                |
| pair   | rev_5d + cluster_mom           |              5 |       0.0161 |       0.0158 |      2.6526 |    nan      |           0.7778 | False                |
| pair   | rev_1d + downside_beta         |              5 |       0.0155 |       0.0167 |      2.9396 |    nan      |           0.8519 | False                |
| pair   | low_volume_rev + resid_mom     |              5 |       0.0209 |       0.0155 |      4.3951 |    nan      |           0.8519 | True                 |
| pair   | rev_21d + intraday_rev         |              5 |       0.0163 |       0.0154 |      3.182  |    nan      |           0.8519 | False                |
| pair   | low_volume_rev + cluster_mom   |              5 |       0.017  |       0.0154 |      2.775  |    nan      |           0.8519 | True                 |
| signal | bollinger_plus_resid_mom       |              5 |       0.0153 |       0.0159 |      3.8284 |      2.9369 |           0.9231 | False                |
| pair   | rev_1d + resid_mom             |              5 |       0.0163 |       0.0153 |      3.5449 |    nan      |           0.8519 | False                |
| pair   | bollinger_z + downside_beta    |              5 |       0.0152 |       0.018  |      3.1003 |    nan      |           0.8519 | False                |
| pair   | rev_21d + peer_gap             |              5 |       0.0153 |       0.0151 |      3.3381 |    nan      |           0.8519 | False                |
| pair   | rev_21d + mom_12_1             |              5 |       0.0151 |       0.0153 |      2.6759 |    nan      |           0.7778 | False                |
| pair   | rev_5d + mom_accel             |              5 |       0.0198 |       0.0151 |      3.8556 |    nan      |           0.8889 | False                |
| pair   | rev_21d + bollinger_z          |              5 |       0.0157 |       0.015  |      3.0608 |    nan      |           0.8889 | False                |
| pair   | rsi_14 + resid_mom             |              5 |       0.0168 |       0.015  |      4.111  |    nan      |           0.9259 | False                |
| pair   | rev_1d + bollinger_z           |              5 |       0.0198 |       0.015  |      4.2881 |    nan      |           0.9259 | False                |
| pair   | rev_1d + mom_accel             |              5 |       0.0178 |       0.015  |      3.5758 |    nan      |           0.8889 | False                |
| pair   | rev_1d + rev_5d                |              5 |       0.0222 |       0.0148 |      4.4388 |    nan      |           0.9259 | False                |
| signal | low_volume_rev                 |             21 |       0.0147 |       0.0151 |      1.4399 |      1.2706 |           0.7778 | True                 |
| pair   | low_volume_rev + mom_accel     |              5 |       0.0208 |       0.0147 |      3.9934 |    nan      |           0.8889 | True                 |
| pair   | rev_5d + mom_12_1              |              5 |       0.0224 |       0.0147 |      3.7975 |    nan      |           0.8148 | False                |
| pair   | bollinger_z + mom_12_1         |              5 |       0.0188 |       0.0147 |      3.4143 |    nan      |           0.7778 | False                |
| pair   | rev_1d + intraday_rev_21       |              5 |       0.017  |       0.0146 |      3.3088 |    nan      |           0.8519 | False                |
| pair   | rev_5d + bollinger_z           |              5 |       0.0208 |       0.0146 |      4.3755 |    nan      |           0.8889 | False                |
| pair   | resid_mom + peer_gap           |              5 |       0.0147 |       0.0144 |      4.0457 |    nan      |           0.8148 | False                |
| pair   | rev_1d + rsi_14                |              5 |       0.0207 |       0.0144 |      4.2981 |    nan      |           0.8889 | False                |

