# Model zoo: what forecasts best, and does it last?

272 fitted models, 1632 traded strategies (model x signal set x horizon x smoothing x universe), refit yearly on 5 years, costs from measured spreads. Period 1 = 2006-2014, period 2 = 2015-2026.

## Does picking the best in period 1 work in period 2?

* Rank correlation of net Sharpe between the periods: **0.63** (IC: -0.15).
* With 1632 strategies tried, the best period-1 Sharpe expected from pure luck is up to **3.16** (deflated-Sharpe hurdle; an upper bound, since the strategies overlap heavily).
* Top 1 by period 1: Sharpe 0.54 in period 1 -> **-0.02** in period 2.
* Top 10 by period 1: Sharpe 0.42 in period 1 -> **0.09** in period 2.
* Top 50 by period 1: Sharpe 0.26 in period 1 -> **-0.00** in period 2.
* Ensemble of the 10 best period-1 models (equal weight): IC 0.0085 -> **0.0040**; best single of them in period 2: 0.0214.

## Model families: results, pros and cons

| name            |   ic_1st |   ic_2nd |   net_sharpe_2nd_best |   net_sharpe_2nd_median |   breakeven_2nd_median |   years_positive | pros                                                    | cons                                                   |
|:----------------|---------:|---------:|----------------------:|------------------------:|-----------------------:|-----------------:|:--------------------------------------------------------|:-------------------------------------------------------|
| regime_ridge    |  -0.0005 |   0.0126 |                0.4691 |                  0.0008 |                 4.4527 |           0.6607 | Different weights in calm vs stressed markets           | Doubles parameters; HMM noise feeds in                 |
| sign_ic         |   0.0079 |   0.0094 |                0.496  |                 -0.1405 |                 3.0715 |           0.7739 | Nothing to overfit; transparent                         | Ignores how strong each signal is and their overlap    |
| ridge_expanding |   0.0045 |   0.0092 |                0.1392 |                 -0.1246 |                 2.4208 |           0.7143 | Uses all history: most stable weights                   | Slow to adapt to decaying signals                      |
| tstat_ic        |   0.0075 |   0.0092 |                0.5567 |                 -0.2159 |                 2.2482 |           0.7752 | Weights by proven reliability; robust (Grinold)         | Ignores correlation between signals: double-counts     |
| stack_avg       |   0.0014 |   0.0091 |                0.2475 |                 -0.1514 |                 2.2548 |           0.6845 | Diversifies across model types                          | Three times the cost; inherits each model's flaws      |
| gbm_shallow     |   0.005  |   0.0087 |                0.3283 |                 -0.2176 |                 2.0974 |           0.7202 | Finds interactions (e.g. reversal x low volume); robust | Slower; harder to explain                              |
| random_forest   |   0.0037 |   0.0085 |                0.2475 |                 -0.132  |                 2.2983 |           0.7202 | Bagging: low variance, hard to overfit                  | Coarse step functions; slow                            |
| extra_trees     |   0.0046 |   0.0084 |                0.1677 |                 -0.0992 |                 2.91   |           0.7262 | Averages many random trees: low variance                | Coarse; slow on big data                               |
| gbm_early_stop  |   0.0051 |   0.0082 |                0.3271 |                 -0.2439 |                 1.7411 |           0.7202 | Picks its own complexity on held-out data               | Random validation split leaks across days              |
| lasso           |  -0.0022 |   0.0081 |                0.0992 |                 -0.154  |                 2.5515 |           0.6429 | Sparse, interpretable                                   | Arbitrary pick between near-duplicates                 |
| elastic_net     |  -0.0022 |   0.0081 |                0.0995 |                 -0.1532 |                 2.5894 |           0.6429 | Drops useless signals                                   | Unstable choice among correlated signals               |
| best_single     |   0.0066 |   0.0078 |                0.1582 |                 -0.2135 |                 2.9887 |           0.7321 | Simplest possible; easy to monitor                      | No diversification; chases last period's winner        |
| gbm_deep        |   0.0054 |   0.0077 |                0.2987 |                 -0.3339 |                 1.5292 |           0.75   | Captures complex interactions                           | Overfits easily; slow                                  |
| ridge_100       |  -0.0022 |   0.0077 |                0.1813 |                 -0.1639 |                 2.5116 |           0.6429 | Balanced shrinkage                                      | Linear only                                            |
| pls_3           |  -0.0012 |   0.0076 |                0.1155 |                 -0.1841 |                 2.3485 |           0.6488 | Components chosen for predictive power, not variance    | Few components may miss edges                          |
| ridge_1         |  -0.0021 |   0.0076 |                0.1849 |                 -0.1664 |                 2.3466 |           0.6429 | Handles correlated signals jointly                      | Nearly unpenalised: noisy weights                      |
| logistic        |  -0.0005 |   0.0076 |                0.0712 |                 -0.2075 |                 2.1085 |           0.6548 | Direction model, less shrinkage                         | Same; more overfitting                                 |
| logistic_weak   |  -0.0008 |   0.0075 |                0.0605 |                 -0.2067 |                 1.8845 |           0.6548 | Only direction matters: robust to outliers              | Throws away magnitude                                  |
| bayesian_ridge  |  -0.0023 |   0.0072 |                0.1046 |                 -0.1622 |                 2.4514 |           0.6369 | Learns its own penalty from the data                    | Assumes Gaussian noise; linear                         |
| ridge_1e4       |  -0.0013 |   0.0072 |                0.0937 |                 -0.1636 |                 2.1045 |           0.6548 | Heavy shrinkage, stable weights                         | Can shrink away real edges                             |
| kernel_rff      |   0.0027 |   0.0072 |                0.3304 |                 -0.1619 |                 2.127  |           0.6845 | Nonlinear at linear cost                                | Bandwidth chosen by rule of thumb, not tuned           |
| linear_svr      |  -0.0011 |   0.0071 |                0.1094 |                 -0.18   |                 1.5419 |           0.6488 | Margin-based loss: robust                               | Sensitive to its C setting; linear                     |
| gbm_l1          |   0.0044 |   0.007  |                0.1223 |                 -0.2337 |                 1.1446 |           0.7262 | Boosting that ignores outsized moves                    | Loses information in large moves                       |
| pca15_ridge     |   0.0008 |   0.007  |                0.1596 |                 -0.1732 |                 2.3182 |           0.6667 | Keeps more detail than PCA-5                            | Same issue; more components = more noise               |
| pls_8           |  -0.0022 |   0.0069 |                0.0848 |                 -0.1731 |                 2.088  |           0.6429 | More detail than PLS-3                                  | Closer to plain regression; more noise                 |
| ridge_1e6       |   0.0016 |   0.0069 |                0.1873 |                 -0.0864 |                 3.1484 |           0.7024 | Close to an equal-weighted blend                        | Barely learns anything                                 |
| rff_wide        |   0.0013 |   0.0068 |                0.2748 |                 -0.1655 |                 2.0154 |           0.6845 | Smooth nonlinearity, close to linear                    | Little gain over ridge                                 |
| huber           |  -0.0009 |   0.0066 |                0.0646 |                 -0.191  |                 1.8233 |           0.6488 | Downweights extreme returns                             | Slow; similar to ridge in practice                     |
| rff_narrow      |   0.0012 |   0.0065 |                0.2334 |                 -0.2345 |                 1.9052 |           0.6845 | Captures sharp nonlinear effects                        | Overfits noise easily                                  |
| mlp_16          |   0.0015 |   0.0062 |                0.26   |                 -0.2202 |                 1.6902 |           0.6786 | Smooth nonlinearity                                     | Random initialisation adds noise between refits        |
| pca5_ridge      |  -0.0007 |   0.006  |                0.2442 |                 -0.0767 |                 3.031  |           0.6726 | Strips redundancy between signals                       | First components follow variance, not predictive power |
| ridge_decay     |  -0.0039 |   0.006  |                0.1507 |                 -0.1182 |                 2.1268 |           0.6488 | Adapts as signals strengthen or fade                    | Noisier: effectively less data                         |
| mlp_64_32       |   0.0035 |   0.0056 |                0.4049 |                 -0.3379 |                 1.1923 |           0.6964 | Deepest network                                         | Least stable; needs more data than a few years give    |
| mlp_64          |   0.0026 |   0.0053 |                0.2376 |                 -0.3027 |                 1.8312 |           0.6845 | More capacity                                           | More noise and overfitting risk                        |

