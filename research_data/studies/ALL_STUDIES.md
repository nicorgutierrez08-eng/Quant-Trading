# Research results

## Data quality

Bars removed as bad prints: 0

(none)

Largest close-to-close moves after cleaning:

| date       | ticker   |   return |
|:-----------|:---------|---------:|
| 2020-11-20 | CHRD     |  257.333 |
| 2004-11-18 | WT       |   36.5   |
| 2012-02-06 | TGTX     |    5.667 |
| 2002-08-30 | ARWR     |    5     |
| 2002-10-02 | ARWR     |    3     |
| 2002-04-26 | ARWR     |    3     |
| 2002-05-30 | ARWR     |    3     |
| 2009-06-10 | JAZZ     |    2.098 |
| 2011-07-21 | TGTX     |    2     |
| 2003-04-22 | ARWR     |    2     |
| 2002-03-28 | ARWR     |    2     |
| 2012-10-03 | SRPT     |    1.997 |
| 2003-04-23 | SBRA     |    1.833 |
| 2000-09-21 | DAR      |    1.75  |
| 2000-01-19 | ARWR     |    1.727 |

Largest overnight moves after cleaning:

| date       | ticker   |   return |
|:-----------|:---------|---------:|
| 2020-11-20 | CHRD     |  225.25  |
| 2004-11-18 | WT       |    5     |
| 2002-08-30 | ARWR     |    5     |
| 2002-05-30 | ARWR     |    3     |
| 2002-10-02 | ARWR     |    3     |
| 2011-07-21 | TGTX     |    2     |
| 2002-03-28 | ARWR     |    2     |
| 2012-11-27 | ACAD     |    1.826 |
| 2003-06-13 | WT       |    1.8   |
| 2000-01-26 | ACHC     |    1.625 |
| 2001-09-17 | OSIS     |    1.41  |
| 2021-01-27 | GME      |    1.398 |
| 2002-02-19 | SNEX     |    1.234 |
| 2024-05-14 | GME      |    1.129 |
| 2012-07-24 | SRPT     |    1.127 |

Largest intraday moves after cleaning:

| date       | ticker   |   return |
|:-----------|:---------|---------:|
| 2004-11-18 | WT       |    5.25  |
| 2000-11-22 | ACHC     |    3.5   |
| 2012-02-06 | TGTX     |    3.286 |
| 2002-11-06 | WT       |    1.714 |
| 2002-04-26 | ARWR     |    1.667 |
| 2014-07-01 | LEU      |    1.423 |
| 2008-10-20 | CELH     |    1.333 |
| 2002-10-28 | WT       |    1.333 |
| 2003-06-09 | CCOI     |    1.26  |
| 2005-10-25 | AGX      |    1.228 |
| 2020-03-13 | CHRD     |    1.222 |
| 2003-07-07 | EHC      |    1.1   |
| 2021-02-24 | GME      |    1.052 |
| 2000-01-26 | THRM     |    1.05  |
| 2021-11-02 | CAR      |    1.049 |


## Bid-ask spreads (Alpaca SIP quotes)

24668 measurements: 140 stocks x 33 days x 6 times of day, 10-second windows.

Half-spread in bp, 10:00-15:30 (what an intraday market order pays):

| liquidity (21-day median $ volume) | obs | median | mean | 90th pct | model: daily | model: intraday | Corwin-Schultz |
|---|---|---|---|---|---|---|---|
| < $20M | 2771.0 | 10.24 | 16.23 | 33.47 | 12.0 | 8.0 | 31.6 |
| $20-100M | 4811.0 | 4.19 | 7.80 | 16.77 | 6.0 | 8.0 | 28.9 |
| $100-500M | 3655.0 | 2.92 | 5.05 | 10.92 | 3.0 | 4.0 | 25.8 |
| > $500M | 986.0 | 1.61 | 2.88 | 6.37 | 1.5 | 2.0 | 24.1 |

Median half-spread (bp) by time of day:

| time     |   < $20M |   $20-100M |   $100-500M |   > $500M |
|:---------|---------:|-----------:|------------:|----------:|
| 09:30:05 |    75.96 |      39.12 |       19.28 |      8.83 |
| 09:35:00 |    39.61 |      16.52 |        9.42 |      3.93 |
| 10:00:00 |    19.18 |       7.79 |        5.1  |      2.57 |
| 12:00:00 |     9.36 |       3.91 |        2.65 |      1.47 |
| 15:30:00 |     6.08 |       2.83 |        1.92 |      1.15 |
| 15:55:00 |     5.05 |       2.59 |        1.65 |      1.16 |

Corwin-Schultz vs quoted spread, rank correlation: 0.25.

Opening auction: official open vs midquote 0-10 s after the open: median |gap| 18.5 bp (mean signed -1.4 bp).

## Edge vs. cost, signal by signal

Break-even cost = gross profit per dollar traded (bp). A one-way trade costs about half-spread + 1 bp slippage: ~2.5 bp for the most liquid names, 4-13 bp for the rest.

### Composite (signals and weights chosen on 2004-2014 only)

|   halflife | universe   |   gross_ret_1st |   gross_sharpe_1st |   turnover_1st |   breakeven_bp_1st |   net_sharpe_1st |   gross_ret_2nd |   gross_sharpe_2nd |   turnover_2nd |   breakeven_bp_2nd |   net_sharpe_2nd |
|-----------:|:-----------|----------------:|-------------------:|---------------:|-------------------:|-----------------:|----------------:|-------------------:|---------------:|-------------------:|-----------------:|
|          0 | all        |           0.103 |              1.875 |          0.858 |              4.749 |           -1.427 |           0.057 |              0.92  |          0.908 |              2.507 |           -1.651 |
|          0 | top300     |           0.105 |              1.636 |          0.869 |              4.784 |           -0.214 |           0.053 |              0.734 |          0.915 |              2.284 |           -0.444 |
|          5 | all        |           0.063 |              1.138 |          0.187 |             13.472 |            0.42  |           0.03  |              0.455 |          0.191 |              6.315 |           -0.053 |
|          5 | top300     |           0.061 |              0.942 |          0.194 |             12.555 |            0.521 |           0.023 |              0.294 |          0.203 |              4.486 |            0.05  |
|         20 | all        |           0.046 |              0.846 |          0.093 |             19.569 |            0.467 |           0.015 |              0.258 |          0.089 |              6.827 |           -0.011 |
|         20 | top300     |           0.039 |              0.593 |          0.099 |             15.375 |            0.368 |           0.012 |              0.161 |          0.104 |              4.458 |            0.023 |

### Top 15 signal/smoothing/universe by 2004-2014 break-even

| signal      |   halflife | universe   |   breakeven_bp_1st |   breakeven_bp_2nd |   gross_sharpe_1st |   gross_sharpe_2nd |   net_sharpe_1st |   net_sharpe_2nd |   turnover_1st |
|:------------|-----------:|:-----------|-------------------:|-------------------:|-------------------:|-------------------:|-----------------:|-----------------:|---------------:|
| amihud      |         20 | all        |              78.92 |             122.84 |               0.83 |               0.52 |             0.71 |             0.48 |           0.02 |
| size_proxy  |         20 | all        |              71.92 |              90.97 |               0.69 |               0.38 |             0.58 |             0.34 |           0.02 |
| size_proxy  |          5 | all        |              68.33 |              80    |               0.72 |               0.38 |             0.6  |             0.33 |           0.02 |
| amihud      |          5 | all        |              65.49 |              79.85 |               0.85 |               0.51 |             0.71 |             0.46 |           0.02 |
| size_proxy  |          0 | all        |              57.22 |              57.38 |               0.72 |               0.38 |             0.58 |             0.32 |           0.02 |
| amihud      |         20 | top300     |              44.45 |              -3.84 |               0.64 |              -0.07 |             0.53 |            -0.15 |           0.03 |
| amihud      |          5 | top300     |              38.27 |              -2.84 |               0.66 |              -0.06 |             0.54 |            -0.15 |           0.04 |
| size_proxy  |         20 | top300     |              37.18 |             -25.89 |               0.58 |              -0.53 |             0.46 |            -0.62 |           0.03 |
| size_proxy  |          5 | top300     |              36.66 |             -25.5  |               0.62 |              -0.54 |             0.49 |            -0.64 |           0.03 |
| amihud      |          0 | all        |              34.7  |              32.12 |               0.83 |               0.52 |             0.6  |             0.4  |           0.04 |
| cs_spread   |         20 | all        |              34.05 |              79.23 |               0.24 |               0.66 |             0.17 |             0.59 |           0.03 |
| size_proxy  |          0 | top300     |              31.06 |             -21.35 |               0.62 |              -0.54 |             0.48 |            -0.65 |           0.04 |
| bollinger_z |         20 | all        |              27.68 |              13.73 |               0.94 |               0.39 |             0.64 |             0.19 |           0.08 |
| rsi_14      |         20 | all        |              26.86 |              12.48 |               0.65 |               0.23 |             0.44 |             0.1  |           0.06 |
| cs_spread   |         20 | top300     |              25.12 |              36.3  |               0.19 |               0.43 |             0.14 |             0.38 |           0.04 |

Signals whose break-even is above 5 bp in **both** periods: 48

| signal          |   halflife | universe   |   breakeven_bp_1st |   breakeven_bp_2nd |   net_sharpe_1st |   net_sharpe_2nd |
|:----------------|-----------:|:-----------|-------------------:|-------------------:|-----------------:|-----------------:|
| rev_1d          |          5 | all        |               9.14 |               5.24 |             0.11 |            -0.28 |
| rev_1d          |         20 | all        |              14.49 |               7.36 |             0.45 |             0.02 |
| rev_1d          |         20 | top300     |              12.77 |               6.12 |             0.46 |             0.16 |
| rev_5d          |          5 | all        |              12.8  |               8.01 |             0.3  |             0.07 |
| rev_5d          |          5 | top300     |              12.47 |               5.66 |             0.42 |             0.12 |
| rev_5d          |         20 | all        |              20.49 |              11    |             0.44 |             0.14 |
| rev_5d          |         20 | top300     |              15.88 |               6.58 |             0.33 |             0.1  |
| rev_21d         |          0 | all        |               8.08 |               6.87 |            -0.04 |            -0.02 |
| rev_21d         |          5 | all        |              13.29 |              12.81 |             0.14 |             0.18 |
| rev_21d         |          5 | top300     |               8.13 |               7.81 |             0.06 |             0.12 |
| rev_21d         |         20 | all        |              19.9  |              14.88 |             0.21 |             0.14 |
| rev_21d         |         20 | top300     |              11.77 |               9.93 |             0.1  |             0.12 |
| resid_rev_5d    |          5 | all        |               8.55 |               5.29 |             0.03 |            -0.2  |
| resid_rev_5d    |         20 | all        |              15.76 |               7.75 |             0.63 |             0.05 |
| resid_rev_5d    |         20 | top300     |              11.55 |               5.95 |             0.44 |             0.13 |
| ou_sscore       |         20 | all        |              21.83 |               5.91 |             0.88 |            -0.07 |
| bollinger_z     |          5 | all        |              17.19 |               9.92 |             0.55 |             0.15 |
| bollinger_z     |          5 | top300     |              16.27 |               7.36 |             0.61 |             0.18 |
| bollinger_z     |         20 | all        |              27.68 |              13.73 |             0.64 |             0.19 |
| bollinger_z     |         20 | top300     |              22.93 |              10.15 |             0.54 |             0.18 |
| rsi_14          |          0 | all        |               8.27 |               5.37 |            -0.02 |            -0.18 |
| rsi_14          |          5 | all        |              19.29 |              11.1  |             0.47 |             0.15 |
| rsi_14          |          5 | top300     |              15.9  |               6.31 |             0.42 |             0.09 |
| rsi_14          |         20 | all        |              26.86 |              12.48 |             0.44 |             0.1  |
| rsi_14          |         20 | top300     |              20.9  |               8.37 |             0.36 |             0.09 |
| intraday_rev    |         20 | all        |              11.03 |               5.61 |             0.18 |            -0.13 |
| low_volume_rev  |          5 | all        |              12.76 |               7.6  |             0.31 |             0.04 |
| low_volume_rev  |          5 | top300     |              12.66 |               6.03 |             0.46 |             0.15 |
| low_volume_rev  |         20 | all        |              19.73 |              10.53 |             0.44 |             0.13 |
| low_volume_rev  |         20 | top300     |              15.64 |               6.48 |             0.35 |             0.1  |
| intraday_rev_21 |          0 | all        |               7.68 |               5.6  |            -0.08 |            -0.15 |
| intraday_rev_21 |          5 | all        |              10.36 |               8.19 |             0.05 |             0.03 |
| intraday_rev_21 |         20 | all        |              13.49 |               7.24 |             0.09 |            -0    |
| amihud          |          0 | all        |              34.7  |              32.12 |             0.6  |             0.4  |
| amihud          |          5 | all        |              65.49 |              79.85 |             0.71 |             0.46 |
| amihud          |         20 | all        |              78.92 |             122.84 |             0.71 |             0.48 |
| size_proxy      |          0 | all        |              57.22 |              57.38 |             0.58 |             0.32 |
| size_proxy      |          5 | all        |              68.33 |              80    |             0.6  |             0.33 |
| size_proxy      |         20 | all        |              71.92 |              90.97 |             0.58 |             0.34 |
| close_location  |         20 | all        |              18.89 |               7.64 |             0.49 |             0.02 |
| cs_spread       |          0 | all        |               5.48 |               8.23 |            -0.13 |             0.07 |
| cs_spread       |          5 | all        |              16.76 |              31.1  |             0.1  |             0.46 |
| cs_spread       |          5 | top300     |              13.67 |              19.28 |             0.1  |             0.33 |
| cs_spread       |         20 | all        |              34.05 |              79.23 |             0.17 |             0.59 |
| cs_spread       |         20 | top300     |              25.12 |              36.3  |             0.14 |             0.38 |
| peer_gap        |          5 | all        |               9.87 |               7.12 |             0.14 |             0    |
| peer_gap        |         20 | all        |              16.7  |               9.79 |             0.44 |             0.13 |
| peer_gap        |         20 | top300     |              11.99 |               5.85 |             0.3  |             0.1  |


