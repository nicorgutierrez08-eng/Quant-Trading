# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                    |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:----------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                      |              0.554 |            0.13  |             22.045 |          0.061 |              0.251 |           -0.067 |             10.976 |
| all        | momentum (monthly)                      |             -0.145 |           -0.249 |            -24.948 |          0.02  |             -0.186 |           -0.264 |            -34.263 |
| all        | 50/50                                   |              0.259 |           -0.07  |             13.351 |          0.032 |              0.028 |           -0.257 |              1.355 |
| all        | regime switch: vix_gt20                 |              0.61  |            0.287 |             31.872 |          0.039 |              0.648 |            0.462 |             48.761 |
| all        | regime switch (signed): vix_gt20        |              0.633 |            0.319 |             34.12  |          0.036 |              0.774 |            0.599 |             61.742 |
| all        | stress-only reversal: vix_gt20          |              0.624 |            0.403 |             46.932 |          0.029 |              0.482 |            0.356 |             52.995 |
| all        | stress-only short momentum: vix_gt20    |              0.359 |            0.285 |             82.45  |          0.014 |              0.681 |            0.607 |            126.736 |
| all        | calm-only momentum: vix_gt20            |              0.513 |            0.285 |             39.032 |          0.016 |              0.486 |            0.341 |             47.062 |
| all        | calm-only reversal: vix_gt20            |             -0.015 |           -0.567 |             -0.441 |          0.036 |             -0.186 |           -0.582 |             -6.448 |
| all        | stress-only long losers: vix_gt20       |              0.387 |            0.365 |            305.504 |          0.014 |              0.984 |            0.958 |            546.521 |
| all        | stress-only short winners: vix_gt20     |             -0.293 |           -0.328 |           -143.438 |          0.014 |             -0.888 |           -0.927 |           -296.082 |
| all        | regime switch: vol_tercile              |              0.376 |            0.007 |             17.15  |          0.04  |              0.58  |            0.352 |             35.554 |
| all        | regime switch (signed): vol_tercile     |              0.357 |            0.006 |             17.138 |          0.037 |              0.695 |            0.475 |             44.213 |
| all        | stress-only reversal: vol_tercile       |              0.39  |            0.175 |             29.866 |          0.021 |              0.508 |            0.361 |             48.228 |
| all        | stress-only short momentum: vol_tercile |              0.458 |            0.378 |             98.112 |          0.01  |              0.633 |            0.539 |             93.737 |
| all        | calm-only momentum: vol_tercile         |              0.193 |            0.071 |             27.871 |          0.018 |              0.433 |            0.275 |             38.784 |
| all        | calm-only reversal: vol_tercile         |              0.394 |           -0.011 |             16.5   |          0.043 |             -0.244 |           -0.644 |             -8.33  |
| all        | stress-only long losers: vol_tercile    |              0.321 |            0.301 |            286.218 |          0.01  |              0.914 |            0.882 |            416.345 |
| all        | stress-only short winners: vol_tercile  |             -0.155 |           -0.181 |            -97.208 |          0.01  |             -0.812 |           -0.859 |           -230.898 |
| top300     | reversal (monthly)                      |              0.305 |            0.065 |             14.052 |          0.061 |              0.201 |            0.046 |              9.644 |
| top300     | momentum (monthly)                      |             -0.14  |           -0.207 |            -24.846 |          0.022 |             -0.145 |           -0.192 |            -24.279 |
| top300     | 50/50                                   |              0.083 |           -0.103 |              4.972 |          0.032 |              0.02  |           -0.117 |              1.109 |
| top300     | regime switch: vix_gt20                 |              0.44  |            0.262 |             27.139 |          0.038 |              0.54  |            0.449 |             45.059 |
| top300     | regime switch (signed): vix_gt20        |              0.424 |            0.25  |             26.769 |          0.036 |              0.612 |            0.525 |             53.365 |
| top300     | stress-only reversal: vix_gt20          |              0.47  |            0.34  |             40.766 |          0.029 |              0.42  |            0.357 |             49.008 |
| top300     | stress-only short momentum: vix_gt20    |              0.311 |            0.265 |             78.416 |          0.014 |              0.534 |            0.499 |            111.671 |
| top300     | calm-only momentum: vix_gt20            |              0.4   |            0.265 |             33.155 |          0.017 |              0.372 |            0.294 |             36.807 |
| top300     | calm-only reversal: vix_gt20            |             -0.251 |           -0.548 |             -8.876 |          0.036 |             -0.152 |           -0.333 |             -6.265 |
| top300     | stress-only long losers: vix_gt20       |              0.339 |            0.325 |            271.8   |          0.014 |              0.876 |            0.862 |            476.825 |
| top300     | stress-only short winners: vix_gt20     |             -0.249 |           -0.274 |           -118.213 |          0.014 |             -0.8   |           -0.823 |           -252.96  |
| top300     | regime switch: vol_tercile              |              0.197 |           -0.008 |             10.469 |          0.041 |              0.503 |            0.389 |             33.128 |
| top300     | regime switch (signed): vol_tercile     |              0.206 |            0.007 |             11.352 |          0.038 |              0.641 |            0.525 |             41.659 |
| top300     | stress-only reversal: vol_tercile       |              0.205 |            0.091 |             18.55  |          0.021 |              0.492 |            0.42  |             50.066 |
| top300     | stress-only short momentum: vol_tercile |              0.381 |            0.336 |             93.674 |          0.011 |              0.589 |            0.545 |             97.082 |
| top300     | calm-only momentum: vol_tercile         |              0.16  |            0.08  |             23.768 |          0.019 |              0.422 |            0.341 |             40.038 |
| top300     | calm-only reversal: vol_tercile         |              0.226 |           -0.012 |             10.754 |          0.044 |             -0.259 |           -0.442 |            -10.504 |
| top300     | stress-only long losers: vol_tercile    |              0.294 |            0.282 |            264.439 |          0.011 |              0.879 |            0.862 |            388.206 |
| top300     | stress-only short winners: vol_tercile  |             -0.139 |           -0.157 |            -83.183 |          0.01  |             -0.729 |           -0.757 |           -194.386 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:-----------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_gt20), 2015-26 |   0.0081 |   0.0205 |          0.7095 |
| all        | IC in regime 1 (vix_gt20), 2015-26 |   0.036  |  -0.0471 |          0.2905 |
| top300     | IC in regime 0 (vix_gt20), 2015-26 |   0.0067 |   0.0152 |          0.7095 |
| top300     | IC in regime 1 (vix_gt20), 2015-26 |   0.0388 |  -0.048  |          0.2905 |

