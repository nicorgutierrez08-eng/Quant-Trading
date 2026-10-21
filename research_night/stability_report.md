# Stability analysis of the Quant-Trading research outputs

Source: `/home/user/ascoding11/keen/research_data/` (read-only). Scripts and intermediate CSVs: `/tmp/claude-0/-home-user-Quant-Trading/585e6a9d-2322-50ca-8eb6-13135510aa5f/scratchpad/stability/` (`p1_signals.py`, `p2_pairs_models.py`, `p3_strategies.py`, `p3b_checks.py`, `p4_conditional_decay.py`, `build_report.py`).

Conventions: 2006-14 = selection period, 2015-26 = check period; sub-split 2015-20 / 2021-26 where the file provides it. IC = daily cross-sectional rank IC; 0.02 is "useful". `ic2/ic1` = `ic_2015_26 / ic_2006_14` (1.0 = no drift, <1 = decay, >1 = strengthened). All Sharpes are net of measured costs where the source says "net".

Classification used throughout:
- **Invariant**: same sign both periods, |t| > 2 in both, 0.6 <= ic2/ic1 <= 1.6, years_positive >= 0.8, sub-split (where available) same sign and within 2x, not survivorship-prone.
- **Monotone / decaying**: same sign, |t_2006_14| > 2, ic2/ic1 < 0.5 (or a steady fall across the thirds of 2004-14 in `stability.csv` continuing into 2015-26).
- **Regime-dependent**: in-regime vs out-of-regime 5-day IC spread in `conditional.csv` of the same sign in both periods and >= 0.008.

---

## 1. Single signals

`best_correlations.csv` holds 410 signal rows (104 names x 4 horizons). Only **40 rows (29 distinct signals)** have |t| > 2 in *both* periods with the same sign. Among the 84 rows with |t_2006_14| > 2, 95% kept their sign, but only 48% also have |t_2015_26| > 2 and the median ic2/ic1 is **0.68**: the typical period-1 edge survived at about two-thirds of its size.

Cross-period rank correlation of signal IC (89 signals per horizon with both periods): h1 0.62, h5 0.79, h21 0.73, h63 0.63; same-sign share 76-80%.

### Top 25 single signals by weaker-period |IC|, |t| > 2 in both periods

| name                     | family           |   h |   ic_06_14 |   ic_15_26 |   t_06_14 |   t_15_26 |   ic_15_20 |   ic_21_26 |   yrs_pos | surv   |   ic2/ic1 |
|:-------------------------|:-----------------|----:|-----------:|-----------:|----------:|----------:|-----------:|-----------:|----------:|:-------|----------:|
| rev5_plus_resid_mom      | idea:combination |   5 |     0.0189 |     0.0159 |    4.2000 |    2.7000 |     0.0149 |     0.0170 |    0.8846 | False  |    0.8409 |
| bollinger_plus_resid_mom | idea:combination |   5 |     0.0153 |     0.0159 |    3.8000 |    2.9000 |     0.0162 |     0.0157 |    0.9231 | False  |    1.0402 |
| rev_5d                   | mean_reversion   |   5 |     0.0215 |     0.0136 |    4.2000 |    2.1000 |   nan      |   nan      |    0.8519 | False  |    0.6326 |
| bollinger_z              | mean_reversion   |   5 |     0.0165 |     0.0133 |    3.8000 |    2.2000 |   nan      |   nan      |    0.8889 | False  |    0.8052 |
| low_volume_rev           | mean_reversion   |   5 |     0.0227 |     0.0130 |    4.3000 |    2.0000 |   nan      |   nan      |    0.8519 | True   |    0.5719 |
| rev5_plus_resid_mom      | idea:combination |   1 |     0.0127 |     0.0122 |    6.5000 |    4.5000 |     0.0115 |     0.0129 |    0.8846 | False  |    0.9598 |
| rev_1d                   | mean_reversion   |   1 |     0.0159 |     0.0121 |    7.1000 |    4.1000 |   nan      |   nan      |    0.8889 | False  |    0.7664 |
| rev21_plus_resid_mom     | idea:combination |   5 |     0.0120 |     0.0165 |    2.7000 |    2.9000 |     0.0173 |     0.0157 |    0.9231 | False  |    1.3765 |
| rev_21d                  | mean_reversion   |   5 |     0.0115 |     0.0143 |    2.1000 |    2.2000 |   nan      |   nan      |    0.7407 | False  |    1.2481 |
| peer_gap                 | structure        |   5 |     0.0147 |     0.0113 |    4.3000 |    2.8000 |   nan      |   nan      |    0.8519 | False  |    0.7674 |
| network_mom              | idea:network     |   5 |     0.0110 |     0.0121 |    2.3000 |    2.2000 |     0.0157 |     0.0085 |    0.8148 | False  |    1.1037 |
| intraday_rev             | mean_reversion   |   1 |     0.0144 |     0.0106 |    6.7000 |    3.9000 |   nan      |   nan      |    0.8519 | False  |    0.7322 |
| rev_5d                   | mean_reversion   |   1 |     0.0141 |     0.0097 |    6.1000 |    3.2000 |   nan      |   nan      |    0.9630 | False  |    0.6915 |
| low_volume_rev           | mean_reversion   |   1 |     0.0136 |     0.0096 |    5.8000 |    3.1000 |   nan      |   nan      |    0.9630 | True   |    0.7026 |
| resid_rev_5d             | mean_reversion   |   5 |     0.0111 |     0.0083 |    4.5000 |    2.7000 |   nan      |   nan      |    0.8846 | False  |    0.7445 |
| bollinger_plus_resid_mom | idea:combination |   1 |     0.0082 |     0.0121 |    4.8000 |    4.8000 |     0.0125 |     0.0117 |    0.9231 | False  |    1.4692 |
| sharpe_mom               | idea:momentum    |   1 |     0.0081 |     0.0110 |    3.3000 |    3.0000 |     0.0101 |     0.0118 |    0.8519 | False  |    1.3458 |
| peer_gap                 | structure        |   1 |     0.0106 |     0.0078 |    6.9000 |    4.1000 |   nan      |   nan      |    0.9259 | False  |    0.7355 |
| bollinger_z              | mean_reversion   |   1 |     0.0075 |     0.0092 |    3.9000 |    3.3000 |   nan      |   nan      |    0.8148 | False  |    1.2193 |
| mom_12_1                 | momentum         |   1 |     0.0075 |     0.0109 |    2.7000 |    2.8000 |   nan      |   nan      |    0.7308 | False  |    1.4595 |
| resid_rev_1d             | mean_reversion   |   1 |     0.0148 |     0.0075 |   13.3000 |    6.1000 |   nan      |   nan      |    0.9231 | False  |    0.5034 |
| rev21_plus_resid_mom     | idea:combination |   1 |     0.0074 |     0.0106 |    3.9000 |    4.1000 |     0.0107 |     0.0104 |    0.9615 | False  |    1.4251 |
| rev_21d                  | mean_reversion   |   1 |     0.0065 |     0.0072 |    2.7000 |    2.4000 |   nan      |   nan      |    0.7778 | False  |    1.1109 |
| resid_rev_1d             | mean_reversion   |   5 |     0.0113 |     0.0064 |    5.2000 |    2.7000 |   nan      |   nan      |    0.9231 | False  |    0.5660 |
| rsi_14                   | mean_reversion   |   1 |     0.0087 |     0.0064 |    4.2000 |    2.1000 |   nan      |   nan      |    0.7407 | False  |    0.7301 |

Notes on the table:
- `ic_15_20` / `ic_21_26` exist only for the `idea:*` families (141 of 410 rows; 102 with both halves). For those 102 the rank correlation between the two halves is 0.60 and 74% keep their sign. For the core signals (rev_*, bollinger_z, peer_gap, ...) the sub-split is not in the file; `studies/stability.csv` gives instead the IC in each third of 2004-14 (see below).
- `rev5_plus_resid_mom`, `bollinger_plus_resid_mom`, `rev21_plus_resid_mom` are hand-built combinations of the two most stable primitives (short-term reversal + residual momentum); they are the only signals above IC 0.015 with t > 2.7 in both periods and essentially flat sub-split halves (0.0149/0.0170, 0.0162/0.0157, 0.0173/0.0157).

### Verdict by signal