## Fundamental and news signals

Fundamentals start in 2009 and news in 2015, so '1st' covers 2009/2015-2014 only (empty for news) - judge news on the 2nd period.

IC by horizon:

| signal         |   horizon |   ic_1st |   ic_2nd |    t_1st |   t_2nd |
|:---------------|----------:|---------:|---------:|---------:|--------:|
| earnings_yield |         5 |  -0.0008 |  -0.0017 |  -0.1468 | -0.3133 |
| earnings_yield |        21 |  -0.0028 |   0.0014 |  -0.2684 |  0.126  |
| book_to_market |         5 |  -0.0045 |  -0.0061 |  -0.8194 | -0.9641 |
| book_to_market |        21 |  -0.0076 |  -0.0033 |  -0.6786 | -0.2473 |
| gross_prof     |         5 |   0.0022 |   0.001  |   0.5386 |  0.3544 |
| gross_prof     |        21 |   0.0024 |  -0.0002 |   0.2828 | -0.0335 |
| asset_growth   |         5 |   0.0031 |  -0.0071 |   0.7239 | -2.2472 |
| asset_growth   |        21 |   0.006  |  -0.009  |   0.7343 | -1.3544 |
| accruals       |         5 |   0.007  |   0.0015 |   1.938  |  0.5062 |
| accruals       |        21 |   0.0178 |  -0.0007 |   2.5599 | -0.116  |
| sue            |         5 |   0.0074 |   0.0056 |   2.5282 |  1.7071 |
| sue            |        21 |   0.0072 |   0.0038 |   1.2335 |  0.5909 |
| ear            |         5 |   0.0043 |   0.0029 |   1.2386 |  1.072  |
| ear            |        21 |   0.006  |   0.0011 |   0.8658 |  0.2036 |
| news_volume    |         5 |   0.0137 |   0.0045 |   1.0678 |  2.0269 |
| news_volume    |        21 |   0.033  |   0.0025 |   3.4909 |  0.6119 |
| news_tone      |         5 | nan      |  -0.0035 | nan      | -1.7802 |
| news_tone      |        21 | nan      |  -0.0049 | nan      | -1.2677 |
| no_news_rev    |         5 |  -0.0001 |   0.0081 |  -0.0178 |  1.8175 |
| no_news_rev    |        21 |   0.0011 |   0.0099 |   0.1675 |  1.1888 |
| news_mom       |         5 |   0.0009 |  -0.0087 | nan      | -1.9398 |
| news_mom       |        21 |   0.0065 |  -0.0083 | nan      | -0.9879 |

| signal         | family      |   halflife | universe   |   breakeven_bp_1st |   breakeven_bp_2nd |   gross_sharpe_1st |   gross_sharpe_2nd |   net_sharpe_1st |   net_sharpe_2nd |   turnover_1st |
|:---------------|:------------|-----------:|:-----------|-------------------:|-------------------:|-------------------:|-------------------:|-----------------:|-----------------:|---------------:|
| earnings_yield | fundamental |          0 | all        |            -69.683 |            -18.21  |             -0.518 |             -0.22  |           -0.571 |           -0.31  |          0.013 |
| earnings_yield | fundamental |          0 | top300     |            -46.694 |              2.309 |             -0.477 |              0.036 |           -0.529 |           -0.026 |          0.019 |
| earnings_yield | fundamental |          5 | all        |           -138.216 |            -51.316 |             -0.525 |             -0.309 |           -0.554 |           -0.357 |          0.007 |
| earnings_yield | fundamental |          5 | top300     |            -66.994 |             -2.718 |             -0.468 |             -0.032 |           -0.507 |           -0.079 |          0.013 |
| earnings_yield | fundamental |         20 | all        |           -180.953 |            -81.477 |             -0.531 |             -0.388 |           -0.554 |           -0.427 |          0.005 |
| earnings_yield | fundamental |         20 | top300     |            -71.146 |             -8.584 |             -0.448 |             -0.094 |           -0.483 |           -0.138 |          0.012 |
| book_to_market | fundamental |          0 | all        |              4.759 |             28.955 |              0.045 |              0.257 |           -0.025 |            0.187 |          0.013 |
| book_to_market | fundamental |          0 | top300     |              7.522 |             10.973 |              0.087 |              0.151 |            0.026 |            0.096 |          0.018 |
| book_to_market | fundamental |          5 | all        |              7.468 |             48.169 |              0.037 |              0.178 |           -0.002 |            0.147 |          0.007 |
| book_to_market | fundamental |          5 | top300     |              8.441 |             10.912 |              0.07  |              0.112 |            0.023 |            0.069 |          0.013 |
| book_to_market | fundamental |         20 | all        |              5.053 |             46.473 |              0.02  |              0.129 |           -0.011 |            0.104 |          0.005 |
| book_to_market | fundamental |         20 | top300     |              8.474 |              9.238 |              0.067 |              0.091 |            0.022 |            0.05  |          0.012 |
| gross_prof     | fundamental |          0 | all        |             24.871 |             39.019 |              0.163 |              0.173 |            0.118 |            0.136 |          0.007 |
| gross_prof     | fundamental |          0 | top300     |             -9.43  |              2.038 |             -0.161 |              0.041 |           -0.253 |           -0.042 |          0.02  |
| gross_prof     | fundamental |          5 | all        |             38.736 |             40.398 |              0.18  |              0.158 |            0.145 |            0.125 |          0.005 |
| gross_prof     | fundamental |          5 | top300     |             -8.968 |              2.037 |             -0.132 |              0.039 |           -0.214 |           -0.04  |          0.017 |
| gross_prof     | fundamental |         20 | all        |             47.88  |             44.524 |              0.179 |              0.154 |            0.15  |            0.124 |          0.004 |
| gross_prof     | fundamental |         20 | top300     |             -8.982 |              2.482 |             -0.124 |              0.047 |           -0.201 |           -0.031 |          0.016 |
| asset_growth   | fundamental |          0 | all        |             -8.017 |            -20.093 |             -0.098 |             -0.274 |           -0.184 |           -0.377 |          0.01  |
| asset_growth   | fundamental |          0 | top300     |             -0.329 |             -5.352 |             -0.005 |             -0.12  |           -0.089 |           -0.209 |          0.016 |
| asset_growth   | fundamental |          5 | all        |            -17.35  |            -36.113 |             -0.137 |             -0.319 |           -0.195 |           -0.388 |          0.007 |
| asset_growth   | fundamental |          5 | top300     |             -1.494 |             -9.319 |             -0.018 |             -0.169 |           -0.084 |           -0.243 |          0.012 |
| asset_growth   | fundamental |         20 | all        |            -16.546 |            -43.224 |             -0.105 |             -0.314 |           -0.152 |           -0.372 |          0.005 |
| asset_growth   | fundamental |         20 | top300     |              1.273 |             -8.126 |              0.014 |             -0.137 |           -0.046 |           -0.206 |          0.011 |
| accruals       | fundamental |          0 | all        |            126.039 |             58.987 |              0.557 |              0.518 |            0.524 |            0.447 |          0.007 |
| accruals       | fundamental |          0 | top300     |             68.95  |              5.577 |              0.544 |              0.139 |            0.501 |            0.036 |          0.014 |
| accruals       | fundamental |          5 | all        |            165.474 |             66.184 |              0.567 |              0.486 |            0.539 |            0.425 |          0.006 |
| accruals       | fundamental |          5 | top300     |             79.665 |              7.401 |              0.55  |              0.172 |            0.512 |            0.076 |          0.012 |
| accruals       | fundamental |         20 | all        |            202.639 |             74.838 |              0.589 |              0.491 |            0.565 |            0.436 |          0.005 |
| accruals       | fundamental |         20 | top300     |             86.26  |             10.03  |              0.558 |              0.227 |            0.521 |            0.132 |          0.011 |
| sue            | fundamental |          0 | all        |              1.087 |              1.151 |              0.018 |              0.035 |           -0.095 |           -0.178 |          0.018 |
| sue            | fundamental |          0 | top300     |             -0.211 |              9.736 |             -0.006 |              0.332 |           -0.137 |            0.2   |          0.025 |
| sue            | fundamental |          5 | all        |             17.076 |              3.177 |              0.131 |              0.062 |            0.077 |           -0.079 |          0.011 |
| sue            | fundamental |          5 | top300     |             10.441 |             13.163 |              0.147 |              0.332 |            0.074 |            0.233 |          0.018 |
| sue            | fundamental |         20 | all        |             16.265 |              3.404 |              0.093 |              0.049 |            0.053 |           -0.056 |          0.008 |
| sue            | fundamental |         20 | top300     |             10.498 |             14.685 |              0.123 |              0.299 |            0.061 |            0.218 |          0.015 |
| ear            | fundamental |          0 | all        |             12.562 |              3.147 |              0.259 |              0.115 |            0.107 |           -0.156 |          0.021 |
| ear            | fundamental |          0 | top300     |             10.208 |             -2.187 |              0.264 |             -0.088 |            0.135 |           -0.244 |          0.029 |
| ear            | fundamental |          5 | all        |             19.136 |              1.822 |              0.282 |              0.05  |            0.17  |           -0.156 |          0.015 |
| ear            | fundamental |          5 | top300     |             12.175 |             -9.717 |              0.24  |             -0.309 |            0.138 |           -0.434 |          0.022 |
| ear            | fundamental |         20 | all        |             25.441 |             -0.037 |              0.3   |             -0.001 |            0.208 |           -0.165 |          0.012 |
| ear            | fundamental |         20 | top300     |             16.582 |            -14.099 |              0.277 |             -0.383 |            0.188 |           -0.492 |          0.018 |
| news_volume    | news        |          0 | all        |            205.098 |              0.623 |              0.206 |              0.221 |            0.202 |           -1.961 |          0.001 |
| news_volume    | news        |          0 | top300     |            205.705 |              0.362 |              0.206 |              0.122 |            0.203 |           -1.114 |          0.001 |
| news_volume    | news        |          5 | all        |            455.793 |              2.261 |              0.285 |              0.401 |            0.283 |           -0.733 |          0.001 |
| news_volume    | news        |          5 | top300     |            200.621 |              1.076 |              0.309 |              0.167 |            0.301 |           -0.412 |          0.002 |
| news_volume    | news        |         20 | all        |            455.794 |              3.345 |              0.285 |              0.315 |            0.283 |           -0.294 |          0.001 |
| news_volume    | news        |         20 | top300     |            200.621 |              1.551 |              0.309 |              0.139 |            0.301 |           -0.2   |          0.002 |
| news_tone      | news        |          0 | all        |              0     |             -1.418 |            nan     |             -0.579 |          nan     |           -2.789 |          0     |
| news_tone      | news        |          0 | top300     |              0     |             -1.32  |            nan     |             -0.471 |          nan     |           -1.709 |          0     |
| news_tone      | news        |          5 | all        |              0     |             -2.139 |            nan     |             -0.274 |          nan     |           -0.986 |          0     |
| news_tone      | news        |          5 | top300     |              0     |             -2.505 |            nan     |             -0.28  |          nan     |           -0.676 |          0     |
| news_tone      | news        |         20 | all        |              0     |             -3.671 |            nan     |             -0.151 |          nan     |           -0.382 |          0     |
| news_tone      | news        |         20 | top300     |              0     |             -1.932 |            nan     |             -0.079 |          nan     |           -0.226 |          0     |
| no_news_rev    | news        |          0 | all        |              1.477 |              3.229 |              0.05  |              0.831 |           -0.098 |           -1.192 |          0.065 |
| no_news_rev    | news        |          0 | top300     |              0.827 |              2.44  |              0.031 |              0.677 |           -0.123 |           -0.401 |          0.066 |
| no_news_rev    | news        |          5 | all        |             12.165 |              7.225 |              0.221 |              0.676 |            0.143 |           -0.063 |          0.035 |
| no_news_rev    | news        |          5 | top300     |              8.287 |              4.818 |              0.169 |              0.47  |            0.086 |            0.086 |          0.036 |
| no_news_rev    | news        |         20 | all        |             15.201 |             10.295 |              0.169 |              0.51  |            0.123 |            0.113 |          0.021 |
| no_news_rev    | news        |         20 | top300     |              8.218 |              5.103 |              0.106 |              0.279 |            0.054 |            0.061 |          0.022 |
| news_mom       | news        |          0 | all        |             12.941 |             -4.538 |              0.128 |             -0.878 |            0.083 |           -2.066 |          0.003 |
| news_mom       | news        |          0 | top300     |             25.58  |             -3.545 |              0.304 |             -0.621 |            0.257 |           -1.254 |          0.003 |
| news_mom       | news        |          5 | all        |              3.96  |             -7.121 |              0.003 |             -0.507 |           -0     |           -0.954 |          0.002 |
| news_mom       | news        |          5 | top300     |             -1.736 |             -5.458 |             -0.003 |             -0.343 |           -0.012 |           -0.573 |          0.003 |
| news_mom       | news        |         20 | all        |             -5.031 |            -10.037 |             -0.004 |             -0.356 |           -0.007 |           -0.581 |          0.002 |
| news_mom       | news        |         20 | top300     |             -6.102 |             -7.154 |             -0.011 |             -0.242 |           -0.019 |           -0.367 |          0.003 |


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

