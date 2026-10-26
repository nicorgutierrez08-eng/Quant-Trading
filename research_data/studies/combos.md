## Signal combinations: which stick?

1891 pairs x 2 ways (sum, product) = 3782 combinations of 62 signals.

How well does the 2004-2014 ranking predict 2015-2026? Rank correlation of |IC| between the periods: **0.61** (1 = the ranking fully survives, 0 = it was luck).

### Top pairs chosen on 2004-2014, and how they did afterwards

| a              | b                 | kind   |   ic5_1st |   ic5_2nd |   years_positive |   persistence |   gain_2nd |
|:---------------|:------------------|:-------|----------:|----------:|-----------------:|--------------:|-----------:|
| resid_rev_1d   | ou_sscore         | sum    |    0.0138 |    0.0071 |           0.8519 |        1.1587 |     0.0007 |
| resid_rev_1d   | sue               | sum    |    0.0124 |    0.0074 |           0.8889 |        0.7052 |     0.001  |
| resid_rev_1d   | accruals          | sum    |    0.0125 |    0.006  |           0.8519 |        0.8381 |    -0.0003 |
| resid_rev_1d   | ear               | sum    |    0.0124 |    0.0068 |           0.9259 |        0.7586 |     0.0004 |
| resid_rev_1d   | close_location    | sum    |    0.0166 |    0.0082 |           0.8889 |        1.0791 |     0.0015 |
| resid_rev_1d   | peer_gap          | sum    |    0.0159 |    0.0107 |           0.9259 |        0.9204 |    -0.0005 |
| resid_rev_1d   | resid_rev_5d      | sum    |    0.0132 |    0.0086 |           0.8889 |        1.0143 |     0.0004 |
| resid_rev_1d   | gross_prof        | sum    |    0.0119 |    0.0054 |           0.8148 |        0.7027 |    -0.001  |
| resid_rev_1d   | low_volume_rev    | sum    |    0.0209 |    0.0119 |           0.9259 |        0.9742 |    -0.0011 |
| resid_rev_1d   | news_surprise     | sum    |    0.0115 |    0.0069 |           0.8519 |        0.7588 |     0.0005 |
| close_location | same_month        | sum    |    0.0191 |    0.0053 |           0.8148 |        1.0944 |    -0.0013 |
| resid_rev_1d   | vol_price_corr    | sum    |    0.0144 |    0.0064 |           0.8148 |        1.1902 |     0      |
| low_volume_rev | same_month        | sum    |    0.0248 |    0.01   |           0.8148 |        0.9507 |    -0.0029 |
| resid_rev_1d   | asset_growth      | sum    |    0.0115 |    0.0009 |           0.7407 |        0.504  |    -0.0055 |
| resid_rev_1d   | same_month        | sum    |    0.0162 |    0.0053 |           0.7778 |        0.5023 |    -0.0011 |
| resid_rev_1d   | no_news_rev       | sum    |    0.0113 |    0.0096 |           0.9259 |        0.8101 |     0.0003 |
| resid_rev_1d   | news_surprise_glm | sum    |    0.0113 |    0.0041 |           0.8889 |        0.5568 |    -0.0023 |
| ou_sscore      | accruals          | sum    |    0.0112 |    0.0047 |           0.8148 |        2.8086 |     0.0001 |
| resid_rev_1d   | news_volume       | sum    |    0.0113 |    0.0074 |           0.8889 |        0.7097 |     0.001  |
| resid_rev_1d   | news_mom          | sum    |    0.0113 |   -0.0009 |           0.6667 |        0.513  |    -0.0097 |
| ou_sscore      | sue               | sum    |    0.011  |    0.0061 |           0.8148 |        2.1155 |     0.0014 |
| resid_rev_1d   | pred_jump_skew    | sum    |    0.0188 |    0.0018 |           0.7037 |        1.3551 |    -0.0046 |
| rev_5d         | resid_rev_1d      | sum    |    0.0201 |    0.0122 |           0.9259 |        0.9467 |    -0.0014 |
| ou_sscore      | close_location    | sum    |    0.0159 |    0.0072 |           0.8519 |        2.0838 |     0.0006 |
| rev_5d         | same_month        | sum    |    0.0238 |    0.0104 |           0.8148 |        0.9089 |    -0.0032 |

### Pairs that stuck: same sign in both periods, positive IC in >= 80% of years, and better than either signal alone in 2015-2026

