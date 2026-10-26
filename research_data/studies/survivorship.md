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