## Trading only when the edge is biggest

IC over the next 5 days inside vs. outside each condition, and a portfolio that only trades inside it (hl = smoothing half-life in days). Break-even in bp per dollar traded.

| signal         | condition   |   share_in |   ic5_in_1st |   ic5_out_1st |   ic5_in_2nd |   ic5_out_2nd |   hl0_breakeven_bp_1st |   hl0_breakeven_bp_2nd |   hl5_breakeven_bp_1st |   hl5_breakeven_bp_2nd |   hl5_net_sharpe_1st |   hl5_net_sharpe_2nd |
|:---------------|:------------|-----------:|-------------:|--------------:|-------------:|--------------:|-----------------------:|-----------------------:|-----------------------:|-----------------------:|---------------------:|---------------------:|
| rev_5d         | stressed    |     0.2784 |       0.0338 |        0.0176 |       0.0247 |        0.0087 |                 8.5706 |                 6.5097 |                 9.9094 |                 9.2807 |               0.0748 |               0.0832 |
| rev_5d         | dispersed   |     0.2797 |       0.0315 |        0.02   |       0.0232 |        0.0069 |                 7.6377 |                 5.4065 |                 6.5453 |                 4.4203 |              -0.1186 |              -0.2779 |
| rev_5d         | low_volume  |     0.3237 |       0.0214 |        0.0221 |       0.0103 |        0.0141 |                 2.9373 |                 2.1763 |                 3.1186 |                 2.9886 |              -0.9265 |              -0.7794 |
| rev_5d         | no_news     |     0.8031 |       0.0225 |      nan      |       0.0126 |        0.0131 |                 6.2702 |                 3.0248 |                12.7969 |                 4.1916 |               0.3024 |              -0.4443 |
| rev_5d         | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 6.2701 |                 4.2874 |                12.7987 |                 8.0143 |               0.3026 |               0.0663 |
| resid_rev_1d   | stressed    |     0.2784 |       0.0145 |        0.011  |       0.0102 |        0.0056 |                 3.012  |                 1.2655 |                 6.9371 |                 4.432  |              -0.2049 |              -0.2729 |
| resid_rev_1d   | dispersed   |     0.2797 |       0.0193 |        0.0101 |       0.0131 |        0.0031 |                 3.3133 |                 1.4443 |                 7.3193 |                 3.3715 |              -0.1438 |              -0.7769 |
| resid_rev_1d   | low_volume  |     0.3237 |       0.0158 |        0.0102 |       0.0064 |        0.0072 |                 2.6781 |                 0.7817 |                 4.0194 |                 1.348  |              -2.5122 |              -3.0369 |
| resid_rev_1d   | no_news     |     0.8031 |       0.0121 |      nan      |       0.0065 |        0.0078 |                 2.4889 |                 0.7044 |                 6.978  |                 1.9758 |              -0.4956 |              -2.2306 |
| resid_rev_1d   | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 2.4889 |                 0.9125 |                 6.9786 |                 3.1417 |              -0.4953 |              -1.0226 |
| low_volume_rev | stressed    |     0.2784 |       0.035  |        0.0172 |       0.0244 |        0.0085 |                 7.8754 |                 5.9222 |                11.0005 |                 9      |               0.1298 |               0.0754 |
| low_volume_rev | dispersed   |     0.2797 |       0.0314 |        0.0201 |       0.023  |        0.0067 |                 6.591  |                 4.8681 |                 6.3357 |                 4.082  |              -0.1479 |              -0.3452 |
| low_volume_rev | low_volume  |     0.3237 |       0.0213 |        0.0226 |       0.0103 |        0.0139 |                 2.7989 |                 2.2327 |                 4.0035 |                 3.0961 |              -0.7901 |              -0.7553 |
| low_volume_rev | no_news     |     0.8031 |       0.0225 |      nan      |       0.0127 |        0.0126 |                 5.4903 |                 2.8627 |                12.7631 |                 4.1605 |               0.312  |              -0.4677 |
| low_volume_rev | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 5.4902 |                 3.8513 |                12.765  |                 7.5983 |               0.3121 |               0.0354 |
| peer_gap       | stressed    |     0.2784 |       0.0211 |        0.0128 |       0.0157 |        0.0089 |                 5.7678 |                 5.0614 |                 7.9497 |                 7.7661 |              -0.0232 |               0.03   |
| peer_gap       | dispersed   |     0.2797 |       0.0214 |        0.0136 |       0.0182 |        0.0061 |                 6.1645 |                 4.1219 |                 5.8631 |                 3.906  |              -0.2427 |              -0.4436 |
| peer_gap       | low_volume  |     0.3237 |       0.0158 |        0.0146 |       0.008  |        0.0118 |                 2.5244 |                 1.9448 |                 2.0692 |                 2.686  |              -1.5669 |              -1.2196 |
| peer_gap       | no_news     |     0.8031 |       0.0153 |      nan      |       0.0106 |        0.0105 |                 4.7465 |                 2.4588 |                 9.8647 |                 3.6436 |               0.1381 |              -0.7285 |
| peer_gap       | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 4.7467 |                 3.6618 |                 9.8672 |                 7.1243 |               0.1383 |               0.0034 |
| composite      | stressed    |     0.2784 |       0.0278 |        0.0192 |       0.0232 |        0.0105 |                 5.7861 |                 2.8667 |                 7.5474 |                 5.6365 |              -0.0371 |              -0.0634 |
| composite      | dispersed   |     0.2797 |       0.0318 |        0.019  |       0.0247 |        0.0075 |                 6.1387 |                 2.9909 |                 6.3961 |                 2.4852 |              -0.169  |              -0.5932 |
| composite      | low_volume  |     0.3237 |       0.0243 |        0.0204 |       0.0125 |        0.0146 |                 3.3017 |                 1.7183 |                 3.4303 |                 1.8321 |              -1.1753 |              -1.159  |
| composite      | no_news     |     0.8031 |       0.0218 |      nan      |       0.0139 |        0.014  |                 4.6137 |                 1.9803 |                13.4534 |                 2.8235 |               0.4308 |              -0.7092 |
| composite      | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 4.6139 |                 2.4685 |                13.4563 |                 6.3923 |               0.431  |              -0.0482 |
| no_news_rev    | stressed    |     0.2784 |       0.0114 |       -0.0016 |       0.0186 |        0.0041 |                -2.082  |                 6.8415 |                -9.343  |                10.3685 |              -0.1563 |               0.1303 |
| no_news_rev    | dispersed   |     0.2797 |       0.001  |       -0.0003 |       0.0151 |        0.0038 |                 5.8316 |                 4.4107 |                 1.3716 |                 3.2843 |              -0.1163 |              -0.6678 |
| no_news_rev    | low_volume  |     0.3237 |      -0.0014 |        0.0012 |       0.0072 |        0.0083 |                -3.154  |                 2.4872 |                 1.1597 |                 2.9082 |              -0.3381 |              -1.0896 |
| no_news_rev    | no_news     |     0.8031 |      -0.0001 |      nan      |       0.0126 |        0.0018 |                 1.4766 |                 3.2036 |                12.1648 |                 5.0726 |               0.1434 |              -0.3884 |
| no_news_rev    | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 1.4766 |                 3.2286 |                12.1648 |                 7.2251 |               0.1434 |              -0.063  |
| sue            | stressed    |     0.2784 |       0.0091 |        0.0069 |       0.0038 |        0.0062 |                13.7967 |                -5.3239 |                16.3228 |                -5.5428 |               0.2127 |              -0.5376 |
| sue            | dispersed   |     0.2797 |       0.0073 |        0.0074 |       0.0039 |        0.0066 |                 2.4466 |                -2.3233 |                 2.3996 |                -2.3222 |              -0.935  |              -1.8931 |
| sue            | low_volume  |     0.3237 |       0.0076 |        0.0079 |       0.0064 |        0.0053 |                 0.9487 |                 0.0175 |                 0.7613 |                 0.6255 |              -0.7644 |              -1.2492 |
| sue            | no_news     |     0.8031 |       0.0074 |      nan      |       0.0048 |        0.0061 |                 1.0826 |                 0.2917 |                17.0606 |                 0.939  |               0.0773 |              -0.8698 |
| sue            | always      |     1      |     nan      |      nan      |     nan      |      nan      |                 1.0875 |                 1.1508 |                17.0761 |                 3.1771 |               0.0774 |              -0.0786 |
| ear            | stressed    |     0.2784 |       0.0037 |        0.0044 |       0.0025 |        0.003  |                 5.5851 |                -2.8832 |                 6.8794 |                -4.459  |               0.0011 |              -0.7438 |
| ear            | dispersed   |     0.2797 |      -0.007  |        0.0064 |       0.0024 |        0.0031 |                -1.0811 |                -0.3691 |                -1.5035 |                -0.7456 |              -0.7798 |              -2.0972 |
| ear            | low_volume  |     0.3237 |       0.0033 |        0.0051 |       0.0028 |        0.0027 |                 2.0295 |                 0.6756 |                 2.7681 |                 0.6767 |              -0.6233 |              -1.4596 |
| ear            | no_news     |     0.8031 |       0.0043 |      nan      |       0.0028 |        0.0036 |                12.5588 |                 1.6575 |                19.1318 |                 2.2477 |               0.1698 |              -0.7885 |
| ear            | always      |     1      |     nan      |      nan      |     nan      |      nan      |                12.5616 |                 3.1468 |                19.1359 |                 1.8223 |               0.1698 |              -0.1562 |


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