| class | signals (horizon) | evidence |
|---|---|---|
| **Invariant** | `rev_1d` (h1: 0.0159 -> 0.0121, t 7.1/4.1, 89% yrs), `rev_5d` (h1 0.69x, 96% yrs; h5 0.63x), `bollinger_z` (h1 1.22x, h5 0.81x), `peer_gap` (h1 0.74x, 93% yrs; h5 0.77x), `intraday_rev` (h1 0.73x), `rev_21d` (h1 1.11x, h5 1.25x but only 74-78% yrs), `rev5_plus_resid_mom`, `bollinger_plus_resid_mom`, `rev21_plus_resid_mom` (all 0.84-1.47x, 88-96% yrs, flat sub-split), `sue` (h1 0.0039 -> 0.0040, t 3.3/3.1, 89% yrs; tiny but rock-steady), `resid_mom` (h1 0.0048 -> 0.0085, t 3.0/3.4) | same sign, |t|>2 both, ratio 0.6-1.5, high years_positive |
| **Invariant but modest / borderline** | `sharpe_mom`, `frog_in_pan`, `mom_consistency`, `stock_tsmom`, `ma50_200`, `mom_6_1`, `mom_12_1` (h1, all ic 0.004-0.011, ratio 1.2-1.6, 70-85% yrs) | momentum family *strengthened* (family median ratio 1.22) but IC stays below 0.011 at h1 |
| **Decaying (monotone)** | `resid_rev_1d` (h1: 0.0148 -> 0.0075, 0.50x; thirds of 2004-14: 0.0185/0.0123/0.0048 -> 0.0064), `resid_rev_5d` (h1 0.49x), `ou_sscore` (h5 0.45x, h21 0.23x, h63 0.18x; thirds 0.013/0.009/0.009 -> 0.005), `close_location` (0.41-0.46x; thirds 0.030/0.012/0.0045 -> 0.0066), `rsi_14` (h1 0.73x but thirds 0.038/0.008/0.009), `low_volume_rev` (h5 0.57x; survivorship-prone), `reversal_in_winners` (0.47-0.48x), `same_month` (h5 0.09x, h1 0.46x), `autocorr_signal` (0.36x), `accruals` (0.10-0.28x), `vol_price_corr` (0.18-0.31x), `size_proxy` / `amihud` (0.13-0.44x, survivorship-prone, t_2015_26 ~ 1), `neg_skew` h63 (0.07x), `max_effect` h1 (0.03x) | same sign, t1 > 2, ratio < 0.5 |
| **Sign flip** | `low_vol` h1 (+0.0086 -> -0.0022), `idio_vol` h1 (+0.0066 -> -0.0014), `cs_spread` h1 (-0.0075 -> +0.0006), `range_vol_ratio` h1 (+0.0040 -> -0.0002) | the only four rows with t1 > 2 that changed sign; three are survivorship-prone volatility/liquidity tilts |
| **Strengthened** | `resid_mom` h1 (1.78x), `frog_in_pan` (1.60x), `momentum_trio` (1.66x), `rd_intensity` h5/h21 (2.7x / 1.6x, but t1 < 1.3 so period-1 value was noise), `no_news_rev` h5 (0.0017 -> 0.0093; news data only exists from 2015, so "period 1" is a stub) | |

Family-level drift (same-sign rows, median ic2/ic1): mean_reversion 0.71 (n=44), volume 0.42, fundamental 0.46, microstructure 0.46, structure 0.74, momentum 1.22, volatility 1.20, idea:combination 1.12, idea:momentum 1.29. Reversal/liquidity edges shrank by roughly a third to a half; momentum-type edges grew but from a low base.

`studies/stability.csv` corroborates: the "same sign in each third of 2004-14 and |t| >= 2" rule kept 18 of 62 signals; 17 of those 18 (94%) kept their sign in 2015-26 versus 20 of 44 (45%) of the dropped ones. The rule works as a filter but does not stop magnitude decay: every kept mean-reversion signal lost 30-80% of its IC.

---

## 2. Pairs and models

### 2a. Pairs (`combos.csv` / `best_correlations.csv`, all at horizon 5)

Data caveat: `t_2015_26` is NaN for **all 3,782 pair rows** in `best_correlations.csv` (and `combos.csv` only has `t5_1st`). A period-2 t-stat is therefore *estimated* here as `ic5_2nd x median(t5_1st/ic5_1st) x sqrt(N2/N1)` (scale 221, N ratio 2970/2265). Treat `t_15_26_est` as approximate.

- Sum pairs: cross-period IC rank correlation **0.62**, same-sign share 84%, median ic2/ic1 (for |ic1| > 0.01) **0.60**. Product pairs: rank corr 0.14, same-sign 56% -> products are noise and none passes the t filter.
- 479 of 3,782 pairs pass |t1| > 2 and est. |t2| > 2 with the same sign; **all are sums**, and the top 100 are built from the same 8 primitives (rev_5d 19x, bollinger_z 18x, low_volume_rev 16x, rev_1d 15x, rev_21d 15x, peer_gap 15x, rsi_14 13x, intraday_rev 12x).
- `gain_2nd` (pair IC minus best component IC in 2015-26) is positive for only **35%** of the strong pairs: most pairs are not better than their best leg. The pairs with real positive gain in both periods are reversal + momentum/structure mixes: `rev_1d + resid_mom`, `rsi_14 + resid_mom`, `rev_5d + resid_mom`, `bollinger_z + resid_mom`, `resid_mom + peer_gap`, `mom_12_1 + high_52w` (+0.006).
- The `* + downside_beta` pairs at the top of the ranking have `gain_2nd` of -0.017 to -0.019: their "best single" benchmark is `downside_beta` itself, whose 2015-26 IC is an artefact (see section 6). Discount them.

#### Top 25 pairs by weaker-period IC (|t1| > 2, est. |t2| > 2, same sign)

| pair                           | families          |   ic5_06_14 |   ic5_15_26 |   t_06_14 |   t_15_26_est |   yrs_pos |   gain_vs_best_single_2nd |   ic2/ic1 |
|:-------------------------------|:------------------|------------:|------------:|----------:|--------------:|----------:|--------------------------:|----------:|
| rev_5d + downside_beta         | MR/volatility     |      0.0205 |      0.0181 |    3.7000 |        4.6000 |    0.8519 |                   -0.0172 |    0.8859 |
| low_volume_rev + downside_beta | MR/volatility     |      0.0216 |      0.0174 |    3.9000 |        4.4000 |    0.8519 |                   -0.0180 |    0.8025 |
| rev_1d + rev_21d               | MR/MR             |      0.0178 |      0.0168 |    3.4000 |        4.2000 |    0.8889 |                    0.0025 |    0.9422 |
| rev_5d + rev_21d               | MR/MR             |      0.0189 |      0.0161 |    3.6000 |        4.1000 |    0.8519 |                    0.0018 |    0.8525 |
| rev_5d + resid_mom             | MR/momentum       |      0.0199 |      0.0160 |    4.3000 |        4.0000 |    0.8148 |                    0.0024 |    0.8014 |
| bollinger_z + resid_mom        | MR/momentum       |      0.0160 |      0.0160 |    4.0000 |        4.0000 |    0.8889 |                    0.0027 |    0.9947 |
| rsi_14 + downside_beta         | MR/volatility     |      0.0159 |      0.0168 |    3.0000 |        4.2000 |    0.8148 |                   -0.0185 |    1.0539 |
| rev_21d + low_volume_rev       | MR/MR             |      0.0199 |      0.0159 |    3.7000 |        4.0000 |    0.8519 |                    0.0016 |    0.7990 |
| mom_12_1 + high_52w            | momentum/momentum |      0.0171 |      0.0158 |    2.7000 |        4.0000 |    0.8519 |                    0.0060 |    0.9234 |
| rev_5d + cluster_mom           | MR/momentum       |      0.0161 |      0.0158 |    2.7000 |        4.0000 |    0.7778 |                    0.0022 |    0.9793 |
| rev_1d + downside_beta         | MR/volatility     |      0.0155 |      0.0167 |    2.9000 |        4.2000 |    0.8519 |                   -0.0186 |    1.0741 |
| low_volume_rev + resid_mom     | MR/momentum       |      0.0209 |      0.0155 |    4.4000 |        3.9000 |    0.8519 |                    0.0026 |    0.7416 |
| rev_21d + intraday_rev         | MR/MR             |      0.0163 |      0.0154 |    3.2000 |        3.9000 |    0.8519 |                    0.0011 |    0.9452 |
| low_volume_rev + cluster_mom   | MR/momentum       |      0.0170 |      0.0154 |    2.8000 |        3.9000 |    0.8519 |                    0.0024 |    0.9066 |
| rev_1d + resid_mom             | MR/momentum       |      0.0163 |      0.0153 |    3.5000 |        3.9000 |    0.8519 |                    0.0030 |    0.9358 |
| bollinger_z + downside_beta    | MR/volatility     |      0.0152 |      0.0180 |    3.1000 |        4.6000 |    0.8519 |                   -0.0173 |    1.1829 |
| rev_21d + peer_gap             | MR/structure      |      0.0153 |      0.0151 |    3.3000 |        3.8000 |    0.8519 |                    0.0008 |    0.9887 |
| rev_21d + mom_12_1             | MR/momentum       |      0.0151 |      0.0153 |    2.7000 |        3.9000 |    0.7778 |                    0.0010 |    1.0135 |
| rev_5d + mom_accel             | MR/momentum       |      0.0198 |      0.0151 |    3.9000 |        3.8000 |    0.8889 |                    0.0014 |    0.7591 |
| rev_21d + bollinger_z          | MR/MR             |      0.0157 |      0.0150 |    3.1000 |        3.8000 |    0.8889 |                    0.0007 |    0.9579 |
| rsi_14 + resid_mom             | MR/momentum       |      0.0168 |      0.0150 |    4.1000 |        3.8000 |    0.9259 |                    0.0034 |    0.8928 |
| rev_1d + bollinger_z           | MR/MR             |      0.0198 |      0.0150 |    4.3000 |        3.8000 |    0.9259 |                    0.0018 |    0.7602 |
| rev_1d + mom_accel             | MR/momentum       |      0.0178 |      0.0150 |    3.6000 |        3.8000 |    0.8889 |                    0.0028 |    0.8421 |
| rev_1d + rev_5d                | MR/MR             |      0.0222 |      0.0148 |    4.4000 |        3.7000 |    0.9259 |                    0.0011 |    0.6653 |
| low_volume_rev + mom_accel     | MR/momentum       |      0.0208 |      0.0147 |    4.0000 |        3.7000 |    0.8889 |                    0.0017 |    0.7048 |

