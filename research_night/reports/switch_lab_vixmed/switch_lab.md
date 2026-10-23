# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                      |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:------------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                        |              0.554 |            0.342 |             22.045 |          0.061 |              0.251 |            0.092 |             10.976 |
| all        | momentum (monthly)                        |             -0.145 |           -0.197 |            -24.948 |          0.02  |             -0.186 |           -0.225 |            -34.263 |
| all        | 50/50                                     |              0.259 |            0.095 |             13.351 |          0.032 |              0.028 |           -0.115 |              1.355 |
| all        | regime switch: vix_gt_median              |              0.335 |            0.155 |             15.679 |          0.037 |              0.613 |            0.496 |             36.3   |
| all        | regime switch (signed): vix_gt_median     |              0.309 |            0.135 |             14.958 |          0.035 |              0.804 |            0.701 |             54.299 |
| all        | stress-only reversal: vix_gt_median       |              0.479 |            0.373 |             36.904 |          0.022 |              0.407 |            0.323 |             32.806 |
| all        | stress-only short momentum: vix_gt_median |              0.443 |            0.404 |             96.134 |          0.01  |              0.658 |            0.615 |            104.085 |
| all        | calm-only momentum: vix_gt_median         |              0.202 |            0.142 |             29.018 |          0.017 |              0.676 |            0.591 |             56.299 |
| all        | calm-only reversal: vix_gt_median         |              0.308 |            0.102 |             12.674 |          0.042 |             -0.176 |           -0.379 |             -6.047 |
| all        | stress-only long losers: vix_gt_median    |              0.361 |            0.351 |            321.208 |          0.011 |              0.964 |            0.949 |            452.793 |
| all        | stress-only short winners: vix_gt_median  |             -0.225 |           -0.238 |           -138.503 |          0.01  |             -0.793 |           -0.814 |           -245.005 |
| all        | regime switch: vol_tercile                |              0.376 |            0.191 |             17.15  |          0.04  |              0.58  |            0.466 |             35.554 |
| all        | regime switch (signed): vol_tercile       |              0.357 |            0.182 |             17.138 |          0.037 |              0.695 |            0.585 |             44.213 |
| all        | stress-only reversal: vol_tercile         |              0.39  |            0.283 |             29.866 |          0.021 |              0.508 |            0.435 |             48.228 |
| all        | stress-only short momentum: vol_tercile   |              0.458 |            0.418 |             98.112 |          0.01  |              0.633 |            0.586 |             93.737 |
| all        | calm-only momentum: vol_tercile           |              0.193 |            0.132 |             27.871 |          0.018 |              0.433 |            0.354 |             38.784 |
| all        | calm-only reversal: vol_tercile           |              0.394 |            0.191 |             16.5   |          0.043 |             -0.244 |           -0.446 |             -8.33  |
| all        | stress-only long losers: vol_tercile      |              0.321 |            0.311 |            286.218 |          0.01  |              0.914 |            0.898 |            416.345 |
| all        | stress-only short winners: vol_tercile    |             -0.155 |           -0.168 |            -97.208 |          0.01  |             -0.812 |           -0.835 |           -230.898 |
| top300     | reversal (monthly)                        |              0.305 |            0.185 |             14.052 |          0.061 |              0.201 |            0.123 |              9.644 |
| top300     | momentum (monthly)                        |             -0.14  |           -0.173 |            -24.846 |          0.022 |             -0.145 |           -0.168 |            -24.279 |
| top300     | 50/50                                     |              0.083 |           -0.01  |              4.972 |          0.032 |              0.02  |           -0.048 |              1.109 |
| top300     | regime switch: vix_gt_median              |              0.131 |            0.042 |              8.084 |          0.034 |              0.713 |            0.658 |             48.572 |
| top300     | regime switch (signed): vix_gt_median     |              0.093 |            0.006 |              5.96  |          0.033 |              0.889 |            0.841 |             68.905 |
| top300     | stress-only reversal: vix_gt_median       |              0.322 |            0.264 |             29.23  |          0.022 |              0.4   |            0.359 |             35.078 |
| top300     | stress-only short momentum: vix_gt_median |              0.411 |            0.39  |            101.935 |          0.011 |              0.63  |            0.609 |            110.068 |
| top300     | calm-only momentum: vix_gt_median         |              0.205 |            0.166 |             30.342 |          0.019 |              0.712 |            0.667 |             61.459 |
| top300     | calm-only reversal: vix_gt_median         |              0.11  |           -0.009 |              5.157 |          0.043 |             -0.228 |           -0.32  |             -9.251 |
| top300     | stress-only long losers: vix_gt_median    |              0.342 |            0.336 |            308.714 |          0.011 |              0.947 |            0.939 |            418.271 |
| top300     | stress-only short winners: vix_gt_median  |             -0.19  |           -0.199 |           -112.243 |          0.011 |             -0.684 |           -0.696 |           -196.769 |
| top300     | regime switch: vol_tercile                |              0.197 |            0.094 |             10.469 |          0.041 |              0.503 |            0.446 |             33.128 |
| top300     | regime switch (signed): vol_tercile       |              0.206 |            0.106 |             11.352 |          0.038 |              0.641 |            0.583 |             41.659 |
| top300     | stress-only reversal: vol_tercile         |              0.205 |            0.148 |             18.55  |          0.021 |              0.492 |            0.456 |             50.066 |
| top300     | stress-only short momentum: vol_tercile   |              0.381 |            0.359 |             93.674 |          0.011 |              0.589 |            0.567 |             97.082 |
| top300     | calm-only momentum: vol_tercile           |              0.16  |            0.12  |             23.768 |          0.019 |              0.422 |            0.382 |             40.038 |
| top300     | calm-only reversal: vol_tercile           |              0.226 |            0.107 |             10.754 |          0.044 |             -0.259 |           -0.351 |            -10.504 |
| top300     | stress-only long losers: vol_tercile      |              0.294 |            0.288 |            264.439 |          0.011 |              0.879 |            0.871 |            388.206 |
| top300     | stress-only short winners: vol_tercile    |             -0.139 |           -0.148 |            -83.183 |          0.01  |             -0.729 |           -0.743 |           -194.386 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                                    |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:----------------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_gt_median), 2015-26 |   0.0098 |   0.0234 |          0.5912 |
| all        | IC in regime 1 (vix_gt_median), 2015-26 |   0.0256 |  -0.0317 |          0.4088 |
| top300     | IC in regime 0 (vix_gt_median), 2015-26 |   0.0069 |   0.0194 |          0.5912 |
| top300     | IC in regime 1 (vix_gt_median), 2015-26 |   0.0292 |  -0.0358 |          0.4088 |