## Beyond reversal: other kinds of strategy

Daily returns net of costs. Sharpe in 2006-2014 and 2015-2026; correlation with the current reversal book and with the S&P 500 over the whole period (low = diversifying).

|                                             |   sharpe_1st |   ret_1st |   max_dd_1st |   sharpe_2nd |   ret_2nd |   max_dd_2nd |   vol |   corr_with_reversal |   corr_with_spy |
|:--------------------------------------------|-------------:|----------:|-------------:|-------------:|----------:|-------------:|------:|---------------------:|----------------:|
| spy_vol_managed                             |        0.704 |     0.093 |       -0.306 |        0.84  |     0.113 |       -0.172 | 0.133 |                0.025 |           0.837 |
| spy_buy_hold                                |        0.466 |     0.099 |       -0.552 |        0.822 |     0.144 |       -0.337 | 0.192 |                0.042 |           1     |
| spy_ma200                                   |        0.614 |     0.071 |       -0.235 |        0.79  |     0.093 |       -0.236 | 0.117 |                0.038 |           0.609 |
| cross_asset_mom                             |        1.014 |     0.155 |       -0.205 |        0.783 |     0.093 |       -0.193 | 0.134 |                0.06  |           0.435 |
| pairs                                       |        0.847 |     0.012 |       -0.024 |        0.718 |     0.008 |       -0.032 | 0.013 |                0.148 |           0.225 |
| risk_parity                                 |        0.88  |     0.079 |       -0.208 |        0.697 |     0.057 |       -0.205 | 0.085 |                0.068 |           0.73  |
| spy_tsmom_12m                               |        0.716 |     0.097 |       -0.186 |        0.694 |     0.098 |       -0.267 | 0.139 |                0.119 |           0.722 |
| spy_macro_timing                            |        0.728 |     0.071 |       -0.159 |        0.612 |     0.068 |       -0.18  | 0.106 |                0.105 |           0.55  |
| broad_trend_12m                             |        0.598 |     0.029 |       -0.083 |        0.54  |     0.023 |       -0.108 | 0.045 |                0.045 |          -0.013 |
| short_vol_contango                          |        0.562 |     0.193 |       -0.424 |        0.518 |     0.213 |       -0.66  | 0.384 |                0.039 |           0.437 |
| spy_turn_of_month                           |        0.379 |     0.029 |       -0.224 |        0.476 |     0.031 |       -0.118 | 0.071 |                0.009 |           0.368 |
| multi_asset_trend                           |        0.769 |     0.043 |       -0.086 |        0.423 |     0.022 |       -0.131 | 0.054 |                0.044 |          -0.011 |
| short_vol_always                            |        0.722 |     0.263 |       -0.425 |        0.376 |     0.199 |       -0.952 | 0.465 |                0.077 |           0.479 |
| spy_hmm_timing                              |        0.524 |     0.039 |       -0.098 |        0.376 |     0.039 |       -0.208 | 0.092 |                0.028 |           0.479 |
| spy_overnight                               |        0.178 |     0.021 |       -0.276 |        0.37  |     0.042 |       -0.298 | 0.116 |                0.105 |           0.636 |
| spy_after_vix_spike                         |        0.263 |     0.041 |       -0.392 |        0.326 |     0.042 |       -0.283 | 0.142 |                0.101 |           0.74  |
| risk_parity(momentum_vol_scaled + reversal) |        0.232 |     0.014 |       -0.186 |        0.279 |     0.016 |       -0.134 | 0.058 |                0.747 |           0.009 |
| broad_trend_blend                           |        0.662 |     0.025 |       -0.044 |        0.228 |     0.008 |       -0.084 | 0.036 |               -0.073 |          -0.21  |
| risk_parity(mom_12_1 + reversal)            |       -0.013 |    -0.001 |       -0.258 |        0.217 |     0.012 |       -0.137 | 0.059 |                0.716 |          -0.052 |
| momentum_vol_scaled                         |        0.023 |     0.002 |       -0.261 |        0.209 |     0.019 |       -0.209 | 0.09  |                0.13  |          -0.006 |
| mom_12_1_beta_neutral                       |       -0.397 |    -0.038 |       -0.412 |        0.186 |     0.018 |       -0.153 | 0.097 |                0.135 |          -0.098 |
| momentum_macro_timed                        |        0.121 |     0.012 |       -0.414 |        0.172 |     0.023 |       -0.338 | 0.12  |                0.08  |          -0.004 |
| REVERSAL BOOK (current system)              |        0.436 |     0.034 |       -0.185 |        0.156 |     0.011 |       -0.231 | 0.074 |                1     |           0.042 |
| broad_xs_momentum                           |        0.19  |     0.026 |       -0.289 |        0.139 |     0.012 |       -0.208 | 0.11  |                0.118 |          -0.056 |
| broad_trend_3m                              |        0.701 |     0.034 |       -0.067 |        0.118 |     0.005 |       -0.121 | 0.045 |               -0.089 |          -0.19  |
| mom_12_1                                    |       -0.37  |    -0.031 |       -0.414 |        0.046 |     0.004 |       -0.262 | 0.089 |                0.139 |          -0.094 |
| spy_intraday                                |       -0.148 |    -0.025 |       -0.512 |        0.007 |     0.001 |       -0.285 | 0.148 |               -0.027 |           0.797 |
| mom_12_1_sector_neutral                     |       -0.083 |    -0.005 |       -0.278 |       -0.026 |    -0.002 |       -0.205 | 0.058 |                0.157 |          -0.018 |
| low_vol_beta_neutral                        |        0.033 |     0.005 |       -0.306 |       -0.04  |    -0.005 |       -0.353 | 0.141 |                0.01  |          -0.346 |
| factor_momentum                             |       -0.33  |    -0.027 |       -0.325 |       -0.083 |    -0.007 |       -0.307 | 0.086 |                0.072 |          -0.217 |
| etf_pairs                                   |        0.589 |     0.007 |       -0.016 |       -0.096 |    -0.001 |       -0.067 | 0.014 |                0.183 |           0.248 |
| high_52w_beta_neutral                       |       -0.185 |    -0.02  |       -0.393 |       -0.101 |    -0.011 |       -0.279 | 0.109 |                0.024 |          -0.316 |
| high_52w_vol_scaled                         |       -0.263 |    -0.027 |       -0.453 |       -0.193 |    -0.021 |       -0.422 | 0.107 |               -0.015 |          -0.293 |
| long_vol_backwardation                      |       -0.098 |    -0.019 |       -0.527 |       -0.221 |    -0.078 |       -0.876 | 0.293 |               -0.164 |          -0.385 |
| sector_momentum                             |       -0.183 |    -0.031 |       -0.497 |       -0.226 |    -0.033 |       -0.612 | 0.156 |                0.097 |          -0.17  |
| low_vol_vol_scaled                          |       -0.317 |    -0.042 |       -0.434 |       -0.335 |    -0.044 |       -0.593 | 0.132 |               -0.032 |          -0.367 |
| multi_factor                                |       -0.535 |    -0.047 |       -0.451 |       -0.373 |    -0.032 |       -0.427 | 0.086 |                0.051 |          -0.336 |
| high_52w_sector_neutral                     |       -0.591 |    -0.035 |       -0.425 |       -0.379 |    -0.023 |       -0.331 | 0.06  |                0.019 |          -0.286 |
| high_52w                                    |       -0.59  |    -0.056 |       -0.542 |       -0.406 |    -0.04  |       -0.475 | 0.097 |                0.013 |          -0.341 |
| earnings_premium                            |       -0.635 |    -0.141 |       -0.818 |       -0.457 |    -0.081 |       -0.75  | 0.198 |                0.078 |          -0.293 |
| low_vol                                     |       -0.446 |    -0.053 |       -0.483 |       -0.542 |    -0.06  |       -0.615 | 0.115 |               -0.005 |          -0.399 |
| sector_seasonality                          |       -0.748 |    -0.025 |       -0.215 |       -0.562 |    -0.071 |       -0.665 | 0.097 |                0.013 |           0.097 |
| low_vol_sector_neutral                      |       -0.369 |    -0.027 |       -0.338 |       -0.588 |    -0.038 |       -0.442 | 0.068 |               -0.003 |          -0.384 |

### A diversified book

Strategies with period-1 Sharpe > 0.3 (spy_tsmom_12m, spy_ma200, spy_vol_managed, spy_hmm_timing, spy_turn_of_month, multi_asset_trend, risk_parity, cross_asset_mom, broad_trend_3m, broad_trend_12m, broad_trend_blend, short_vol_contango, short_vol_always, spy_macro_timing, pairs, etf_pairs, REVERSAL BOOK (current system)), weighted by 1 / volatility, scaled to 10% volatility on period 1 only.

| portfolio                                       |   sharpe_1st |   ret_1st |   max_dd_1st |   sharpe_2nd |   ret_2nd |   max_dd_2nd |   vol |
|:------------------------------------------------|-------------:|----------:|-------------:|-------------:|----------:|-------------:|------:|
| diversified (17 strategies chosen on 2006-2014) |        1.284 |     0.128 |       -0.091 |        0.833 |     0.092 |       -0.178 | 0.106 |
| reversal book alone (10% vol)                   |        0.436 |     0.044 |       -0.23  |        0.156 |     0.014 |       -0.284 | 0.093 |

### Optimising across strategies (weights from 2006-2014 only)

| weights                   |   sharpe_1st |   ret_1st |   max_dd_1st |   sharpe_2nd |   ret_2nd |   max_dd_2nd |   vol | top_weights                                                                                 |
|:--------------------------|-------------:|----------:|-------------:|-------------:|----------:|-------------:|------:|:--------------------------------------------------------------------------------------------|
| Ledoit-Wolf mean-variance |        1.475 |     0.148 |       -0.091 |        0.744 |     0.089 |       -0.292 | 0.111 | pairs 31%, etf_pairs 21%, broad_trend_3m 13%, multi_asset_trend 8%, broad_trend_blend 6%    |
| inverse volatility        |        1.284 |     0.128 |       -0.091 |        0.833 |     0.092 |       -0.178 | 0.106 | etf_pairs 25%, pairs 20%, broad_trend_blend 8%, broad_trend_12m 6%, broad_trend_3m 6%       |
| equal weight              |        1.048 |     0.105 |       -0.102 |        0.72  |     0.089 |       -0.232 | 0.114 | spy_tsmom_12m 6%, spy_ma200 6%, spy_vol_managed 6%, spy_hmm_timing 6%, spy_turn_of_month 6% |

### Macro variables vs. next month's market and momentum returns

| variable              |   corr_next_month_market_1st |   corr_next_month_momentum_1st |   corr_next_month_market_2nd |   corr_next_month_momentum_2nd |
|:----------------------|-----------------------------:|-------------------------------:|-----------------------------:|-------------------------------:|
| term_spread_10y3m     |                       -0.162 |                          0.053 |                        0.041 |                          0.053 |
| term_spread_10y5y     |                       -0.096 |                          0.088 |                        0.201 |                          0.056 |
| credit_spread_hyg_lqd |                       -0.016 |                         -0.178 |                        0.097 |                         -0.065 |
| breakeven_tip_ief     |                       -0.048 |                          0.045 |                       -0.089 |                         -0.001 |
| dollar_index          |                       -0.036 |                         -0.105 |                       -0.132 |                         -0.043 |
| oil_wti               |                       -0.06  |                          0.122 |                       -0.032 |                          0.097 |
| vix                   |                       -0.072 |                          0.019 |                        0.09  |                          0.001 |

### Capacity: net Sharpe as the account grows (square-root market impact)

