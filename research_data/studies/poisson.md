## Poisson models of jumps and news

### Do jumps cluster? (Poisson: variance / mean = 1)

|            |   mean_per_day |   variance |   var_over_mean |
|:-----------|---------------:|-----------:|----------------:|
| all jumps  |          13.26 |     323.78 |           24.43 |
| up jumps   |           6.93 |      86.3  |           12.46 |
| down jumps |           6.33 |      83.37 |           13.17 |

### Self-exciting jumps: INGARCH(1,1) lambda_t = 0.93 + 0.495 N_t-1 + 0.415 lambda_t-1

Persistence a + b = **0.910** (1 = jump storms never die out; the half-life of a shock is 7.3 days).

| period                    |   ll_ingarch |   ll_constant_rate |   corr(predicted, actual) |
|:--------------------------|-------------:|-------------------:|--------------------------:|
| 2004-2014 (fit)           |      -3.5615 |            -5.7832 |                    0.7296 |
| 2015-2026 (out of sample) |      -5.3266 |           -11.5627 |                    0.771  |

### Poisson HMM on daily jump counts (walk-forward)

Compare brier_skill and rev_ic with the Gaussian HMM table: same tests, different symptoms.

|   states | rates (jumps/day)   | expected_days_in_state   |   pred_ll_1st |   brier_skill_1st |   rev_ic_calm_1st |   rev_ic_stormy_1st |   pred_ll_2nd |   brier_skill_2nd |   rev_ic_calm_2nd |   rev_ic_stormy_2nd |
|---------:|:--------------------|:-------------------------|--------------:|------------------:|------------------:|--------------------:|--------------:|------------------:|------------------:|--------------------:|
|        2 | [8.0, 37.3]         | [15.4, 3.3]              |       -4.0694 |            0.0005 |            0.017  |              0.0289 |       -6.1835 |           -0      |            0.0116 |              0.0168 |
|        3 | [7.2, 27.4, 124.5]  | [12.1, 3.4, 1.8]         |       -3.6578 |            0.0014 |            0.0165 |              0.0431 |       -5.3076 |            0.0016 |            0.0136 |              0.0303 |

### After a jump: market-relative return over the next days (bp)

Negative after an up jump (or positive after a down jump) = reversal; same sign = drift.

| event     | news      | period   |   events |   car_1d_bp |   car_3d_bp |   car_5d_bp |   t_5d |   car_10d_bp |
|:----------|:----------|:---------|---------:|------------:|------------:|------------:|-------:|-------------:|
| up jump   | all       | 1st      |    20258 |       -9.24 |      -19.71 |      -22.72 | -90.26 |       -27.45 |
| up jump   | all       | 2nd      |    24672 |        2.66 |       -6.08 |      -16.41 | -46.85 |       -23.86 |
| up jump   | with news | 1st      |        0 |      nan    |      nan    |      nan    | nan    |       nan    |
| up jump   | with news | 2nd      |    17255 |        3.71 |       -0.91 |       -9.32 | -27.22 |       -13.94 |
| up jump   | no news   | 1st      |    20258 |       -9.24 |      -19.71 |      -22.72 | -90.26 |       -27.45 |
| up jump   | no news   | 2nd      |     7417 |        0.21 |      -18.12 |      -32.9  | -89.43 |       -46.9  |
| down jump | all       | 1st      |    16602 |        1.66 |        8.63 |       12.05 |  38.67 |        14.65 |
| down jump | all       | 2nd      |    24454 |       -4.3  |       -0.35 |        3.42 |   9.13 |        10.61 |
| down jump | with news | 1st      |        0 |      nan    |      nan    |      nan    | nan    |       nan    |
| down jump | with news | 2nd      |    16409 |       -2.39 |        1.5  |        6.05 |  15.82 |        16.84 |
| down jump | no news   | 1st      |    16602 |        1.66 |        8.63 |       12.05 |  38.67 |        14.65 |
| down jump | no news   | 2nd      |     8045 |       -8.2  |       -4.12 |       -1.95 |  -5.44 |        -2.08 |

### Hawkes processes

**Up/down Hawkes** (shared decay, half-life 1.0 days). Branching matrix: expected follow-on jumps of each type caused by one jump (spectral radius 0.80; below 1 = storms die out):

