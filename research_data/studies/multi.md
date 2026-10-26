## Multi-strategy book (ETF sleeves + stock book)

The ETF book exactly as it trades: GARCH fitted on 2004-2014, sleeves weighted by 1 / trailing volatility, scaled to 10% volatility, gross capped at 1.5x, 1 bp per unit traded. Some sleeve exclusions were made after seeing 2015-2026, so that period is not fully out of sample.

| book                                         |   sharpe_2006_14 |   return_2006_14 |   vol_2006_14 |   max_dd_2006_14 |   sharpe_2015_26 |   return_2015_26 |   vol_2015_26 |   max_dd_2015_26 |
|:---------------------------------------------|-----------------:|-----------------:|--------------:|-----------------:|-----------------:|-----------------:|--------------:|-----------------:|
| ETF sleeves: all 8 sleeves                   |            0.926 |            0.092 |         0.099 |           -0.124 |            0.93  |            0.089 |         0.095 |           -0.132 |
| ETF sleeves: small account (no 30-ETF trend) |            0.914 |            0.093 |         0.102 |           -0.151 |            0.902 |            0.092 |         0.101 |           -0.136 |
| stock book (reversal, as backtested)         |            0.436 |            0.034 |         0.079 |           -0.185 |            0.156 |            0.011 |         0.069 |           -0.231 |

ETF book turnover: 18.3x a year. Correlation with the stock book: 0.07.

### Capital split between the two books

|   etf_fraction |   sharpe_2006_14 |   return_2006_14 |   vol_2006_14 |   max_dd_2006_14 |   sharpe_2015_26 |   return_2015_26 |   vol_2015_26 |   max_dd_2015_26 |
|---------------:|-----------------:|-----------------:|--------------:|-----------------:|-----------------:|-----------------:|--------------:|-----------------:|
|            0.3 |            0.816 |            0.052 |         0.063 |           -0.117 |            0.58  |            0.034 |         0.059 |           -0.161 |
|            0.5 |            0.986 |            0.063 |         0.064 |           -0.084 |            0.804 |            0.05  |         0.062 |           -0.132 |
|            0.7 |            1.01  |            0.075 |         0.074 |           -0.076 |            0.907 |            0.065 |         0.072 |           -0.123 |

### Each sleeve

|                   |   sharpe_2006_14 |   return_2006_14 |   vol_2006_14 |   max_dd_2006_14 |   sharpe_2015_26 |   return_2015_26 |   vol_2015_26 |   max_dd_2015_26 |
|:------------------|-----------------:|-----------------:|--------------:|-----------------:|-----------------:|-----------------:|--------------:|-----------------:|
| spy_vol_managed   |            0.704 |            0.093 |         0.133 |           -0.306 |            0.84  |            0.113 |         0.134 |           -0.172 |
| cross_asset_mom   |            1.014 |            0.155 |         0.152 |           -0.205 |            0.783 |            0.093 |         0.118 |           -0.193 |
| spy_ma200         |            0.614 |            0.071 |         0.115 |           -0.235 |            0.79  |            0.093 |         0.118 |           -0.236 |
| risk_parity       |            0.88  |            0.079 |         0.09  |           -0.208 |            0.697 |            0.057 |         0.081 |           -0.205 |
| spy_tsmom_12m     |            0.716 |            0.097 |         0.136 |           -0.186 |            0.694 |            0.098 |         0.141 |           -0.267 |
| broad_trend_12m   |            0.598 |            0.029 |         0.048 |           -0.083 |            0.54  |            0.023 |         0.043 |           -0.108 |
| spy_turn_of_month |            0.379 |            0.029 |         0.077 |           -0.224 |            0.476 |            0.031 |         0.066 |           -0.118 |
| multi_asset_trend |            0.769 |            0.043 |         0.055 |           -0.086 |            0.423 |            0.022 |         0.052 |           -0.131 |

Average sleeve weights since 2015: spy_vol_managed 7%, cross_asset_mom 8%, spy_ma200 8%, risk_parity 12%, spy_tsmom_12m 7%, broad_trend_12m 23%, spy_turn_of_month 15%, multi_asset_trend 18%