| strategy   |   account_usd |   sharpe_1st |   ret_1st |   max_dd_1st |   sharpe_2nd |   ret_2nd |   max_dd_2nd |   vol |
|:-----------|--------------:|-------------:|----------:|-------------:|-------------:|----------:|-------------:|------:|
| mom_12_1   |     10000     |       -0.372 |    -0.031 |       -0.414 |        0.046 |     0.004 |       -0.262 | 0.089 |
| mom_12_1   |         1e+06 |       -0.382 |    -0.032 |       -0.415 |        0.04  |     0.004 |       -0.266 | 0.089 |
| mom_12_1   |         1e+07 |       -0.406 |    -0.034 |       -0.418 |        0.025 |     0.002 |       -0.275 | 0.089 |
| mom_12_1   |         1e+08 |       -0.483 |    -0.041 |       -0.434 |       -0.019 |    -0.002 |       -0.302 | 0.09  |
| mom_12_1   |         1e+09 |       -0.724 |    -0.061 |       -0.5   |       -0.16  |    -0.015 |       -0.381 | 0.09  |
| high_52w   |     10000     |       -0.591 |    -0.056 |       -0.542 |       -0.407 |    -0.04  |       -0.476 | 0.097 |
| high_52w   |         1e+06 |       -0.602 |    -0.057 |       -0.545 |       -0.413 |    -0.041 |       -0.479 | 0.097 |
| high_52w   |         1e+07 |       -0.627 |    -0.059 |       -0.551 |       -0.428 |    -0.042 |       -0.487 | 0.097 |
| high_52w   |         1e+08 |       -0.706 |    -0.067 |       -0.57  |       -0.475 |    -0.047 |       -0.512 | 0.097 |
| high_52w   |         1e+09 |       -0.952 |    -0.091 |       -0.627 |       -0.623 |    -0.061 |       -0.583 | 0.097 |

### Execution: trade at the next open or the next close?

| signal       | fill       |   sharpe_1st |   ret_1st |   max_dd_1st |   sharpe_2nd |   ret_2nd |   max_dd_2nd |   vol |
|:-------------|:-----------|-------------:|----------:|-------------:|-------------:|----------:|-------------:|------:|
| rev_5d       | next open  |        0.089 |     0.006 |       -0.155 |        0.068 |     0.006 |       -0.251 | 0.079 |
| rev_5d       | next close |       -0.028 |    -0.002 |       -0.149 |       -0.037 |    -0.003 |       -0.231 | 0.077 |
| resid_rev_1d | next open  |       -1.085 |    -0.037 |       -0.313 |       -1.022 |    -0.049 |       -0.46  | 0.043 |
| resid_rev_1d | next close |       -1.693 |    -0.056 |       -0.404 |       -1.344 |    -0.063 |       -0.54  | 0.041 |
| mom_12_1     | next open  |       -0.391 |    -0.032 |       -0.413 |       -0.011 |    -0.001 |       -0.302 | 0.088 |
| mom_12_1     | next close |       -0.376 |    -0.032 |       -0.408 |       -0.021 |    -0.002 |       -0.309 | 0.091 |

### Correlation matrix

