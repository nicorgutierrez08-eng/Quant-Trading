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