### 2b. Fitted models (`best_correlations.csv`, 648 models = 162 per horizon)

114 models have |t| > 2 in both periods with the same sign; 113 of them are 1-day models and one is 5-day (`ridge_1e6 on reversal`). **IC rank correlation across periods for models is -0.13 overall and ~0 within each horizon** (h1 -0.03, h5 -0.01, h21 -0.01, h63 +0.06), i.e. which model forecast best in 2006-14 says nothing about 2015-26. At h21/h63 the median model IC in 2006-14 is *negative* (-0.011 / -0.014) and positive in 2015-26 (+0.009 / +0.008); same-sign share only 14% / 33%. The 21- and 63-day models are unreliable (overlapping targets, yearly refit on 5 years -> few independent observations); only h1/h5 models should be read.

#### Top 25 models by weaker-period IC (|t| > 2 both periods)

| name                          | family   |   h |   ic_06_14 |   ic_15_26 |   t_06_14 |   t_15_26 |   yrs_pos |   netSR_06_14 |   netSR_15_26 |   be_bp_15_26 |   ic2/ic1 |
|:------------------------------|:---------|----:|-----------:|-----------:|----------:|----------:|----------:|--------------:|--------------:|--------------:|----------:|
| ridge_1e6 on reversal         | linear   |   1 |      0.012 |      0.012 |     5.100 |     4.500 |     0.905 |         0.321 |         0.224 |         7.132 |     1.038 |
| ridge_1e6 on price+fund       | linear   |   1 |      0.012 |      0.012 |     3.400 |     3.900 |     0.857 |        -0.158 |         0.139 |         7.879 |     1.049 |
| ridge_1e6 on all              | linear   |   1 |      0.012 |      0.013 |     3.400 |     4.000 |     0.857 |        -0.158 |         0.150 |         8.155 |     1.066 |
| ridge_1e6 on price            | linear   |   1 |      0.012 |      0.012 |     3.400 |     3.700 |     0.857 |        -0.157 |         0.109 |         7.016 |     1.011 |
| ridge_1e6 on reversal         | linear   |   5 |      0.015 |      0.012 |     2.800 |     2.000 |     0.905 |         0.327 |         0.090 |         5.251 |     0.764 |
| ridge_expanding on price      | extra    |   1 |      0.013 |      0.011 |     4.200 |     3.600 |     0.857 |        -0.110 |        -0.272 |         2.438 |     0.887 |
| ridge_expanding on reversal   | extra    |   1 |      0.013 |      0.011 |     4.100 |     3.500 |     0.952 |        -0.113 |         0.062 |         8.539 |     0.896 |
| random_forest on price+fund   | extra    |   1 |      0.014 |      0.011 |     4.700 |     3.500 |     0.905 |        -0.287 |         0.064 |         5.298 |     0.763 |
| extra_trees on all            | tree     |   1 |      0.015 |      0.011 |     4.800 |     3.400 |     0.905 |        -0.193 |        -0.102 |         3.118 |     0.690 |
| ridge_expanding on price+fund | extra    |   1 |      0.012 |      0.011 |     4.200 |     3.400 |     0.857 |        -0.087 |        -0.303 |         2.280 |     0.868 |
| extra_trees on price+fund     | tree     |   1 |      0.015 |      0.011 |     4.600 |     3.300 |     0.810 |        -0.162 |        -0.030 |         3.486 |     0.708 |
| pls_3 on price+fund           | extra    |   1 |      0.010 |      0.011 |     3.400 |     3.400 |     0.905 |        -0.324 |         0.019 |         4.253 |     1.020 |
| pls_3 on all                  | extra    |   1 |      0.010 |      0.011 |     3.400 |     3.500 |     0.905 |        -0.324 |         0.033 |         4.604 |     1.035 |
| random_forest on all          | extra    |   1 |      0.015 |      0.010 |     4.800 |     3.400 |     0.905 |        -0.275 |         0.103 |         6.340 |     0.706 |
| pca5_ridge on price+fund      | simple   |   1 |      0.010 |      0.010 |     3.100 |     3.500 |     0.857 |        -0.041 |         0.203 |         9.955 |     0.994 |
| pca5_ridge on all             | simple   |   1 |      0.010 |      0.010 |     3.100 |     3.400 |     0.857 |        -0.041 |         0.202 |         9.906 |     0.985 |
| extra_trees on price          | tree     |   1 |      0.015 |      0.010 |     4.400 |     3.200 |     0.857 |        -0.133 |        -0.060 |         3.311 |     0.689 |
| pca5_ridge on price           | simple   |   1 |      0.010 |      0.010 |     3.100 |     3.400 |     0.857 |        -0.041 |         0.185 |         9.414 |     0.970 |
| ridge_1e4 on reversal         | linear   |   1 |      0.010 |      0.010 |     3.900 |     3.400 |     0.810 |        -0.143 |         0.067 |         5.773 |     1.040 |
| pca5_ridge on reversal        | simple   |   1 |      0.010 |      0.011 |     4.400 |     3.800 |     0.905 |         0.031 |         0.185 |         8.985 |     1.099 |
| random_forest on price        | extra    |   1 |      0.015 |      0.010 |     4.800 |     3.300 |     0.952 |        -0.285 |         0.023 |         4.279 |     0.687 |
| pls_3 on price                | extra    |   1 |      0.010 |      0.010 |     3.300 |     3.100 |     0.857 |        -0.322 |         0.008 |         3.963 |     0.953 |
| tstat_ic on reversal          | simple   |   1 |      0.010 |      0.010 |     5.700 |     3.100 |     0.938 |         0.308 |         0.583 |        22.469 |     0.976 |
| elastic_net on reversal       | linear   |   1 |      0.010 |      0.011 |     3.900 |     3.500 |     0.810 |        -0.117 |         0.070 |         5.821 |     1.100 |
| lasso on reversal             | linear   |   1 |      0.010 |      0.011 |     3.900 |     3.500 |     0.810 |        -0.117 |         0.069 |         5.805 |     1.100 |

The IC-stable models are all heavily shrunk or simple: `ridge_1e6` (near equal-weight blend) on any signal set at h1 has ic 0.0118-0.0120 -> 0.0119-0.0126 (ratio 1.01-1.07), `pca5_ridge` ~1.0x, `tstat_ic`/`sign_ic` ~1.0x, `ridge_expanding` 0.87-0.90x. Trees (random_forest, extra_trees, rff_wide, stack_avg) have the highest period-1 IC (0.014-0.015) and the largest decay (0.64-0.72x): the extra fit in period 1 did not carry over.

### 2c. Traded strategies (`zoo_all_strategies.csv`, 3,888 rows)

- Net Sharpe > 0 in **both** periods: **45 of 3,888 (1.2%)**. Period 1: 3.1% positive; period 2: 24% positive (lower measured spreads after 2015).
- Overall rank correlation of net Sharpe between periods **0.62** (as in the zoo README), but IC rank corr is **-0.13** and turnover rank corr is **0.98**. The net-Sharpe persistence is almost entirely *cost structure* persisting, not alpha: by smoothing half-life the rank corr is 0.80 (hl 0), 0.33 (hl 5), **0.07 (hl 20)**; within (family x horizon x hl x universe) cells the mean rank corr is 0.19 (median 0.24, 168 cells).
- Selecting on period 1: top-10 by period-1 net Sharpe averaged 0.35 -> 0.14 in period 2 (8/10 positive); top-50 0.24 -> 0.04 (58% positive); top-200 0.06 -> -0.03.

Rank correlation and share positive-in-both by model family (zoo group):