|                                             |   mom_12_1 |   low_vol |   high_52w |   multi_factor |   factor_momentum |   spy_buy_hold |   spy_tsmom_12m |   spy_ma200 |   spy_vol_managed |   spy_hmm_timing |   spy_overnight |   spy_intraday |   spy_turn_of_month |   spy_after_vix_spike |   multi_asset_trend |   risk_parity |   cross_asset_mom |   sector_momentum |   broad_trend_3m |   broad_trend_12m |   broad_trend_blend |   broad_xs_momentum |   short_vol_contango |   short_vol_always |   long_vol_backwardation |   sector_seasonality |   spy_macro_timing |   momentum_macro_timed |   momentum_vol_scaled |   pairs |   etf_pairs |   mom_12_1_sector_neutral |   mom_12_1_beta_neutral |   low_vol_sector_neutral |   low_vol_beta_neutral |   low_vol_vol_scaled |   high_52w_sector_neutral |   high_52w_beta_neutral |   high_52w_vol_scaled |   earnings_premium |   REVERSAL BOOK (current system) |   risk_parity(mom_12_1 + reversal) |   risk_parity(momentum_vol_scaled + reversal) |
|:--------------------------------------------|-----------:|----------:|-----------:|---------------:|------------------:|---------------:|----------------:|------------:|------------------:|-----------------:|----------------:|---------------:|--------------------:|----------------------:|--------------------:|--------------:|------------------:|------------------:|-----------------:|------------------:|--------------------:|--------------------:|---------------------:|-------------------:|-------------------------:|---------------------:|-------------------:|-----------------------:|----------------------:|--------:|------------:|--------------------------:|------------------------:|-------------------------:|-----------------------:|---------------------:|--------------------------:|------------------------:|----------------------:|-------------------:|---------------------------------:|-----------------------------------:|----------------------------------------------:|
| mom_12_1                                    |       1    |      0.33 |       0.68 |           0.74 |              0.79 |          -0.09 |            0.07 |        0.05 |             -0.03 |             0.06 |           -0.03 |          -0.1  |               -0.05 |                 -0.02 |                0.28 |         -0.06 |              0.13 |              0.49 |             0.06 |              0.28 |                0.13 |                0.37 |                 0.01 |               0.01 |                    -0.02 |                 0.1  |              -0.06 |                   0.77 |                  0.9  |   -0.09 |       -0.01 |                      0.94 |                    0.92 |                     0.35 |                   0.27 |                 0.15 |                      0.71 |                    0.6  |                  0.49 |               0.2  |                             0.14 |                               0.76 |                                          0.69 |
| low_vol                                     |       0.33 |      1    |       0.82 |           0.86 |              0.56 |          -0.4  |           -0.26 |       -0.26 |             -0.37 |            -0.2  |            0.01 |          -0.52 |               -0.18 |                 -0.22 |                0.05 |         -0.3  |             -0.17 |              0.24 |             0.04 |              0.02 |                0.04 |                0.1  |                -0.18 |              -0.16 |                     0.09 |                -0.01 |              -0.22 |                   0.12 |                  0.16 |   -0.17 |       -0.08 |                      0.23 |                    0.3  |                     0.96 |                   0.81 |                 0.92 |                      0.74 |                    0.72 |                  0.72 |               0.34 |                            -0    |                               0.26 |                                          0.16 |
| high_52w                                    |       0.68 |      0.82 |       1    |           0.97 |              0.78 |          -0.34 |           -0.16 |       -0.14 |             -0.27 |            -0.1  |           -0.04 |          -0.41 |               -0.16 |                 -0.21 |                0.17 |         -0.25 |             -0.04 |              0.42 |             0.12 |              0.16 |                0.14 |                0.24 |                -0.12 |              -0.11 |                     0.06 |                 0.04 |              -0.18 |                   0.44 |                  0.54 |   -0.24 |       -0.11 |                      0.59 |                    0.62 |                     0.81 |                   0.66 |                 0.69 |                      0.95 |                    0.88 |                  0.89 |               0.31 |                             0.01 |                               0.5  |                                          0.41 |
| multi_factor                                |       0.74 |      0.86 |       0.97 |           1    |              0.81 |          -0.34 |           -0.15 |       -0.15 |             -0.27 |            -0.1  |           -0.02 |          -0.42 |               -0.16 |                 -0.18 |                0.18 |         -0.24 |             -0.04 |              0.43 |             0.08 |              0.17 |                0.11 |                0.26 |                -0.12 |              -0.11 |                     0.06 |                 0.05 |              -0.19 |                   0.48 |                  0.58 |   -0.2  |       -0.08 |                      0.64 |                    0.69 |                     0.85 |                   0.7  |                 0.72 |                      0.93 |                    0.86 |                  0.82 |               0.34 |                             0.05 |                               0.57 |                                          0.46 |
| factor_momentum                             |       0.79 |      0.56 |       0.78 |           0.81 |              1    |          -0.22 |           -0.04 |       -0.02 |             -0.13 |            -0.01 |           -0.03 |          -0.26 |               -0.09 |                 -0.14 |                0.23 |         -0.14 |              0.07 |              0.46 |             0.12 |              0.24 |                0.17 |                0.28 |                -0.08 |              -0.08 |                     0.02 |                 0.05 |              -0.08 |                   0.56 |                  0.68 |   -0.19 |       -0.08 |                      0.7  |                    0.72 |                     0.56 |                   0.46 |                 0.39 |                      0.77 |                    0.69 |                  0.6  |               0.26 |                             0.07 |                               0.61 |                                          0.53 |
| spy_buy_hold                                |      -0.09 |     -0.4  |      -0.34 |          -0.34 |             -0.22 |           1    |            0.72 |        0.61 |              0.84 |             0.48 |            0.64 |           0.8  |                0.37 |                  0.74 |               -0.01 |          0.73 |              0.43 |             -0.17 |            -0.19 |             -0.01 |               -0.21 |               -0.06 |                 0.44 |               0.48 |                    -0.39 |                 0.1  |               0.55 |                  -0    |                 -0.01 |    0.22 |        0.25 |                     -0.02 |                   -0.1  |                    -0.38 |                  -0.35 |                -0.37 |                     -0.29 |                   -0.32 |                 -0.29 |              -0.29 |                             0.04 |                              -0.05 |                                          0.01 |
| spy_tsmom_12m                               |       0.07 |     -0.26 |      -0.16 |          -0.15 |             -0.04 |           0.72 |            1    |        0.78 |              0.82 |             0.62 |            0.48 |           0.56 |                0.31 |                  0.43 |                0.36 |          0.56 |              0.49 |              0.04 |             0.04 |              0.38 |                0.11 |                0.32 |                 0.53 |               0.54 |                    -0.36 |                 0.08 |               0.5  |                   0.09 |                  0.12 |    0.11 |        0.2  |                      0.15 |                    0.07 |                    -0.24 |                  -0.21 |                -0.32 |                     -0.1  |                   -0.14 |                 -0.21 |              -0.07 |                             0.12 |                               0.12 |                                          0.14 |
| spy_ma200                                   |       0.05 |     -0.26 |      -0.14 |          -0.15 |             -0.02 |           0.61 |            0.78 |        1    |              0.83 |             0.7  |            0.36 |           0.51 |                0.29 |                  0.19 |                0.36 |          0.5  |              0.56 |              0.11 |             0.29 |              0.4  |                0.3  |                0.26 |                 0.55 |               0.51 |                    -0.16 |                 0.09 |               0.43 |                   0.08 |                  0.11 |    0.02 |        0.05 |                      0.12 |                    0.05 |                    -0.24 |                  -0.21 |                -0.31 |                     -0.08 |                   -0.12 |                 -0.17 |              -0.07 |                             0.04 |                               0.06 |                                          0.08 |
| spy_vol_managed                             |      -0.03 |     -0.37 |      -0.27 |          -0.27 |             -0.13 |           0.84 |            0.82 |        0.83 |              1    |             0.74 |            0.5  |           0.69 |                0.36 |                  0.39 |                0.23 |          0.66 |              0.54 |             -0.05 |             0.12 |              0.25 |                0.14 |                0.14 |                 0.6  |               0.57 |                    -0.23 |                 0.11 |               0.58 |                   0.03 |                  0.04 |    0.1  |        0.12 |                      0.05 |                   -0.03 |                    -0.35 |                  -0.3  |                -0.39 |                     -0.21 |                   -0.24 |                 -0.27 |              -0.19 |                             0.03 |                              -0.01 |                                          0.03 |
| spy_hmm_timing                              |       0.06 |     -0.2  |      -0.1  |          -0.1  |             -0.01 |           0.48 |            0.62 |        0.7  |              0.74 |             1    |            0.28 |           0.4  |                0.23 |                  0.11 |                0.35 |          0.41 |              0.41 |              0.09 |             0.27 |              0.36 |                0.29 |                0.23 |                 0.53 |               0.49 |                    -0.15 |                 0.14 |               0.37 |                   0.09 |                  0.1  |    0.02 |        0.04 |                      0.1  |                    0.05 |                    -0.18 |                  -0.17 |                -0.25 |                     -0.05 |                   -0.09 |                 -0.12 |              -0.05 |                             0.03 |                               0.06 |                                          0.07 |
| spy_overnight                               |      -0.03 |      0.01 |      -0.04 |          -0.02 |             -0.03 |           0.64 |            0.48 |        0.36 |              0.5  |             0.28 |            1    |           0.04 |                0.23 |                  0.49 |               -0.04 |          0.5  |              0.28 |             -0.11 |            -0.17 |             -0.05 |               -0.19 |               -0.04 |                 0.27 |               0.36 |                    -0.35 |                 0.04 |               0.39 |                  -0    |                 -0.02 |    0.23 |        0.23 |                     -0.04 |                   -0.02 |                     0.01 |                   0.02 |                 0.03 |                     -0.07 |                   -0.02 |                 -0.01 |              -0.04 |                             0.1  |                               0.04 |                                          0.06 |
| spy_intraday                                |      -0.1  |     -0.52 |      -0.41 |          -0.42 |             -0.26 |           0.8  |            0.56 |        0.51 |              0.69 |             0.4  |            0.04 |           1    |                0.3  |                  0.57 |                0.02 |          0.55 |              0.34 |             -0.13 |            -0.11 |              0.03 |               -0.12 |               -0.04 |                 0.35 |               0.34 |                    -0.23 |                 0.1  |               0.4  |                  -0.01 |                  0.01 |    0.11 |        0.14 |                      0.01 |                   -0.11 |                    -0.5  |                  -0.46 |                -0.5  |                     -0.32 |                   -0.39 |                 -0.37 |              -0.35 |                            -0.03 |                              -0.1  |                                         -0.04 |
| spy_turn_of_month                           |      -0.05 |     -0.18 |      -0.16 |          -0.16 |             -0.09 |           0.37 |            0.31 |        0.29 |              0.36 |             0.23 |            0.23 |           0.3  |                1    |                  0.25 |                0.01 |          0.26 |              0.17 |             -0.06 |            -0.03 |              0.03 |               -0.02 |               -0.02 |                 0.21 |               0.22 |                    -0.1  |                 0.06 |               0.21 |                   0.01 |                 -0.03 |    0.07 |        0.05 |                     -0.03 |                   -0.04 |                    -0.18 |                  -0.14 |                -0.17 |                     -0.15 |                   -0.14 |                 -0.17 |              -0.09 |                             0.01 |                              -0.04 |                                         -0.02 |
| spy_after_vix_spike                         |      -0.02 |     -0.22 |      -0.21 |          -0.18 |             -0.14 |           0.74 |            0.43 |        0.19 |              0.39 |             0.11 |            0.49 |           0.57 |                0.25 |                  1    |               -0.11 |          0.48 |              0.2  |             -0.12 |            -0.4  |             -0.13 |               -0.39 |               -0.06 |                 0.16 |               0.26 |                    -0.43 |                 0.07 |               0.29 |                  -0    |                  0.03 |    0.26 |        0.3  |                      0.04 |                   -0.03 |                    -0.22 |                  -0.21 |                -0.21 |                     -0.17 |                   -0.21 |                 -0.19 |              -0.24 |                             0.1  |                               0.04 |                                          0.08 |
| multi_asset_trend                           |       0.28 |      0.05 |       0.17 |           0.18 |              0.23 |          -0.01 |            0.36 |        0.36 |              0.23 |             0.35 |           -0.04 |           0.02 |                0.01 |                 -0.11 |                1    |          0.2  |              0.47 |              0.28 |             0.47 |              0.88 |                0.65 |                0.61 |                 0.16 |               0.11 |                     0.01 |                 0.02 |              -0.05 |                   0.2  |                  0.29 |   -0.1  |       -0.06 |                      0.3  |                    0.26 |                     0.05 |                   0.05 |                -0.02 |                      0.19 |                    0.16 |                  0.11 |               0.07 |                             0.04 |                               0.22 |                                          0.22 |
| risk_parity                                 |      -0.06 |     -0.3  |      -0.25 |          -0.24 |             -0.14 |           0.73 |            0.56 |        0.5  |              0.66 |             0.41 |            0.5  |           0.55 |                0.26 |                  0.48 |                0.2  |          1    |              0.69 |             -0.1  |            -0.01 |              0.16 |               -0    |                0.05 |                 0.34 |               0.37 |                    -0.28 |                 0.06 |               0.42 |                   0.02 |                  0.01 |    0.17 |        0.19 |                     -0.01 |                   -0.05 |                    -0.3  |                  -0.24 |                -0.27 |                     -0.22 |                   -0.22 |                 -0.22 |              -0.23 |                             0.07 |                              -0    |                                          0.04 |
| cross_asset_mom                             |       0.13 |     -0.17 |      -0.04 |          -0.04 |              0.07 |           0.43 |            0.49 |        0.56 |              0.54 |             0.41 |            0.28 |           0.34 |                0.17 |                  0.2  |                0.47 |          0.69 |              1    |              0.23 |             0.28 |              0.43 |                0.29 |                0.41 |                 0.28 |               0.28 |                    -0.15 |                 0.05 |               0.25 |                   0.1  |                  0.19 |    0.02 |        0.04 |                      0.17 |                    0.12 |                    -0.17 |                  -0.14 |                -0.2  |                     -0.01 |                   -0.03 |                 -0.04 |              -0.1  |                             0.06 |                               0.13 |                                          0.16 |
| sector_momentum                             |       0.49 |      0.24 |       0.42 |           0.43 |              0.46 |          -0.17 |            0.04 |        0.11 |             -0.05 |             0.09 |           -0.11 |          -0.13 |               -0.06 |                 -0.12 |                0.28 |         -0.1  |              0.23 |              1    |             0.19 |              0.29 |                0.21 |                0.39 |                 0    |              -0.01 |                     0.01 |                 0.05 |              -0.09 |                   0.31 |                  0.44 |   -0.14 |       -0.08 |                      0.45 |                    0.45 |                     0.24 |                   0.19 |                 0.13 |                      0.43 |                    0.37 |                  0.32 |               0.15 |                             0.1  |                               0.42 |                                          0.37 |
| broad_trend_3m                              |       0.06 |      0.04 |       0.12 |           0.08 |              0.12 |          -0.19 |            0.04 |        0.29 |              0.12 |             0.27 |           -0.17 |          -0.11 |               -0.03 |                 -0.4  |                0.47 |         -0.01 |              0.28 |              0.19 |             1    |              0.53 |                0.88 |                0.24 |                 0.07 |              -0    |                     0.2  |                -0    |              -0.1  |                   0.03 |                  0.08 |   -0.22 |       -0.27 |                      0.06 |                    0.06 |                     0.05 |                   0.04 |                 0.03 |                      0.13 |                    0.12 |                  0.13 |               0.05 |                            -0.09 |                              -0    |                                         -0.01 |
| broad_trend_12m                             |       0.28 |      0.02 |       0.16 |           0.17 |              0.24 |          -0.01 |            0.38 |        0.4  |              0.25 |             0.36 |           -0.05 |           0.03 |                0.03 |                 -0.13 |                0.88 |          0.16 |              0.43 |              0.29 |             0.53 |              1    |                0.74 |                0.69 |                 0.14 |               0.09 |                     0.01 |                 0.03 |              -0.06 |                   0.18 |                  0.3  |   -0.11 |       -0.07 |                      0.31 |                    0.26 |                     0.02 |                   0.02 |                -0.07 |                      0.19 |                    0.15 |                  0.09 |               0.07 |                             0.05 |                               0.23 |                                          0.22 |
| broad_trend_blend                           |       0.13 |      0.04 |       0.14 |           0.11 |              0.17 |          -0.21 |            0.11 |        0.3  |              0.14 |             0.29 |           -0.19 |          -0.12 |               -0.02 |                 -0.39 |                0.65 |         -0    |              0.29 |              0.21 |             0.88 |              0.74 |                1    |                0.38 |                 0.08 |              -0.01 |                     0.21 |                 0.01 |              -0.11 |                   0.08 |                  0.14 |   -0.24 |       -0.28 |                      0.13 |                    0.12 |                     0.05 |                   0.04 |                 0    |                      0.15 |                    0.13 |                  0.12 |               0.07 |                            -0.07 |                               0.05 |                                          0.04 |
| broad_xs_momentum                           |       0.37 |      0.1  |       0.24 |           0.26 |              0.28 |          -0.06 |            0.32 |        0.26 |              0.14 |             0.23 |           -0.04 |          -0.04 |               -0.02 |                 -0.06 |                0.61 |          0.05 |              0.41 |              0.39 |             0.24 |              0.69 |                0.38 |                1    |                 0.09 |               0.09 |                    -0.11 |                 0.07 |               0    |                   0.22 |                  0.34 |   -0.02 |       -0.01 |                      0.37 |                    0.34 |                     0.1  |                   0.08 |                -0.01 |                      0.25 |                    0.21 |                  0.13 |               0.15 |                             0.12 |                               0.33 |                                          0.31 |
| short_vol_contango                          |       0.01 |     -0.18 |      -0.12 |          -0.12 |             -0.08 |           0.44 |            0.53 |        0.55 |              0.6  |             0.53 |            0.27 |           0.35 |                0.21 |                  0.16 |                0.16 |          0.34 |              0.28 |              0    |             0.07 |              0.14 |                0.08 |                0.09 |                 1    |               0.82 |                     0    |                 0.05 |               0.44 |                   0.05 |                  0.03 |    0.05 |        0.07 |                      0.05 |                    0.01 |                    -0.17 |                  -0.15 |                -0.23 |                     -0.09 |                   -0.11 |                 -0.14 |              -0.02 |                             0.04 |                               0.03 |                                          0.03 |
| short_vol_always                            |       0.01 |     -0.16 |      -0.11 |          -0.11 |             -0.08 |           0.48 |            0.54 |        0.51 |              0.57 |             0.49 |            0.36 |           0.34 |                0.22 |                  0.26 |                0.11 |          0.37 |              0.28 |             -0.01 |            -0    |              0.09 |               -0.01 |                0.09 |                 0.82 |               1    |                    -0.35 |                 0.03 |               0.46 |                   0.04 |                  0.02 |    0.09 |        0.11 |                      0.05 |                    0.01 |                    -0.15 |                  -0.14 |                -0.2  |                     -0.08 |                   -0.1  |                 -0.12 |              -0.02 |                             0.08 |                               0.05 |                                          0.06 |
| long_vol_backwardation                      |      -0.02 |      0.09 |       0.06 |           0.06 |              0.02 |          -0.39 |           -0.36 |       -0.16 |             -0.23 |            -0.15 |           -0.35 |          -0.23 |               -0.1  |                 -0.43 |                0.01 |         -0.28 |             -0.15 |              0.01 |             0.2  |              0.01 |                0.21 |               -0.11 |                 0    |              -0.35 |                     1    |                -0.06 |              -0.26 |                  -0.04 |                 -0.04 |   -0.19 |       -0.25 |                     -0.06 |                   -0.02 |                     0.08 |                   0.08 |                 0.1  |                      0.05 |                    0.06 |                  0.06 |               0.01 |                            -0.16 |                              -0.11 |                                         -0.12 |
| sector_seasonality                          |       0.1  |     -0.01 |       0.04 |           0.05 |              0.05 |           0.1  |            0.08 |        0.09 |              0.11 |             0.14 |            0.04 |           0.1  |                0.06 |                  0.07 |                0.02 |          0.06 |              0.05 |              0.05 |            -0    |              0.03 |                0.01 |                0.07 |                 0.05 |               0.03 |                    -0.06 |                 1    |               0.08 |                   0.1  |                  0.08 |   -0.01 |       -0.05 |                      0.11 |                    0.08 |                    -0    |                  -0.01 |                -0.03 |                      0.05 |                    0.03 |                  0.02 |               0.03 |                             0.01 |                               0.07 |                                          0.06 |
| spy_macro_timing                            |      -0.06 |     -0.22 |      -0.18 |          -0.19 |             -0.08 |           0.55 |            0.5  |        0.43 |              0.58 |             0.37 |            0.39 |           0.4  |                0.21 |                  0.29 |               -0.05 |          0.42 |              0.25 |             -0.09 |            -0.1  |             -0.06 |               -0.11 |                0    |                 0.44 |               0.46 |                    -0.26 |                 0.08 |               1    |                  -0    |                 -0.03 |    0.11 |        0.12 |                     -0.02 |                   -0.05 |                    -0.2  |                  -0.18 |                -0.24 |                     -0.16 |                   -0.16 |                 -0.2  |              -0.04 |                             0.11 |                               0.02 |                                          0.04 |
| momentum_macro_timed                        |       0.77 |      0.12 |       0.44 |           0.48 |              0.56 |          -0    |            0.09 |        0.08 |              0.03 |             0.09 |           -0    |          -0.01 |                0.01 |                 -0    |                0.2  |          0.02 |              0.1  |              0.31 |             0.03 |              0.18 |                0.08 |                0.22 |                 0.05 |               0.04 |                    -0.04 |                 0.1  |              -0    |                   1    |                  0.65 |   -0.04 |       -0.02 |                      0.7  |                    0.71 |                     0.13 |                   0.1  |                 0.01 |                      0.44 |                    0.39 |                  0.31 |               0.12 |                             0.08 |                               0.53 |                                          0.47 |
| momentum_vol_scaled                         |       0.9  |      0.16 |       0.54 |           0.58 |              0.68 |          -0.01 |            0.12 |        0.11 |              0.04 |             0.1  |           -0.02 |           0.01 |               -0.03 |                  0.03 |                0.29 |          0.01 |              0.19 |              0.44 |             0.08 |              0.3  |                0.14 |                0.34 |                 0.03 |               0.02 |                    -0.04 |                 0.08 |              -0.03 |                   0.65 |                  1    |   -0.08 |       -0.02 |                      0.87 |                    0.82 |                     0.18 |                   0.13 |                 0.04 |                      0.58 |                    0.48 |                  0.48 |               0.1  |                             0.13 |                               0.71 |                                          0.72 |
| pairs                                       |      -0.09 |     -0.17 |      -0.24 |          -0.2  |             -0.19 |           0.22 |            0.11 |        0.02 |              0.1  |             0.02 |            0.23 |           0.11 |                0.07 |                  0.26 |               -0.1  |          0.17 |              0.02 |             -0.14 |            -0.22 |             -0.11 |               -0.24 |               -0.02 |                 0.05 |               0.09 |                    -0.19 |                -0.01 |               0.11 |                  -0.04 |                 -0.08 |    1    |        0.28 |                     -0.06 |                   -0.09 |                    -0.19 |                  -0.17 |                -0.17 |                     -0.26 |                   -0.23 |                 -0.24 |              -0.1  |                             0.15 |                               0.01 |                                          0.04 |
| etf_pairs                                   |      -0.01 |     -0.08 |      -0.11 |          -0.08 |             -0.08 |           0.25 |            0.2  |        0.05 |              0.12 |             0.04 |            0.23 |           0.14 |                0.05 |                  0.3  |               -0.06 |          0.19 |              0.04 |             -0.08 |            -0.27 |             -0.07 |               -0.28 |               -0.01 |                 0.07 |               0.11 |                    -0.25 |                -0.05 |               0.12 |                  -0.02 |                 -0.02 |    0.28 |        1    |                      0.02 |                   -0.02 |                    -0.08 |                  -0.06 |                -0.09 |                     -0.1  |                   -0.1  |                 -0.14 |              -0.07 |                             0.18 |                               0.09 |                                          0.1  |
| mom_12_1_sector_neutral                     |       0.94 |      0.23 |       0.59 |           0.64 |              0.7  |          -0.02 |            0.15 |        0.12 |              0.05 |             0.1  |           -0.04 |           0.01 |               -0.03 |                  0.04 |                0.3  |         -0.01 |              0.17 |              0.45 |             0.06 |              0.31 |                0.13 |                0.37 |                 0.05 |               0.05 |                    -0.06 |                 0.11 |              -0.02 |                   0.7  |                  0.87 |   -0.06 |        0.02 |                      1    |                    0.86 |                     0.26 |                   0.18 |                 0.04 |                      0.67 |                    0.52 |                  0.41 |               0.15 |                             0.16 |                               0.73 |                                          0.67 |
| mom_12_1_beta_neutral                       |       0.92 |      0.3  |       0.62 |           0.69 |              0.72 |          -0.1  |            0.07 |        0.05 |             -0.03 |             0.05 |           -0.02 |          -0.11 |               -0.04 |                 -0.03 |                0.26 |         -0.05 |              0.12 |              0.45 |             0.06 |              0.26 |                0.12 |                0.34 |                 0.01 |               0.01 |                    -0.02 |                 0.08 |              -0.05 |                   0.71 |                  0.82 |   -0.09 |       -0.02 |                      0.86 |                    1    |                     0.32 |                   0.36 |                 0.14 |                      0.65 |                    0.66 |                  0.45 |               0.2  |                             0.14 |                               0.7  |                                          0.64 |
| low_vol_sector_neutral                      |       0.35 |      0.96 |       0.81 |           0.85 |              0.56 |          -0.38 |           -0.24 |       -0.24 |             -0.35 |            -0.18 |            0.01 |          -0.5  |               -0.18 |                 -0.22 |                0.05 |         -0.3  |             -0.17 |              0.24 |             0.05 |              0.02 |                0.05 |                0.1  |                -0.17 |              -0.15 |                     0.08 |                -0    |              -0.2  |                   0.13 |                  0.18 |   -0.19 |       -0.08 |                      0.26 |                    0.32 |                     1    |                   0.78 |                 0.87 |                      0.77 |                    0.72 |                  0.71 |               0.35 |                            -0    |                               0.27 |                                          0.17 |
| low_vol_beta_neutral                        |       0.27 |      0.81 |       0.66 |           0.7  |              0.46 |          -0.35 |           -0.21 |       -0.21 |             -0.3  |            -0.17 |            0.02 |          -0.46 |               -0.14 |                 -0.21 |                0.05 |         -0.24 |             -0.14 |              0.19 |             0.04 |              0.02 |                0.04 |                0.08 |                -0.15 |              -0.14 |                     0.08 |                -0.01 |              -0.18 |                   0.1  |                  0.13 |   -0.17 |       -0.06 |                      0.18 |                    0.36 |                     0.78 |                   1    |                 0.74 |                      0.6  |                    0.84 |                  0.58 |               0.29 |                             0.01 |                               0.22 |                                          0.14 |
| low_vol_vol_scaled                          |       0.15 |      0.92 |       0.69 |           0.72 |              0.39 |          -0.37 |           -0.32 |       -0.31 |             -0.39 |            -0.25 |            0.03 |          -0.5  |               -0.17 |                 -0.21 |               -0.02 |         -0.27 |             -0.2  |              0.13 |             0.03 |             -0.07 |                0    |               -0.01 |                -0.23 |              -0.2  |                     0.1  |                -0.03 |              -0.24 |                   0.01 |                  0.04 |   -0.17 |       -0.09 |                      0.04 |                    0.14 |                     0.87 |                   0.74 |                 1    |                      0.6  |                    0.61 |                  0.74 |               0.24 |                            -0.03 |                               0.11 |                                          0.05 |
| high_52w_sector_neutral                     |       0.71 |      0.74 |       0.95 |           0.93 |              0.77 |          -0.29 |           -0.1  |       -0.08 |             -0.21 |            -0.05 |           -0.07 |          -0.32 |               -0.15 |                 -0.17 |                0.19 |         -0.22 |             -0.01 |              0.43 |             0.13 |              0.19 |                0.15 |                0.25 |                -0.09 |              -0.08 |                     0.05 |                 0.05 |              -0.16 |                   0.44 |                  0.58 |   -0.26 |       -0.1  |                      0.67 |                    0.65 |                     0.77 |                   0.6  |                 0.6  |                      1    |                    0.83 |                  0.83 |               0.28 |                             0.02 |                               0.53 |                                          0.43 |
| high_52w_beta_neutral                       |       0.6  |      0.72 |       0.88 |           0.86 |              0.69 |          -0.32 |           -0.14 |       -0.12 |             -0.24 |            -0.09 |           -0.02 |          -0.39 |               -0.14 |                 -0.21 |                0.16 |         -0.22 |             -0.03 |              0.37 |             0.12 |              0.15 |                0.13 |                0.21 |                -0.11 |              -0.1  |                     0.06 |                 0.03 |              -0.16 |                   0.39 |                  0.48 |   -0.23 |       -0.1  |                      0.52 |                    0.66 |                     0.72 |                   0.84 |                 0.61 |                      0.83 |                    1    |                  0.78 |               0.28 |                             0.02 |                               0.45 |                                          0.37 |
| high_52w_vol_scaled                         |       0.49 |      0.72 |       0.89 |           0.82 |              0.6  |          -0.29 |           -0.21 |       -0.17 |             -0.27 |            -0.12 |           -0.01 |          -0.37 |               -0.17 |                 -0.19 |                0.11 |         -0.22 |             -0.04 |              0.32 |             0.13 |              0.09 |                0.12 |                0.13 |                -0.14 |              -0.12 |                     0.06 |                 0.02 |              -0.2  |                   0.31 |                  0.48 |   -0.24 |       -0.14 |                      0.41 |                    0.45 |                     0.71 |                   0.58 |                 0.74 |                      0.83 |                    0.78 |                  1    |               0.21 |                            -0.01 |                               0.36 |                                          0.33 |
| earnings_premium                            |       0.2  |      0.34 |       0.31 |           0.34 |              0.26 |          -0.29 |           -0.07 |       -0.07 |             -0.19 |            -0.05 |           -0.04 |          -0.35 |               -0.09 |                 -0.24 |                0.07 |         -0.23 |             -0.1  |              0.15 |             0.05 |              0.07 |                0.07 |                0.15 |                -0.02 |              -0.02 |                     0.01 |                 0.03 |              -0.04 |                   0.12 |                  0.1  |   -0.1  |       -0.07 |                      0.15 |                    0.2  |                     0.35 |                   0.29 |                 0.24 |                      0.28 |                    0.28 |                  0.21 |               1    |                             0.08 |                               0.2  |                                          0.14 |
| REVERSAL BOOK (current system)              |       0.14 |     -0    |       0.01 |           0.05 |              0.07 |           0.04 |            0.12 |        0.04 |              0.03 |             0.03 |            0.1  |          -0.03 |                0.01 |                  0.1  |                0.04 |          0.07 |              0.06 |              0.1  |            -0.09 |              0.05 |               -0.07 |                0.12 |                 0.04 |               0.08 |                    -0.16 |                 0.01 |               0.11 |                   0.08 |                  0.13 |    0.15 |        0.18 |                      0.16 |                    0.14 |                    -0    |                   0.01 |                -0.03 |                      0.02 |                    0.02 |                 -0.01 |               0.08 |                             1    |                               0.72 |                                          0.75 |
| risk_parity(mom_12_1 + reversal)            |       0.76 |      0.26 |       0.5  |           0.57 |              0.61 |          -0.05 |            0.12 |        0.06 |             -0.01 |             0.06 |            0.04 |          -0.1  |               -0.04 |                  0.04 |                0.22 |         -0    |              0.13 |              0.42 |            -0    |              0.23 |                0.05 |                0.33 |                 0.03 |               0.05 |                    -0.11 |                 0.07 |               0.02 |                   0.53 |                  0.71 |    0.01 |        0.09 |                      0.73 |                    0.7  |                     0.27 |                   0.22 |                 0.11 |                      0.53 |                    0.45 |                  0.36 |               0.2  |                             0.72 |                               1    |                                          0.97 |
| risk_parity(momentum_vol_scaled + reversal) |       0.69 |      0.16 |       0.41 |           0.46 |              0.53 |           0.01 |            0.14 |        0.08 |              0.03 |             0.07 |            0.06 |          -0.04 |               -0.02 |                  0.08 |                0.22 |          0.04 |              0.16 |              0.37 |            -0.01 |              0.22 |                0.04 |                0.31 |                 0.03 |               0.06 |                    -0.12 |                 0.06 |               0.04 |                   0.47 |                  0.72 |    0.04 |        0.1  |                      0.67 |                    0.64 |                     0.17 |                   0.14 |                 0.05 |                      0.43 |                    0.37 |                  0.33 |               0.14 |                             0.75 |                               0.97 |                                          1    |