|               |   from up jump |   from down jump |
|:--------------|---------------:|-----------------:|
| -> up jumps   |          0.578 |            0.348 |
| -> down jumps |          0     |            0.802 |

**Two-kernel Hawkes** on all jumps: fast half-life 0.0 days, slow half-life 1.6 days, total branching ratio 0.87.

Average daily log-likelihood (higher is better; the up/down model scores two series, so compare it only across periods):

| period                    |   constant |   INGARCH(1,1) |   Hawkes, 2 kernels |   Hawkes up/down (total) |
|:--------------------------|-----------:|---------------:|--------------------:|-------------------------:|
| 2004-2014 (fit)           |    -5.7832 |        -3.5615 |             -3.5296 |                  -5.3271 |
| 2015-2026 (out of sample) |   -11.5627 |        -5.3266 |             -5.2984 |                  -7.3178 |

### Poisson regression: up-jumps in the next 21 days

109417 training rows (2004-2014), 132471 test rows (2015-2026). Deviance explained: 0.016 in-sample, **-2.225 out of sample**. rate_ratio_per_sd: how much one standard deviation of the feature multiplies the jump rate.

| feature                        |   coef_per_sd |   rate_ratio_per_sd |
|:-------------------------------|--------------:|--------------------:|
| ret_21d                        |        -0.144 |               0.866 |
| log_vol_63                     |        -0.137 |               0.872 |
| own_jumps_slow (63d half-life) |        -0.11  |               0.896 |
| market_jumps_fast              |         0.066 |               1.068 |
| own_jumps_fast (5d half-life)  |        -0.032 |               0.968 |
| log_dollar_volume              |        -0.031 |               0.969 |
| news_fast (5d half-life)       |        -0.027 |               0.973 |
| own_down_jumps_slow            |        -0.016 |               0.984 |
| abn_volume_5d                  |         0.001 |               1.001 |

### Poisson regression: down-jumps in the next 21 days

109417 training rows (2004-2014), 132471 test rows (2015-2026). Deviance explained: 0.014 in-sample, **0.013 out of sample**. rate_ratio_per_sd: how much one standard deviation of the feature multiplies the jump rate.

| feature                        |   coef_per_sd |   rate_ratio_per_sd |
|:-------------------------------|--------------:|--------------------:|
| own_jumps_slow (63d half-life) |        -0.141 |               0.869 |
| log_vol_63                     |        -0.122 |               0.885 |
| ret_21d                        |        -0.117 |               0.89  |
| market_jumps_fast              |         0.086 |               1.089 |
| own_jumps_fast (5d half-life)  |        -0.053 |               0.948 |
| abn_volume_5d                  |         0.018 |               1.019 |
| own_down_jumps_slow            |         0.017 |               1.017 |
| log_dollar_volume              |         0.008 |               1.008 |
| news_fast (5d half-life)       |        -0     |               1     |

### Poisson regression: what makes news arrive

Trained on before 2015. Deviance explained out of sample: **-31.124**.

| feature           |   coef_per_sd |   rate_ratio_per_sd |
|:------------------|--------------:|--------------------:|
| past_news_rate    |        -1.808 |               0.164 |
| abs_ret_today     |        -1.705 |               0.182 |
| log_dollar_volume |         0.89  |               2.435 |
| abn_volume        |         0.57  |               1.769 |
| abs_ret_5d        |         0.529 |               1.697 |
| monday            |         0.173 |               1.189 |


### Jump-intensity and news-surprise signals

IC by horizon:

