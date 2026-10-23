# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                    |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:----------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                      |              0.554 |           -0.08  |             22.045 |          0.061 |              0.251 |           -0.224 |             10.976 |
| all        | momentum (monthly)                      |             -0.145 |           -0.3   |            -24.948 |          0.02  |             -0.186 |           -0.303 |            -34.263 |
| all        | 50/50                                   |              0.259 |           -0.232 |             13.351 |          0.032 |              0.028 |           -0.398 |              1.355 |
| all        | regime switch: vix_gt20                 |              0.61  |            0.125 |             31.872 |          0.039 |              0.648 |            0.369 |             48.761 |
| all        | regime switch (signed): vix_gt20        |              0.633 |            0.162 |             34.12  |          0.036 |              0.774 |            0.511 |             61.742 |
| all        | stress-only reversal: vix_gt20          |              0.624 |            0.291 |             46.932 |          0.029 |              0.482 |            0.293 |             52.995 |
| all        | stress-only short momentum: vix_gt20    |              0.359 |            0.248 |             82.45  |          0.014 |              0.681 |            0.569 |            126.736 |
| all        | calm-only momentum: vix_gt20            |              0.513 |            0.172 |             39.032 |          0.016 |              0.486 |            0.268 |             47.062 |
| all        | calm-only reversal: vix_gt20            |             -0.015 |           -0.82  |             -0.441 |          0.036 |             -0.186 |           -0.773 |             -6.448 |
| all        | stress-only long losers: vix_gt20       |              0.387 |            0.354 |            305.504 |          0.014 |              0.984 |            0.945 |            546.521 |
| all        | stress-only short winners: vix_gt20     |             -0.293 |           -0.345 |           -143.438 |          0.014 |             -0.888 |           -0.946 |           -296.082 |
| all        | regime switch: vol_tercile              |              0.376 |           -0.175 |             17.15  |          0.04  |              0.58  |            0.238 |             35.554 |
| all        | regime switch (signed): vol_tercile     |              0.357 |           -0.168 |             17.138 |          0.037 |              0.695 |            0.365 |             44.213 |
| all        | stress-only reversal: vol_tercile       |              0.39  |            0.067 |             29.866 |          0.021 |              0.508 |            0.287 |             48.228 |
| all        | stress-only short momentum: vol_tercile |              0.458 |            0.338 |             98.112 |          0.01  |              0.633 |            0.491 |             93.737 |
| all        | calm-only momentum: vol_tercile         |              0.193 |            0.011 |             27.871 |          0.018 |              0.433 |            0.196 |             38.784 |
| all        | calm-only reversal: vol_tercile         |              0.394 |           -0.21  |             16.5   |          0.043 |             -0.244 |           -0.836 |             -8.33  |
| all        | stress-only long losers: vol_tercile    |              0.321 |            0.292 |            286.218 |          0.01  |              0.914 |            0.865 |            416.345 |
| all        | stress-only short winners: vol_tercile  |             -0.155 |           -0.194 |            -97.208 |          0.01  |             -0.812 |           -0.882 |           -230.898 |
| top300     | reversal (monthly)                      |              0.305 |           -0.054 |             14.052 |          0.061 |              0.201 |           -0.032 |              9.644 |
| top300     | momentum (monthly)                      |             -0.14  |           -0.24  |            -24.846 |          0.022 |             -0.145 |           -0.215 |            -24.279 |
| top300     | 50/50                                   |              0.083 |           -0.196 |              4.972 |          0.032 |              0.02  |           -0.186 |              1.109 |
| top300     | regime switch: vix_gt20                 |              0.44  |            0.173 |             27.139 |          0.038 |              0.54  |            0.404 |             45.059 |
| top300     | regime switch (signed): vix_gt20        |              0.424 |            0.162 |             26.769 |          0.036 |              0.612 |            0.482 |             53.365 |
| top300     | stress-only reversal: vix_gt20          |              0.47  |            0.274 |             40.766 |          0.029 |              0.42  |            0.326 |             49.008 |
| top300     | stress-only short momentum: vix_gt20    |              0.311 |            0.242 |             78.416 |          0.014 |              0.534 |            0.481 |            111.671 |
| top300     | calm-only momentum: vix_gt20            |              0.4   |            0.198 |             33.155 |          0.017 |              0.372 |            0.255 |             36.807 |
| top300     | calm-only reversal: vix_gt20            |             -0.251 |           -0.691 |             -8.876 |          0.036 |             -0.152 |           -0.423 |             -6.265 |
| top300     | stress-only long losers: vix_gt20       |              0.339 |            0.318 |            271.8   |          0.014 |              0.876 |            0.856 |            476.825 |
| top300     | stress-only short winners: vix_gt20     |             -0.249 |           -0.286 |           -118.213 |          0.014 |             -0.8   |           -0.834 |           -252.96  |
| top300     | regime switch: vol_tercile              |              0.197 |           -0.11  |             10.469 |          0.041 |              0.503 |            0.332 |             33.128 |
| top300     | regime switch (signed): vol_tercile     |              0.206 |           -0.092 |             11.352 |          0.038 |              0.641 |            0.468 |             41.659 |
| top300     | stress-only reversal: vol_tercile       |              0.205 |            0.034 |             18.55  |          0.021 |              0.492 |            0.384 |             50.066 |
| top300     | stress-only short momentum: vol_tercile |              0.381 |            0.314 |             93.674 |          0.011 |              0.589 |            0.522 |             97.082 |
| top300     | calm-only momentum: vol_tercile         |              0.16  |            0.04  |             23.768 |          0.019 |              0.422 |            0.301 |             40.038 |
| top300     | calm-only reversal: vol_tercile         |              0.226 |           -0.13  |             10.754 |          0.044 |             -0.259 |           -0.533 |            -10.504 |
| top300     | stress-only long losers: vol_tercile    |              0.294 |            0.276 |            264.439 |          0.011 |              0.879 |            0.854 |            388.206 |
| top300     | stress-only short winners: vol_tercile  |             -0.139 |           -0.166 |            -83.183 |          0.01  |             -0.729 |           -0.77  |           -194.386 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:-----------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_gt20), 2015-26 |   0.0081 |   0.0205 |          0.7095 |
| all        | IC in regime 1 (vix_gt20), 2015-26 |   0.036  |  -0.0471 |          0.2905 |
| top300     | IC in regime 0 (vix_gt20), 2015-26 |   0.0067 |   0.0152 |          0.7095 |
| top300     | IC in regime 1 (vix_gt20), 2015-26 |   0.0388 |  -0.048  |          0.2905 |