| a              | b               | kind   |   ic5_1st |   ic5_2nd |   years_positive |   persistence |   gain_2nd |
|:---------------|:----------------|:-------|----------:|----------:|-----------------:|--------------:|-----------:|
| rev_1d         | rev_21d         | sum    |    0.0178 |    0.0168 |           0.8889 |        1.2083 |     0.0025 |
| rev_21d        | resid_mom       | sum    |    0.0126 |    0.0165 |           0.8889 |        1.8327 |     0.0022 |
| rev_5d         | rev_21d         | sum    |    0.0189 |    0.0161 |           0.8519 |        1.6305 |     0.0018 |
| cluster_mom    | peer_gap        | sum    |    0.0139 |    0.0161 |           0.8519 |        1.501  |     0.0047 |
| rev_5d         | resid_mom       | sum    |    0.0199 |    0.016  |           0.8148 |        1.1603 |     0.0024 |
| bollinger_z    | resid_mom       | sum    |    0.016  |    0.016  |           0.8889 |        1.7572 |     0.0027 |
| rev_21d        | low_volume_rev  | sum    |    0.0199 |    0.0159 |           0.8519 |        1.6746 |     0.0016 |
| mom_12_1       | high_52w        | sum    |    0.0171 |    0.0158 |           0.8519 |        2.7484 |     0.006  |
| rev_1d         | cluster_mom     | sum    |    0.0138 |    0.0157 |           0.8519 |        0.9627 |     0.0035 |
| low_volume_rev | resid_mom       | sum    |    0.0209 |    0.0155 |           0.8519 |        1.1989 |     0.0026 |
| rev_21d        | intraday_rev    | sum    |    0.0163 |    0.0154 |           0.8519 |        1.2302 |     0.0011 |
| low_volume_rev | cluster_mom     | sum    |    0.017  |    0.0154 |           0.8519 |        1.5019 |     0.0024 |
| rev_1d         | resid_mom       | sum    |    0.0163 |    0.0153 |           0.8519 |        0.8006 |     0.003  |
| rev_21d        | peer_gap        | sum    |    0.0153 |    0.0151 |           0.8519 |        1.7449 |     0.0008 |
| rev_5d         | mom_accel       | sum    |    0.0198 |    0.0151 |           0.8889 |        1.4516 |     0.0014 |
| rev_21d        | bollinger_z     | sum    |    0.0157 |    0.015  |           0.8889 |        2.3205 |     0.0007 |
| rsi_14         | resid_mom       | sum    |    0.0168 |    0.015  |           0.9259 |        1.8254 |     0.0034 |
| rev_1d         | bollinger_z     | sum    |    0.0198 |    0.015  |           0.9259 |        1.2689 |     0.0018 |
| rev_1d         | mom_accel       | sum    |    0.0178 |    0.015  |           0.8889 |        1.036  |     0.0028 |
| rev_1d         | rev_5d          | sum    |    0.0222 |    0.0148 |           0.9259 |        0.9209 |     0.0011 |
| low_volume_rev | mom_accel       | sum    |    0.0208 |    0.0147 |           0.8889 |        1.497  |     0.0017 |
| rev_5d         | mom_12_1        | sum    |    0.0224 |    0.0147 |           0.8148 |        0.9997 |     0.0011 |
| rev_1d         | intraday_rev_21 | sum    |    0.017  |    0.0146 |           0.8519 |        0.9764 |     0.0024 |
| rev_5d         | bollinger_z     | sum    |    0.0208 |    0.0146 |           0.8889 |        1.632  |     0.0009 |
| resid_mom      | peer_gap        | sum    |    0.0147 |    0.0144 |           0.8148 |        1.1371 |     0.0032 |

### Does consistency up to 2014 predict consistency after?

Rule, using 2004-2014 only: IC of the same sign in each third of 2004-2014 and |t| >= 2. The model's `select_stable` option applies the same rule at every refit on its own training window.

Kept by the rule: 18 of 62. Of those, 17 kept the same sign in 2015-2026; of the dropped ones, 20 of 44 did.