| family | n | pos both | share | rank corr net SR | rank corr IC | med netSR 06-14 | med netSR 15-26 |
|---|---|---|---|---|---|---|---|
| simple (best_single, tstat_ic, sign_ic, pca*_ridge) | 480 | 27 | 5.6% | 0.63 | +0.12 | -0.35 | -0.12 |
| linear (ridge_*, lasso, elastic_net, logistic*, huber) | 864 | 9 | 1.0% | 0.54 | -0.02 | -0.44 | -0.16 |
| targets (resid/volscaled/decile targets) | 480 | 4 | 0.8% | 0.67 | -0.19 | -0.47 | -0.33 |
| tree (gbm_shallow/deep, extra_trees) | 288 | 2 | 0.7% | 0.59 | -0.46 | -0.44 | -0.08 |
| extra (random_forest, ridge_expanding, rff, pls, stack, gbm_l1, ...) | 1248 | 3 | 0.2% | 0.64 | -0.05 | -0.46 | -0.15 |
| nn (mlp_*, kernel_rff) | 384 | 0 | 0% | 0.68 | -0.63 | -0.44 | -0.20 |
| features (gbm/ridge_engineered, lasso_then_gbm) | 144 | 0 | 0% | 0.58 | -0.60 | -0.43 | -0.05 |

By model (top 12 by share of configurations net-positive in both periods):

| model                  | family   |   n |   n_cfg_pos_both |   share_pos_both |   rankcorr_netSR |   med_netSR_06_14 |   med_netSR_15_26 |   best_netSR_15_26 |   med_ic_06_14 |   med_ic_15_26 |
|:-----------------------|:---------|----:|-----------------:|-----------------:|-----------------:|------------------:|------------------:|-------------------:|---------------:|---------------:|
| best_single            | simple   |  96 |               12 |            0.125 |            0.833 |            -0.436 |            -0.221 |              0.198 |          0.007 |          0.007 |
| ridge_1e6              | linear   |  96 |                9 |            0.094 |            0.502 |            -0.360 |            -0.091 |              0.224 |          0.007 |          0.008 |
| tstat_ic               | simple   |  96 |                6 |            0.062 |            0.591 |            -0.188 |            -0.163 |              0.583 |          0.009 |          0.007 |
| sign_ic                | simple   |  96 |                5 |            0.052 |            0.480 |            -0.199 |            -0.123 |              0.522 |          0.008 |          0.009 |
| pca5_ridge             | simple   |  96 |                4 |            0.042 |            0.607 |            -0.405 |            -0.051 |              0.290 |          0.003 |          0.008 |
| ridge_expanding        | extra    |  96 |                3 |            0.031 |            0.713 |            -0.394 |            -0.187 |              0.138 |          0.008 |          0.009 |
| ridge_resid_target     | targets  |  96 |                2 |            0.021 |            0.728 |            -0.407 |            -0.447 |              0.337 |          0.003 |          0.002 |
| extra_trees            | tree     |  96 |                2 |            0.021 |            0.412 |            -0.398 |            -0.031 |              0.282 |          0.007 |          0.010 |
| gbm_volscaled_target   | targets  |  96 |                1 |            0.010 |            0.883 |            -0.424 |            -0.284 |              0.174 |          0.005 |          0.004 |
| ridge_volscaled_target | targets  |  96 |                1 |            0.010 |            0.683 |            -0.493 |            -0.340 |              0.093 |          0.003 |          0.004 |
| gbm_shallow            | tree     |  96 |                0 |            0.000 |            0.642 |            -0.471 |            -0.128 |              0.460 |          0.004 |          0.013 |
| gbm_resid_target       | targets  |  96 |                0 |            0.000 |            0.693 |            -0.460 |            -0.363 |              0.138 |          0.006 |          0.004 |

Of the 45 both-positive strategies: 36 use the `reversal` set (3.8% of reversal rows vs <=0.5% for other sets), 27 are h5 and 17 h1 (h21: 0, h63: 1), 30 use hl 20 and 15 hl 5 (hl 0: none), 31 are top300. No GBM, MLP, lasso or ridge with penalty < 1e6 configuration is positive in both periods.

Model x signal-set x horizon combos whose *median* net Sharpe over the 6 smoothing/universe configs is > 0 in both periods (only 2 of 648):

| name      | set      |   horizon |   n |   both_pos |   med_ns1 |   med_ns2 |   ic1 |   ic2 |    t1 |    t2 |    yp |
|:----------|:---------|----------:|----:|-----------:|----------:|----------:|------:|------:|------:|------:|------:|
| ridge_1e6 | reversal |         1 |   6 |          4 |     0.112 |     0.162 | 0.012 | 0.013 | 5.097 | 4.493 | 0.905 |
| ridge_1e6 | reversal |         5 |   6 |          4 |     0.159 |     0.045 | 0.015 | 0.012 | 2.777 | 2.011 | 0.905 |

Conclusion for models: the only thing that is invariant is "equal-weight the stable reversal signals, forecast 1-5 days, smooth 5-20 days, trade liquid names". Everything that learns more than that from 5 years of data has an IC that does not persist.

---

## 3. Strategy returns (`strategy_returns.csv`, 43 series, 2006-01-03 to 2026-10-20)

Sharpe computed from the strategy's first non-zero day (strategies.csv includes the flat days before inception, which lowers e.g. `short_vol_always` to 0.72 vs 1.21 here, `spy_macro_timing` 0.73 vs 0.89, `sector_seasonality` -0.75 vs -1.63; otherwise the two agree to 3 decimals). Max drawdown on compounded returns.