## Events: news types, novelty and index changes

### After each kind of news (market-relative, from the first open after the article)

t-stats average same-day events first, since they move together.

| event                |   events |   car_1d_bp |   t_1d |   car_5d_bp |   t_5d |   car_21d_bp |   t_21d |
|:---------------------|---------:|------------:|-------:|------------:|-------:|-------------:|--------:|
| buyback              |     4157 |       33.33 |   6.62 |       35.05 |   4.18 |        37    |    2.64 |
| analyst upgrade      |    38232 |        4.51 |   3.18 |        8.43 |   2.71 |        10.75 |    1.69 |
| merger / acquisition |    24644 |       -0.37 |  -0.21 |       -9.89 |  -2.55 |       -22.31 |   -3.19 |
| CEO change           |      581 |      -38.18 |  -2.82 |      -35.58 |  -1.49 |       -10.81 |   -0.26 |
| earnings beat        |    31192 |       -3.99 |  -0.93 |      -10.03 |  -1.42 |        -5.77 |   -0.52 |
| dividend raise       |     1886 |       17.8  |   3.18 |       14.19 |   1.36 |       -17.75 |   -0.99 |
| guidance raised      |      741 |       -8.82 |  -0.64 |      -23.34 |  -1.08 |       -58.83 |   -1.73 |
| lawsuit / probe      |     4502 |       -3.18 |  -0.74 |       13.69 |   1.08 |        76.42 |    3.62 |
| price target cut     |    41547 |       -0.7  |  -0.33 |        3.81 |   0.91 |        -0.12 |   -0.02 |
| guidance cut         |      296 |      -23.72 |  -0.79 |       30.38 |   0.75 |       -10.09 |   -0.13 |
| FDA / trial          |    10512 |       -1.5  |  -0.47 |       -4.02 |  -0.59 |       -13.36 |   -1.01 |
| share offering       |     4141 |       -7.2  |  -1.5  |        5.82 |   0.53 |        -1.43 |   -0.08 |
| price target raised  |    60860 |        1.54 |   0.83 |        0.92 |   0.24 |        -9.78 |   -1.39 |
| earnings miss        |    14292 |        1.22 |   0.2  |       -1.71 |  -0.17 |        12.96 |    0.88 |
| analyst downgrade    |    37199 |        0.66 |   0.36 |       -0.2  |  -0.05 |         1.16 |    0.17 |

