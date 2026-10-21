# Regime lab: HMM variants scored on money, walk-forward

Every variant is refit yearly on all data to date; 2004-2014 ('1st') is for choosing, 2015-2026 ('2nd') is the check. Gains are Sharpe differences against the matching regime-free baseline (volatility-managed market exposure; constant-gross reversal or momentum book; a 50/50 reversal/momentum split).

## Statistical scores

| features   | emission   |   states |   sticky |   pred_ll_1st |   pred_ll_2nd |   brier_skill_1st |   brier_skill_2nd |   vol_r2_vs_trailing_1st |   vol_r2_vs_trailing_2nd |   confident_share_2nd |
|:-----------|:-----------|---------:|---------:|--------------:|--------------:|------------------:|------------------:|-------------------------:|-------------------------:|----------------------:|
| vixplus    | gauss      |        2 |        0 |       -0.9659 |        0.493  |           -0.0022 |           -0.0124 |                  -0.1822 |                  -0.0558 |                0.9127 |
| vixplus    | gauss      |        3 |        0 |        0.2462 |        1.3957 |           -0.0013 |           -0.0015 |                  -0.2054 |                  -0.0197 |                0.9042 |
| vixplus    | t          |        2 |        0 |       -0.4804 |        1.4137 |           -0.0039 |           -0.0033 |                  -0.2824 |                  -0.035  |                0.8948 |
| vixplus    | t          |        3 |        0 |        0.8132 |        1.7511 |            0      |           -0.0041 |                  -0.3205 |                  -0.0304 |                0.8985 |
| vix_dterm  | gauss      |        2 |        0 |       -1.6935 |       -0.0331 |           -0.0019 |            0.0073 |                  -0.3482 |                  -0.0146 |                0.9228 |
| vix_dterm  | gauss      |        3 |        0 |       -1.2048 |        0.2838 |            0.0201 |            0.0059 |                  -0.4658 |                  -0.0087 |                0.9049 |
| vix_dterm  | t          |        2 |        0 |       -1.3884 |        0.2038 |            0.0065 |           -0.0193 |                  -0.2721 |                  -0.0614 |                0.9509 |
| vix_dterm  | t          |        3 |        0 |       -0.7116 |        0.4724 |            0.0305 |            0.0099 |                  -0.1337 |                  -0.024  |                0.9269 |

## Market timing: regime-conditional exposure vs. volatility-managed (10% target)

| features   | emission   |   states |   sticky |   timing_volmanaged_sharpe_1st |   timing_regime_sharpe_1st |   timing_gain_1st |   timing_volmanaged_sharpe_2nd |   timing_regime_sharpe_2nd |   timing_gain_2nd |
|:-----------|:-----------|---------:|---------:|-------------------------------:|---------------------------:|------------------:|-------------------------------:|---------------------------:|------------------:|
| vix_dterm  | t          |        2 |        0 |                          0.986 |                      1.05  |             0.065 |                          0.653 |                      0.629 |            -0.024 |
| vixplus    | gauss      |        2 |        0 |                          0.986 |                      0.933 |            -0.053 |                          0.653 |                      0.798 |             0.146 |
| vixplus    | t          |        2 |        0 |                          0.986 |                      0.859 |            -0.127 |                          0.653 |                      0.685 |             0.032 |
| vix_dterm  | t          |        3 |        0 |                          0.986 |                      0.857 |            -0.129 |                          0.653 |                      0.621 |            -0.031 |
| vixplus    | t          |        3 |        0 |                          0.986 |                      0.827 |            -0.159 |                          0.653 |                      0.532 |            -0.121 |
| vixplus    | gauss      |        3 |        0 |                          0.986 |                      0.737 |            -0.249 |                          0.653 |                      0.789 |             0.136 |
| vix_dterm  | gauss      |        3 |        0 |                          0.986 |                      0.632 |            -0.354 |                          0.653 |                      0.479 |            -0.173 |
| vix_dterm  | gauss      |        2 |        0 |                          0.986 |                      0.576 |            -0.41  |                          0.653 |                      0.772 |             0.119 |

## Reversal book sized by regime-conditional IC (net of costs)

| features   | emission   |   states |   sticky |   rev_flat_net_sharpe_1st |   rev_sized_net_sharpe_1st |   rev_sizing_gain_1st |   rev_flat_net_sharpe_2nd |   rev_sized_net_sharpe_2nd |   rev_sizing_gain_2nd |   rev_ic_calm_2nd |   rev_ic_stressed_2nd |
|:-----------|:-----------|---------:|---------:|--------------------------:|---------------------------:|----------------------:|--------------------------:|---------------------------:|----------------------:|------------------:|----------------------:|
| vix_dterm  | t          |        3 |        0 |                    -0.61  |                     -0.171 |                 0.439 |                    -0.526 |                     -0.267 |                 0.259 |             0.006 |                 0.028 |
| vix_dterm  | gauss      |        2 |        0 |                    -0.61  |                     -0.247 |                 0.363 |                    -0.526 |                     -0.047 |                 0.479 |             0.006 |                 0.025 |
| vix_dterm  | gauss      |        3 |        0 |                    -0.61  |                     -0.266 |                 0.344 |                    -0.526 |                     -0.257 |                 0.269 |             0.018 |                 0.024 |
| vixplus    | gauss      |        2 |        0 |                    -0.592 |                     -0.591 |                 0.001 |                    -0.531 |                     -0.394 |                 0.136 |             0.007 |                 0.027 |
| vixplus    | t          |        3 |        0 |                    -0.592 |                     -0.611 |                -0.018 |                    -0.531 |                     -0.578 |                -0.047 |             0.017 |                 0.015 |
| vixplus    | t          |        2 |        0 |                    -0.592 |                     -0.629 |                -0.037 |                    -0.531 |                     -0.523 |                 0.007 |             0.011 |                 0.016 |
| vixplus    | gauss      |        3 |        0 |                    -0.592 |                     -0.651 |                -0.058 |                    -0.531 |                     -0.606 |                -0.075 |             0.011 |                 0.012 |
| vix_dterm  | t          |        2 |        0 |                    -0.61  |                     -0.694 |                -0.084 |                    -0.526 |                     -0.332 |                 0.193 |             0.006 |                 0.027 |

