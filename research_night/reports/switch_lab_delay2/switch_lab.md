# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                    |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:----------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                      |              0.389 |            0.172 |             15.084 |          0.061 |              0.141 |           -0.036 |              5.523 |
| all        | momentum (monthly)                      |             -0.071 |           -0.124 |            -11.859 |          0.02  |             -0.168 |           -0.208 |            -30.537 |
| all        | 50/50                                   |              0.213 |            0.045 |             10.738 |          0.032 |             -0.062 |           -0.213 |             -2.886 |
| all        | regime switch: vix_gt20                 |              0.474 |            0.309 |             24.265 |          0.039 |              0.568 |            0.465 |             38.136 |
| all        | regime switch (signed): vix_gt20        |              0.493 |            0.333 |             26.107 |          0.036 |              0.667 |            0.573 |             49.769 |
| all        | stress-only reversal: vix_gt20          |              0.359 |            0.244 |             26.065 |          0.029 |              0.46  |            0.384 |             41.434 |
| all        | stress-only short momentum: vix_gt20    |              0.245 |            0.207 |             54.397 |          0.014 |              0.599 |            0.561 |            108.043 |
| all        | calm-only momentum: vix_gt20            |              0.409 |            0.296 |             31.306 |          0.016 |              0.4   |            0.329 |             39.069 |
| all        | calm-only reversal: vix_gt20            |              0.152 |           -0.129 |              4.553 |          0.036 |             -0.254 |           -0.452 |             -8.833 |
| all        | stress-only long losers: vix_gt20       |              0.345 |            0.334 |            269.417 |          0.014 |              0.924 |            0.91  |            499.055 |
| all        | stress-only short winners: vix_gt20     |             -0.335 |           -0.352 |           -163.355 |          0.014 |             -0.871 |           -0.891 |           -285.794 |
| all        | regime switch: vol_tercile              |              0.318 |            0.13  |             14.258 |          0.04  |              0.543 |            0.416 |             29.576 |
| all        | regime switch (signed): vol_tercile     |              0.286 |            0.107 |             13.494 |          0.037 |              0.641 |            0.525 |             38.174 |
| all        | stress-only reversal: vol_tercile       |              0.222 |            0.111 |             16.564 |          0.021 |              0.485 |            0.398 |             38.408 |
| all        | stress-only short momentum: vol_tercile |              0.455 |            0.415 |             96.459 |          0.01  |              0.574 |            0.525 |             82.661 |
| all        | calm-only momentum: vol_tercile         |              0.297 |            0.234 |             41.33  |          0.018 |              0.378 |            0.3   |             33.965 |
| all        | calm-only reversal: vol_tercile         |              0.324 |            0.115 |             13.155 |          0.043 |             -0.315 |           -0.517 |            -10.732 |
| all        | stress-only long losers: vol_tercile    |              0.382 |            0.372 |            339.157 |          0.01  |              0.859 |            0.842 |            381.225 |
| all        | stress-only short winners: vol_tercile  |             -0.248 |           -0.261 |           -155.549 |          0.01  |             -0.777 |           -0.801 |           -217.778 |
| top300     | reversal (monthly)                      |              0.134 |            0.011 |              6.032 |          0.061 |              0.116 |            0.034 |              5.251 |
| top300     | momentum (monthly)                      |             -0.073 |           -0.107 |            -12.583 |          0.022 |             -0.105 |           -0.129 |            -17.485 |
| top300     | 50/50                                   |              0.025 |           -0.07  |              1.489 |          0.032 |             -0.015 |           -0.087 |             -0.803 |
| top300     | regime switch: vix_gt20                 |              0.253 |            0.163 |             15.399 |          0.038 |              0.451 |            0.404 |             35.773 |
| top300     | regime switch (signed): vix_gt20        |              0.226 |            0.138 |             14.094 |          0.036 |              0.504 |            0.459 |             42.694 |
| top300     | stress-only reversal: vix_gt20          |              0.172 |            0.104 |             14.446 |          0.029 |              0.359 |            0.323 |             36.856 |
| top300     | stress-only short momentum: vix_gt20    |              0.198 |            0.174 |             48.353 |          0.014 |              0.438 |            0.42  |             89.669 |
| top300     | calm-only momentum: vix_gt20            |              0.286 |            0.219 |             23.87  |          0.017 |              0.314 |            0.276 |             31.324 |
| top300     | calm-only reversal: vix_gt20            |             -0.038 |           -0.187 |             -1.368 |          0.036 |             -0.175 |           -0.266 |             -7.204 |
| top300     | stress-only long losers: vix_gt20       |              0.304 |            0.296 |            240.321 |          0.014 |              0.798 |            0.791 |            427.171 |
| top300     | stress-only short winners: vix_gt20     |             -0.311 |           -0.323 |           -146.837 |          0.014 |             -0.792 |           -0.804 |           -247.349 |
| top300     | regime switch: vol_tercile              |              0.093 |           -0.011 |              4.88  |          0.041 |              0.477 |            0.416 |             29.145 |
| top300     | regime switch (signed): vol_tercile     |              0.082 |           -0.019 |              4.471 |          0.038 |              0.57  |            0.51  |             35.583 |
| top300     | stress-only reversal: vol_tercile       |              0.003 |           -0.055 |              0.228 |          0.021 |              0.444 |            0.404 |             40.19  |
| top300     | stress-only short momentum: vol_tercile |              0.366 |            0.343 |             89.095 |          0.011 |              0.524 |            0.501 |             84.651 |
| top300     | calm-only momentum: vol_tercile         |              0.246 |            0.204 |             35.152 |          0.019 |              0.399 |            0.359 |             37.985 |
| top300     | calm-only reversal: vol_tercile         |              0.181 |            0.058 |              8.35  |          0.044 |             -0.287 |           -0.379 |            -11.624 |
| top300     | stress-only long losers: vol_tercile    |              0.346 |            0.34  |            309.869 |          0.011 |              0.815 |            0.806 |            353.255 |
| top300     | stress-only short winners: vol_tercile  |             -0.234 |           -0.243 |           -139.556 |          0.01  |             -0.703 |           -0.717 |           -184.269 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:-----------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_gt20), 2015-26 |   0.0081 |   0.0205 |          0.7095 |
| all        | IC in regime 1 (vix_gt20), 2015-26 |   0.036  |  -0.0471 |          0.2905 |
| top300     | IC in regime 0 (vix_gt20), 2015-26 |   0.0067 |   0.0152 |          0.7095 |
| top300     | IC in regime 1 (vix_gt20), 2015-26 |   0.0388 |  -0.048  |          0.2905 |