| signal               |   horizon |   ic_1st |   ic_2nd |   t_1st |   t_2nd |
|:---------------------|----------:|---------:|---------:|--------:|--------:|
| crash_risk           |         1 |   0.0011 |   0.0021 |  1.0818 |  1.5032 |
| crash_risk           |         5 |  -0      |   0.0012 | -0.0095 |  0.3733 |
| crash_risk           |        21 |  -0.0037 |  -0.0028 | -0.7314 | -0.4471 |
| jump_skew            |         1 |   0.0004 |  -0.0027 |  0.3673 | -1.8072 |
| jump_skew            |         5 |   0.0003 |  -0.003  |  0.1055 | -0.8722 |
| jump_skew            |        21 |   0.0022 |   0.0008 |  0.4503 |  0.1165 |
| jump_intensity       |         1 |   0.0019 |  -0.0002 |  1.866  | -0.1535 |
| jump_intensity       |         5 |  -0.0002 |  -0.0017 | -0.0669 | -0.6947 |
| jump_intensity       |        21 |  -0.0039 |  -0.0027 | -0.8546 | -0.5511 |
| news_surprise        |         1 |   0.0004 |   0.0027 |  0.1232 |  2.7979 |
| news_surprise        |         5 |   0.0026 |   0.0045 |  0.3446 |  1.9854 |
| news_surprise        |        21 |   0.0076 |   0.004  |  0.5364 |  0.9303 |
| pred_crash_intensity |         1 |  -0.0088 |  -0.0034 | -4.1129 | -1.5386 |
| pred_crash_intensity |         5 |  -0.0083 |  -0.0042 | -1.6628 | -0.9087 |
| pred_crash_intensity |        21 |  -0.0065 |  -0.0023 | -0.6818 | -0.2583 |
| pred_jump_skew       |         1 |  -0.0099 |   0.0021 | -4.6273 |  1.1293 |
| pred_jump_skew       |         5 |  -0.0162 |   0.0031 | -3.4142 |  0.7667 |
| pred_jump_skew       |        21 |  -0.0252 |   0.0001 | -2.7443 |  0.0106 |
| news_surprise_glm    |         1 |   0.001  |   0.0013 |  0.665  |  1.6355 |
| news_surprise_glm    |         5 |   0.0013 |   0.0018 |  0.3768 |  1.0461 |
| news_surprise_glm    |        21 |   0.0039 |   0.003  |  0.5805 |  0.832  |

