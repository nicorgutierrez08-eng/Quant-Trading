# Switch lab: monthly momentum / reversal book that follows the regime

Both books rebalance every 21 trading days (unit gross, long/short, equal-weighted z-scores: reversal = rev_21d + bollinger_z + rsi_14; momentum = mom_12_1 + resid_mom + high_52w). The switch puts a share of capital in reversal equal to its predicted IC over the sum of the two predicted ICs, where the prediction is the regime probabilities at the rebalance date times each book's per-regime IC on the training block (yearly refits). Net of measured spreads + 1 bp. 2004-2014 chooses, 2015-2026 checks.

| universe   | book                                    |   gross_sharpe_1st |   net_sharpe_1st |   breakeven_bp_1st |   turnover_1st |   gross_sharpe_2nd |   net_sharpe_2nd |   breakeven_bp_2nd |
|:-----------|:----------------------------------------|-------------------:|-----------------:|-------------------:|---------------:|-------------------:|-----------------:|-------------------:|
| all        | reversal (monthly)                      |              0.554 |            0.342 |             22.045 |          0.061 |              0.251 |            0.092 |             10.976 |
| all        | momentum (monthly)                      |             -0.145 |           -0.197 |            -24.948 |          0.02  |             -0.186 |           -0.225 |            -34.263 |
| all        | 50/50                                   |              0.259 |            0.095 |             13.351 |          0.032 |              0.028 |           -0.115 |              1.355 |
| all        | regime switch: vix_gt16                 |              0.446 |            0.26  |             20.04  |          0.042 |              0.416 |            0.292 |             23.179 |
| all        | regime switch (signed): vix_gt16        |              0.42  |            0.243 |             19.848 |          0.039 |              0.515 |            0.404 |             32.174 |
| all        | stress-only reversal: vix_gt16          |              0.638 |            0.49  |             35.955 |          0.041 |              0.277 |            0.174 |             18.33  |
| all        | stress-only short momentum: vix_gt16    |              0.214 |            0.166 |             38.294 |          0.018 |              0.451 |            0.408 |             71.901 |
| all        | calm-only momentum: vix_gt16            |              0.239 |            0.111 |             15.956 |          0.013 |              0.482 |            0.401 |             42.571 |
| all        | calm-only reversal: vix_gt16            |             -0.189 |           -0.473 |             -5.485 |          0.025 |              0     |           -0.196 |              0.007 |
| all        | stress-only long losers: vix_gt16       |              0.405 |            0.391 |            250.539 |          0.018 |              0.905 |            0.89  |            430.511 |
| all        | stress-only short winners: vix_gt16     |             -0.439 |           -0.46  |           -175.632 |          0.018 |             -0.879 |           -0.9   |           -285.656 |
| all        | regime switch: vix_gt18                 |              0.356 |            0.155 |             14.957 |          0.045 |              0.576 |            0.462 |             34.871 |
| all        | regime switch (signed): vix_gt18        |              0.318 |            0.131 |             14.375 |          0.041 |              0.725 |            0.62  |             47.938 |
| all        | stress-only reversal: vix_gt18          |              0.627 |            0.496 |             39.725 |          0.036 |              0.369 |            0.285 |             29.737 |
| all        | stress-only short momentum: vix_gt18    |              0.215 |            0.172 |             42.874 |          0.016 |              0.635 |            0.592 |            101.726 |
| all        | calm-only momentum: vix_gt18            |              0.206 |            0.083 |             14.353 |          0.014 |              0.642 |            0.559 |             54.256 |
| all        | calm-only reversal: vix_gt18            |             -0.103 |           -0.397 |             -2.911 |          0.029 |             -0.116 |           -0.319 |             -4.011 |
| all        | stress-only long losers: vix_gt18       |              0.373 |            0.36  |            255.916 |          0.016 |              0.944 |            0.929 |            449.174 |
| all        | stress-only short winners: vix_gt18     |             -0.397 |           -0.416 |           -171.765 |          0.016 |             -0.786 |           -0.806 |           -246.302 |
| all        | regime switch: vix_gt20                 |              0.61  |            0.449 |             31.872 |          0.039 |              0.648 |            0.555 |             48.761 |
| all        | regime switch (signed): vix_gt20        |              0.633 |            0.476 |             34.12  |          0.036 |              0.774 |            0.687 |             61.742 |
| all        | stress-only reversal: vix_gt20          |              0.624 |            0.514 |             46.932 |          0.029 |              0.482 |            0.419 |             52.995 |
| all        | stress-only short momentum: vix_gt20    |              0.359 |            0.322 |             82.45  |          0.014 |              0.681 |            0.644 |            126.736 |
| all        | calm-only momentum: vix_gt20            |              0.513 |            0.399 |             39.032 |          0.016 |              0.486 |            0.414 |             47.062 |
| all        | calm-only reversal: vix_gt20            |             -0.015 |           -0.296 |             -0.441 |          0.036 |             -0.186 |           -0.386 |             -6.448 |
| all        | stress-only long losers: vix_gt20       |              0.387 |            0.376 |            305.504 |          0.014 |              0.984 |            0.971 |            546.521 |
| all        | stress-only short winners: vix_gt20     |             -0.293 |           -0.311 |           -143.438 |          0.014 |             -0.888 |           -0.908 |           -296.082 |
| all        | regime switch: vix_gt22                 |              0.616 |            0.468 |             35.22  |          0.035 |              0.504 |            0.412 |             38.129 |
| all        | regime switch (signed): vix_gt22        |              0.723 |            0.579 |             42.924 |          0.032 |              0.617 |            0.53  |             49.463 |
| all        | stress-only reversal: vix_gt22          |              0.676 |            0.583 |             59.866 |          0.023 |              0.401 |            0.346 |             50.641 |
| all        | stress-only short momentum: vix_gt22    |              0.518 |            0.483 |            127.329 |          0.012 |              0.575 |            0.543 |            125.944 |
| all        | calm-only momentum: vix_gt22            |              0.645 |            0.547 |             57.579 |          0.018 |              0.336 |            0.269 |             35.398 |
| all        | calm-only reversal: vix_gt22            |             -0.035 |           -0.307 |             -1.091 |          0.042 |             -0.075 |           -0.274 |             -2.618 |
| all        | stress-only long losers: vix_gt22       |              0.433 |            0.423 |            368.026 |          0.012 |              0.924 |            0.913 |            598.995 |
| all        | stress-only short winners: vix_gt22     |             -0.223 |           -0.239 |           -119.359 |          0.012 |             -0.925 |           -0.941 |           -351.728 |
| all        | regime switch: vix_gt25                 |              0.551 |            0.4   |             30.859 |          0.033 |              0.273 |            0.177 |             19.713 |
| all        | regime switch (signed): vix_gt25        |              0.716 |            0.573 |             42.626 |          0.03  |              0.274 |            0.18  |             20.221 |
| all        | stress-only reversal: vix_gt25          |              0.671 |            0.594 |             71.419 |          0.018 |              0.349 |            0.315 |             69.263 |
| all        | stress-only short momentum: vix_gt25    |              0.643 |            0.612 |            170.845 |          0.01  |              0.305 |            0.282 |             89.655 |
| all        | calm-only momentum: vix_gt25            |              0.623 |            0.538 |             62.774 |          0.02  |              0.011 |           -0.047 |              1.367 |
| all        | calm-only reversal: vix_gt25            |              0.053 |           -0.205 |              1.729 |          0.047 |              0.014 |           -0.186 |              0.469 |
| all        | stress-only long losers: vix_gt25       |              0.464 |            0.455 |            431.235 |          0.01  |              0.616 |            0.607 |            533.929 |
| all        | stress-only short winners: vix_gt25     |             -0.164 |           -0.178 |            -95.629 |          0.01  |             -0.731 |           -0.744 |           -358.705 |
| all        | regime switch: vol_tercile              |              0.376 |            0.191 |             17.15  |          0.04  |              0.58  |            0.466 |             35.554 |
| all        | regime switch (signed): vol_tercile     |              0.357 |            0.182 |             17.138 |          0.037 |              0.695 |            0.585 |             44.213 |
| all        | stress-only reversal: vol_tercile       |              0.39  |            0.283 |             29.866 |          0.021 |              0.508 |            0.435 |             48.228 |
| all        | stress-only short momentum: vol_tercile |              0.458 |            0.418 |             98.112 |          0.01  |              0.633 |            0.586 |             93.737 |
| all        | calm-only momentum: vol_tercile         |              0.193 |            0.132 |             27.871 |          0.018 |              0.433 |            0.354 |             38.784 |
| all        | calm-only reversal: vol_tercile         |              0.394 |            0.191 |             16.5   |          0.043 |             -0.244 |           -0.446 |             -8.33  |
| all        | stress-only long losers: vol_tercile    |              0.321 |            0.311 |            286.218 |          0.01  |              0.914 |            0.898 |            416.345 |
| all        | stress-only short winners: vol_tercile  |             -0.155 |           -0.168 |            -97.208 |          0.01  |             -0.812 |           -0.835 |           -230.898 |
| top300     | reversal (monthly)                      |              0.305 |            0.185 |             14.052 |          0.061 |              0.201 |            0.123 |              9.644 |
| top300     | momentum (monthly)                      |             -0.14  |           -0.173 |            -24.846 |          0.022 |             -0.145 |           -0.168 |            -24.279 |
| top300     | 50/50                                   |              0.083 |           -0.01  |              4.972 |          0.032 |              0.02  |           -0.048 |              1.109 |
| top300     | regime switch: vix_gt16                 |              0.18  |            0.079 |              9.557 |          0.042 |              0.397 |            0.336 |             24.405 |
| top300     | regime switch (signed): vix_gt16        |              0.173 |            0.075 |              9.525 |          0.039 |              0.476 |            0.42  |             31.732 |
| top300     | stress-only reversal: vix_gt16          |              0.433 |            0.347 |             28.218 |          0.041 |              0.26  |            0.21  |             18.829 |
| top300     | stress-only short momentum: vix_gt16    |              0.188 |            0.158 |             36.496 |          0.019 |              0.374 |            0.352 |             63.138 |
| top300     | calm-only momentum: vix_gt16            |              0.156 |            0.085 |             11.709 |          0.014 |              0.429 |            0.386 |             39.096 |
| top300     | calm-only reversal: vix_gt16            |             -0.35  |           -0.499 |            -12.226 |          0.025 |             -0.07  |           -0.159 |             -2.988 |
| top300     | stress-only long losers: vix_gt16       |              0.363 |            0.354 |            223.83  |          0.019 |              0.856 |            0.847 |            361.092 |
| top300     | stress-only short winners: vix_gt16     |             -0.4   |           -0.416 |           -153.745 |          0.019 |             -0.801 |           -0.813 |           -234.862 |
| top300     | regime switch: vix_gt18                 |              0.092 |           -0.013 |              4.782 |          0.043 |              0.669 |            0.614 |             45.703 |
| top300     | regime switch (signed): vix_gt18        |              0.079 |           -0.021 |              4.335 |          0.04  |              0.789 |            0.737 |             57.013 |
| top300     | stress-only reversal: vix_gt18          |              0.453 |            0.376 |             33.143 |          0.036 |              0.37  |            0.329 |             32.443 |
| top300     | stress-only short momentum: vix_gt18    |              0.2   |            0.173 |             43.325 |          0.017 |              0.613 |            0.592 |            108.189 |
| top300     | calm-only momentum: vix_gt18            |              0.167 |            0.098 |             12.937 |          0.015 |              0.687 |            0.642 |             60.065 |
| top300     | calm-only reversal: vix_gt18            |             -0.336 |           -0.489 |            -11.279 |          0.03  |             -0.186 |           -0.278 |             -7.585 |
| top300     | stress-only long losers: vix_gt18       |              0.331 |            0.322 |            227.708 |          0.017 |              0.925 |            0.917 |            412.724 |
| top300     | stress-only short winners: vix_gt18     |             -0.345 |           -0.359 |           -144.131 |          0.017 |             -0.671 |           -0.683 |           -195.71  |
| top300     | regime switch: vix_gt20                 |              0.44  |            0.351 |             27.139 |          0.038 |              0.54  |            0.495 |             45.059 |
| top300     | regime switch (signed): vix_gt20        |              0.424 |            0.337 |             26.769 |          0.036 |              0.612 |            0.569 |             53.365 |
| top300     | stress-only reversal: vix_gt20          |              0.47  |            0.405 |             40.766 |          0.029 |              0.42  |            0.388 |             49.008 |
| top300     | stress-only short momentum: vix_gt20    |              0.311 |            0.288 |             78.416 |          0.014 |              0.534 |            0.516 |            111.671 |
| top300     | calm-only momentum: vix_gt20            |              0.4   |            0.332 |             33.155 |          0.017 |              0.372 |            0.333 |             36.807 |
| top300     | calm-only reversal: vix_gt20            |             -0.251 |           -0.401 |             -8.876 |          0.036 |             -0.152 |           -0.243 |             -6.265 |
| top300     | stress-only long losers: vix_gt20       |              0.339 |            0.332 |            271.8   |          0.014 |              0.876 |            0.869 |            476.825 |
| top300     | stress-only short winners: vix_gt20     |             -0.249 |           -0.262 |           -118.213 |          0.014 |             -0.8   |           -0.812 |           -252.96  |
| top300     | regime switch: vix_gt22                 |              0.524 |            0.443 |             35.782 |          0.036 |              0.435 |            0.392 |             38.379 |
| top300     | regime switch (signed): vix_gt22        |              0.61  |            0.53  |             42.526 |          0.033 |              0.493 |            0.452 |             46.058 |
| top300     | stress-only reversal: vix_gt22          |              0.546 |            0.49  |             55.103 |          0.023 |              0.378 |            0.35  |             50.541 |
| top300     | stress-only short momentum: vix_gt22    |              0.499 |            0.478 |            135.293 |          0.012 |              0.464 |            0.449 |            114.663 |
| top300     | calm-only momentum: vix_gt22            |              0.61  |            0.551 |             58.94  |          0.019 |              0.276 |            0.239 |             28.862 |
| top300     | calm-only reversal: vix_gt22            |             -0.268 |           -0.412 |            -10.007 |          0.042 |             -0.097 |           -0.188 |             -3.947 |
| top300     | stress-only long losers: vix_gt22       |              0.418 |            0.411 |            362.614 |          0.013 |              0.829 |            0.823 |            527.09  |
| top300     | stress-only short winners: vix_gt22     |             -0.188 |           -0.199 |            -97.646 |          0.012 |             -0.835 |           -0.846 |           -298.821 |
| top300     | regime switch: vix_gt25                 |              0.427 |            0.348 |             30.084 |          0.033 |              0.192 |            0.153 |             18.469 |
| top300     | regime switch (signed): vix_gt25        |              0.558 |            0.483 |             42.294 |          0.03  |              0.175 |            0.137 |             17.631 |
| top300     | stress-only reversal: vix_gt25          |              0.556 |            0.509 |             67.173 |          0.018 |              0.305 |            0.288 |             64.198 |
| top300     | stress-only short momentum: vix_gt25    |              0.597 |            0.578 |            176.696 |          0.01  |              0.214 |            0.203 |             71.642 |
| top300     | calm-only momentum: vix_gt25            |              0.567 |            0.514 |             61.057 |          0.021 |             -0.011 |           -0.044 |             -1.346 |
| top300     | calm-only reversal: vix_gt25            |             -0.18  |           -0.32  |             -6.976 |          0.047 |              0.002 |           -0.091 |              0.077 |
| top300     | stress-only long losers: vix_gt25       |              0.44  |            0.434 |            420.782 |          0.011 |              0.54  |            0.535 |            467.979 |
| top300     | stress-only short winners: vix_gt25     |             -0.13  |           -0.14  |            -74.075 |          0.01  |             -0.699 |           -0.707 |           -323.049 |
| top300     | regime switch: vol_tercile              |              0.197 |            0.094 |             10.469 |          0.041 |              0.503 |            0.446 |             33.128 |
| top300     | regime switch (signed): vol_tercile     |              0.206 |            0.106 |             11.352 |          0.038 |              0.641 |            0.583 |             41.659 |
| top300     | stress-only reversal: vol_tercile       |              0.205 |            0.148 |             18.55  |          0.021 |              0.492 |            0.456 |             50.066 |
| top300     | stress-only short momentum: vol_tercile |              0.381 |            0.359 |             93.674 |          0.011 |              0.589 |            0.567 |             97.082 |
| top300     | calm-only momentum: vol_tercile         |              0.16  |            0.12  |             23.768 |          0.019 |              0.422 |            0.382 |             40.038 |
| top300     | calm-only reversal: vol_tercile         |              0.226 |            0.107 |             10.754 |          0.044 |             -0.259 |           -0.351 |            -10.504 |
| top300     | stress-only long losers: vol_tercile    |              0.294 |            0.288 |            264.439 |          0.011 |              0.879 |            0.871 |            388.206 |
| top300     | stress-only short winners: vol_tercile  |             -0.139 |           -0.148 |            -83.183 |          0.01  |             -0.729 |           -0.743 |           -194.386 |

## Monthly IC of each book by regime, 2015-2026

| universe   | book                               |   ic_rev |   ic_mom |   share_of_days |
|:-----------|:-----------------------------------|---------:|---------:|----------------:|
| all        | IC in regime 0 (vix_gt16), 2015-26 |   0.0118 |   0.0295 |          0.4442 |
| all        | IC in regime 1 (vix_gt16), 2015-26 |   0.0198 |  -0.0222 |          0.5558 |
| top300     | IC in regime 0 (vix_gt16), 2015-26 |   0.0076 |   0.0272 |          0.4442 |
| top300     | IC in regime 1 (vix_gt16), 2015-26 |   0.0228 |  -0.0276 |          0.5558 |