## Signal sets

| set      |   ic_1st |   ic_2nd |   net_sharpe_2nd |
|:---------|---------:|---------:|-----------------:|
| price    |   0.0059 |   0.0077 |          -0.1481 |
| reversal |   0.0079 |   0.0069 |          -0.2101 |

## Forecast horizon

|   horizon |   ic_1st |   ic_2nd |   net_sharpe_1st |   net_sharpe_2nd |   turnover_2nd |
|----------:|---------:|---------:|-----------------:|-----------------:|---------------:|
|         1 |   0.011  |   0.0085 |          -0.5144 |          -0.0811 |         0.2285 |
|         5 |   0.0116 |   0.0052 |          -0.3689 |          -0.1676 |         0.2298 |
|        21 |  -0.0093 |   0.0079 |          -0.8953 |          -0.2096 |         0.1949 |
|        63 |  -0.002  |   0.0079 |          -0.5631 |          -0.2378 |         0.1785 |

## How to trade a forecast (median over models)

|                  |   net_sharpe_1st |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------------|-----------------:|-----------------:|-------------------:|
| (0.0, 'all')     |           -1.976 |           -1.641 |              1.178 |
| (0.0, 'top300')  |           -0.734 |           -0.672 |              0.9   |
| (5.0, 'all')     |           -0.567 |           -0.224 |              3.069 |
| (5.0, 'top300')  |           -0.364 |           -0.079 |              2.382 |
| (20.0, 'all')    |           -0.509 |            0.011 |              7.572 |
| (20.0, 'top300') |           -0.436 |            0.017 |              4.405 |

