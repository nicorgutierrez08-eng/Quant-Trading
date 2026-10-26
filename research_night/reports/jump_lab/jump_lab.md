# Jump lab: Poisson regressions for next-month jump counts

Deviance explained is measured against the trailing market jump rate (a moving base rate), and against a constant for comparison with the original study. rank_ic: daily cross-sectional rank correlation between predicted and realised next-21-day jump counts. calibration: predicted / realised mean count (1 = right level).

| model                                            | jumps   |   dev_explained_1st |   dev_explained_2nd |   dev_explained_vs_const_2nd |   calibration_2nd |   rank_ic_1st |   rank_ic_t_1st |   rank_ic_2nd |   rank_ic_t_2nd |
|:-------------------------------------------------|:--------|--------------------:|--------------------:|-----------------------------:|------------------:|--------------:|----------------:|--------------:|----------------:|
| original: raw features, one fit on 2004-14       | down    |               0.023 |               0.06  |                        0.019 |             0.782 |         0.082 |          14.503 |         0.087 |          23.159 |
| original: raw features, one fit on 2004-14       | up      |               0.019 |               0.069 |                        0.024 |             0.97  |         0.075 |          11.225 |         0.079 |          17.651 |
| walk-forward, raw features                       | down    |              -0.02  |               0.054 |                        0.012 |             0.942 |         0.072 |          16.582 |         0.088 |          22.672 |
| walk-forward, raw features                       | up      |              -0.017 |               0.048 |                        0.002 |             0.974 |         0.082 |          15.827 |         0.078 |          18.572 |
| walk-forward, ranked features                    | down    |              -0.014 |               0.058 |                        0.016 |             1.016 |         0.087 |          20.558 |         0.11  |          28.504 |
| walk-forward, ranked features                    | up      |              -0.013 |               0.054 |                        0.008 |             1.04  |         0.089 |          17.644 |         0.1   |          23.709 |
| walk-forward, ranked + market offset             | down    |               0.009 |               0.059 |                        0.018 |             1.021 |         0.087 |          20.731 |         0.11  |          28.584 |
| walk-forward, ranked + market offset             | up      |               0.004 |               0.04  |                       -0.006 |             1.015 |         0.089 |          17.589 |         0.1   |          23.75  |
| walk-forward, ranked + offset, negative binomial | down    |               0.01  |               0.061 |                        0.02  |             1.012 |         0.088 |          20.752 |         0.11  |          28.603 |
| walk-forward, ranked + offset, negative binomial | up      |               0.005 |               0.041 |                       -0.005 |             1.011 |         0.089 |          17.586 |         0.1   |          23.852 |

## Signals from the best walk-forward model (walk-forward, ranked + offset, negative binomial)

| signal               |   horizon |   ic_1st |   ic_2nd |   t_1st |   t_2nd |
|:---------------------|----------:|---------:|---------:|--------:|--------:|
| pred_crash_intensity |         1 |  -0.0066 |  -0.0013 | -2.827  | -0.5176 |
| pred_crash_intensity |         5 |  -0.0047 |   0.0001 | -0.8889 |  0.0161 |
| pred_crash_intensity |        21 |   0.0005 |   0.002  |  0.0517 |  0.2062 |
| pred_jump_skew       |         1 |  -0.0011 |  -0.0027 | -0.3839 | -0.7376 |
| pred_jump_skew       |         5 |  -0.0073 |  -0.0065 | -1.1621 | -0.8224 |
| pred_jump_skew       |        21 |  -0.012  |  -0.0132 | -0.9728 | -0.8799 |
| pred_jump_intensity  |         1 |  -0.0062 |  -0.002  | -2.9355 | -0.9963 |
| pred_jump_intensity  |         5 |  -0.0052 |  -0.0016 | -1.0979 | -0.3865 |
| pred_jump_intensity  |        21 |  -0.0003 |  -0.0014 | -0.0356 | -0.1776 |

