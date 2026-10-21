# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                                 |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:-----------------------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                                   |              0.554 |            0.342 |             22.045 |          0.061 |              0.251 |            0.092 |             10.976 |
| all        | momentum (monthly)                                   |             -0.145 |           -0.197 |            -24.948 |          0.02  |             -0.186 |           -0.225 |            -34.263 |
| all        | 50/50                                                |              0.259 |            0.095 |             13.351 |          0.032 |              0.028 |           -0.115 |              1.355 |
| all        | regime switch: macro_gauss_K2_s0.0_t1.0              |              0.582 |            0.382 |             24.628 |          0.044 |              0.398 |            0.268 |             21.228 |
| all        | regime switch (signed): macro_gauss_K2_s0.0_t1.0     |              0.626 |            0.428 |             26.849 |          0.042 |              0.53  |            0.415 |             32.11  |
| all        | stress-only reversal: macro_gauss_K2_s0.0_t1.0       |              0.506 |            0.392 |             36.972 |          0.019 |              0.311 |            0.218 |             22.815 |
| all        | stress-only short momentum: macro_gauss_K2_s0.0_t1.0 |              0.736 |            0.688 |            129.328 |          0.011 |              0.506 |            0.456 |             69.849 |
| all        | calm-only momentum: macro_gauss_K2_s0.0_t1.0         |              0.311 |            0.252 |             45.784 |          0.019 |              0.383 |            0.3   |             32.487 |
| all        | calm-only reversal: macro_gauss_K2_s0.0_t1.0         |              0.323 |            0.129 |             13.965 |          0.046 |             -0.01  |           -0.198 |             -0.365 |
| all        | stress-only long losers: macro_gauss_K2_s0.0_t1.0    |              0.664 |            0.652 |            489.17  |          0.011 |              0.994 |            0.977 |            422.884 |
| all        | stress-only short winners: macro_gauss_K2_s0.0_t1.0  |             -0.454 |           -0.47  |           -237.315 |          0.01  |             -1.038 |           -1.062 |           -284.386 |
| all        | regime switch: vol_tercile                           |              0.376 |            0.191 |             17.15  |          0.04  |              0.58  |            0.466 |             35.554 |
| all        | regime switch (signed): vol_tercile                  |              0.357 |            0.182 |             17.138 |          0.037 |              0.695 |            0.585 |             44.213 |
| all        | stress-only reversal: vol_tercile                    |              0.39  |            0.283 |             29.866 |          0.021 |              0.508 |            0.435 |             48.228 |
| all        | stress-only short momentum: vol_tercile              |              0.458 |            0.418 |             98.112 |          0.01  |              0.633 |            0.586 |             93.737 |
| all        | calm-only momentum: vol_tercile                      |              0.193 |            0.132 |             27.871 |          0.018 |              0.433 |            0.354 |             38.784 |
| all        | calm-only reversal: vol_tercile                      |              0.394 |            0.191 |             16.5   |          0.043 |             -0.244 |           -0.446 |             -8.33  |
| all        | stress-only long losers: vol_tercile                 |              0.321 |            0.311 |            286.218 |          0.01  |              0.914 |            0.898 |            416.345 |
| all        | stress-only short winners: vol_tercile               |             -0.155 |           -0.168 |            -97.208 |          0.01  |             -0.812 |           -0.835 |           -230.898 |
| top300     | reversal (monthly)                                   |              0.305 |            0.185 |             14.052 |          0.061 |              0.201 |            0.123 |              9.644 |
| top300     | momentum (monthly)                                   |             -0.14  |           -0.173 |            -24.846 |          0.022 |             -0.145 |           -0.168 |            -24.279 |
| top300     | 50/50                                                |              0.083 |           -0.01  |              4.972 |          0.032 |              0.02  |           -0.048 |              1.109 |
| top300     | regime switch: macro_gauss_K2_s0.0_t1.0              |              0.311 |            0.202 |             15.943 |          0.042 |              0.433 |            0.374 |             27.333 |
| top300     | regime switch (signed): macro_gauss_K2_s0.0_t1.0     |              0.293 |            0.188 |             15.542 |          0.04  |              0.547 |            0.494 |             38.928 |
| top300     | stress-only reversal: macro_gauss_K2_s0.0_t1.0       |              0.431 |            0.366 |             36.061 |          0.019 |              0.277 |            0.232 |             21.982 |
| top300     | stress-only short momentum: macro_gauss_K2_s0.0_t1.0 |              0.623 |            0.596 |            125.79  |          0.011 |              0.457 |            0.433 |             69.103 |
| top300     | calm-only momentum: macro_gauss_K2_s0.0_t1.0         |              0.262 |            0.225 |             40.45  |          0.021 |              0.372 |            0.329 |             33.961 |
| top300     | calm-only reversal: macro_gauss_K2_s0.0_t1.0         |              0.075 |           -0.034 |              3.765 |          0.046 |             -0.034 |           -0.12  |             -1.499 |
| top300     | stress-only long losers: macro_gauss_K2_s0.0_t1.0    |              0.62  |            0.612 |            461.63  |          0.011 |              0.945 |            0.935 |            372.928 |
| top300     | stress-only short winners: macro_gauss_K2_s0.0_t1.0  |             -0.425 |           -0.435 |           -212.712 |          0.011 |             -0.937 |           -0.952 |           -237.285 |
| top300     | regime switch: vol_tercile                           |              0.197 |            0.094 |             10.469 |          0.041 |              0.503 |            0.446 |             33.128 |
| top300     | regime switch (signed): vol_tercile                  |              0.206 |            0.106 |             11.352 |          0.038 |              0.641 |            0.583 |             41.659 |
| top300     | stress-only reversal: vol_tercile                    |              0.205 |            0.148 |             18.55  |          0.021 |              0.492 |            0.456 |             50.066 |
| top300     | stress-only short momentum: vol_tercile              |              0.381 |            0.359 |             93.674 |          0.011 |              0.589 |            0.567 |             97.082 |
| top300     | calm-only momentum: vol_tercile                      |              0.16  |            0.12  |             23.768 |          0.019 |              0.422 |            0.382 |             40.038 |
| top300     | calm-only reversal: vol_tercile                      |              0.226 |            0.107 |             10.754 |          0.044 |             -0.259 |           -0.351 |            -10.504 |
| top300     | stress-only long losers: vol_tercile                 |              0.294 |            0.288 |            264.439 |          0.011 |              0.879 |            0.871 |            388.206 |
| top300     | stress-only short winners: vol_tercile               |             -0.139 |           -0.148 |            -83.183 |          0.01  |             -0.729 |           -0.743 |           -194.386 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:---------------------------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0097 |   0.0214 |          0.5807 |
| all        | IC in regime 1 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0252 |  -0.0276 |          0.4193 |
| top300     | IC in regime 0 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0077 |   0.0166 |          0.5807 |
| top300     | IC in regime 1 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0275 |  -0.0306 |          0.4193 |