## Strategies positive in both periods (ranked by the weaker period)

| strategy                                       |   ic_1st |   ic_2nd |   net_sharpe_1st |   net_sharpe_2nd |   breakeven_bp_2nd |   turnover_2nd |
|:-----------------------------------------------|---------:|---------:|-----------------:|-----------------:|-------------------:|---------------:|
| tstat_ic | reversal | h1 | hl5.0 | top300      |    0.01  |    0.01  |            0.357 |            0.557 |             21.672 |          0.17  |
| tstat_ic | reversal | h1 | hl20.0 | all        |    0.01  |    0.01  |            0.312 |            0.292 |             18.871 |          0.116 |
| sign_ic | reversal | h1 | hl5.0 | top300       |    0.01  |    0.009 |            0.274 |            0.496 |             24.224 |          0.137 |
| ridge_1e6 | reversal | h1 | hl20.0 | all       |    0.012 |    0.012 |            0.3   |            0.187 |             12.299 |          0.109 |
| ridge_1e6 | reversal | h1 | hl5.0 | top300     |    0.012 |    0.012 |            0.406 |            0.18  |              6.493 |          0.235 |
| tstat_ic | reversal | h1 | hl20.0 | top300     |    0.01  |    0.01  |            0.18  |            0.527 |             33.262 |          0.097 |
| ridge_1e6 | reversal | h1 | hl20.0 | top300    |    0.012 |    0.012 |            0.264 |            0.179 |              8.976 |          0.123 |
| ridge_1e6 | reversal | h5 | hl20.0 | all       |    0.015 |    0.011 |            0.344 |            0.154 |             11.971 |          0.095 |
| ridge_1e6 | reversal | h5 | hl20.0 | top300    |    0.015 |    0.011 |            0.212 |            0.152 |              8.785 |          0.109 |
| sign_ic | reversal | h1 | hl20.0 | all         |    0.01  |    0.009 |            0.15  |            0.263 |             18.939 |          0.101 |
| best_single | reversal | h1 | hl20.0 | top300  |    0.009 |    0.009 |            0.423 |            0.145 |              5.418 |          0.239 |
| sign_ic | reversal | h1 | hl20.0 | top300      |    0.01  |    0.009 |            0.119 |            0.496 |             36.626 |          0.083 |
| best_single | price | h5 | hl20.0 | top300     |    0.007 |    0.007 |            0.298 |            0.115 |              5.773 |          0.164 |
| best_single | reversal | h5 | hl20.0 | top300  |    0.008 |    0.007 |            0.492 |            0.115 |              5.773 |          0.164 |
| extra_trees | reversal | h1 | hl5.0 | top300   |    0.016 |    0.011 |            0.065 |            0.146 |              5.981 |          0.241 |
| ridge_expanding | reversal | h5 | hl20.0 | all |    0.019 |    0.012 |            0.125 |            0.065 |              9.261 |          0.109 |
| ridge_1e6 | reversal | h5 | hl5.0 | top300     |    0.015 |    0.011 |            0.413 |            0.057 |              4.707 |          0.212 |
| best_single | price | h1 | hl20.0 | top300     |    0.009 |    0.005 |            0.341 |            0.037 |              4.251 |          0.191 |
| pca5_ridge | reversal | h1 | hl20.0 | top300   |    0.01  |    0.011 |            0.036 |            0.177 |              8.658 |          0.129 |
| pca5_ridge | reversal | h5 | hl20.0 | top300   |    0.01  |    0.007 |            0.031 |            0.233 |             10.873 |          0.122 |
| pca5_ridge | reversal | h5 | hl5.0 | top300    |    0.01  |    0.007 |            0.348 |            0.029 |              4.188 |          0.236 |
| sign_ic | reversal | h5 | hl20.0 | all         |    0.013 |    0.008 |            0.356 |            0.023 |              7.672 |          0.123 |
| pca5_ridge | reversal | h5 | hl20.0 | all      |    0.01  |    0.007 |            0.023 |            0.11  |             10.305 |          0.107 |
| ridge_1e6 | reversal | h1 | hl5.0 | all        |    0.012 |    0.012 |            0.019 |            0.088 |              8.332 |          0.223 |
| ridge_1e6 | reversal | h63 | hl20.0 | top300   |    0.011 |    0.008 |            0.021 |            0.017 |              4.377 |          0.112 |

