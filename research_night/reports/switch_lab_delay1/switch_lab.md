# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                    |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:----------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                      |              0.415 |            0.199 |             16.17  |          0.061 |              0.301 |            0.139 |             12.874 |
| all        | momentum (monthly)                      |             -0.094 |           -0.147 |            -15.714 |          0.02  |             -0.203 |           -0.242 |            -37.28  |
| all        | 50/50                                   |              0.208 |            0.042 |             10.588 |          0.032 |              0.05  |           -0.097 |              2.37  |
| all        | regime switch: vix_gt20                 |              0.534 |            0.371 |             27.587 |          0.039 |              0.687 |            0.592 |             50.432 |
| all        | regime switch (signed): vix_gt20        |              0.557 |            0.4   |             29.784 |          0.036 |              0.78  |            0.693 |             61.514 |
| all        | stress-only reversal: vix_gt20          |              0.457 |            0.344 |             33.591 |          0.029 |              0.568 |            0.504 |             60.093 |
| all        | stress-only short momentum: vix_gt20    |              0.297 |            0.259 |             66.395 |          0.014 |              0.676 |            0.639 |            124.934 |
| all        | calm-only momentum: vix_gt20            |              0.481 |            0.368 |             36.716 |          0.016 |              0.45  |            0.377 |             43.616 |
| all        | calm-only reversal: vix_gt20            |              0.012 |           -0.272 |              0.347 |          0.036 |             -0.196 |           -0.396 |             -6.781 |
| all        | stress-only long losers: vix_gt20       |              0.362 |            0.351 |            282.875 |          0.014 |              0.976 |            0.963 |            536.659 |
| all        | stress-only short winners: vix_gt20     |             -0.313 |           -0.33  |           -152.836 |          0.014 |             -0.88  |           -0.9   |           -289.766 |
| all        | regime switch: vol_tercile              |              0.329 |            0.143 |             14.849 |          0.04  |              0.63  |            0.514 |             37.666 |
| all        | regime switch (signed): vol_tercile     |              0.309 |            0.131 |             14.656 |          0.037 |              0.724 |            0.614 |             45.569 |
| all        | stress-only reversal: vol_tercile       |              0.29  |            0.182 |             21.996 |          0.021 |              0.557 |            0.482 |             51.13  |
| all        | stress-only short momentum: vol_tercile |              0.445 |            0.405 |             94.537 |          0.01  |              0.631 |            0.584 |             92.836 |
| all        | calm-only momentum: vol_tercile         |              0.257 |            0.195 |             36.009 |          0.018 |              0.401 |            0.322 |             35.957 |
| all        | calm-only reversal: vol_tercile         |              0.296 |            0.088 |             12.06  |          0.043 |             -0.213 |           -0.417 |             -7.255 |
| all        | stress-only long losers: vol_tercile    |              0.332 |            0.322 |            295.389 |          0.01  |              0.903 |            0.887 |            407.54  |
| all        | stress-only short winners: vol_tercile  |             -0.182 |           -0.195 |           -114.02  |          0.01  |             -0.793 |           -0.816 |           -223.845 |
| top300     | reversal (monthly)                      |              0.153 |            0.031 |              6.909 |          0.061 |              0.22  |            0.142 |             10.463 |
| top300     | momentum (monthly)                      |             -0.101 |           -0.135 |            -17.551 |          0.022 |             -0.145 |           -0.168 |            -24.163 |
| top300     | 50/50                                   |              0.011 |           -0.083 |              0.65  |          0.032 |              0.036 |           -0.034 |              1.922 |
| top300     | regime switch: vix_gt20                 |              0.313 |            0.224 |             19.157 |          0.038 |              0.561 |            0.515 |             46.4   |
| top300     | regime switch (signed): vix_gt20        |              0.295 |            0.207 |             18.488 |          0.036 |              0.611 |            0.568 |             53.236 |
| top300     | stress-only reversal: vix_gt20          |              0.277 |            0.21  |             23.473 |          0.029 |              0.469 |            0.437 |             53.674 |
| top300     | stress-only short momentum: vix_gt20    |              0.256 |            0.232 |             62.838 |          0.014 |              0.526 |            0.509 |            109.505 |
| top300     | calm-only momentum: vix_gt20            |              0.355 |            0.288 |             29.521 |          0.017 |              0.361 |            0.322 |             35.782 |
| top300     | calm-only reversal: vix_gt20            |             -0.203 |           -0.354 |             -7.108 |          0.036 |             -0.17  |           -0.261 |             -6.985 |
| top300     | stress-only long losers: vix_gt20       |              0.321 |            0.314 |            254.931 |          0.014 |              0.86  |            0.853 |            465.691 |
| top300     | stress-only short winners: vix_gt20     |             -0.28  |           -0.292 |           -132.478 |          0.014 |             -0.788 |           -0.799 |           -246.17  |
| top300     | regime switch: vol_tercile              |              0.117 |            0.013 |              6.147 |          0.041 |              0.537 |            0.48  |             34.894 |
| top300     | regime switch (signed): vol_tercile     |              0.123 |            0.023 |              6.749 |          0.038 |              0.646 |            0.589 |             41.934 |
| top300     | stress-only reversal: vol_tercile       |              0.08  |            0.022 |              7.188 |          0.021 |              0.501 |            0.465 |             50.109 |
| top300     | stress-only short momentum: vol_tercile |              0.358 |            0.336 |             87.256 |          0.011 |              0.586 |            0.564 |             96.001 |
| top300     | calm-only momentum: vol_tercile         |              0.198 |            0.156 |             28.49  |          0.019 |              0.415 |            0.374 |             39.464 |
| top300     | calm-only reversal: vol_tercile         |              0.134 |            0.012 |              6.22  |          0.044 |             -0.235 |           -0.327 |             -9.474 |
| top300     | stress-only long losers: vol_tercile    |              0.299 |            0.293 |            268.188 |          0.011 |              0.855 |            0.847 |            375.444 |
| top300     | stress-only short winners: vol_tercile  |             -0.168 |           -0.177 |           -100.13  |          0.01  |             -0.696 |           -0.71  |           -183.772 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:-----------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_gt20), 2015-26 |   0.0081 |   0.0205 |          0.7095 |
| all        | IC in regime 1 (vix_gt20), 2015-26 |   0.036  |  -0.0471 |          0.2905 |
| top300     | IC in regime 0 (vix_gt20), 2015-26 |   0.0067 |   0.0152 |          0.7095 |
| top300     | IC in regime 1 (vix_gt20), 2015-26 |   0.0388 |  -0.048  |          0.2905 |

