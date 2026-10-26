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