| strategy                                    |   SR_06_14 |   SR_15_20 |   SR_21_26 |   SR_full |   maxDD_full |   maxDD_06_14 |   maxDD_15_26 |   corr_SPY | start      | all3>0.3   |
|:--------------------------------------------|-----------:|-----------:|-----------:|----------:|-------------:|--------------:|--------------:|-----------:|:-----------|:-----------|
| pairs                                       |       0.85 |       0.71 |       0.76 |      0.78 |        -0.03 |         -0.02 |         -0.03 |       0.22 | 2006-01-04 | True       |
| spy_vol_managed                             |       0.70 |       0.79 |       0.89 |      0.78 |        -0.31 |         -0.31 |         -0.17 |       0.84 | 2006-01-03 | True       |
| risk_parity                                 |       0.88 |       0.80 |       0.62 |      0.78 |        -0.21 |         -0.21 |         -0.20 |       0.73 | 2006-01-03 | True       |
| spy_ma200                                   |       0.61 |       0.67 |       0.92 |      0.71 |        -0.24 |         -0.23 |         -0.24 |       0.61 | 2006-01-03 | True       |
| cross_asset_mom                             |       1.01 |       0.57 |       0.97 |      0.89 |        -0.21 |         -0.21 |         -0.19 |       0.43 | 2006-01-03 | True       |
| broad_trend_12m                             |       0.60 |       0.48 |       0.60 |      0.57 |        -0.11 |         -0.08 |         -0.11 |      -0.01 | 2006-01-03 | True       |
| short_vol_contango                          |       0.58 |       0.56 |       0.47 |      0.54 |        -0.66 |         -0.42 |         -0.66 |       0.44 | 2006-07-21 | True       |
| spy_buy_hold                                |       0.47 |       0.74 |       0.92 |      0.65 |        -0.55 |         -0.55 |         -0.34 |       1.00 | 2006-01-03 | True       |
| spy_tsmom_12m                               |       0.72 |       0.45 |       0.99 |      0.70 |        -0.27 |         -0.19 |         -0.27 |       0.72 | 2006-01-03 | True       |
| spy_turn_of_month                           |       0.38 |       0.51 |       0.44 |      0.43 |        -0.22 |         -0.22 |         -0.12 |       0.37 | 2006-01-03 | True       |
| spy_macro_timing                            |       0.89 |       0.36 |       0.96 |      0.71 |        -0.18 |         -0.16 |         -0.18 |       0.64 | 2008-12-22 | True       |
| spy_hmm_timing                              |       0.52 |       0.35 |       0.40 |      0.42 |        -0.21 |         -0.10 |         -0.21 |       0.48 | 2006-01-03 | True       |
| multi_asset_trend                           |       0.77 |       0.28 |       0.56 |      0.58 |        -0.13 |         -0.09 |         -0.13 |      -0.01 | 2006-01-03 | False      |
| risk_parity(momentum_vol_scaled + reversal) |       0.23 |       0.22 |       0.35 |      0.26 |        -0.19 |         -0.19 |         -0.13 |       0.01 | 2006-01-03 | False      |
| spy_after_vix_spike                         |       0.27 |       0.22 |       0.48 |      0.30 |        -0.39 |         -0.39 |         -0.28 |       0.74 | 2006-05-19 | False      |
| short_vol_always                            |       1.21 |       0.22 |       0.73 |      0.57 |        -0.95 |         -0.43 |         -0.95 |       0.65 | 2011-10-05 | False      |
| broad_trend_blend                           |       0.66 |       0.26 |       0.19 |      0.42 |        -0.08 |         -0.04 |         -0.08 |      -0.21 | 2006-01-03 | False      |
| spy_overnight                               |       0.18 |       0.38 |       0.36 |      0.28 |        -0.30 |         -0.28 |         -0.30 |       0.64 | 2006-01-03 | False      |
| broad_xs_momentum                           |       0.19 |       0.16 |       0.12 |      0.16 |        -0.29 |         -0.29 |         -0.21 |      -0.06 | 2006-01-03 | False      |
| REVERSAL BOOK (current system)              |       0.44 |       0.06 |       0.27 |      0.29 |        -0.23 |         -0.18 |         -0.23 |       0.04 | 2006-01-03 | False      |
| broad_trend_3m                              |       0.70 |       0.19 |       0.03 |      0.39 |        -0.12 |         -0.07 |         -0.12 |      -0.19 | 2006-01-03 | False      |
| momentum_vol_scaled                         |       0.02 |       0.21 |       0.21 |      0.13 |        -0.26 |         -0.26 |         -0.21 |      -0.01 | 2006-01-03 | False      |
| momentum_macro_timed                        |       0.14 |      -0.00 |       0.33 |      0.16 |        -0.41 |         -0.41 |         -0.34 |      -0.00 | 2007-10-11 | False      |
| risk_parity(mom_12_1 + reversal)            |      -0.01 |       0.10 |       0.36 |      0.11 |        -0.26 |         -0.26 |         -0.14 |      -0.05 | 2006-01-03 | False      |
| spy_intraday                                |      -0.15 |      -0.11 |       0.12 |     -0.07 |        -0.51 |         -0.51 |         -0.28 |       0.80 | 2006-01-03 | False      |
| low_vol_beta_neutral                        |       0.03 |       0.10 |      -0.17 |     -0.01 |        -0.35 |         -0.31 |         -0.35 |      -0.35 | 2006-01-03 | False      |
| high_52w_beta_neutral                       |      -0.18 |      -0.05 |      -0.17 |     -0.14 |        -0.49 |         -0.39 |         -0.28 |      -0.32 | 2006-01-03 | False      |
| mom_12_1_sector_neutral                     |      -0.08 |      -0.20 |       0.17 |     -0.05 |        -0.30 |         -0.28 |         -0.20 |      -0.02 | 2006-01-03 | False      |
| high_52w_vol_scaled                         |      -0.26 |      -0.12 |      -0.26 |     -0.22 |        -0.60 |         -0.45 |         -0.42 |      -0.29 | 2006-01-03 | False      |
| etf_pairs                                   |       0.59 |      -0.33 |       0.19 |      0.16 |        -0.07 |         -0.02 |         -0.07 |       0.25 | 2006-01-04 | False      |
| factor_momentum                             |      -0.33 |      -0.28 |       0.16 |     -0.19 |        -0.43 |         -0.33 |         -0.31 |      -0.22 | 2006-01-03 | False      |
| mom_12_1                                    |      -0.37 |      -0.03 |       0.13 |     -0.12 |        -0.47 |         -0.41 |         -0.26 |      -0.09 | 2006-01-03 | False      |
| mom_12_1_beta_neutral                       |      -0.40 |       0.15 |       0.22 |     -0.06 |        -0.41 |         -0.41 |         -0.15 |      -0.10 | 2006-01-03 | False      |
| multi_factor                                |      -0.54 |      -0.29 |      -0.49 |     -0.44 |        -0.64 |         -0.45 |         -0.43 |      -0.34 | 2006-01-03 | False      |
| low_vol_vol_scaled                          |      -0.32 |      -0.12 |      -0.56 |     -0.33 |        -0.69 |         -0.43 |         -0.59 |      -0.37 | 2006-01-03 | False      |
| high_52w                                    |      -0.59 |      -0.37 |      -0.46 |     -0.48 |        -0.72 |         -0.54 |         -0.48 |      -0.34 | 2006-01-03 | False      |
| high_52w_sector_neutral                     |      -0.59 |      -0.45 |      -0.29 |     -0.47 |        -0.57 |         -0.42 |         -0.33 |      -0.29 | 2006-01-03 | False      |
| earnings_premium                            |      -0.63 |      -0.64 |      -0.28 |     -0.54 |        -0.95 |         -0.82 |         -0.75 |      -0.29 | 2006-01-03 | False      |
| low_vol_sector_neutral                      |      -0.37 |      -0.53 |      -0.65 |     -0.49 |        -0.59 |         -0.34 |         -0.44 |      -0.38 | 2006-01-03 | False      |
| low_vol                                     |      -0.45 |      -0.40 |      -0.68 |     -0.50 |        -0.76 |         -0.48 |         -0.62 |      -0.40 | 2006-01-03 | False      |
| long_vol_backwardation                      |      -0.10 |       0.10 |      -0.78 |     -0.18 |        -0.90 |         -0.53 |         -0.88 |      -0.39 | 2006-07-19 | False      |
| sector_momentum                             |      -0.18 |       0.49 |      -0.88 |     -0.21 |        -0.66 |         -0.50 |         -0.61 |      -0.17 | 2006-01-03 | False      |
| sector_seasonality                          |      -1.63 |      -0.09 |      -0.96 |     -0.65 |        -0.69 |         -0.21 |         -0.67 |       0.14 | 2013-02-04 | False      |

**Sharpe > 0.3 in all three sub-periods (12):** pairs, spy_vol_managed, risk_parity, spy_ma200, cross_asset_mom, broad_trend_12m, short_vol_contango, spy_buy_hold, spy_tsmom_12m, spy_turn_of_month, spy_macro_timing, spy_hmm_timing. Eight of the twelve are long-equity-beta sleeves (corr to SPY 0.37-0.84; pairwise correlations 0.6-0.86 among the spy_* variants). The only market-neutral members are `pairs` (corr 0.23, vol 1.3%/yr, max DD -3.5%) and `broad_trend_12m` (corr -0.01).

**Monotone decay:** `broad_trend_3m` 0.70 -> 0.19 -> 0.03; `broad_trend_blend` 0.66 -> 0.26 -> 0.19; `etf_pairs` 0.59 -> -0.33 -> 0.19; `REVERSAL BOOK (current system)` 0.44 -> 0.06 -> 0.27; `multi_asset_trend` 0.77 -> 0.28 -> 0.56 (partial recovery). **Regime-dependent:** `sector_momentum` -0.18 / +0.50 / -0.88, `long_vol_backwardation` -0.10 / +0.11 / -0.78, `short_vol_always` 1.21 / 0.22 / 0.73 (max DD -95%). **Negative in every sub-period:** low_vol (and its sector/beta-neutral, vol-scaled variants), high_52w (all variants), multi_factor, earnings_premium, factor_momentum. See section 6: on this survivor universe the low-vol family IC has the *wrong* sign relative to a point-in-time universe, so these are not evidence against the factors.

### Inverse-vol blends (63-day trailing vol, lagged one day, weights renormalised daily; the two `risk_parity(...)` composites excluded, 41 strategies)

| blend                                               |   n |   SR_06_14 |   SR_15_20 |   SR_21_26 |   SR_15_26 |   SR_full |   maxDD |   vol |   corr_SPY |
|:----------------------------------------------------|----:|-----------:|-----------:|-----------:|-----------:|----------:|--------:|------:|-----------:|
| ALL strategies (n=41)                               |  41 |      0.334 |     -0.143 |      0.446 |      0.099 |     0.145 |  -0.096 | 0.024 |      0.283 |
| all-3-subperiods Sharpe>0.3 (n=12) [in-sample pick] |  12 |      0.749 |      0.863 |      0.956 |      0.910 |     0.843 |  -0.061 | 0.034 |      0.653 |
| all-3-subperiods Sharpe>0 (n=21) [in-sample pick]   |  21 |      0.695 |      0.747 |      0.904 |      0.826 |     0.769 |  -0.063 | 0.029 |      0.605 |
| Sharpe_2006_14>0.3 only (n=18) [honest pick]        |  18 |      0.739 |      0.843 |      0.983 |      0.914 |     0.840 |  -0.052 | 0.023 |      0.598 |
| ALL ex SPY-timing sleeves                           |  31 |      0.131 |     -0.248 |     -0.009 |     -0.153 |    -0.084 |  -0.135 | 0.024 |      0.007 |

The "honest" pick (Sharpe_2006_14 > 0.3 only, 18 strategies, no look at 2015-26) performs the same as the in-sample all-three pick (0.74 / 0.84 / 0.98 vs 0.75 / 0.86 / 0.96): the stable set would have been identified from period 1 alone. The all-strategies blend is flat (0.15 full-period Sharpe) because the stock-factor long/shorts are negative in every period, and it goes to -0.08 if the SPY-based sleeves are removed.

Robustness: the plain 63-day trailing vol *over*-weights strategies that are flat for long stretches (`short_vol_contango` is active 41% of days in 2006-14, `spy_turn_of_month` 19%, `long_vol_backwardation` 10%), because trailing vol over zeros is tiny. Recomputing vol over the last active (non-zero) days, and optionally capping weights at 25%:

| blend                              |   n |   SR_06_14 |   SR_15_20 |   SR_21_26 |   SR_full |   corr_SPY |   avg_max_weight |
|:-----------------------------------|----:|-----------:|-----------:|-----------:|----------:|-----------:|-----------------:|
| ALL, active-day vol                |  41 |      0.224 |      0.329 |      0.414 |     0.305 |      0.163 |            0.174 |
| ALL, active-day vol, cap 25%       |  41 |      0.224 |      0.332 |      0.414 |     0.306 |      0.163 |            0.174 |
| all-3>0.3, active-day vol          |  12 |      1.004 |      0.937 |      1.083 |     1.007 |      0.812 |            0.537 |
| all-3>0.3, active-day vol, cap 25% |  12 |      0.959 |      0.859 |      1.023 |     0.950 |      0.812 |            0.250 |
| all-3>0.3 ex spy_* sleeves (5)     |   5 |      1.257 |      1.076 |      1.071 |     1.152 |      0.560 |            0.679 |
| all-3>0.3 ex spy_* , cap 25%       |   5 |      1.126 |      0.855 |      0.917 |     0.991 |      0.606 |            0.254 |
| all-3>0.3 ex pairs                 |  11 |      0.920 |      0.823 |      0.997 |     0.915 |      0.794 |            0.277 |

Either way the stable-set blend is ~0.9-1.1 Sharpe in every sub-period, versus 0.2-0.4 for the full set. Caveats: (i) `pairs` takes 38-54% of the uncapped weight because of its 1.3% vol (skew 2.9, kurtosis 46: the low vol hides fat tails); (ii) corr to SPY of the stable blend is 0.65-0.81 and its beta 0.14-0.20 -- the beta-residual Sharpe is 1.06 / 0.57 / 0.58 by sub-period, so roughly half of the 2015-26 Sharpe is equity beta.

---

## 4. Regime dependence (`conditional.csv`: 8 signals x {stressed, dispersed, low_volume, no_news}, 5-day IC)

Sanity check passed: share_in x IC_in + (1 - share_in) x IC_out reproduces the unconditional 5-day IC in `edge_decay.csv` to 4 decimals for every row. `ic5_out_1st` is NaN for `no_news` (news data begins 2015), so that condition has one period only.

Sorted by the 2015-26 in-minus-out spread:

| signal         | condition   |   share_in |   in_06_14 |   out_06_14 |   spread_06_14 |   in_15_26 |   out_15_26 |   spread_15_26 |   be_bp_cond_15_26 |   be_bp_always_15_26 |
|:---------------|:------------|-----------:|-----------:|------------:|---------------:|-----------:|------------:|---------------:|-------------------:|---------------------:|
| composite      | dispersed   |     0.2797 |     0.0318 |      0.0190 |         0.0128 |     0.0247 |      0.0075 |         0.0173 |             2.4852 |               6.3923 |
| low_volume_rev | dispersed   |     0.2797 |     0.0314 |      0.0201 |         0.0113 |     0.0230 |      0.0067 |         0.0164 |             4.0820 |               7.5983 |
| rev_5d         | dispersed   |     0.2797 |     0.0315 |      0.0200 |         0.0115 |     0.0232 |      0.0069 |         0.0163 |             4.4203 |               8.0143 |
| rev_5d         | stressed    |     0.2784 |     0.0338 |      0.0176 |         0.0163 |     0.0247 |      0.0087 |         0.0160 |             9.2807 |               8.0143 |
| low_volume_rev | stressed    |     0.2784 |     0.0350 |      0.0172 |         0.0178 |     0.0244 |      0.0085 |         0.0159 |             9.0000 |               7.5983 |
| no_news_rev    | stressed    |     0.2784 |     0.0114 |     -0.0016 |         0.0130 |     0.0186 |      0.0041 |         0.0145 |            10.3685 |               7.2251 |
| composite      | stressed    |     0.2784 |     0.0278 |      0.0192 |         0.0086 |     0.0232 |      0.0105 |         0.0127 |             5.6365 |               6.3923 |
| peer_gap       | dispersed   |     0.2797 |     0.0214 |      0.0136 |         0.0078 |     0.0182 |      0.0061 |         0.0121 |             3.9060 |               7.1243 |
| no_news_rev    | dispersed   |     0.2797 |     0.0010 |     -0.0003 |         0.0013 |     0.0151 |      0.0038 |         0.0113 |             3.2843 |               7.2251 |
| no_news_rev    | no_news     |     0.8031 |    -0.0001 |    nan      |       nan      |     0.0126 |      0.0018 |         0.0108 |             5.0726 |               7.2251 |
| resid_rev_1d   | dispersed   |     0.2797 |     0.0193 |      0.0101 |         0.0092 |     0.0131 |      0.0031 |         0.0099 |             3.3715 |               3.1417 |
| peer_gap       | stressed    |     0.2784 |     0.0211 |      0.0128 |         0.0083 |     0.0157 |      0.0089 |         0.0068 |             7.7661 |               7.1243 |
| resid_rev_1d   | stressed    |     0.2784 |     0.0145 |      0.0110 |         0.0035 |     0.0102 |      0.0056 |         0.0046 |             4.4320 |               3.1417 |
| rev_5d         | low_volume  |     0.3237 |     0.0214 |      0.0221 |        -0.0007 |     0.0103 |      0.0141 |        -0.0038 |             2.9886 |               8.0143 |
| peer_gap       | low_volume  |     0.3237 |     0.0158 |      0.0146 |         0.0013 |     0.0080 |      0.0118 |        -0.0037 |             2.6860 |               7.1243 |
| low_volume_rev | low_volume  |     0.3237 |     0.0213 |      0.0226 |        -0.0013 |     0.0103 |      0.0139 |        -0.0035 |             3.0961 |               7.5983 |
| sue            | dispersed   |     0.2797 |     0.0073 |      0.0074 |        -0.0001 |     0.0039 |      0.0066 |        -0.0027 |            -2.3222 |               3.1771 |
| sue            | stressed    |     0.2784 |     0.0091 |      0.0069 |         0.0021 |     0.0038 |      0.0062 |        -0.0024 |            -5.5428 |               3.1771 |
| composite      | low_volume  |     0.3237 |     0.0243 |      0.0204 |         0.0039 |     0.0125 |      0.0146 |        -0.0021 |             1.8321 |               6.3923 |
| resid_rev_1d   | no_news     |     0.8031 |     0.0121 |    nan      |       nan      |     0.0065 |      0.0078 |        -0.0013 |             1.9758 |               3.1417 |
| sue            | no_news     |     0.8031 |     0.0074 |    nan      |       nan      |     0.0048 |      0.0061 |        -0.0013 |             0.9390 |               3.1771 |
| no_news_rev    | low_volume  |     0.3237 |    -0.0014 |      0.0012 |        -0.0025 |     0.0072 |      0.0083 |        -0.0011 |             2.9082 |               7.2251 |
| sue            | low_volume  |     0.3237 |     0.0076 |      0.0079 |        -0.0003 |     0.0064 |      0.0053 |         0.0011 |             0.6255 |               3.1771 |
| ear            | no_news     |     0.8031 |     0.0043 |    nan      |       nan      |     0.0028 |      0.0036 |        -0.0009 |             2.2477 |               1.8223 |
| resid_rev_1d   | low_volume  |     0.3237 |     0.0158 |      0.0102 |         0.0056 |     0.0064 |      0.0072 |        -0.0008 |             1.3480 |               3.1417 |
| ear            | dispersed   |     0.2797 |    -0.0070 |      0.0064 |        -0.0133 |     0.0024 |      0.0031 |        -0.0007 |            -0.7456 |               1.8223 |
| rev_5d         | no_news     |     0.8031 |     0.0225 |    nan      |       nan      |     0.0126 |      0.0131 |        -0.0006 |             4.1916 |               8.0143 |
| ear            | stressed    |     0.2784 |     0.0037 |      0.0044 |        -0.0007 |     0.0025 |      0.0030 |        -0.0005 |            -4.4590 |               1.8223 |
| composite      | no_news     |     0.8031 |     0.0218 |    nan      |       nan      |     0.0139 |      0.0140 |        -0.0002 |             2.8235 |               6.3923 |
| peer_gap       | no_news     |     0.8031 |     0.0153 |    nan      |       nan      |     0.0106 |      0.0105 |         0.0001 |             3.6436 |               7.1243 |
| low_volume_rev | no_news     |     0.8031 |     0.0225 |    nan      |       nan      |     0.0127 |      0.0126 |         0.0001 |             4.1605 |               7.5983 |
| ear            | low_volume  |     0.3237 |     0.0033 |      0.0051 |        -0.0017 |     0.0028 |      0.0027 |         0.0001 |             0.6767 |               1.8223 |

