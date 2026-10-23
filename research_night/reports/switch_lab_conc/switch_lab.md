# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                                 |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:-----------------------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                                   |              0.456 |            0.285 |             22.507 |          0.078 |              0.256 |            0.118 |             12.803 |
| all        | momentum (monthly)                                   |             -0.153 |           -0.201 |            -27.656 |          0.027 |             -0.219 |           -0.256 |            -41.921 |
| all        | 50/50                                                |              0.197 |            0.042 |             10.782 |          0.047 |             -0.004 |           -0.141 |             -0.198 |
| all        | regime switch: macro_gauss_K2_s0.0_t1.0              |              0.489 |            0.311 |             23.215 |          0.061 |              0.368 |            0.249 |             21.281 |
| all        | regime switch (signed): macro_gauss_K2_s0.0_t1.0     |              0.54  |            0.361 |             25.562 |          0.058 |              0.522 |            0.413 |             32.979 |
| all        | stress-only reversal: macro_gauss_K2_s0.0_t1.0       |              0.337 |            0.25  |             32.382 |          0.022 |              0.287 |            0.215 |             27.035 |
| all        | stress-only short momentum: macro_gauss_K2_s0.0_t1.0 |              0.72  |            0.684 |            169.702 |          0.012 |              0.53  |            0.494 |             98.126 |
| all        | calm-only momentum: macro_gauss_K2_s0.0_t1.0         |              0.327 |            0.275 |             54.695 |          0.024 |              0.336 |            0.276 |             39.066 |
| all        | calm-only reversal: macro_gauss_K2_s0.0_t1.0         |              0.324 |            0.173 |             18.074 |          0.058 |              0.037 |           -0.11  |              1.75  |
| all        | stress-only long losers: macro_gauss_K2_s0.0_t1.0    |              0.686 |            0.674 |            525.187 |          0.012 |              0.994 |            0.978 |            466.244 |
| all        | stress-only short winners: macro_gauss_K2_s0.0_t1.0  |             -0.374 |           -0.392 |           -169.449 |          0.012 |             -0.946 |           -0.97  |           -246.329 |
| all        | regime switch: vol_tercile                           |              0.276 |            0.111 |             14.103 |          0.055 |              0.52  |            0.418 |             35.357 |
| all        | regime switch (signed): vol_tercile                  |              0.262 |            0.101 |             13.722 |          0.053 |              0.639 |            0.538 |             43.385 |
| all        | stress-only reversal: vol_tercile                    |              0.304 |            0.222 |             30.301 |          0.025 |              0.474 |            0.419 |             60.342 |
| all        | stress-only short momentum: vol_tercile              |              0.48  |            0.449 |            130.244 |          0.012 |              0.643 |            0.61  |            131.615 |
| all        | calm-only momentum: vol_tercile                      |              0.231 |            0.177 |             37.682 |          0.022 |              0.364 |            0.306 |             43.358 |
| all        | calm-only reversal: vol_tercile                      |              0.341 |            0.182 |             18.322 |          0.054 |             -0.181 |           -0.341 |             -7.704 |
| all        | stress-only long losers: vol_tercile                 |              0.364 |            0.354 |            323.461 |          0.012 |              0.915 |            0.901 |            471.878 |
| all        | stress-only short winners: vol_tercile               |             -0.109 |           -0.125 |            -55.577 |          0.012 |             -0.712 |           -0.735 |           -196.001 |
| top300     | reversal (monthly)                                   |              0.222 |            0.127 |             12.891 |          0.078 |              0.237 |            0.171 |             13.265 |
| top300     | momentum (monthly)                                   |             -0.172 |           -0.201 |            -33.857 |          0.029 |             -0.072 |           -0.093 |            -13.735 |
| top300     | 50/50                                                |              0.005 |           -0.084 |              0.31  |          0.047 |              0.121 |            0.055 |              6.835 |
| top300     | regime switch: macro_gauss_K2_s0.0_t1.0              |              0.225 |            0.129 |             13.077 |          0.058 |              0.493 |            0.441 |             35.146 |
| top300     | regime switch (signed): macro_gauss_K2_s0.0_t1.0     |              0.207 |            0.114 |             12.34  |          0.056 |              0.617 |            0.57  |             48.206 |
| top300     | stress-only reversal: macro_gauss_K2_s0.0_t1.0       |              0.304 |            0.256 |             34.807 |          0.022 |              0.264 |            0.228 |             26.847 |
| top300     | stress-only short momentum: macro_gauss_K2_s0.0_t1.0 |              0.615 |            0.595 |            166.909 |          0.013 |              0.447 |            0.429 |             90.49  |
| top300     | calm-only momentum: macro_gauss_K2_s0.0_t1.0         |              0.242 |            0.211 |             44.147 |          0.025 |              0.447 |            0.417 |             58.452 |
| top300     | calm-only reversal: macro_gauss_K2_s0.0_t1.0         |              0.063 |           -0.021 |              4.104 |          0.058 |              0.049 |           -0.017 |              2.786 |
| top300     | stress-only long losers: macro_gauss_K2_s0.0_t1.0    |              0.635 |            0.628 |            509.176 |          0.012 |              0.909 |            0.901 |            419.123 |
| top300     | stress-only short winners: macro_gauss_K2_s0.0_t1.0  |             -0.338 |           -0.35  |           -153.511 |          0.013 |             -0.815 |           -0.829 |           -208.104 |
| top300     | regime switch: vol_tercile                           |              0.102 |            0.012 |              6.214 |          0.055 |              0.525 |            0.475 |             38.894 |
| top300     | regime switch (signed): vol_tercile                  |              0.123 |            0.031 |              7.345 |          0.054 |              0.671 |            0.617 |             45.997 |
| top300     | stress-only reversal: vol_tercile                    |              0.152 |            0.109 |             18.124 |          0.025 |              0.404 |            0.377 |             54.96  |
| top300     | stress-only short momentum: vol_tercile              |              0.416 |            0.399 |            131.523 |          0.013 |              0.611 |            0.595 |            139.579 |
| top300     | calm-only momentum: vol_tercile                      |              0.172 |            0.138 |             29.81  |          0.023 |              0.507 |            0.478 |             66.797 |
| top300     | calm-only reversal: vol_tercile                      |              0.163 |            0.072 |             10.13  |          0.054 |             -0.088 |           -0.16  |             -4.584 |
| top300     | stress-only long losers: vol_tercile                 |              0.345 |            0.339 |            323.321 |          0.012 |              0.861 |            0.853 |            452.674 |
| top300     | stress-only short winners: vol_tercile               |             -0.102 |           -0.112 |            -51.891 |          0.013 |             -0.574 |           -0.587 |           -157.417 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:---------------------------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0097 |   0.0214 |          0.5807 |
| all        | IC in regime 1 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0252 |  -0.0276 |          0.4193 |
| top300     | IC in regime 0 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0077 |   0.0166 |          0.5807 |
| top300     | IC in regime 1 (macro_gauss_K2_s0.0_t1.0), 2015-26 |   0.0275 |  -0.0306 |          0.4193 |

