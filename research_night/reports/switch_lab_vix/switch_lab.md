# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                                |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:----------------------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                                  |              0.554 |            0.342 |             22.045 |          0.061 |              0.251 |            0.092 |             10.976 |
| all        | momentum (monthly)                                  |             -0.145 |           -0.197 |            -24.948 |          0.02  |             -0.186 |           -0.225 |            -34.263 |
| all        | 50/50                                               |              0.259 |            0.095 |             13.351 |          0.032 |              0.028 |           -0.115 |              1.355 |
| all        | regime switch: vix_only_gauss_K2_s0.0_t1.0          |              0.279 |            0.059 |             10.696 |          0.046 |              0.514 |            0.394 |             29.678 |
| all        | regime switch (signed): vix_only_gauss_K2_s0.0_t1.0 |              0.27  |            0.066 |             11.193 |          0.042 |              0.626 |            0.519 |             40.594 |
| all        | regime switch: vix_only_gauss_K3_s0.0_t1.0          |              0.362 |            0.145 |             14.107 |          0.046 |              0.482 |            0.358 |             27.359 |
| all        | regime switch (signed): vix_only_gauss_K3_s0.0_t1.0 |              0.326 |            0.126 |             13.771 |          0.042 |              0.595 |            0.477 |             35.558 |
| all        | regime switch: macro_gauss_K2_s0.0_t1.0             |              0.582 |            0.382 |             24.628 |          0.044 |              0.398 |            0.268 |             21.228 |
| all        | regime switch (signed): macro_gauss_K2_s0.0_t1.0    |              0.626 |            0.428 |             26.849 |          0.042 |              0.53  |            0.415 |             32.11  |
| all        | regime switch: vol_tercile                          |              0.376 |            0.191 |             17.15  |          0.04  |              0.58  |            0.466 |             35.554 |
| all        | regime switch (signed): vol_tercile                 |              0.357 |            0.182 |             17.138 |          0.037 |              0.695 |            0.585 |             44.213 |
| top300     | reversal (monthly)                                  |              0.305 |            0.185 |             14.052 |          0.061 |              0.201 |            0.123 |              9.644 |
| top300     | momentum (monthly)                                  |             -0.14  |           -0.173 |            -24.846 |          0.022 |             -0.145 |           -0.168 |            -24.279 |
| top300     | 50/50                                               |              0.083 |           -0.01  |              4.972 |          0.032 |              0.02  |           -0.048 |              1.109 |
| top300     | regime switch: vix_only_gauss_K2_s0.0_t1.0          |              0.013 |           -0.104 |              0.602 |          0.044 |              0.56  |            0.506 |             39.185 |
| top300     | regime switch (signed): vix_only_gauss_K2_s0.0_t1.0 |              0.031 |           -0.079 |              1.565 |          0.041 |              0.667 |            0.62  |             52.896 |
| top300     | regime switch: vix_only_gauss_K3_s0.0_t1.0          |              0.055 |           -0.059 |              2.647 |          0.046 |              0.466 |            0.408 |             30.216 |
| top300     | regime switch (signed): vix_only_gauss_K3_s0.0_t1.0 |              0.023 |           -0.083 |              1.17  |          0.042 |              0.524 |            0.47  |             36.31  |
| top300     | regime switch: macro_gauss_K2_s0.0_t1.0             |              0.311 |            0.202 |             15.943 |          0.042 |              0.433 |            0.374 |             27.333 |
| top300     | regime switch (signed): macro_gauss_K2_s0.0_t1.0    |              0.293 |            0.188 |             15.542 |          0.04  |              0.547 |            0.494 |             38.928 |
| top300     | regime switch: vol_tercile                          |              0.197 |            0.094 |             10.469 |          0.041 |              0.503 |            0.446 |             33.128 |
| top300     | regime switch (signed): vol_tercile                 |              0.206 |            0.106 |             11.352 |          0.038 |              0.641 |            0.583 |             41.659 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                                                  |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:------------------------------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_only_gauss_K2_s0.0_t1.0), 2015-26 |   0.0071 |   0.024  |          0.6499 |
| all        | IC in regime 1 (vix_only_gauss_K2_s0.0_t1.0), 2015-26 |   0.0331 |  -0.042  |          0.3501 |
| top300     | IC in regime 0 (vix_only_gauss_K2_s0.0_t1.0), 2015-26 |   0.0047 |   0.0191 |          0.6499 |
| top300     | IC in regime 1 (vix_only_gauss_K2_s0.0_t1.0), 2015-26 |   0.0369 |  -0.0445 |          0.3501 |