| signal               | family         |   ic5_part1 |   ic5_part2 |   ic5_part3 |   t_2004_14 | kept_by_2004_14_rule   |   ic5_2015_26 | same_sign_2015_26   |
|:---------------------|:---------------|------------:|------------:|------------:|------------:|:-----------------------|--------------:|:--------------------|
| resid_rev_1d         | mean_reversion |      0.0185 |      0.0123 |      0.0048 |      5.2339 | True                   |        0.0064 | True                |
| ou_sscore            | mean_reversion |      0.013  |      0.0094 |      0.009  |      4.6894 | True                   |        0.0047 | True                |
| resid_rev_5d         | mean_reversion |      0.0154 |      0.0103 |      0.0085 |      4.4552 | True                   |        0.0083 | True                |
| peer_gap             | structure      |      0.0168 |      0.0147 |      0.013  |      4.3116 | True                   |        0.0113 | True                |
| low_volume_rev       | mean_reversion |      0.0289 |      0.0216 |      0.0187 |      4.3049 | True                   |        0.013  | True                |
| close_location       | microstructure |      0.0302 |      0.0116 |      0.0045 |      4.2241 | True                   |        0.0066 | True                |
| rev_5d               | mean_reversion |      0.0291 |      0.0193 |      0.0177 |      4.1647 | True                   |        0.0136 | True                |
| bollinger_z          | mean_reversion |      0.0306 |      0.0115 |      0.01   |      3.7811 | True                   |        0.0133 | True                |
| rsi_14               | mean_reversion |      0.0378 |      0.0084 |      0.0088 |      3.5387 | True                   |        0.0116 | True                |
| pred_jump_skew       | poisson        |     -0.0324 |     -0.0075 |     -0.012  |     -3.4995 | True                   |        0.0039 | False               |
| rev_1d               | mean_reversion |      0.0229 |      0.0169 |      0.0109 |      3.312  | True                   |        0.0122 | True                |
| vol_price_corr       | volume         |      0.0159 |      0.0086 |      0.0058 |      3.2711 | True                   |        0.003  | True                |
| same_month           | seasonality    |      0.0246 |      0.0087 |      0.0076 |      3.1196 | True                   |        0.001  | True                |
| intraday_rev         | mean_reversion |      0.0217 |      0.0145 |      0.0072 |      2.937  | True                   |        0.0098 | True                |
| size_proxy           | volume         |      0.0262 |      0.0041 |      0.0052 |      2.6774 | True                   |        0.0014 | True                |
| kalman_trend         | structure      |     -0.0301 |     -0.0016 |     -0.0071 |     -2.293  | True                   |       -0.0078 | True                |
| amihud               | volume         |      0.022  |      0.0043 |      0.0065 |      2.1193 | True                   |        0.0028 | True                |
| rev_21d              | mean_reversion |      0.0261 |      0.0029 |      0.0082 |      2.0581 | True                   |        0.0143 | True                |
| accruals             | fundamental    |    nan      |      0.0162 |      0.0069 |      2.2452 | False                  |        0.0021 | False               |
| sue                  | fundamental    |    nan      |      0.0172 |      0.0053 |      2.0928 | False                  |        0.004  | False               |
| mom_accel            | momentum       |     -0.0186 |     -0.0094 |     -0.0033 |     -1.9624 | False                  |       -0.0105 | True                |
| overnight_rev        | mean_reversion |      0.0058 |      0.0085 |      0.0092 |      1.9591 | False                  |        0.0063 | True                |
| intraday_rev_21      | momentum       |      0.0172 |      0.0041 |      0.0097 |      1.8268 | False                  |        0.0106 | True                |
| peer_lead            | structure      |     -0.0142 |     -0.0107 |     -0.009  |     -1.8044 | False                  |       -0.0065 | True                |
| pred_crash_intensity | poisson        |     -0.0152 |     -0.0088 |     -0.0018 |     -1.6671 | False                  |       -0.0041 | True                |
| ear                  | fundamental    |    nan      |      0.0052 |      0.0054 |      1.5902 | False                  |        0.0028 | False               |
| mom_12_1             | momentum       |      0.0135 |      0.0072 |      0.0126 |      1.5339 | False                  |        0.0098 | True                |
| trend_quality        | momentum       |     -0.0189 |     -0.0034 |     -0.0064 |     -1.5318 | False                  |       -0.0048 | True                |
| overnight_mom        | momentum       |     -0.0166 |     -0.0013 |      0.0009 |     -1.4692 | False                  |       -0.0085 | True                |
| resid_mom            | momentum       |      0.0051 |      0.0029 |      0.0098 |      1.4453 | False                  |        0.01   | True                |
| earnings_yield       | fundamental    |    nan      |     -0.0159 |     -0.0039 |     -0.9921 | False                  |       -0.0026 | False               |
| range_vol_ratio      | microstructure |     -0.0015 |      0.0043 |      0.0057 |      0.9875 | False                  |        0.0001 | False               |
| vol_of_vol           | volatility     |     -0.0078 |     -0.0015 |      0      |     -0.9772 | False                  |       -0.0031 | True                |
| gross_prof           | fundamental    |    nan      |      0.0114 |      0.0039 |      0.936  | False                  |        0.0003 | False               |
| neg_skew             | volatility     |      0.0106 |     -0.0006 |     -0.0013 |      0.9164 | False                  |        0      | True                |
| autocorr_signal      | structure      |     -0.0009 |      0.0055 |      0.0007 |      0.7735 | False                  |        0.0019 | False               |
| cluster_mom          | momentum       |     -0.0258 |      0.0047 |      0.0027 |     -0.742  | False                  |       -0.0114 | True                |
| weekday_seasonality  | seasonality    |      0.0016 |      0.0014 |      0.0024 |      0.7065 | False                  |        0.0034 | True                |
| cs_spread            | microstructure |     -0.0069 |     -0.0052 |     -0.002  |     -0.6352 | False                  |        0.0025 | False               |
| turnover_trend       | volume         |     -0.0039 |      0.0037 |      0.0074 |      0.6167 | False                  |       -0.0001 | True                |
| turn_of_month        | seasonality    |      0.0129 |      0.0062 |      0.0006 |      0.5946 | False                  |        0.0059 | True                |
| abn_volume           | volume         |      0.004  |     -0.0013 |     -0.006  |     -0.5779 | False                  |       -0.0031 | False               |
| high_52w             | momentum       |     -0.0056 |     -0.0035 |     -0.0045 |     -0.5685 | False                  |       -0.0042 | True                |
| book_to_market       | fundamental    |    nan      |      0.0014 |     -0.004  |     -0.5668 | False                  |       -0.0027 | False               |
| no_news_rev          | news           |    nan      |    nan      |      0.0017 |      0.5484 | False                  |        0.0093 | False               |
| market_corr          | structure      |      0.0146 |     -0.0059 |      0.0027 |      0.5341 | False                  |       -0.0012 | False               |
| mom_6_1              | momentum       |      0.0033 |      0.0088 |     -0.0021 |      0.5124 | False                  |        0.0055 | True                |
| max_effect           | volatility     |      0.0065 |      0.0042 |     -0.0007 |      0.4672 | False                  |       -0.002  | False               |
| bab                  | volatility     |      0.0234 |     -0.0016 |     -0.0049 |      0.4332 | False                  |       -0.0063 | False               |
| news_surprise        | poisson        |    nan      |    nan      |      0.0021 |      0.3706 | False                  |        0.0034 | False               |
| news_surprise_glm    | poisson        |    nan      |    nan      |      0.001  |      0.3383 | False                  |       -0.005  | False               |
| low_vol              | volatility     |      0.0075 |      0.0008 |     -0.0002 |      0.264  | False                  |       -0.0066 | False               |
| jump_intensity       | poisson        |     -0.0091 |      0.0076 |     -0.0028 |     -0.2614 | False                  |       -0.0011 | True                |
| asset_growth         | fundamental    |    nan      |    nan      |      0.001  |      0.2494 | False                  |       -0.0061 | False               |
| gk_ratio             | microstructure |     -0.0068 |     -0.0013 |      0.0054 |     -0.1709 | False                  |        0.0042 | False               |
| downside_beta        | volatility     |     -0.0234 |      0.0197 |    nan      |     -0.0819 | False                  |       -0.0353 | True                |
| idio_vol             | volatility     |     -0.0011 |      0.0032 |     -0.0015 |      0.0454 | False                  |       -0.0037 | True                |
| jump_skew            | poisson        |      0.0085 |     -0.0003 |     -0.0056 |      0.0135 | False                  |       -0.0026 | False               |
| crash_risk           | poisson        |     -0.0118 |      0.006  |      0.0024 |     -0.0089 | False                  |        0.0016 | False               |
| news_volume          | news           |    nan      |    nan      |      0.0115 |    nan      | False                  |        0.0041 | False               |
| news_tone            | news           |    nan      |    nan      |    nan      |    nan      | False                  |       -0.0024 | False               |
| news_mom             | news           |    nan      |    nan      |      0.0016 |    nan      | False                  |       -0.0106 | False               |