### Novel vs. stale news: does the move continue?

continuation = return in the direction of the stock's move into the open after the news (positive = it keeps going, negative = it reverses).

| news                  |   horizon |   continuation_bp |     t |   days |
|:----------------------|----------:|------------------:|------:|-------:|
| novel (overlap < 30%) |         1 |             -1.15 | -1.98 |   2970 |
| novel (overlap < 30%) |         5 |             -2.06 | -1.47 |   2970 |
| novel (overlap < 30%) |        21 |             -4.57 | -1.71 |   2970 |
| stale (overlap > 70%) |         1 |             -4.53 | -2.2  |   2268 |
| stale (overlap > 70%) |         5 |             -6.29 | -1.34 |   2268 |
| stale (overlap > 70%) |        21 |            -22.4  | -2.64 |   2268 |


## Survivorship bias, signal by signal

14736 US stocks from Alpaca since 2016, 1954 of them no longer trading. Point-in-time universe: top 1,000 by dollar volume at each month end. Same signals, same dates (mid-2017 on), close-to-close.

|                             |   point-in-time (incl. delisted) |   survivors (current method) |   bias (survivor - pit) |
|:----------------------------|---------------------------------:|-----------------------------:|------------------------:|
| amihud (5d)                 |                          -0.011  |                       0.0029 |                  0.0139 |
| amihud (21d)                |                          -0.0241 |                       0.0148 |                  0.0389 |
| low_vol (5d)                |                           0.008  |                      -0.009  |                 -0.017  |
| low_vol (21d)               |                           0.0197 |                      -0.0214 |                 -0.0411 |
| max_effect (5d)             |                           0.0062 |                      -0.0037 |                 -0.0099 |
| max_effect (21d)            |                           0.0171 |                      -0.0111 |                 -0.0283 |
| mom_12_1 (5d)               |                           0.0272 |                       0.0102 |                 -0.017  |
| mom_12_1 (21d)              |                           0.0345 |                       0.0051 |                 -0.0295 |
| rev_1d (5d)                 |                           0.0109 |                       0.0123 |                  0.0014 |
| rev_1d (21d)                |                           0.0036 |                       0.0098 |                  0.0062 |
| rev_21d (5d)                |                           0.0052 |                       0.0159 |                  0.0107 |
| rev_21d (21d)               |                           0.0032 |                       0.0207 |                  0.0175 |
| rev_5d (5d)                 |                           0.0147 |                       0.0163 |                  0.0016 |
| rev_5d (21d)                |                           0.0048 |                       0.0148 |                  0.01   |
| size_proxy (illiquid) (5d)  |                          -0.0081 |                       0.0003 |                  0.0084 |
| size_proxy (illiquid) (21d) |                          -0.015  |                       0.0095 |                  0.0245 |

A large positive bias means the signal looks better on today's survivors than it would have been in real time.


## Intraday strategies (5-minute data, 2016-2026)

Periods: 2016-2020 (1st) and 2021-2026 (2nd). Long top / short bottom fifth, rebuilt daily. gross_bp_day = average daily return before costs; breakeven = gross return per unit traded, to compare with the one-way cost (about 2.5-4 bp in liquid names, 3x at the open).

| strategy                                                       |   gross_bp_day_1st |   gross_bp_day_2nd |   breakeven_bp_1st |   breakeven_bp_2nd |   gross_sharpe_1st |   gross_sharpe_2nd |   net_sharpe_1st |   net_sharpe_2nd |   days_1st |   days_2nd |
|:---------------------------------------------------------------|-------------------:|-------------------:|-------------------:|-------------------:|-------------------:|-------------------:|-----------------:|-----------------:|-----------:|-----------:|
| market_intraday_momentum (equal-weight market, 15:30 -> close) |               0.35 |              -0.95 |               0.18 |              -0.47 |               0.17 |              -0.61 |            -0.78 |            -1.91 |       1255 |       1455 |
| opening_drive (first 30 min -> rest of day)                    |              -5.64 |              -3.22 |              -2.82 |              -1.61 |              -3.43 |              -1.89 |           -12.38 |            -9.47 |       1259 |       1455 |
| late_momentum (overnight + first 30 -> last 30)                |              -0.65 |              -0.46 |              -0.32 |              -0.23 |              -1.66 |              -0.98 |           -38.47 |           -27.46 |       1259 |       1455 |
| gap_reversal_open (gap -> open to close, short gappers)        |               3.22 |               5.3  |               1.61 |               2.65 |               1.22 |               1.84 |            -9.67 |            -6.95 |       1259 |       1455 |
| gap_reversal_10am (gap -> 10:00 to close)                      |              -0.15 |               0.98 |              -0.08 |               0.49 |              -0.07 |               0.45 |            -7.05 |            -5.3  |       1259 |       1455 |
| overnight_persistence (past month's overnight -> tonight)      |               3.77 |               1.04 |               1.89 |               0.52 |               3.27 |               0.59 |           -24.51 |           -13.89 |       5045 |       1454 |
| intraday_persistence (past month's open-to-close -> today's)   |              -1.18 |              -0.11 |              -0.59 |              -0.06 |              -0.38 |              -0.05 |            -9.92 |           -10.94 |       1244 |       1455 |
| last30_next_overnight (last 30 min -> tonight)                 |              -2.8  |              -2.01 |              -1.4  |              -1.01 |              -2.84 |              -1.74 |           -34.1  |           -25.32 |       1259 |       1454 |


## HMM variants, walk-forward on real data

pred_ll: average log-likelihood of tomorrow's symptoms given today's regime beliefs (higher is better; compare within a feature set). brier_skill: calibration of P(market falls > 3% in 5 days) vs. always predicting the base rate (> 0 = useful). vol_r2_vs_trailing: improvement in forecasting next month's volatility over using last month's alone (> 0 = useful). confident_share: days with one regime > 90%. rev_ic: 5-day reversal IC in the calmest and most stressed regime, weighted by the regime probabilities.

| features   |   states |   temper |   pred_ll_1st |   pred_ll_2nd |   brier_skill_1st |   brier_skill_2nd |   vol_r2_vs_trailing_1st |   vol_r2_vs_trailing_2nd |   confident_share_2nd |   rev_ic_calm_2nd |   rev_ic_stressed_2nd |
|:-----------|---------:|---------:|--------------:|--------------:|------------------:|------------------:|-------------------------:|-------------------------:|----------------------:|------------------:|----------------------:|
| rolling    |        1 |      1   |        1.4911 |        2.3587 |            0      |            0      |                  -0.174  |                  -0.0264 |                1      |            0.0129 |                0.0129 |
| rolling    |        2 |      1   |        2.1409 |        2.9671 |            0.0097 |            0.0097 |                  -0.1644 |                  -0.0278 |                0.9313 |            0.0073 |                0.019  |
| rolling    |        2 |      0.5 |        2.132  |        2.9503 |            0.011  |            0.0094 |                  -0.1624 |                  -0.0292 |                0.8957 |            0.0054 |                0.0214 |
| rolling    |        2 |      0.2 |        1.7607 |        2.8499 |           -0.0011 |            0.0042 |                  -0.2294 |                  -0.0211 |                0.8104 |            0.0017 |                0.0291 |
| rolling    |        2 |      0.1 |        1.68   |        2.8432 |           -0.0038 |            0.0017 |                  -0.2684 |                  -0.0204 |                0.8064 |            0.0073 |                0.0309 |
| rolling    |        3 |      1   |        2.5716 |        3.2706 |            0.0105 |            0.0099 |                  -0.1975 |                  -0.0317 |                0.9008 |            0.0065 |                0.0249 |
| rolling    |        3 |      0.5 |        2.5222 |        3.1957 |            0.013  |            0.0063 |                  -0.2896 |                  -0.0317 |                0.8531 |            0.0019 |                0.0285 |
| rolling    |        3 |      0.2 |        2.2668 |        3.1045 |            0.0091 |            0.0065 |                  -0.3335 |                  -0.029  |                0.7918 |            0.0014 |                0.031  |
| rolling    |        3 |      0.1 |        2.3363 |        2.9971 |            0.0148 |            0.0117 |                  -0.3215 |                  -0.0285 |                0.7901 |            0.0058 |                0.0352 |
| rolling    |        4 |      1   |        2.3819 |        3.5547 |            0.009  |            0.0123 |                  -0.2327 |                  -0.0478 |                0.9035 |            0.0046 |                0.035  |
| rolling    |        4 |      0.5 |        2.5411 |        3.5019 |            0.0077 |            0.0149 |                  -0.2795 |                  -0.0561 |                0.8595 |            0.0032 |                0.0393 |
| rolling    |        4 |      0.2 |        2.4135 |        3.3477 |            0.0067 |            0.0082 |                  -0.2899 |                  -0.0354 |                0.7566 |            0.0017 |                0.0536 |
| rolling    |        4 |      0.1 |        2.4092 |        3.2443 |            0.0115 |            0.0055 |                  -0.473  |                  -0.0505 |                0.6676 |            0.0017 |                0.0645 |
| daily      |        1 |      1   |        2.0167 |        2.7709 |            0      |            0      |                  -0.1699 |                  -0.0267 |                1      |            0.0131 |                0.0131 |
| daily      |        3 |      1   |        4.8053 |        5.4659 |           -0.0005 |            0.0013 |                  -0.176  |                  -0.0248 |                0.9221 |            0.0108 |                0.0186 |
| daily      |        3 |      0.5 |        4.0603 |        5.046  |            0.0005 |           -0.0006 |                  -0.234  |                  -0.0396 |                0.8758 |            0.0037 |                0.0146 |
| daily      |        3 |      0.2 |        2.6837 |        3.2971 |            0.0122 |            0.0073 |                  -0.3464 |                  -0.028  |                0.8839 |            0.04   |                0.0573 |