Findings:
- **Stressed (HMM high-vol state, 28% of days) and dispersed (high cross-sectional dispersion, 28%)** are the regimes that matter, and the dependence *increased*: mean spread for `dispersed` went from 0.005 (2006-14) to 0.010 (2015-26), 8/8 signals same sign both periods; `stressed` 0.0086 -> 0.0085, 7/8 same sign. For rev_5d / low_volume_rev / composite, 2015-26 IC is 0.023-0.025 inside stress or dispersion and only **0.007-0.009 outside** (vs 0.018-0.020 outside in 2006-14). The decay of short-term reversal documented in section 1 is almost entirely a decay in *calm* markets; in-regime IC fell only ~30% (0.034 -> 0.025).
- **Low volume** (32% of days): spread ~0 and sign flips between periods (3/8 same sign) -> not a regime signal.
- **No news** (80% of days): spread 0.0008 on average in 2015-26; only `no_news_rev` (by construction) shows a 0.011 gap.
- `sue` and `ear` (earnings signals) have no regime dependence (|spread| <= 0.003) in either period.
- Trading only in-regime does **not** translate into better economics except for `stressed`: break-even (hl 5, 2015-26) improves vs "always" for 5/8 signals in `stressed` (median +0.95 bp, e.g. rev_5d 9.3 vs 8.0 bp, no_news_rev 10.4 vs 7.2 bp), but *worsens* for `dispersed` (median -3.6 bp) and `low_volume` (-4.4 bp), because the conditional book trades fewer days with the same entry/exit cost. Regime conditioning is a risk-budgeting input (scale up in stress/dispersion), not an on/off switch.

---

## 5. IC decay with horizon (`edge_decay.csv`, 44 signals x horizons 1/5/21)

IC at horizon h is against the cumulative h-day return. To estimate a half-life, the cumulative information is taken as IC_h x sqrt(h) (independent daily returns), the average *incremental* information per day is computed for day 1, days 2-5 and days 6-21, and an exponential is fitted through those three points (representative lags 1, 3.5, 13.5). The half-life is reported only when the increments are positive and falling; `nan` means the signal's information grows with horizon (slow characteristic) or changes sign. `hmax` = horizon with the largest |IC|. Signals with |IC5| < 0.005 in both periods omitted.

| signal          |   ic1_1st |   ic5_1st |   ic21_1st |   t1_h1 |   t1_h21 |   HL_days_06_14 |   hmax_06_14 |   ic1_2nd |   ic5_2nd |   ic21_2nd |   t2_h1 |   t2_h21 |   HL_days_15_26 |   hmax_15_26 |
|:----------------|----------:|----------:|-----------:|--------:|---------:|----------------:|-------------:|----------:|----------:|-----------:|--------:|---------:|----------------:|-------------:|
| rev_5d          |    0.0130 |    0.0225 |     0.0162 |  5.6000 |   1.6000 |          4.0000 |            5 |    0.0085 |    0.0131 |     0.0144 |  2.7000 |   1.2000 |          7.1000 |           21 |
| low_volume_rev  |    0.0129 |    0.0225 |     0.0159 |  5.6000 |   1.6000 |          3.8000 |            5 |    0.0083 |    0.0129 |     0.0143 |  2.7000 |   1.2000 |          7.2000 |           21 |
| rev_1d          |    0.0140 |    0.0171 |     0.0113 |  6.3000 |   1.2000 |          3.2000 |            5 |    0.0117 |    0.0114 |     0.0094 |  3.9000 |   0.8000 |          4.1000 |            1 |
| bollinger_z     |    0.0071 |    0.0153 |     0.0217 |  3.6000 |   2.4000 |         15.0000 |           21 |    0.0076 |    0.0121 |     0.0146 |  2.7000 |   1.3000 |          8.4000 |           21 |
| peer_gap        |    0.0095 |    0.0153 |     0.0144 |  6.6000 |   2.3000 |          5.7000 |            5 |    0.0063 |    0.0107 |     0.0096 |  3.4000 |   1.4000 |          5.4000 |            5 |
| rsi_14          |    0.0067 |    0.0152 |     0.0217 |  3.2000 |   2.2000 |         16.0000 |           21 |    0.0048 |    0.0101 |     0.0140 |  1.6000 |   1.2000 |         13.8000 |           21 |
| intraday_rev    |    0.0118 |    0.0140 |     0.0095 |  5.6000 |   1.1000 |          3.3000 |            5 |    0.0106 |    0.0093 |     0.0080 |  3.9000 |   0.7000 |          4.2000 |            1 |
| close_location  |    0.0076 |    0.0136 |     0.0158 |  4.8000 |   2.3000 |          8.4000 |           21 |    0.0025 |    0.0064 |     0.0062 |  1.1000 |   0.7000 |          7.4000 |            5 |
| rev_21d         |    0.0058 |    0.0125 |     0.0189 |  2.5000 |   1.8000 |         18.2000 |           21 |    0.0065 |    0.0131 |     0.0166 |  2.1000 |   1.3000 |         10.7000 |           21 |
| resid_rev_1d    |    0.0153 |    0.0121 |     0.0105 | 13.9000 |   2.6000 |          4.3000 |            1 |    0.0070 |    0.0069 |     0.0057 |  5.8000 |   1.3000 |          4.1000 |            1 |
| same_month      |    0.0056 |    0.0121 |     0.0068 |  3.5000 |   0.9000 |          2.7000 |            5 |    0.0027 |    0.0021 |    -0.0092 |  1.3000 |  -0.9000 |        nan      |           21 |
| kalman_trend    |   -0.0018 |   -0.0118 |    -0.0221 | -0.9000 |  -2.0000 |        nan      |           21 |   -0.0008 |   -0.0061 |    -0.0122 | -0.3000 |  -1.0000 |        nan      |           21 |
| intraday_rev_21 |    0.0053 |    0.0117 |     0.0155 |  2.4000 |   1.6000 |         12.8000 |           21 |    0.0064 |    0.0095 |     0.0090 |  2.3000 |   0.8000 |          5.5000 |            5 |
| resid_rev_5d    |    0.0088 |    0.0111 |     0.0145 |  7.9000 |   3.1000 |          8.4000 |           21 |    0.0035 |    0.0080 |     0.0078 |  2.5000 |   1.5000 |          6.9000 |            5 |
| peer_lead       |   -0.0023 |   -0.0107 |    -0.0021 | -0.9000 |  -0.2000 |        nan      |            5 |   -0.0083 |   -0.0057 |    -0.0049 | -2.6000 |  -0.4000 |          4.2000 |            1 |
| mom_12_1        |    0.0076 |    0.0106 |     0.0069 |  2.8000 |   0.5000 |          3.2000 |            5 |    0.0118 |    0.0107 |     0.0005 |  3.1000 |   0.0000 |        nan      |            1 |
| vol_price_corr  |    0.0056 |    0.0104 |     0.0158 |  4.3000 |   2.8000 |         15.6000 |           21 |    0.0027 |    0.0030 |     0.0040 |  1.7000 |   0.6000 |          8.2000 |           21 |
| ou_sscore       |    0.0046 |    0.0104 |     0.0183 |  4.9000 |   3.9000 |         39.7000 |           21 |    0.0015 |    0.0035 |     0.0023 |  1.4000 |   0.5000 |          3.8000 |            5 |
| mom_accel       |   -0.0043 |   -0.0094 |    -0.0082 | -2.1000 |  -0.8000 |          5.7000 |            5 |   -0.0051 |   -0.0094 |    -0.0137 | -1.8000 |  -1.1000 |         13.7000 |           21 |
| trend_quality   |   -0.0012 |   -0.0090 |    -0.0183 | -0.5000 |  -1.5000 |        nan      |           21 |    0.0008 |   -0.0046 |    -0.0111 |  0.3000 |  -0.8000 |        nan      |           21 |
| size_proxy      |    0.0034 |    0.0088 |     0.0212 |  1.7000 |   2.8000 |        nan      |           21 |    0.0003 |    0.0005 |     0.0065 |  0.1000 |   0.6000 |        nan      |           21 |
| amihud          |    0.0008 |    0.0080 |     0.0232 |  0.3000 |   2.5000 |        nan      |           21 |    0.0005 |    0.0013 |     0.0087 |  0.2000 |   0.7000 |        nan      |           21 |
| high_52w        |    0.0022 |   -0.0072 |    -0.0170 |  0.7000 |  -1.0000 |        nan      |           21 |    0.0026 |   -0.0019 |    -0.0098 |  0.7000 |  -0.6000 |        nan      |           21 |
| resid_mom       |    0.0058 |    0.0072 |     0.0033 |  3.7000 |   0.4000 |        nan      |            5 |    0.0097 |    0.0118 |     0.0092 |  4.0000 |   0.8000 |          4.0000 |            5 |
| overnight_rev   |    0.0048 |    0.0072 |     0.0039 |  2.5000 |   0.5000 |          2.3000 |            5 |    0.0031 |    0.0057 |     0.0053 |  0.9000 |   0.4000 |          6.0000 |            5 |
| cluster_mom     |   -0.0016 |   -0.0053 |    -0.0047 | -0.6000 |  -0.4000 |          7.5000 |            5 |   -0.0062 |   -0.0117 |    -0.0181 | -1.9000 |  -1.3000 |         16.7000 |           21 |
| turn_of_month   |    0.0077 |    0.0049 |    -0.0015 |  1.7000 |  -0.1000 |        nan      |            1 |   -0.0049 |    0.0072 |    -0.0109 | -0.9000 |  -0.5000 |        nan      |           21 |
| overnight_mom   |   -0.0023 |   -0.0027 |    -0.0048 | -1.6000 |  -0.7000 |         15.1000 |           21 |   -0.0004 |   -0.0075 |    -0.0167 | -0.2000 |  -1.5000 |        nan      |           21 |
| downside_beta   |    0.0061 |    0.0020 |    -0.0084 |  0.5000 |  -0.1000 |        nan      |           21 |   -0.0144 |   -0.0355 |    -0.0886 | -1.3000 |  -1.9000 |        nan      |           21 |
| mom_6_1         |    0.0054 |    0.0019 |    -0.0092 |  2.2000 |  -0.7000 |        nan      |           21 |    0.0083 |    0.0057 |    -0.0055 |  2.3000 |  -0.4000 |        nan      |            1 |