### Single signals for reference

| signal               | family         |   ic5_1st |   ic5_2nd |   years_positive |   persistence |
|:---------------------|:---------------|----------:|----------:|-----------------:|--------------:|
| low_volume_rev       | mean_reversion |    0.0227 |    0.013  |           0.8519 |        1.2669 |
| rev_5d               | mean_reversion |    0.0215 |    0.0136 |           0.8519 |        1.205  |
| rsi_14               | mean_reversion |    0.017  |    0.0116 |           0.8519 |        2.4254 |
| rev_1d               | mean_reversion |    0.0165 |    0.0122 |           0.9259 |        0.7244 |
| bollinger_z          | mean_reversion |    0.0165 |    0.0133 |           0.8889 |        2.2921 |
| pred_jump_skew       | poisson        |   -0.0163 |    0.0039 |           0.4444 |        2.9281 |
| peer_gap             | structure      |    0.0147 |    0.0113 |           0.8519 |        1.233  |
| close_location       | microstructure |    0.0144 |    0.0066 |           0.8519 |        1.795  |
| intraday_rev         | mean_reversion |    0.014  |    0.0098 |           0.8889 |        0.6796 |
| same_month           | seasonality    |    0.012  |    0.001  |           0.6667 |       -0.07   |
| kalman_trend         | structure      |   -0.0118 |   -0.0078 |           0.3704 |        6.2967 |
| news_volume          | news           |    0.0115 |    0.0041 |           0.3333 |        1.2174 |
| rev_21d              | mean_reversion |    0.0115 |    0.0143 |           0.7407 |        2.4264 |
| resid_rev_1d         | mean_reversion |    0.0113 |    0.0064 |           0.8889 |        0.6893 |
| resid_rev_5d         | mean_reversion |    0.0111 |    0.0083 |           0.8519 |        1.5748 |
| peer_lead            | structure      |   -0.0111 |   -0.0065 |           0.1111 |        0.6381 |
| mom_12_1             | momentum       |    0.0109 |    0.0098 |           0.6667 |        0.6863 |
| size_proxy           | volume         |    0.0109 |    0.0014 |           0.6667 |        6.0992 |
| ou_sscore            | mean_reversion |    0.0103 |    0.0047 |           0.8148 |        2.6536 |
| amihud               | volume         |    0.0102 |    0.0028 |           0.6667 |       11.9683 |
| mom_accel            | momentum       |   -0.0099 |   -0.0105 |           0.2222 |        2.0832 |
| intraday_rev_21      | momentum       |    0.0099 |    0.0106 |           0.7407 |        1.7636 |
| vol_price_corr       | volume         |    0.0097 |    0.003  |           0.7778 |        2.6035 |
| trend_quality        | momentum       |   -0.0089 |   -0.0048 |           0.3704 |       10.7776 |
| pred_crash_intensity | poisson        |   -0.0081 |   -0.0041 |           0.2593 |        0.8373 |
| overnight_rev        | mean_reversion |    0.008  |    0.0063 |           0.8519 |        1.0705 |
| accruals             | fundamental    |    0.0074 |    0.0021 |           0.4444 |        3.2563 |
| turn_of_month        | seasonality    |    0.0061 |    0.0059 |           0.6667 |       -2.646  |
| resid_mom            | momentum       |    0.006  |    0.01   |           0.7037 |        0.977  |
| sue                  | fundamental    |    0.0054 |    0.004  |           0.4815 |        0.9846 |
| ear                  | fundamental    |    0.0053 |    0.0028 |           0.4444 |        1.6886 |
| overnight_mom        | momentum       |   -0.0049 |   -0.0085 |           0.2593 |        5.7574 |
| cluster_mom          | momentum       |   -0.0047 |   -0.0114 |           0.3333 |        2.1535 |
| earnings_yield       | fundamental    |   -0.0045 |   -0.0026 |           0.2222 |        4.589  |
| cs_spread            | microstructure |   -0.0045 |    0.0025 |           0.5185 |       -1.0859 |
| high_52w             | momentum       |   -0.0045 |   -0.0042 |           0.4444 |       -5.0876 |
| bab                  | volatility     |    0.0045 |   -0.0063 |           0.4815 |       -2.5047 |
| gross_prof           | fundamental    |    0.0042 |    0.0003 |           0.3704 |        1.6851 |
| book_to_market       | fundamental    |   -0.0033 |   -0.0027 |           0.3704 |        0.1551 |
| mom_6_1              | momentum       |    0.0033 |    0.0055 |           0.5926 |       -0.3961 |
| range_vol_ratio      | microstructure |    0.0031 |    0.0001 |           0.6667 |        0.6812 |
| max_effect           | volatility     |    0.0031 |   -0.002  |           0.4815 |       -1.208  |
| market_corr          | structure      |    0.003  |   -0.0012 |           0.4444 |       -1.3248 |
| turnover_trend       | volume         |    0.0028 |   -0.0001 |           0.5556 |       -4.9474 |
| vol_of_vol           | volatility     |   -0.0028 |   -0.0031 |           0.4074 |        7.5897 |
| neg_skew             | volatility     |    0.0024 |    0      |           0.5926 |        3.8471 |
| low_vol              | volatility     |    0.0024 |   -0.0066 |           0.5185 |       -2.7877 |
| downside_beta        | volatility     |   -0.0024 |   -0.0353 |           0.1852 |        7.3426 |
| news_surprise        | poisson        |    0.0021 |    0.0034 |           0.3333 |        1.7943 |
| autocorr_signal      | structure      |    0.0019 |    0.0019 |           0.5556 |        0.3429 |
| weekday_seasonality  | seasonality    |    0.0018 |    0.0034 |           0.5556 |        0.9142 |
| no_news_rev          | news           |    0.0017 |    0.0093 |           0.4815 |        1.6754 |
| news_mom             | news           |    0.0016 |   -0.0106 |           0.1111 |        1.4035 |
| abn_volume           | volume         |   -0.0014 |   -0.0031 |           0.4444 |       17.0343 |
| news_surprise_glm    | poisson        |    0.001  |   -0.005  |           0.1111 |        5.1983 |
| asset_growth         | fundamental    |    0.001  |   -0.0061 |           0.2593 |        2.643  |
| jump_intensity       | poisson        |   -0.0006 |   -0.0011 |           0.4444 |       -4.1049 |
| gk_ratio             | microstructure |   -0.0005 |    0.0042 |           0.5185 |       -8.2079 |
| idio_vol             | volatility     |    0.0003 |   -0.0037 |           0.5556 |       -2.855  |
| jump_skew            | poisson        |    0      |   -0.0026 |           0.4444 |       -0.6053 |
| crash_risk           | poisson        |   -0      |    0.0016 |           0.4815 |       -1.2338 |
| news_tone            | news           |  nan      |   -0.0024 |           0.1481 |        1.0845 |