## Momentum book sized by regime-conditional IC (net of costs)

| features   | emission   |   states |   sticky |   mom_flat_net_sharpe_1st |   mom_sized_net_sharpe_1st |   mom_sizing_gain_1st |   mom_flat_net_sharpe_2nd |   mom_sized_net_sharpe_2nd |   mom_sizing_gain_2nd |
|:-----------|:-----------|---------:|---------:|--------------------------:|---------------------------:|----------------------:|--------------------------:|---------------------------:|----------------------:|
| vixplus    | gauss      |        2 |        0 |                    -0.379 |                     -0.274 |                 0.105 |                    -0.118 |                     -0.18  |                -0.061 |
| vix_dterm  | gauss      |        3 |        0 |                    -0.416 |                     -0.381 |                 0.036 |                    -0.087 |                     -0.352 |                -0.265 |
| vix_dterm  | t          |        3 |        0 |                    -0.416 |                     -0.4   |                 0.016 |                    -0.087 |                     -0.175 |                -0.088 |
| vix_dterm  | t          |        2 |        0 |                    -0.416 |                     -0.534 |                -0.118 |                    -0.087 |                     -0.187 |                -0.099 |
| vixplus    | t          |        2 |        0 |                    -0.379 |                     -0.504 |                -0.124 |                    -0.118 |                     -0.612 |                -0.494 |
| vix_dterm  | gauss      |        2 |        0 |                    -0.416 |                     -0.564 |                -0.148 |                    -0.087 |                     -0.253 |                -0.165 |
| vixplus    | gauss      |        3 |        0 |                    -0.379 |                     -0.632 |                -0.253 |                    -0.118 |                     -0.555 |                -0.437 |
| vixplus    | t          |        3 |        0 |                    -0.379 |                     -0.722 |                -0.343 |                    -0.118 |                     -0.519 |                -0.401 |

## Reversal / momentum capital split by regime (net of costs)

| features   | emission   |   states |   sticky |   fifty_net_sharpe_1st |   switch_net_sharpe_1st |   switch_gain_1st |   fifty_net_sharpe_2nd |   switch_net_sharpe_2nd |   switch_gain_2nd |
|:-----------|:-----------|---------:|---------:|-----------------------:|------------------------:|------------------:|-----------------------:|------------------------:|------------------:|
| vix_dterm  | gauss      |        3 |        0 |                 -0.538 |                  -0.471 |             0.068 |                 -0.293 |                  -0.295 |            -0.002 |
| vix_dterm  | t          |        3 |        0 |                 -0.538 |                  -0.504 |             0.035 |                 -0.293 |                  -0.143 |             0.15  |
| vix_dterm  | gauss      |        2 |        0 |                 -0.538 |                  -0.55  |            -0.012 |                 -0.293 |                  -0.126 |             0.168 |
| vixplus    | gauss      |        3 |        0 |                 -0.496 |                  -0.698 |            -0.201 |                 -0.317 |                  -0.474 |            -0.157 |
| vix_dterm  | t          |        2 |        0 |                 -0.538 |                  -0.757 |            -0.219 |                 -0.293 |                  -0.313 |            -0.02  |
| vixplus    | t          |        3 |        0 |                 -0.496 |                  -0.743 |            -0.247 |                 -0.317 |                  -0.497 |            -0.18  |
| vixplus    | gauss      |        2 |        0 |                 -0.496 |                  -0.769 |            -0.272 |                 -0.317 |                  -0.231 |             0.086 |
| vixplus    | t          |        2 |        0 |                 -0.496 |                  -0.784 |            -0.288 |                 -0.317 |                  -0.502 |            -0.185 |

## Picked on 2004-2014, checked on 2015-2026

score = timing gain + reversal sizing gain + switch gain (Sharpe units).

| features   | emission   |   states |   sticky |   score_1st |   score_2nd |   timing_gain_2nd |   rev_sizing_gain_2nd |   switch_gain_2nd |
|:-----------|:-----------|---------:|---------:|------------:|------------:|------------------:|----------------------:|------------------:|
| vix_dterm  | t          |        3 |        0 |       0.345 |       0.378 |            -0.031 |                 0.259 |             0.15  |
| vix_dterm  | gauss      |        3 |        0 |       0.058 |       0.094 |            -0.173 |                 0.269 |            -0.002 |
| vix_dterm  | gauss      |        2 |        0 |      -0.059 |       0.765 |             0.119 |                 0.479 |             0.168 |
| vix_dterm  | t          |        2 |        0 |      -0.238 |       0.15  |            -0.024 |                 0.193 |            -0.02  |
| vixplus    | gauss      |        2 |        0 |      -0.323 |       0.368 |             0.146 |                 0.136 |             0.086 |

### The chosen model's regimes (last fit, 2015-2026 statistics)

|   regime |   expected_days |   share_2015_26 |   ann_return |   ann_vol |   sharpe |
|---------:|----------------:|----------------:|-------------:|----------:|---------:|
|        0 |           1.565 |           0.566 |        0.112 |     0.121 |    0.929 |
|        1 |           1.485 |           0.072 |        1.988 |     0.171 |   11.636 |
|        2 |           1.552 |           0.363 |       -0.126 |     0.28  |   -0.449 |

Rank correlation of score between periods across all variants: 0.69