## Strongest and most consistent correlations with future returns

Full list: `best_correlations.csv`. Ranked by the IC in the *weaker* of the two periods; only entries with the same sign in both periods and a positive IC in at least 70% of years. Survivorship-prone = small/illiquid tilts that a universe of today's survivors flatters.

| what   | name                        |   horizon_days |   ic_2006_14 |   ic_2015_26 |   t_2006_14 |   t_2015_26 |   years_positive | survivorship_prone   |
|:-------|:----------------------------|---------------:|-------------:|-------------:|------------:|------------:|-----------------:|:---------------------|
| signal | amihud                      |             63 |       0.0226 |       0.037  |      1.2315 |      2.4804 |           0.7407 | True                 |
| signal | size_proxy                  |             63 |       0.0195 |       0.0365 |      1.3066 |      2.8275 |           0.7407 | True                 |
| signal | rev_5d                      |              5 |       0.0179 |       0.0174 |      2.9236 |      3.3054 |           0.8519 | False                |
| signal | low_volume_rev              |              5 |       0.0198 |       0.017  |      3.1914 |      3.1581 |           0.8148 | True                 |
| signal | bollinger_z                 |             63 |       0.0164 |       0.0178 |      0.9433 |      1.2347 |           0.7407 | False                |
| signal | rsi_14                      |             63 |       0.0157 |       0.017  |      0.7825 |      1.1051 |           0.7407 | False                |
| signal | vol_price_corr              |             63 |       0.0138 |       0.0152 |      1.2867 |      1.5427 |           0.7407 | False                |
| signal | amihud                      |             21 |       0.0137 |       0.0209 |      1.1753 |      2.2328 |           0.7407 | True                 |
| signal | rev_1d                      |              5 |       0.013  |       0.0151 |      2.1666 |      2.9573 |           0.9259 | False                |
| signal | peer_gap                    |              5 |       0.0128 |       0.0124 |      2.9119 |      3.7754 |           0.8519 | False                |
| model  | regime_ridge on price       |              5 |       0.0131 |       0.0122 |      1.8117 |      1.6355 |           0.7143 | False                |
| model  | ridge_1e6 on reversal       |              1 |       0.012  |       0.0125 |      5.102  |      4.4862 |           0.9048 | False                |
| signal | bollinger_z                 |             21 |       0.0119 |       0.0231 |      1.1801 |      2.6146 |           0.7407 | False                |
| model  | ridge_expanding on reversal |              5 |       0.0194 |       0.0117 |      2.6749 |      1.5357 |           0.8095 | False                |
| model  | ridge_1e6 on price          |              1 |       0.0117 |       0.0118 |      3.3922 |      3.704  |           0.8571 | False                |
| signal | rev_1d                      |              1 |       0.0115 |       0.0156 |      4.1376 |      6.6089 |           0.8889 | False                |
| model  | best_single on price        |             63 |       0.0118 |       0.0114 |      0.9346 |      0.7813 |           0.7619 | False                |
| model  | ridge_expanding on reversal |              1 |       0.0127 |       0.0113 |      4.2138 |      3.534  |           0.9524 | False                |
| model  | ridge_expanding on price    |              1 |       0.0127 |       0.0113 |      4.2344 |      3.5984 |           0.8571 | False                |
| model  | ridge_1e6 on reversal       |              5 |       0.0152 |       0.0112 |      2.7653 |      1.9318 |           0.9048 | False                |
| signal | low_volume_rev              |              1 |       0.0111 |       0.012  |      3.9464 |      4.8184 |           0.963  | True                 |
| signal | peer_gap                    |             21 |       0.011  |       0.0117 |      1.3628 |      1.9451 |           0.8889 | False                |
| signal | bollinger_z                 |              5 |       0.011  |       0.0168 |      2.1168 |      3.5106 |           0.8889 | False                |
| model  | ridge_expanding on price    |              5 |       0.0177 |       0.0109 |      2.5543 |      1.5147 |           0.7619 | False                |
| signal | resid_rev_5d                |             21 |       0.012  |       0.0108 |      2.1594 |      2.4518 |           0.8462 | False                |
| model  | extra_trees on reversal     |              1 |       0.0165 |       0.0107 |      7.7359 |      4.1014 |           0.9524 | False                |
| signal | low_volume_rev              |             21 |       0.0105 |       0.0176 |      0.8958 |      1.7368 |           0.8148 | True                 |
| signal | rev_5d                      |             63 |       0.0105 |       0.0131 |      0.56   |      0.8131 |           0.8148 | False                |
| signal | rev_5d                      |              1 |       0.0105 |       0.0128 |      3.7488 |      5.2183 |           0.963  | False                |
| model  | extra_trees on price        |              1 |       0.0152 |       0.0105 |      4.5912 |      3.3233 |           0.8571 | False                |
| model  | ridge_1e4 on reversal       |              1 |       0.0104 |       0.0105 |      4.0426 |      3.4157 |           0.8095 | False                |
| model  | elastic_net on reversal     |              1 |       0.0103 |       0.011  |      4.0191 |      3.5719 |           0.8095 | False                |
| model  | lasso on reversal           |              1 |       0.0103 |       0.011  |      4.0148 |      3.5712 |           0.8095 | False                |
| model  | bayesian_ridge on reversal  |              1 |       0.0103 |       0.0103 |      3.9731 |      3.3887 |           0.8095 | False                |
| model  | stack_avg on reversal       |              1 |       0.015  |       0.0102 |      6.2881 |      3.5684 |           0.9524 | False                |
| model  | pca5_ridge on reversal      |              1 |       0.01   |       0.0111 |      4.3641 |      3.8212 |           0.9048 | False                |
| model  | pca5_ridge on price         |              1 |       0.0103 |       0.01   |      3.0915 |      3.321  |           0.8571 | False                |
| model  | pls_3 on price              |              1 |       0.0102 |       0.0099 |      3.2549 |      3.104  |           0.9048 | False                |
| signal | intraday_rev                |              5 |       0.0098 |       0.0131 |      1.712  |      2.7831 |           0.8889 | False                |
| model  | tstat_ic on reversal        |              1 |       0.0098 |       0.0097 |      5.3821 |      2.998  |           0.9375 | False                |