### Break-even cost of the top and sticky pairs (bp per dollar traded)

| a              | b                 | kind   |   halflife |   breakeven_bp_1st |   net_sharpe_1st |   breakeven_bp_2nd |   net_sharpe_2nd |
|:---------------|:------------------|:-------|-----------:|-------------------:|-----------------:|-------------------:|-----------------:|
| resid_rev_1d   | ou_sscore         | sum    |          0 |               3.13 |            -4.46 |               1.27 |            -4.85 |
| resid_rev_1d   | ou_sscore         | sum    |          5 |              11    |             0.47 |               4.39 |            -0.35 |
| resid_rev_1d   | ou_sscore         | sum    |         20 |              19.59 |             0.96 |               6.74 |            -0.02 |
| resid_rev_1d   | sue               | sum    |          0 |               2.65 |            -6    |               0.9  |            -5.23 |
| resid_rev_1d   | sue               | sum    |          5 |               8.03 |            -0.12 |               2.64 |            -0.53 |
| resid_rev_1d   | sue               | sum    |         20 |              13.49 |             0.73 |               4.75 |            -0.1  |
| resid_rev_1d   | accruals          | sum    |          0 |               2.76 |            -5.76 |               1.28 |            -4.93 |
| resid_rev_1d   | accruals          | sum    |          5 |               8.77 |             0.09 |               6.75 |            -0.03 |
| resid_rev_1d   | accruals          | sum    |         20 |              15.43 |             0.92 |              18.36 |             0.39 |
| resid_rev_1d   | ear               | sum    |          0 |               2.74 |            -5.7  |               1.01 |            -5.78 |
| resid_rev_1d   | ear               | sum    |          5 |               8.57 |             0.03 |               3.01 |            -0.64 |
| resid_rev_1d   | ear               | sum    |         20 |              14.36 |             0.77 |               3.51 |            -0.21 |
| resid_rev_1d   | close_location    | sum    |          0 |               3.89 |            -2.8  |               1.54 |            -3.2  |
| resid_rev_1d   | close_location    | sum    |          5 |              11.58 |             0.44 |               4.76 |            -0.27 |
| resid_rev_1d   | close_location    | sum    |         20 |              19.26 |             0.66 |               7.62 |             0.03 |
| resid_rev_1d   | peer_gap          | sum    |          0 |               3.72 |            -2.8  |               2.01 |            -2.79 |
| resid_rev_1d   | peer_gap          | sum    |          5 |              10.32 |             0.27 |               6.13 |            -0.11 |
| resid_rev_1d   | peer_gap          | sum    |         20 |              16.97 |             0.61 |               8.67 |             0.1  |
| resid_rev_1d   | resid_rev_5d      | sum    |          0 |               3.36 |            -3.91 |               1.48 |            -3.83 |
| resid_rev_1d   | resid_rev_5d      | sum    |          5 |               9.31 |             0.2  |               5.05 |            -0.28 |
| resid_rev_1d   | resid_rev_5d      | sum    |         20 |              16.08 |             0.76 |               7.34 |             0.02 |
| resid_rev_1d   | gross_prof        | sum    |          0 |               2.62 |            -6.06 |               1.01 |            -5.84 |
| resid_rev_1d   | gross_prof        | sum    |          5 |               8.02 |            -0.12 |               3.9  |            -0.44 |
| resid_rev_1d   | gross_prof        | sum    |         20 |              13.82 |             0.72 |               8.05 |             0.04 |
| resid_rev_1d   | low_volume_rev    | sum    |          0 |               4.06 |            -1.88 |               2.15 |            -2.18 |
| resid_rev_1d   | low_volume_rev    | sum    |          5 |              12.25 |             0.41 |               6.38 |            -0.07 |
| resid_rev_1d   | low_volume_rev    | sum    |         20 |              19.39 |             0.59 |               9.24 |             0.11 |
| resid_rev_1d   | news_surprise     | sum    |          0 |               2.56 |            -6.21 |               0.96 |            -6.58 |
| resid_rev_1d   | news_surprise     | sum    |          5 |               7.49 |            -0.3  |               3.05 |            -0.99 |
| resid_rev_1d   | news_surprise     | sum    |         20 |              12.47 |             0.62 |               4.88 |            -0.2  |
| close_location | same_month        | sum    |          0 |               6.06 |            -0.65 |               2.07 |            -1.32 |
| close_location | same_month        | sum    |          5 |              15.12 |             0.53 |               2.34 |            -0.37 |
| close_location | same_month        | sum    |         20 |              15.72 |             0.28 |               2.14 |            -0.2  |
| resid_rev_1d   | vol_price_corr    | sum    |          0 |               2.87 |            -3.63 |               1.01 |            -4.15 |
| resid_rev_1d   | vol_price_corr    | sum    |          5 |               9.52 |             0.12 |               2.65 |            -0.48 |
| resid_rev_1d   | vol_price_corr    | sum    |         20 |              16.79 |             0.43 |               2.68 |            -0.23 |
| low_volume_rev | same_month        | sum    |          0 |               6.64 |            -0.35 |               3.7  |            -0.69 |
| low_volume_rev | same_month        | sum    |          5 |              16.93 |             0.52 |               5.27 |            -0.13 |
| low_volume_rev | same_month        | sum    |         20 |              19.44 |             0.36 |               5.56 |            -0.06 |
| resid_rev_1d   | asset_growth      | sum    |          0 |               2.63 |            -5.96 |               0.72 |            -5.79 |
| resid_rev_1d   | asset_growth      | sum    |          5 |               7.98 |            -0.13 |               0.45 |            -0.81 |
| resid_rev_1d   | asset_growth      | sum    |         20 |              13.68 |             0.69 |              -4.3  |            -0.41 |
| resid_rev_1d   | same_month        | sum    |          0 |               3.22 |            -3.59 |               0.99 |            -4.07 |
| resid_rev_1d   | same_month        | sum    |          5 |              10.41 |             0.24 |               1.34 |            -0.58 |
| resid_rev_1d   | same_month        | sum    |         20 |              10.05 |             0.08 |              -0.28 |            -0.34 |
| resid_rev_1d   | no_news_rev       | sum    |          0 |               2.49 |            -6.45 |               1.47 |            -4.09 |
| resid_rev_1d   | no_news_rev       | sum    |          5 |               6.98 |            -0.5  |               5.01 |            -0.32 |
| resid_rev_1d   | no_news_rev       | sum    |         20 |              11.53 |             0.54 |               7.88 |             0.05 |
| resid_rev_1d   | news_surprise_glm | sum    |          0 |               2.49 |            -6.45 |               0.72 |            -6.87 |
| resid_rev_1d   | news_surprise_glm | sum    |          5 |               6.98 |            -0.49 |               1.05 |            -1.25 |
| resid_rev_1d   | news_surprise_glm | sum    |         20 |              11.55 |             0.55 |              -3.27 |            -0.76 |
| ou_sscore      | accruals          | sum    |          0 |               5.43 |            -0.91 |               4.28 |            -0.62 |
| ou_sscore      | accruals          | sum    |          5 |              14.88 |             0.65 |              10.22 |             0.19 |
| ou_sscore      | accruals          | sum    |         20 |              27.33 |             1.06 |              21.81 |             0.39 |
| resid_rev_1d   | news_volume       | sum    |          0 |               2.49 |            -6.45 |               0.98 |            -6.34 |
| resid_rev_1d   | news_volume       | sum    |          5 |               6.98 |            -0.5  |               3.51 |            -0.84 |
| resid_rev_1d   | news_volume       | sum    |         20 |              11.53 |             0.54 |               5.6  |            -0.14 |
| resid_rev_1d   | news_mom          | sum    |          0 |               2.49 |            -6.45 |              -0.13 |            -6.05 |
| resid_rev_1d   | news_mom          | sum    |          5 |               6.97 |            -0.5  |              -0.59 |            -1.69 |
| resid_rev_1d   | news_mom          | sum    |         20 |              11.53 |             0.54 |              -0.91 |            -0.92 |
| ou_sscore      | sue               | sum    |          0 |               5.02 |            -1.08 |               2.38 |            -1.08 |
| ou_sscore      | sue               | sum    |          5 |              13.13 |             0.5  |               3    |            -0.29 |
| ou_sscore      | sue               | sum    |         20 |              22.68 |             0.88 |               4.38 |            -0.1  |
| resid_rev_1d   | pred_jump_skew    | sum    |          0 |               3.88 |            -2.16 |               0.66 |            -5.18 |
| resid_rev_1d   | pred_jump_skew    | sum    |          5 |              15.49 |             0.46 |               3.58 |            -0.39 |
| resid_rev_1d   | pred_jump_skew    | sum    |         20 |              30.34 |             0.54 |              10.23 |             0.1  |
| rev_5d         | resid_rev_1d      | sum    |          0 |               4.27 |            -1.75 |               2.27 |            -2.04 |
| rev_5d         | resid_rev_1d      | sum    |          5 |              12.23 |             0.39 |               6.64 |            -0.04 |
| rev_5d         | resid_rev_1d      | sum    |         20 |              19.72 |             0.58 |               9.51 |             0.12 |
| ou_sscore      | close_location    | sum    |          0 |               5.67 |            -0.88 |               2.65 |            -1.26 |
| ou_sscore      | close_location    | sum    |          5 |              14.8  |             0.6  |               5.66 |            -0.11 |
| ou_sscore      | close_location    | sum    |         20 |              25.32 |             0.77 |               8.92 |             0.07 |
| rev_5d         | same_month        | sum    |          0 |               7.45 |            -0.17 |               4.12 |            -0.56 |
| rev_5d         | same_month        | sum    |          5 |              16.95 |             0.5  |               5.53 |            -0.1  |
| rev_5d         | same_month        | sum    |         20 |              19.73 |             0.37 |               5.85 |            -0.05 |
| rev_1d         | rev_21d           | sum    |          0 |               4.17 |            -1.32 |               2.76 |            -1.34 |
| rev_1d         | rev_21d           | sum    |          5 |              13.89 |             0.28 |              10.07 |             0.16 |
| rev_1d         | rev_21d           | sum    |         20 |              21.47 |             0.32 |              13.45 |             0.16 |
| rev_21d        | resid_mom         | sum    |          0 |               7.73 |            -0.07 |               6.41 |            -0.06 |
| rev_21d        | resid_mom         | sum    |          5 |              13.68 |             0.15 |              13.88 |             0.21 |
| rev_21d        | resid_mom         | sum    |         20 |              23.65 |             0.27 |              22.78 |             0.3  |
| rev_5d         | rev_21d           | sum    |          0 |               7.63 |            -0.11 |               5.74 |            -0.18 |
| rev_5d         | rev_21d           | sum    |          5 |              15.63 |             0.29 |              11.39 |             0.18 |
| rev_5d         | rev_21d           | sum    |         20 |              23.85 |             0.34 |              14.96 |             0.17 |
| cluster_mom    | peer_gap          | sum    |          0 |               5.86 |            -0.38 |               4.61 |            -0.35 |
| cluster_mom    | peer_gap          | sum    |          5 |              11.01 |             0.1  |               9.65 |             0.11 |
| cluster_mom    | peer_gap          | sum    |         20 |              17.04 |             0.18 |              13.81 |             0.15 |
| rev_5d         | resid_mom         | sum    |          0 |               6.62 |            -0.29 |               4.43 |            -0.41 |
| rev_5d         | resid_mom         | sum    |          5 |              14.47 |             0.29 |              10.27 |             0.14 |
| rev_5d         | resid_mom         | sum    |         20 |              24.41 |             0.36 |              20.19 |             0.26 |
| bollinger_z    | resid_mom         | sum    |          0 |               5.31 |            -0.52 |               4.61 |            -0.34 |
| bollinger_z    | resid_mom         | sum    |          5 |              16.15 |             0.38 |              11.48 |             0.19 |
| bollinger_z    | resid_mom         | sum    |         20 |              26.7  |             0.46 |              21.08 |             0.3  |
| rev_21d        | low_volume_rev    | sum    |          0 |               7.06 |            -0.21 |               5.34 |            -0.25 |
| rev_21d        | low_volume_rev    | sum    |          5 |              15.64 |             0.3  |              11.04 |             0.17 |
| rev_21d        | low_volume_rev    | sum    |         20 |              23.93 |             0.34 |              14.64 |             0.17 |
| mom_12_1       | high_52w          | sum    |          0 |              17.65 |             0.5  |              16.01 |             0.45 |
| mom_12_1       | high_52w          | sum    |          5 |              38.58 |             0.49 |              45.53 |             0.59 |
| mom_12_1       | high_52w          | sum    |         20 |              52.42 |             0.39 |              85.05 |             0.62 |
| rev_1d         | cluster_mom       | sum    |          0 |               3.48 |            -1.45 |               2.13 |            -1.52 |
| rev_1d         | cluster_mom       | sum    |          5 |               9.63 |             0.06 |               7.39 |             0.02 |
| rev_1d         | cluster_mom       | sum    |         20 |              12.8  |             0.1  |              10.9  |             0.1  |
| low_volume_rev | resid_mom         | sum    |          0 |               5.8  |            -0.46 |               3.94 |            -0.54 |
| low_volume_rev | resid_mom         | sum    |          5 |              14.66 |             0.31 |               9.7  |             0.12 |
| low_volume_rev | resid_mom         | sum    |         20 |              24.17 |             0.35 |              19.39 |             0.25 |
| rev_21d        | intraday_rev      | sum    |          0 |               4.32 |            -1.3  |               2.58 |            -1.47 |
| rev_21d        | intraday_rev      | sum    |          5 |              12.96 |             0.23 |               9.4  |             0.12 |
| rev_21d        | intraday_rev      | sum    |         20 |              19.41 |             0.27 |              12.37 |             0.13 |
| low_volume_rev | cluster_mom       | sum    |          0 |               5.6  |            -0.4  |               4.23 |            -0.42 |
| low_volume_rev | cluster_mom       | sum    |          5 |              11.92 |             0.14 |               8.75 |             0.07 |
| low_volume_rev | cluster_mom       | sum    |         20 |              16.89 |             0.18 |              12.66 |             0.13 |
| rev_1d         | resid_mom         | sum    |          0 |               2.83 |            -2.1  |               1.99 |            -1.87 |
| rev_1d         | resid_mom         | sum    |          5 |              10.96 |             0.16 |               7.62 |             0.03 |
| rev_1d         | resid_mom         | sum    |         20 |              18.77 |             0.25 |              16.17 |             0.18 |
| rev_21d        | peer_gap          | sum    |          0 |               6.63 |            -0.3  |               5.42 |            -0.26 |
| rev_21d        | peer_gap          | sum    |          5 |              13.84 |             0.24 |              11.07 |             0.18 |
| rev_21d        | peer_gap          | sum    |         20 |              22.17 |             0.32 |              14.6  |             0.17 |
| rev_5d         | mom_accel         | sum    |          0 |               7.77 |            -0.1  |               6.07 |            -0.14 |
| rev_5d         | mom_accel         | sum    |          5 |              14.66 |             0.27 |              13.4  |             0.25 |
| rev_5d         | mom_accel         | sum    |         20 |              17.19 |             0.19 |              21.55 |             0.29 |
| rev_21d        | bollinger_z       | sum    |          0 |               7.38 |            -0.13 |               5.97 |            -0.12 |
| rev_21d        | bollinger_z       | sum    |          5 |              17.7  |             0.36 |              12.53 |             0.2  |
| rev_21d        | bollinger_z       | sum    |         20 |              26.23 |             0.4  |              15.56 |             0.18 |
| rsi_14         | resid_mom         | sum    |          0 |               8.09 |            -0.04 |               5.32 |            -0.18 |
| rsi_14         | resid_mom         | sum    |          5 |              17.93 |             0.38 |              12.62 |             0.2  |
| rsi_14         | resid_mom         | sum    |         20 |              26.4  |             0.41 |              20.98 |             0.29 |
| rev_1d         | bollinger_z       | sum    |          0 |               3.69 |            -1.83 |               2.41 |            -1.67 |
| rev_1d         | bollinger_z       | sum    |          5 |              15.38 |             0.59 |               8.71 |             0.12 |
| rev_1d         | bollinger_z       | sum    |         20 |              25.06 |             0.67 |              12.48 |             0.19 |
| rev_1d         | mom_accel         | sum    |          0 |               3.83 |            -1.56 |               2.81 |            -1.36 |
| rev_1d         | mom_accel         | sum    |          5 |              11.89 |             0.19 |              11.58 |             0.23 |
| rev_1d         | mom_accel         | sum    |         20 |              13.07 |             0.11 |              19.21 |             0.28 |
| rev_1d         | rev_5d            | sum    |          0 |               4.34 |            -1.36 |               2.67 |            -1.47 |
| rev_1d         | rev_5d            | sum    |          5 |              12.94 |             0.38 |               7.74 |             0.06 |
| rev_1d         | rev_5d            | sum    |         20 |              20.22 |             0.5  |              10.45 |             0.15 |
| low_volume_rev | mom_accel         | sum    |          0 |               7.07 |            -0.23 |               5.57 |            -0.23 |
| low_volume_rev | mom_accel         | sum    |          5 |              14.84 |             0.29 |              12.81 |             0.24 |
| low_volume_rev | mom_accel         | sum    |         20 |              17.48 |             0.2  |              20.79 |             0.28 |
| rev_5d         | mom_12_1          | sum    |          0 |               6.34 |            -0.3  |               3.8  |            -0.43 |
| rev_5d         | mom_12_1          | sum    |          5 |              13.56 |             0.18 |               7.7  |             0.02 |
| rev_5d         | mom_12_1          | sum    |         20 |              17.97 |             0.14 |              13.14 |             0.07 |
| rev_1d         | intraday_rev_21   | sum    |          0 |               4.13 |            -1.36 |               2.58 |            -1.45 |
| rev_1d         | intraday_rev_21   | sum    |          5 |              12.46 |             0.21 |               8.16 |             0.06 |
| rev_1d         | intraday_rev_21   | sum    |         20 |              17.23 |             0.22 |               9.17 |             0.05 |
| rev_5d         | bollinger_z       | sum    |          0 |               6.52 |            -0.36 |               4.81 |            -0.38 |
| rev_5d         | bollinger_z       | sum    |          5 |              16.67 |             0.53 |               9.59 |             0.14 |
| rev_5d         | bollinger_z       | sum    |         20 |              26.54 |             0.61 |              13.52 |             0.19 |
| resid_mom      | peer_gap          | sum    |          0 |               4.98 |            -0.82 |               3.91 |            -0.62 |
| resid_mom      | peer_gap          | sum    |          5 |              10.29 |             0.11 |               9.15 |             0.1  |
| resid_mom      | peer_gap          | sum    |         20 |              17.47 |             0.24 |              17.78 |             0.21 |