| signal               |   halflife | universe   |   breakeven_bp_1st |   breakeven_bp_2nd |   net_sharpe_1st |   net_sharpe_2nd |   turnover_1st |
|:---------------------|-----------:|:-----------|-------------------:|-------------------:|-----------------:|-----------------:|---------------:|
| pred_crash_intensity |          0 | all        |              1.251 |              5.667 |           -0.482 |           -0.09  |          0.098 |
| pred_crash_intensity |          0 | top300     |              1.226 |              4.375 |           -0.216 |            0.038 |          0.105 |
| pred_crash_intensity |          5 | all        |              8.596 |             18.307 |            0.001 |            0.246 |          0.034 |
| pred_crash_intensity |          5 | top300     |              5.971 |             10.743 |            0.015 |            0.176 |          0.041 |
| pred_crash_intensity |         20 | all        |             20.42  |             47.16  |            0.13  |            0.415 |          0.02  |
| pred_crash_intensity |         20 | top300     |             11.95  |             22.312 |            0.078 |            0.281 |          0.027 |
| pred_jump_skew       |          0 | all        |             -3.997 |             -8.569 |           -1.303 |           -1.175 |          0.16  |
| pred_jump_skew       |          0 | top300     |             -1.717 |             -5.324 |           -0.608 |           -0.65  |          0.169 |
| pred_jump_skew       |          5 | all        |            -14.156 |            -30.953 |           -0.718 |           -0.725 |          0.049 |
| pred_jump_skew       |          5 | top300     |             -5.321 |            -16.413 |           -0.314 |           -0.439 |          0.056 |
| pred_jump_skew       |         20 | all        |            -25.137 |            -69.142 |           -0.515 |           -0.628 |          0.025 |
| pred_jump_skew       |         20 | top300     |             -6.533 |            -26.691 |           -0.195 |           -0.375 |          0.032 |
| pred_jump_intensity  |          0 | all        |              0.498 |              2.733 |           -0.63  |           -0.344 |          0.11  |
| pred_jump_intensity  |          0 | top300     |              1.389 |              2.927 |           -0.232 |           -0.06  |          0.116 |
| pred_jump_intensity  |          5 | all        |              5.882 |             10.796 |           -0.068 |            0.098 |          0.037 |
| pred_jump_intensity  |          5 | top300     |              5.777 |              7.88  |            0.012 |            0.123 |          0.044 |
| pred_jump_intensity  |         20 | all        |             15.868 |             32.59  |            0.086 |            0.332 |          0.021 |
| pred_jump_intensity  |         20 | top300     |             11.431 |             18.238 |            0.076 |            0.259 |          0.028 |

## Jump intensity as a risk filter on the 5-day reversal book

| book                          |   halflife |   gross_sharpe_1st |   breakeven_bp_1st |   net_sharpe_1st |   gross_sharpe_2nd |   breakeven_bp_2nd |   net_sharpe_2nd |
|:------------------------------|-----------:|-------------------:|-------------------:|-----------------:|-------------------:|-------------------:|-----------------:|
| plain reversal                |          0 |              1.177 |              6.27  |           -0.401 |              0.773 |              4.208 |           -0.52  |
| plain reversal                |          5 |              0.898 |             12.799 |            0.303 |              0.539 |              7.827 |            0.053 |
| drop top-10% crash risk       |          0 |              0.897 |              5.337 |           -0.46  |              0.797 |              4.296 |           -0.514 |
| drop top-10% crash risk       |          5 |              0.595 |              9.052 |            0.06  |              0.526 |              7.321 |            0.018 |
| drop top-20% crash risk       |          0 |              0.894 |              5.308 |           -0.463 |              0.816 |              4.407 |           -0.495 |
| drop top-20% crash risk       |          5 |              0.594 |              8.721 |            0.041 |              0.513 |              6.964 |           -0.008 |
| drop top-10% jump intensity   |          0 |              0.893 |              5.314 |           -0.46  |              0.787 |              4.257 |           -0.513 |
| drop top-10% jump intensity   |          5 |              0.598 |              9.085 |            0.062 |              0.521 |              7.297 |            0.018 |
| weights / predicted intensity |          0 |              0.857 |              5.484 |           -0.391 |              0.784 |              4.478 |           -0.445 |
| weights / predicted intensity |          5 |              0.55  |              9.032 |            0.059 |              0.611 |              9.114 |            0.138 |
| weights / sqrt(intensity)     |          0 |              0.871 |              5.391 |           -0.428 |              0.782 |              4.361 |           -0.478 |
| weights / sqrt(intensity)     |          5 |              0.564 |              9.057 |            0.059 |              0.624 |              9.187 |            0.146 |