| signal               |   halflife | universe   |   breakeven_bp_1st |   breakeven_bp_2nd |   gross_sharpe_1st |   gross_sharpe_2nd |   net_sharpe_1st |   net_sharpe_2nd |   turnover_1st |
|:---------------------|-----------:|:-----------|-------------------:|-------------------:|-------------------:|-------------------:|-----------------:|-----------------:|---------------:|
| crash_risk           |          0 | all        |            -13.833 |            -11.227 |             -0.264 |             -0.179 |           -0.43  |           -0.292 |          0.023 |
| crash_risk           |          0 | top300     |            -10.221 |             -9.478 |             -0.221 |             -0.236 |           -0.358 |           -0.335 |          0.039 |
| crash_risk           |          5 | all        |            -17.543 |            -16.857 |             -0.265 |             -0.198 |           -0.401 |           -0.281 |          0.018 |
| crash_risk           |          5 | top300     |            -12.86  |            -12.904 |             -0.237 |             -0.27  |           -0.358 |           -0.355 |          0.032 |
| crash_risk           |         20 | all        |            -20.679 |            -15.554 |             -0.26  |             -0.151 |           -0.376 |           -0.221 |          0.015 |
| crash_risk           |         20 | top300     |            -11.538 |            -11.771 |             -0.193 |             -0.227 |           -0.305 |           -0.306 |          0.028 |
| jump_skew            |          0 | all        |              7.438 |              8.973 |              0.209 |              0.145 |           -0.032 |            0.031 |          0.027 |
| jump_skew            |          0 | top300     |              2.273 |              9.8   |              0.075 |              0.231 |           -0.13  |            0.138 |          0.043 |
| jump_skew            |          5 | all        |              9.643 |             11.094 |              0.199 |              0.132 |            0.017 |            0.047 |          0.02  |
| jump_skew            |          5 | top300     |              4.394 |             12.427 |              0.116 |              0.239 |           -0.055 |            0.161 |          0.034 |
| jump_skew            |         20 | all        |              9.946 |              4.847 |              0.157 |              0.045 |            0.014 |           -0.022 |          0.015 |
| jump_skew            |         20 | top300     |              1.502 |              9.757 |              0.034 |              0.167 |           -0.117 |            0.097 |          0.029 |
| jump_intensity       |          0 | all        |             -9.587 |             -5.98  |             -0.266 |             -0.218 |           -0.502 |           -0.472 |          0.033 |
| jump_intensity       |          0 | top300     |            -10.762 |             -3.07  |             -0.3   |             -0.149 |           -0.47  |           -0.34  |          0.048 |
| jump_intensity       |          5 | all        |            -14.685 |            -12.228 |             -0.28  |             -0.264 |           -0.447 |           -0.418 |          0.023 |
| jump_intensity       |          5 | top300     |            -13.508 |             -6.168 |             -0.287 |             -0.218 |           -0.423 |           -0.36  |          0.036 |
| jump_intensity       |         20 | all        |            -21.682 |            -19.85  |             -0.304 |             -0.298 |           -0.43  |           -0.407 |          0.016 |
| jump_intensity       |         20 | top300     |            -16.135 |             -8.475 |             -0.287 |             -0.254 |           -0.406 |           -0.377 |          0.03  |
| news_surprise        |          0 | all        |             16.685 |              0.582 |              0.175 |              0.242 |            0.052 |           -2.237 |          0.005 |
| news_surprise        |          0 | top300     |             23.172 |              0.724 |              0.127 |              0.254 |            0.097 |           -1.002 |          0.005 |
| news_surprise        |          5 | all        |             -9.21  |              1.611 |             -0.104 |              0.273 |           -0.244 |           -0.769 |          0.008 |
| news_surprise        |          5 | top300     |             22.316 |             -0.439 |              0.109 |             -0.057 |            0.081 |           -0.535 |          0.005 |
| news_surprise        |         20 | all        |              8.022 |              2.256 |              0.078 |              0.163 |           -0.04  |           -0.288 |          0.005 |
| news_surprise        |         20 | top300     |             30.825 |             -3.713 |              0.15  |             -0.21  |            0.123 |           -0.42  |          0.004 |
| pred_crash_intensity |          0 | all        |             -5.864 |             -1.943 |             -0.416 |             -0.161 |           -1.02  |           -0.744 |          0.164 |
| pred_crash_intensity |          0 | top300     |             -5.971 |              0.166 |             -0.379 |              0.012 |           -0.739 |           -0.261 |          0.17  |
| pred_crash_intensity |          5 | all        |             -6.374 |              3.567 |             -0.162 |              0.105 |           -0.386 |           -0.106 |          0.059 |
| pred_crash_intensity |          5 | top300     |             -4.211 |              7.748 |             -0.104 |              0.23  |           -0.254 |            0.115 |          0.067 |
| pred_crash_intensity |         20 | all        |             -4.125 |             24.424 |             -0.058 |              0.333 |           -0.188 |            0.232 |          0.033 |
| pred_crash_intensity |         20 | top300     |             -2.331 |             22.123 |             -0.035 |              0.372 |           -0.132 |            0.305 |          0.042 |
| pred_jump_skew       |          0 | all        |            -10.355 |              2.457 |             -0.845 |              0.229 |           -1.565 |           -0.473 |          0.194 |
| pred_jump_skew       |          0 | top300     |            -10.48  |              3.131 |             -0.811 |              0.242 |           -1.25  |           -0.05  |          0.222 |
| pred_jump_skew       |          5 | all        |            -24.829 |             -2.216 |             -0.666 |             -0.103 |           -0.917 |           -0.472 |          0.061 |
| pred_jump_skew       |          5 | top300     |            -18.238 |              1.401 |             -0.494 |              0.049 |           -0.66  |           -0.088 |          0.074 |
| pred_jump_skew       |         20 | all        |            -39.976 |            -10.875 |             -0.592 |             -0.232 |           -0.739 |           -0.406 |          0.033 |
| pred_jump_skew       |         20 | top300     |            -24.757 |             -1.272 |             -0.408 |             -0.026 |           -0.517 |           -0.11  |          0.044 |
| news_surprise_glm    |          0 | all        |              4.453 |            -64.573 |              0.101 |             -0.701 |            0.011 |           -0.739 |          0.046 |
| news_surprise_glm    |          0 | top300     |              4.786 |            -60.387 |              0.124 |             -0.82  |            0.023 |           -0.863 |          0.048 |
| news_surprise_glm    |          5 | all        |             -2.195 |           -193.763 |             -0.021 |             -0.702 |           -0.059 |           -0.717 |          0.02  |
| news_surprise_glm    |          5 | top300     |             -1.748 |           -133.825 |             -0.021 |             -0.833 |           -0.068 |           -0.855 |          0.022 |
| news_surprise_glm    |         20 | all        |              4.752 |           -346.113 |              0.029 |             -0.76  |            0.004 |           -0.771 |          0.013 |
| news_surprise_glm    |         20 | top300     |              8.068 |           -187.664 |              0.066 |             -0.904 |            0.032 |           -0.923 |          0.015 |
