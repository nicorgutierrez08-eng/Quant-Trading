# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                             |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:-------------------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                               |              0.531 |            0.285 |             18.231 |          0.062 |              0.368 |            0.184 |             13.952 |
| all        | momentum (monthly)                               |             -0.164 |           -0.203 |            -37.647 |          0.018 |             -0.301 |           -0.333 |            -68.403 |
| all        | 50/50                                            |              0.118 |           -0.023 |              7.083 |          0.033 |             -0.056 |           -0.198 |             -2.735 |
| all        | regime switch: macro_gauss_K2_s0.0_t1.0          |              0.243 |            0.039 |             10.047 |          0.044 |              0.495 |            0.346 |             23.1   |
| all        | regime switch (signed): macro_gauss_K2_s0.0_t1.0 |              0.212 |            0.017 |              9.153 |          0.043 |              0.681 |            0.561 |             39.763 |
| all        | regime switch: vol_tercile                       |              0.28  |            0.102 |             13.258 |          0.041 |              0.61  |            0.479 |             32.652 |
| all        | regime switch (signed): vol_tercile              |              0.233 |            0.069 |             11.99  |          0.038 |              0.736 |            0.623 |             45.402 |
| top300     | reversal (monthly)                               |              0.218 |            0.081 |              8.764 |          0.063 |              0.295 |            0.205 |             12.215 |
| top300     | momentum (monthly)                               |             -0.156 |           -0.182 |            -35.863 |          0.02  |             -0.234 |           -0.255 |            -44.065 |
| top300     | 50/50                                            |             -0.039 |           -0.121 |             -2.644 |          0.033 |             -0.034 |           -0.106 |             -1.761 |
| top300     | regime switch: macro_gauss_K2_s0.0_t1.0          |             -0.093 |           -0.204 |             -4.611 |          0.043 |              0.525 |            0.456 |             28.204 |
| top300     | regime switch (signed): macro_gauss_K2_s0.0_t1.0 |             -0.125 |           -0.231 |             -6.43  |          0.042 |              0.699 |            0.642 |             46.034 |
| top300     | regime switch: vol_tercile                       |              0.088 |           -0.015 |              4.626 |          0.044 |              0.51  |            0.442 |             27.945 |
| top300     | regime switch (signed): vol_tercile              |              0.082 |           -0.013 |              4.701 |          0.039 |              0.626 |            0.566 |             38.513 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:---------------------------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0085 |   0.0295 |          0.5807 |
| all        | IC in regime 1 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0235 |  -0.045  |          0.4193 |
| top300     | IC in regime 0 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0055 |   0.0253 |          0.5807 |
| top300     | IC in regime 1 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0247 |  -0.0503 |          0.4193 |