Reading:
- **Fast reversal signals** have half-lives of 3-4 days in 2006-14 (`rev_1d` 3.2, `intraday_rev` 3.3, `rev_5d` 4.0, `low_volume_rev` 3.8, `resid_rev_1d` 4.3) and 4-7 days in 2015-26: the first-day IC fell most (`rev_5d` h1 0.0130 -> 0.0085, -35%) while the 21-day IC fell least (0.0162 -> 0.0144, -11%), so the *fastest* component of reversal is what got arbitraged away; the peak-|IC| horizon of `rev_5d`/`low_volume_rev` moved from h5 to h21.
- **Oscillator / medium reversal** (`bollinger_z` 15 -> 8 d, `rsi_14` 16 -> 14 d, `rev_21d` 18 -> 11 d, `resid_rev_5d` 8 -> 7 d, `close_location` 8 -> 7 d): 1-3 week half-lives, shortening.
- **`peer_gap`**: half-life 5.7 -> 5.4 d, peak at h5 in both periods: the most horizon-stable signal in the set.
- **`ou_sscore`**: 40 d -> 3.8 d, 21-day IC 0.018 -> 0.002: the slow component vanished entirely.
- **Momentum**: `mom_12_1` 1-day IC rose (0.0076 -> 0.0118) but its 21-day IC collapsed (0.0069 -> 0.0005), so no half-life is estimable in 2015-26; `resid_mom` now peaks at h5 (0.0118) with a 4-day half-life.
- **No decay (information grows with horizon)**: `size_proxy`, `amihud`, `kalman_trend`, `trend_quality`, `high_52w`, `cluster_mom`: slow characteristics. `size_proxy`/`amihud` are survivorship-prone and their 21-day t falls from 2.5-2.8 to 0.6-0.7 in 2015-26.
- `same_month` flips sign at h21 in 2015-26 (0.0068 -> -0.0092): the calendar effect is gone.

---

## 6. Things that look like data artefacts

1. **`downside_beta`**: h63 IC -0.137 (t -2.5, years_positive 0.20), h21 2015-26 IC -0.089 at t -1.9; `stability.csv` has NaN for its third 2004-14 sub-period. An |IC| of 0.09-0.14 with |t| < 2.5 implies a handful of dates or a near-empty cross-section; the signal's coverage is broken. It also contaminates the `gain_2nd` of every `* + downside_beta` pair and the top rows of `best_correlations.csv`.
2. **Pairs have no period-2 t-stat**: `t_2015_26` is NaN for all 3,782 pair rows; `same_sign_both_periods` and `weaker_period_ic` are filled anyway, so pairs rank alongside signals in the main table without the second-period significance check.
3. **Sub-split only for ideas**: `ic_2015_20` / `ic_2021_26` are populated for 141/410 signal rows (idea families) and for no pair or model. The core signals cannot be checked on 2021-26 from this file.
4. **21/63-day models**: median model IC *negative* in 2006-14, positive in 2015-26, same-sign share 14%/33%. Overlapping multi-day targets with yearly refits give too few independent observations; the zoo README horizon table (ic_1st -0.011 / -0.014) should be read as "unreliable", not as a regime change.
5. **`rd_intensity` h1**: ic2/ic1 = 42 because ic_2006_14 is 0.0001; several `idea:fundamental` signals have period-1 ICs that are effectively zero (t < 1), so their "strengthening" is a denominator effect.
6. **Factor strategies negative everywhere**: low_vol, high_52w, multi_factor, earnings_premium are negative in all three sub-periods and in 16-17 of 21 calendar years. `survivorship.md` shows low_vol's 2017+ IC is +0.020 point-in-time vs -0.021 on the survivor universe (bias -0.04), max_effect -0.028, mom_12_1 -0.03. These results reflect the survivor universe (today's top-1000 by volume excludes the low-vol names that died or shrank), not the factors. Conversely `amihud`/`size_proxy`/`rev_21d` are flattered by +0.01 to +0.04.
7. **strategies.csv Sharpe for late-starting series** includes zero returns before inception (short_vol_always from 2011-10, spy_macro_timing from 2008-12, sector_seasonality from 2013-02), understating |Sharpe| by 20-50%.
8. **Inverse-vol weighting on intermittent series**: `spy_turn_of_month` (81% zero days), `long_vol_backwardation` (90%), `spy_after_vix_spike` (77%), `short_vol_contango` (29%) get inflated weights from a plain 63-day trailing vol; the "active-day vol" blend above corrects this.
9. **`pairs` strategy**: 1.3% vol, max DD -3.5%, Sharpe 0.78 with skew 2.9 and kurtosis 46; Sharpe by year ranges -0.87 to +2.24. Not necessarily wrong, but its low vol makes it dominate any inverse-vol blend, and its 2026 Sharpe of 2.15 on a partial year is noise.
10. `news`-family signals and `no_news_rev` have a 2006-14 "period" with no news data; their period-1 ICs (~0.002) are stubs and their ic2/ic1 ratios (3-5x) are meaningless.

---

## 7. Summary (10 lines)

1. **Genuinely invariant**: 1-5 day stock reversal (`rev_1d`, `rev_5d`, `bollinger_z`, `intraday_rev`), the peer-relative gap (`peer_gap`), residual momentum (`resid_mom`), and their hand-built sums (`rev5/bollinger/rev21 + resid_mom`): same sign, t > 2 in both periods, IC ratio 0.65-1.5, 85-96% of years positive, and flat across 2015-20 vs 2021-26 where measurable.
2. But the invariant reversal edges are *smaller*: the mean-reversion family kept ~70% of its IC (0.013 -> 0.009 median), and the loss sits almost entirely in calm markets (out-of-regime IC 0.019 -> 0.008; in stressed/dispersed regimes 0.034 -> 0.025).
3. **Monotone decay / gone**: residual 1-day reversal (0.0185/0.0123/0.0048 across 2004-14 thirds -> 0.0064), `ou_sscore` slow component, `close_location`, `rsi_14` magnitude, accruals, `same_month`, `vol_price_corr`, and the liquidity tilts `amihud`/`size_proxy` (which were also survivorship-flattered). The fastest (day-1) component of reversal decayed most (-35%) and half-lives lengthened from 3-4 to 4-7 days.
4. **Sign flips** are confined to volatility/liquidity characteristics (`low_vol`, `idio_vol`, `cs_spread`, `range_vol_ratio`), i.e. exactly the survivorship-prone group.
5. **Momentum-type signals strengthened** (family median ratio 1.2-1.3; `resid_mom` 1.8x) but remain small (IC < 0.012 at h1) and `mom_12_1`'s 21-day IC vanished.
6. **Pairs** add little: sums of the same 8 reversal primitives, cross-period rank corr 0.62, only 35% beat their best leg in 2015-26; product pairs are noise (rank corr 0.14). The one useful pairing is reversal + residual momentum.
7. **Models**: IC rank correlation across periods is ~0; only equal-weight-like combinations (`ridge_1e6`, `tstat_ic`, `sign_ic`, `pca5_ridge`) of the reversal set at h1/h5 with 5-20 day smoothing in liquid names are net-positive in both periods (45 of 3,888 configs). The 0.62 net-Sharpe rank correlation is cost structure (turnover rank corr 0.98); within hl 20 it is 0.07.
8. **Strategies**: 12 of 43 have Sharpe > 0.3 in all three sub-periods, and 8 of those are SPY-beta variants; the market-neutral survivors are `pairs` and `broad_trend_12m`. The stable-set inverse-vol blend is 0.9-1.1 Sharpe in every sub-period (0.75/0.86/0.96 plain, ~1.0 with active-day vol) vs 0.15-0.3 for the all-strategy blend, and it would have been picked from 2006-14 alone; about half of its 2015-26 Sharpe is equity beta (residual Sharpe 0.57-0.58).
9. **Regime dependence is real and growing** for reversal (dispersed/stressed spreads 0.010-0.016 in 2015-26, same sign in 15/16 cases); low-volume and news-day conditioning carry no information; earnings signals (`sue`, `ear`) are regime-free but decayed by half.
10. **Trust with care**: pair t-stats for 2015-26 are missing, 21/63-day model ICs are unreliable, `downside_beta` is broken, and every factor-style long/short result (low_vol, 52w-high, quality) is dominated by survivor-universe bias and should be re-run point-in-time before being believed in either direction.
