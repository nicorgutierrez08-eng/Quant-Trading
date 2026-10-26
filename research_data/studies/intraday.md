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

