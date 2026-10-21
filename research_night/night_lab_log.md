# Night lab log (2026-10-21, 01:00-11:00 EDT)

(Section times are approximate and run about 1.5 h ahead of the real clock.)

Running notes from a second research pass over Arjun's system, on the same
1,000-stock daily universe (Yahoo, 2000-2026, rebuilt locally). New modules
under `qtrade/research/`: `lab_prep` (cache), `regime_lab` (HMM variants scored
on money), `jump_lab` (Poisson/negative-binomial jump GLMs), `book_lab`
(regime-aware allocation across strategies), `invariants_lab` (what is stable,
what decays, what depends on the regime). Conventions unchanged: 2004/2006-2014
chooses, 2015-2026 checks; measured spreads + 1 bp; walk-forward everything.

## 05:15 UTC - invariants lab (5-day horizon, 44 signals, regimes = trailing-vol terciles)

- **11 signals are invariant** (same sign in 2004-09, 2010-14, 2015-20, 2021-26;
  |t| > 3; no significant trend): every short-term reversal variant (rev_1d,
  rev_5d, resid_rev_5d, low_volume_rev, ou_sscore, bollinger_z, rsi_14,
  intraday_rev), peer_gap, close_location, vol_price_corr. Nothing else.
- **The reversal edge is shrinking but not dead.** rev_5d IC 0.022 (2004-09) ->
  0.019 -> 0.014 -> 0.012 (2021-26); slope about -0.005 per decade, t = -1.4
  (not significant); trend line hits zero around 2045. The research's "edge has
  faded" is really "costs ate a slowly shrinking gross edge": the IC is still
  there, just half of what it was.
- **Every reversal signal is 2-3x stronger in the stressed vol tercile**
  (rev_5d: 0.011 calm vs 0.032 stressed; ou_sscore 6x). This is the one robust
  regime effect in the data.
- **Momentum flips sign in stress**: resid_mom 0.013 calm vs -0.003 stressed,
  mom_12_1 0.017 vs -0.009 (momentum crashes). At 5 days momentum is otherwise
  noise; see the 21-day run.
- 27 of 44 signals are noise at 5 days (volatility, volume, seasonality, most
  momentum). The 15-factor-residual versions do not beat the raw ones.
- **Market structure is flat**: annual vol, dispersion, correlation share and
  market autocorrelation show no trend 2004-2026 (|t| < 1.6). Jumps per day
  drift up slightly (15 -> 18, t = 1.5). The only strong monovariant is the
  number of tradable names (540 -> 950, t = 17): the universe is today's
  survivors filling in, which is the survivorship bias Arjun already flagged.

## 05:11 UTC - book lab baseline (no HMM yet)

Reproduced the ETF book: inverse-vol weights Sharpe 1.01 (2006-14) / 0.91
(2015-26) (Arjun: 0.93 / 0.93; small differences from my re-implementation of
the vol targeting). A VIX-tercile tilt gives 0.75 / 1.07 and a vol-tercile
tilt 0.99 / 0.95: inconsistent across periods, so neither would have been
chosen on 2006-14. That is the bar an HMM has to clear.

## 05:15 UTC - jump lab (Poisson GLMs for next-month jump counts)

- **The original -2.2 out-of-sample deviance is a bug, not a finding.** My
  rebuild of the same design (raw features, one fit on 2004-14, no news) gives
  +0.06 for both up and down jumps. The difference: the original included
  `news_fast`, and news only starts in 2015, so the feature is identically zero
  over the whole training period; `_poisson_glm` standardises by
  `std + 1e-12`, so every 2015+ value became ~1e12 standard deviations and the
  log link drove the predicted up-jump rate to zero. The down-jump model was
  spared only because its news coefficient was ~0. Fix: drop features that are
  constant in training (or floor the sd). Not confirmable here without the news
  data, but it is the only feature that differs between the two models.
- **Jump propensity is very predictable across stocks**: rank correlation of
  predicted vs realised next-21-day jump counts 0.09-0.11 (t 20-28) in both
  periods. Ranking the stock features within each day and adding the trailing
  market jump rate as an exposure offset raises it from 0.087 to 0.110 and
  fixes calibration (predicted/realised 0.78 -> 1.01). Negative binomial =
  Poisson for the mean (as expected).
- **As alpha it is weak.** -predicted down-jump rate, 20-day smoothing: net
  Sharpe 0.13 / 0.42, break-even 20 / 47 bp, turnover 0.02. Note the jump
  definition (3x *trailing* vol) makes recently volatile stocks *less* likely
  to "jump", so this is partly a high-vol tilt, which pays only in this
  survivor universe (Arjun's low_vol signal loses -0.3 / -0.7). Treat as
  survivorship-flattered.
- **Jump risk is where reversal alpha lives.** Dropping the 10-20% most
  jump-prone stocks from the 5-day reversal book cuts its gross Sharpe from
  1.18 to 0.90 (2004-14). Weighting by 1/intensity helps in 2015-26 (0.14 vs
  0.05 net) but hurts in 2004-14 (0.06 vs 0.30): inconsistent, not adopted.

## 05:30 UTC - stability review of Arjun's existing outputs (full report: docs/stability_report.md)

A separate pass over `research_data/` (zoo, combos, strategies, conditional, decay):
- **Invariant across 2006-14 / 2015-26 / 2015-20 / 2021-26:** 1-5 day reversal
  (rev_1d, rev_5d, bollinger_z, intraday_rev), peer_gap, residual momentum, and
  the sums reversal + resid_mom (IC ratio 0.65-1.5, 85-96% of years positive).
- **Reversal's decay is a calm-market decay.** Out-of-regime IC 0.019 -> 0.008;
  in the HMM-stressed / high-dispersion regimes 0.034 -> 0.025 (-30%). The
  regime dependence *grew*. Conditioning only pays as a risk-budget dial on
  "stressed" (break-even +1 bp); switching the book off otherwise costs more
  than it saves.
- **Models:** IC rank correlation between periods is ~0 for every horizon. Only
  equal-weight-like combinations (ridge_1e6, tstat_ic, sign_ic, pca5_ridge) of
  the reversal set at 1-5 days with 5-20 day smoothing in liquid names are net
  positive in both periods (45 of 3,888 strategies). The 0.62 rank correlation
  of net Sharpe is turnover (rank corr 0.98), not alpha. Trees decayed most.
- **Strategies:** 12 of 43 have Sharpe > 0.3 in all three sub-periods; 8 are
  SPY-beta variants. Market-neutral survivors: pairs, broad_trend_12m. The
  stable-set inverse-vol blend is 0.9-1.1 in every sub-period and *would have
  been picked on 2006-14 alone*; about half of its 2015-26 Sharpe is equity
  beta (beta-residual Sharpe 0.57).
- **Artefacts to fix in the research outputs:** `downside_beta` is broken (h63
  IC -0.137, NaN coverage) and sits at the top of best_correlations.csv via
  pairs; pairs have no 2015-26 t-stat; 21/63-day model ICs are unreliable
  (overlapping targets, yearly refits); factor long/shorts (low_vol, 52w high,
  quality) are survivor-universe artefacts in both directions; strategies.csv
  Sharpe includes pre-inception zeros for late starters.

## 05:35 UTC - invariants lab at the 21-day horizon

- At a monthly horizon only 1 of 44 signals is unconditionally invariant
  (resid_rev_5d); 11 are **regime-dependent** and 32 noise. The reason: the
  monthly edge lives almost entirely in stressed markets. bollinger_z IC -0.002
  calm vs +0.040 stressed; rev_21d 0.001 vs 0.035; rsi_14 -0.005 vs 0.043;
  peer_gap 0.002 vs 0.024; amihud/size -0.002 vs 0.031 (survivorship-prone).
- **Momentum is the mirror image**: mom_12_1 +0.019 calm vs -0.042 stressed,
  high_52w +0.021 vs -0.063, resid_mom +0.018 vs -0.021, bab +0.029 vs -0.050.
  Unconditionally these are "noise" because the regimes cancel.
- So the stable structure of this market is a *sign pattern*, not a level:
  reversal pays when volatility is high, momentum/trend/low-beta pay when it is
  low, in every sub-period 2004-2026. The lever is a regime-conditional
  allocation between the two families, rebalanced slowly (monthly), rather
  than a better unconditional forecast. (Regimes here = trailing-vol terciles,
  expanding quantiles, lagged; HMM versions to follow from the regime lab.)

## 05:45 UTC - switch lab, vol-tercile regimes (monthly rebalance, net of costs)

| book (all 1,000) | net Sharpe 2004-14 | 2015-26 | break-even bp 2nd |
|---|---|---|---|
| monthly reversal (rev_21d + bollinger_z + rsi_14) | 0.34 | 0.09 | 11 |
| monthly momentum (mom_12_1 + resid_mom + high_52w) | -0.20 | -0.23 | -34 |
| 50/50 | 0.10 | -0.12 | 1 |
| **regime switch** (capital by regime-conditional IC) | 0.19 | **0.47** | 36 |

- Monthly ICs by regime, 2015-26: calm tercile reversal -0.001 / momentum
  +0.034; stressed tercile reversal **+0.042** / momentum **-0.061**. The pattern
  is the same in the top-300 names (switch 0.09 / 0.45).
- Honest caveats: (1) on 2004-14 alone plain reversal (0.34) beats the switch
  (0.19), so a Sharpe-maximiser would not have picked it; the switch is a
  structural rule, not a tuned parameter, but the 2015-26 number is still only
  one out-of-sample period. (2) The momentum book is survivorship-penalised
  (today's survivors include the 2008 crashers that rebounded in 2009), which
  drags the calm-regime leg and probably understates the switch.
- Next: let the switch go *short* momentum in stress (IC -0.06 is too big to
  floor at zero), and swap the vol terciles for the HMM probabilities.

## 06:00 UTC - regime lab, full sweep (72 HMM variants, walk-forward, scored on money)

Baselines (regime-free): vol-managed market exposure Sharpe 0.99 / 0.65; the
daily rev_5d book -0.63 / -0.56 net; 50/50 rev/mom -0.55 / -0.34.

- **Market timing: no HMM beats volatility management.** Median timing gain
  -0.29 Sharpe in 2004-14; rank correlation of the gain between periods -0.15;
  zero of 72 variants positive in both. Regime x vol-managed is worse still.
  Vol targeting already captures what the regime knows about risk.
- **Crash calibration and volatility forecasting**: Brier skill 0.00-0.01 for
  every variant; the HMM never beats last month's realised vol (vol_r2 < 0).
  Same as Arjun's finding; Student-t emissions, sticky transitions and 4 states
  change nothing (sticky = identical results: the chains are already sticky).
- **Reversal sizing by regime**: 24% of variants positive in both periods, rank
  correlation 0.04. The one consistent variant is the simplest: **2-state
  Gaussian on VIX + term spread + GARCH vol** (gain +0.30 / +0.30; stressed
  regime 42% of 2015-26 days, vol 28% vs 11%, lasts ~33 days; reversal IC
  0.021 in stress vs 0.007 calm). Even so the daily book stays negative
  (-0.29 / -0.23) because its costs are too high. The switch gain for that
  variant is +0.34 / +0.07.
- **Selection does not transfer**: rank correlation of the total score across
  periods is 0.05 over the 72 variants. With one variant in 72 consistent,
  that variant could be luck; it is kept because it is also the simplest and
  the economically obvious one (VIX level).
- **Design bug found and fixed**: symptom sets containing the signed market
  return (`garch`, `daily`, `poisson`) learn up-day / down-day states lasting
  1.5-8 days, not regimes. Direction-free versions (`*_abs`, `vix_only`) are
  being re-run.
- Conclusion so far: a regime model earns its keep only as a *risk-budget dial
  between reversal and momentum/trend*, not as a market timer or a volatility
  forecaster, and a two-state VIX/vol model does that as well as anything more
  elaborate.

## 06:05 UTC - signed switch (vol terciles)

Letting a book with a negative predicted IC be traded the other way (short the
momentum book in the stressed regime): net Sharpe 0.18 / **0.59** (all names),
0.11 / 0.58 (top 300), break-even 44 bp, turnover 0.04/day. The 2004-14 number
is unchanged, so the caveat stands: this would not have been picked over plain
monthly reversal on period 1 alone.

## 06:10 UTC - book lab with HMM regimes (capital tilt across strategies)

| ETF sleeves, rule | 2006-14 | 2015-26 |
|---|---|---|
| inverse vol (Arjun) | 1.01 | 0.91 |
| x regime Sharpe, 2-state VIX/vol HMM | 0.75 | 0.79 |
| x regime Sharpe, rolling 3-state (current config) | 0.98 | 0.98 |
| x regime Sharpe, Poisson-mixed 3-state | 1.02 | 0.75 |
| x vol tercile / VIX tercile | 0.99 / 0.75 | 0.95 / 1.07 |

No regime tilt beats plain inverse-vol in both periods on any of the three
books; the ordering flips between books. Why: in the stressed regime (42% of
2015-26 days) *every* strategy except pairs (1.09) has Sharpe ~0 or negative,
and in the calm regime everything pays (SPY 1.85, trend 1.4-1.7). So the
regime's message is "cut gross in stress", which inverse-vol + 10% vol
targeting already does more smoothly. Regime-based risk budgeting across
*long-biased* sleeves adds noise, not information.

## 06:15 UTC - switch lab with HMM regimes (monthly, signed, net of costs)

| regime model | all names 2004-14 / 2015-26 | top 300 |
|---|---|---|
| plain monthly reversal (no regime) | 0.34 / 0.09 | 0.19 / 0.12 |
| **2-state Gaussian HMM on VIX + term spread + GARCH vol** | **0.43 / 0.42** | 0.19 / 0.49 |
| rolling 3-state HMM (the system's current config) | -0.01 / 0.47 | -0.13 / 0.53 |
| Poisson-mixed 3-state (jump counts as a symptom) | 0.45 / -0.03 | 0.18 / 0.06 |
| trailing-vol terciles | 0.18 / 0.59 | 0.11 / 0.58 |

- The VIX/vol 2-state HMM is the only regime model that beats plain reversal
  in *both* periods, and it was also the top variant by 2004-14 score in the
  72-variant sweep, so picking it is legitimate. Its regimes: calm 58% of
  2015-26 days (reversal IC 0.010, momentum 0.021), stressed 42% (reversal
  0.025, momentum **-0.028**).
- Break-even 32 bp vs 11 bp for plain reversal; turnover 0.04/day.
- The current 3-state rolling HMM would have looked useless on 2004-14 and
  great afterwards; the Poisson-mixed one the reverse. Two states on an
  observable (VIX) are more stable than three on rolling symptoms.

## 06:25 UTC - direction-free HMM symptom sets (16 more variants)

- Removing the signed return does not help the daily-symptom sets: HMMs on
  daily |z|, dispersion, correlation and jumps still learn 1-3 day "big day /
  small day" states, not regimes. Daily non-overlapping symptoms are too noisy
  for an HMM to find persistence; the rolling or macro level is needed.
- **VIX + GARCH vol alone is the best regime model of the night.** 2 states:
  durations 117 / 89 days, calm 65% of 2015-26 days (vol 13%) vs stressed 35%
  (vol 29%); reversal sizing gain +0.27 / +0.26; 3 states: +0.33 / +0.37 and
  switch gain +0.04 / +0.19; crash Brier skill 0.02 (best of all 88 variants);
  reversal IC in the stressed state 0.025-0.035 vs 0.006-0.009 calm.
- Reading: the regime that matters is simply the level of expected volatility,
  and it is persistent. The HMM adds learned thresholds and persistence to the
  VIX; everything fancier (jump counts, dispersion, Student-t, 4 states) adds
  noise. Market timing still never beats vol management (gain -0.13 to -0.5).

## 06:30 UTC - the switch as a sleeve of the multi-strategy book

| book (inverse-vol weights, 10% vol target) | 2006-14 | 2015-26 |
|---|---|---|
| 8 ETF sleeves (Arjun) | 1.01 | 0.91 |
| 8 ETF sleeves + stock book | 1.00 | 0.91 |
| **8 ETF sleeves + regime switch** | 0.90 | **1.07** |
| sleeves + stock book + regime switch | 0.90 | 1.07 |

- The switch is the complement the ETF book lacks: in the stressed regime
  (42% of 2015-26 days) every ETF sleeve has Sharpe ~0 or negative
  (broad_trend_12m +1.37 calm / -0.23 stressed) while the switch has -0.14 calm
  / **+0.82 stressed**. Pairs is the only other strategy that pays in stress.
- The 2006-14 blend Sharpe falls (1.01 -> 0.90) because the switch earned 0.43
  then against the sleeves' 1.0 and inverse-vol gives it a large weight; a
  risk-budget cap would fix that. This is the one allocation change tonight
  that improves the check period without a regime tilt.

## 06:35 UTC - switch with the VIX-only HMMs

| regime model (signed switch, all names) | 2004-14 | 2015-26 |
|---|---|---|
| VIX + GARCH vol, 2 states | 0.07 | 0.52 |
| VIX + GARCH vol, 3 states | 0.13 | 0.48 |
| VIX + term spread + GARCH vol, 2 states | **0.43** | **0.42** |
| vol terciles | 0.18 | 0.59 |
| plain monthly reversal | 0.34 | 0.09 |

Every regime proxy gives 0.4-0.6 in 2015-26, but only the model with the term
spread also beats plain reversal in 2004-14 (the 2007-08 yield-curve inversion
is information the VIX level alone does not carry early enough). The VIX-only
2-state model has 90-120 day regimes - too slow to switch - even though it
separates the ICs most sharply (stressed: reversal 0.033, momentum -0.042).
Selection risk is real: three regime proxies tried, one consistent.

## 06:50 UTC - robustness of the switch, and a correction to every "1st period" number

**Correction.** `edge.summarize` (Arjun's Bench, which my switch tables reuse)
defines the 1st period as *all dates before 2015*, so it includes 2001-2005,
when short-term reversal was spectacularly profitable (dot-com bust). The
research_data README says the selection period is 2006-2014; the tables in
edge/combos/poisson/alt use 2001-2014. Recomputed on the saved daily series:

| signed switch, all names, monthly | 2001-14 (as reported) | **2006-14** | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|---|
| plain monthly reversal | 0.35 | **-0.04** | 0.16 | 0.01 | 0.09 |
| 50/50 reversal / momentum | 0.10 | -0.40 | -0.12 | -0.11 | -0.12 |
| HMM: VIX + term spread + GARCH, 2 states | 0.44 | **0.27** | **0.77** | -0.09 | 0.42 |
| HMM: rolling 3-state (current config) | -0.01 | -0.45 | 0.88 | -0.10 | 0.47 |
| HMM: Poisson-mixed 3-state | 0.47 | 0.35 | 0.08 | -0.16 | -0.03 |
| HMM: VIX only, 2 states | 0.07 | -0.34 | 0.79 | 0.14 | 0.52 |
| vol terciles | 0.19 | -0.20 | 0.82 | 0.26 | 0.59 |

- The VIX + term-spread HMM is still the only regime model positive in
  2006-14 and it beats plain reversal in both halves (+0.31 and +0.33), but
  the absolute level is 0.27 / 0.42, not 0.43 / 0.42.
- **The edge is concentrated in volatility spikes**: the switch's good years
  are 2008 (+14.7%), 2015, 2019-2021 (+8%, +20%, +7%); 2022-2026 is flat
  (Sharpe -0.09 for 2021-26, with 2024 at -5.6%). Every regime proxy shares
  this pattern. Reversal in stress + short momentum in stress is a crisis
  strategy; it does nothing in calm trending years, and the last five years
  had one short crisis (2022) that was a trend, not a reversal, market.
- **Bootstrap (21-day blocks, 2,000 draws), 2015-26:** Sharpe 90% interval
  [0.00, 0.78], P(Sharpe < 0) = 4.8%; gain over plain reversal median +0.31,
  P(no gain) = 6.2%. Borderline significant, one out-of-sample period.
- **Robust to design choices?** Mostly: 21- or 42-day rebalance, either book
  composition and both universes give 0.26-0.49 in 2015-26 for the HMM switch
  (10-day rebalance is too costly: 0.1-0.2). Correlation with the market
  -0.08, with plain reversal 0.63-0.86.
- Net verdict: a real, economically sensible, modest edge (0.3-0.4 Sharpe,
  market-neutral, pays in crises) that diversifies the ETF book - not a 0.6.

## 06:55 UTC - does the HMM separate signal regimes better than a vol tercile? No.

21-day signal ICs by regime, 2004-26: mean |stressed - calm| spread is 0.028
with trailing-vol terciles vs 0.021 with the VIX/vol 2-state HMM. The sign
pattern is identical (momentum / 52w-high / low-beta / low-vol / trend
positive in calm and strongly negative in stress; reversal, RSI, Bollinger,
illiquidity positive only in stress). The HMM's value is persistence (fewer
switches, lower cost), not sharper classification.

Push of commit 603cd13 (research_night/) to origin was blocked by the session's
permission filter; the commit is local on claude/practical-ride-wggb8u.

## 07:05 UTC - multi-strategy book, corrected (one switch series, with and without pairs)

| inverse-vol, 10% vol target | 2006-14 | 2015-26 |
|---|---|---|
| 8 ETF sleeves | 1.01 | 0.91 |
| + stock book | 1.00 | 0.91 |
| + regime switch (HMM) | 0.99 | 0.99 |
| **+ regime switch + pairs** | **1.07** | **1.10** |
| + switch + pairs, 25% weight cap | 1.06 | 1.05 |

(The earlier 0.90 / 1.07 line double-counted the switch by including both the
HMM and the tercile versions.) The switch and pairs are the two sleeves that
earn in stressed markets; together they lift the book in both periods.
An ensemble regime probability (HMM + VIX HMM + vol tercile averaged) does
not beat the VIX + term HMM: switch -0.14 / 0.47.

## 07:40 UTC - pairs lab (72 configurations of Arjun's pairs strategy)

- **Arjun's parameters are already the robust ones.** 5 pairs per cluster,
  enter |z| > 2, exit |z| < 0.5, 21-day max hold, 60-day window: 0.85 / 0.77
  (2006-14 / 2015-26). The only configuration better in both periods is the
  same with a 63-day max hold (1.01 / 0.81) - within noise.
- **The configuration a Sharpe-maximiser would have picked on 2006-14 fails**:
  25 pairs per cluster, enter at 1.5, hold 63 days gives 1.02 -> 0.35. More
  pairs per cluster (10 or 25) is worse everywhere (median 0.3-0.4 vs 0.6 in
  2015-26): the 6th-25th most correlated pairs in a cluster are noise, and the
  same stocks appear in many pairs, so the book gets concentrated (vol 10% vs
  1%). Exit at 0 (wait for the full reversion) is worse than exit at 0.5.
- Rank correlation of Sharpe across the 72 configurations between periods is
  0.59, but the top pick still collapsed. 13 of 72 configurations are above
  0.5 in both periods, all with 5 pairs per cluster.
- Caveat for the book: the unlevered pairs book has ~1% volatility (most
  pairs are flat most days) and kurtosis ~46; the 0.8 Sharpe becomes 8% a
  year only at ~10x leverage, which is where the fat tails and borrow matter.

## 07:50 UTC - a wider switch composite? No.

Adding peer_gap and resid_rev_5d to the reversal book and bab to the momentum
book: signed HMM switch 2015-26 rises to 0.56 but 2006-14 falls to -0.27 (from
0.27). Inconsistent, so the three-signal composites stay. (Also a reminder that
2015-26 is easy to improve by choices that would not have been made in 2014.)

## 08:00 UTC - is dispersion a better regime variable than market volatility? No.

Signed switch, all names: dispersion terciles -0.68 / 0.34 (2006-14 / 2015-26);
high-vol-and-high-dispersion -0.41 / 0.25; market-vol terciles -0.20 / 0.59;
the VIX + term HMM 0.27 / 0.42. The regime that flips reversal and momentum is
the level of market volatility, not how spread out stock returns are (the
conditional study's "dispersed" regime helps reversal's IC but costs more in
turnover than it adds).

## 08:40 UTC - the macro HMM inside Arjun's live pipeline (fast models: ridge, regime_ridge, ic_weighted)

| | 3-state rolling HMM (current) | 2-state VIX + term HMM |
|---|---|---|
| regime_ridge mean IC | 0.009 | **0.012** |
| regime_ridge Sharpe (net, 2004-26) | -0.24 | -0.20 |
| ensemble Sharpe 2004-14 / 2015-20 / 2021-26 | 0.34 / -0.60 / -0.71 | 0.49 / -0.66 / -0.68 |
| frictionless ensemble Sharpe | 0.86 | 0.93 |

The better regime model lifts the regime-conditional forecast's IC by a
third and the frictionless Sharpe slightly, but the daily stock book stays
negative after costs in 2015-2026 under either HMM (turnover 16x a year at
measured spreads). Consistent with everything else tonight: the problem with
the stock book is turnover, not the regime model. Full six-model comparison
running.

## 09:05 UTC - where the switch's money comes from (one leg at a time, VIX + term HMM, monthly)

| leg (all names, net, unit gross) | 2006-14 | 2015-20 | 2021-26 | 2015-26 | return/yr 2015-26 |
|---|---|---|---|---|---|
| stress-only **short momentum** (buy losers, sell winners) | **0.81** | **0.75** | 0.03 | 0.46 | 3.0% |
| stress-only reversal | 0.49 | 0.48 | -0.21 | 0.22 | 1.3% |
| calm-only momentum | 0.37 | 0.74 | -0.14 | 0.30 | 1.4% |
| calm-only reversal | -0.64 | -0.62 | 0.17 | -0.20 | -0.8% |
| the signed switch (all four, IC-weighted) | 0.27 | 0.77 | -0.09 | 0.42 | 2.5% |

- The strongest and most stable leg is **shorting momentum in stressed
  markets** - the Daniel-Moskowitz momentum crash / loser rebound - positive in
  2006-14 and 2015-20, flat in 2021-26. Reversal in calm markets loses money
  after costs in every period: the "invariant" 5-day reversal is a stressed-
  market effect once costs are charged.
- With vol terciles instead of the HMM, every stressed leg is weaker in
  2006-14 (short momentum 0.48, reversal 0.08) but holds up in 2021-26
  (0.40, 0.12): the HMM's regimes are better early, the terciles' later.
- Returns are small in absolute terms at unit gross (2.5-3% a year); at a 10%
  volatility target this is a 4-6% a year market-neutral book.

## 09:20 UTC - the "long losers in stress" leg is mostly market beta

Splitting stress-only short momentum into its two sides (each unit gross):

| all names, net | 2006-14 | 2015-20 | 2021-26 | 2015-26 | return/yr 15-26 |
|---|---|---|---|---|---|
| stress-only **long losers** | 0.62 | 1.17 | 0.76 | 0.98 | 20.0% |
| stress-only short winners | -0.35 | -1.18 | -0.97 | -1.06 | -14.0% |
| stress-only long *the whole market* (equal weight) | 0.50 | 1.22 | 0.89 | 1.06 | 15.7% |
| long losers minus the market (the actual alpha) | **0.80** | **0.83** | 0.15 | 0.55 | 4.3% |

- A long-only book is long the market, and in 2015-26 the market's Sharpe in
  HMM-stressed months was 1.66 vs -0.1 in calm months: the regime is flagged
  after the fall, so "buy when the HMM says stress" caught the rebounds of
  2016, 2019, 2020 and 2023. In 2006-14 the same rule gave 0.50 (2008 was a
  stressed regime that kept falling), well below vol-managed exposure (0.99),
  so it is not a timing rule anyone would have adopted in 2014.
- The loser-rebound alpha net of the market is real but modest: Sharpe 0.80 /
  0.83 in 2006-14 / 2015-20, 0.15 in 2021-26; losers have beta 1.27 in stress.
- For a small account that cannot short: long losers in stress + nothing in
  calm is a 20%-a-year, 0.98-Sharpe line in 2015-26 but it is 75% market
  rebound; its 2006-14 Sharpe of 0.62 includes a 2008 drawdown.

## 09:30 UTC - the switch, beta-hedged

The switch is dollar-neutral but not beta-neutral: in stressed months the
losers it buys have beta ~1.3 and the winners it sells ~0.8, so it is net long
beta exactly when the market rebounds. Hedging with the trailing-252-day beta
(lagged a day, no lookahead):

| signed switch, all names | 2006-14 | 2015-20 | 2021-26 |
|---|---|---|---|
| as reported | 0.27 | 0.77 | -0.09 |
| beta in stressed months | 0.06 | 0.28 | 0.10 |
| **beta-hedged Sharpe** | **0.19** | **0.45** | **-0.46** |
| hedged return / yr (unit gross) | 0.8% | 2.8% | -2.3% |

Roughly 40% of the 2015-20 Sharpe was the market rebounding while the book was
net long. The hedged edge is 0.2-0.45 through 2020 and negative since 2021.
This is the number to carry: a modest crisis-rebound alpha, not a strategy.

## 09:40 UTC - book with pairs, with and without the switch (25% cap per strategy)

| inverse-vol, 10% vol, 25% cap | 2006-14 | 2015-26 |
|---|---|---|
| 8 ETF sleeves | 1.01 | 0.91 |
| + pairs | 1.05 | 0.96 |
| + switch | 0.99 | 0.99 |
| + pairs + switch | 1.06 | 1.05 |

Each of the two stressed-market earners adds about 0.05-0.10 to the check
period; together +0.14. Given the switch's beta and its flat 2021-26, the
safer recommendation is pairs first, the switch as an optional sleeve.

## 09:50 UTC - alpha decay by 5-year block, and where the regime model is now

IC x 10,000 of the 11 "invariant" signals, 5-day horizon:

| signal | 2004-08 | 2009-13 | 2014-18 | 2019-23 | 2024-26 |
|---|---|---|---|---|---|
| rev_5d | 222 | 200 | 123 | 120 | 164 |
| low_volume_rev | 237 | 198 | 113 | 115 | 173 |
| peer_gap | 181 | 135 | 105 | 99 | 121 |
| bollinger_z | 105 | 108 | 84 | 127 | 132 |
| rev_1d | 212 | 80 | 78 | 163 | 110 |
| resid_rev_5d | 126 | 86 | 91 | 71 | 78 |

- Not a monotone decay: reversal fell from ~220 to ~120 by 2014-18 and has
  recovered to ~165 since 2024. It is cyclical with volatility, not dying. At
  21 days the same signals are weak or negative in 2024-26 (rev_5d 79,
  bollinger -37, rsi -103): the monthly horizon has had a bad three years,
  which is the switch's flat 2021-26 seen from the other side.
- **The regime model's blind spot**: the VIX + term-spread HMM called 2022
  (89% of days), **2023 (73%)** and 2024-25 (~45%) "stressed". 2022 was; 2023
  was not - the inverted yield curve kept the state on while VIX sat at 13-20
  and momentum ran. That is where the term spread, which helped in 2007-08,
  cost the switch in 2023-24. The VIX-only model has the opposite problem
  (weak 2006-14). No fix tonight; a model with both and a looser prior on the
  term spread is the obvious next experiment.
- **Now (20 Oct 2026)**: P(stressed) = 0.01, VIX 18, term spread +1.1%: calm.
  The switch's last monthly rebalance holds 38% reversal / 62% momentum.

## 10:00 UTC - regime model without the term-spread level

| signed switch, all names | 2006-14 | 2015-20 | 2021-26 | 2023 "stressed" share |
|---|---|---|---|---|
| VIX + term level + GARCH (the pick) | 0.27 | 0.77 | -0.09 | 73% |
| VIX + GARCH, no term | -0.11 | 0.81 | 0.24 | 18% |
| VIX + 63-day *change* in term + GARCH | -0.39 | 0.70 | 0.07 | 28% |
| vol terciles | -0.20 | 0.82 | 0.26 | - |

Dropping the term level fixes 2023 (stressed share 73% -> 18%) and 2021-26
(-0.09 -> 0.24) at the cost of 2006-14 (0.27 -> -0.11): the yield curve is
what catches 2007-08 early. Each version wins one cycle and loses another.
There have been three stress cycles in the sample; that is too few to decide
how much weight a slow macro input should get, and the honest statement is
that the regime switch is 0.2-0.5 Sharpe in crises with a model-choice risk
of about +-0.3. Student-t emissions again change nothing useful.

## 10:15 UTC - a concentrated switch (top and bottom decile only), as a small account would trade it

| signed switch, HMM regimes, monthly | 2006-14 | 2015-20 | 2021-26 | 2015-26 | vol at unit gross |
|---|---|---|---|---|---|
| all names, diversified (~1,000 positions) | 0.27 | 0.77 | -0.09 | 0.42 | ~3% |
| all names, top/bottom decile (~100 + 100) | 0.20 | 0.79 | -0.10 | 0.41 | 9% |
| top 300, top/bottom decile (~30 + 30) | -0.05 | 0.86 | 0.21 | 0.57 | 11% |

Concentrating to the extremes keeps the Sharpe and brings the volatility to
~10% without leverage, which is the form a $10k account could actually hold
(30 longs and 30 shorts of ~$160; shorting still needed for the stressed-
regime leg). Break-even 33-48 bp; turnover 0.06/day.

## 10:40 UTC - full six-model live backtests did not finish

Both full-model runs (ridge, regime_ridge, kernel_ridge, gbm, ic_weighted) were
stopped at the 2-hour limit without output: GBM over ~90 walk-forward refits
on 1,000 stocks is a 4+ hour job on this machine. Re-running the comparison
with the four non-GBM models instead.

## 11:20 UTC - live pipeline, four models (ridge, regime_ridge, kernel_ridge, ic_weighted)

| | 3-state rolling HMM | 2-state VIX + term HMM |
|---|---|---|
| regime_ridge Sharpe / IC | -0.24 / 0.009 | -0.20 / 0.012 |
| kernel_ridge Sharpe / IC | -0.17 / 0.006 | -0.21 / 0.006 |
| ensemble Sharpe 2004-14 / 2015-20 / 2021-26 | 0.47 / -0.67 / -0.66 | 0.47 / -0.70 / -0.71 |
| frictionless ensemble | 0.83 | 0.91 |

Same answer with four models as with three: the regime model moves the
regime-conditional forecast a little and the live book not at all. The daily
stock book is -0.7 Sharpe after costs in both halves of 2015-26 under either
regime model. (The six-model runs including GBM did not finish in 2 hours;
Arjun's own full run shows the same second-half sign with GBM included.)

## 11:40 UTC - the simplest regime rule beats the HMM

| signed switch, all names, monthly | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| **VIX > 20** | 0.24 | **0.95** | **0.33** | **0.69** |
| VIX > 25 | 0.42 | 0.44 | -0.22 | 0.18 |
| 2-state VIX + term HMM (88-variant pick) | 0.27 | 0.77 | -0.09 | 0.42 |
| vol terciles | -0.20 | 0.82 | 0.26 | 0.59 |

"VIX above 20" agrees with the HMM's stressed state on 84% of days and does
better in both halves of the check period while matching it in 2006-14. It
is not fitted, so there is nothing to overfit, but 20 is a number chosen by
hand and 25 is much worse: the rule is sensitive to the threshold. 20 is close
to the VIX's long-run median (~19), so the parameter-free "VIX above its
expanding median" is the right version to test (running).
Lesson of the night in one line: 88 HMM variants, Student-t emissions, sticky
transitions, Poisson symptoms and macro inputs added nothing over asking
whether the VIX is above its typical level.

## 11:50 UTC - VIX above its expanding median (no number chosen by hand)

| signed switch, monthly | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| VIX > expanding median, all names | -0.26 | 0.91 | 0.43 | 0.70 |
| VIX > expanding median, top 300 | -0.30 | 0.98 | 0.67 | 0.84 |
| VIX > 20, all names | 0.24 | 0.95 | 0.33 | 0.69 |
| 2-state VIX + term HMM, all names | 0.27 | 0.77 | -0.09 | 0.42 |

The parameter-free rule is the best of all in the check period (0.70 / 0.84)
and negative in 2006-14, like the vol terciles: in 2006-07 the expanding
median (set by the high-VIX 1990s-2002) was ~20 and called few stress days,
then 2008 was called late. Every regime proxy tried gives 0.4-0.7 in
2015-26; they differ only on the single 2008 cycle. Two are positive in
2006-14 as well: the HMM with the term spread and the fixed VIX > 20.
Threshold sensitivity (16-25) being checked.

## 12:00 UTC - VIX threshold sensitivity (signed switch, all names, monthly)

| threshold | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| VIX > 16 | -0.20 | 0.62 | 0.10 | 0.40 |
| VIX > 18 | -0.12 | 0.79 | 0.38 | 0.62 |
| **VIX > 20** | 0.24 | 0.95 | 0.33 | 0.69 |
| VIX > 22 | 0.47 | 0.83 | 0.08 | 0.53 |
| VIX > 25 | 0.42 | 0.44 | -0.22 | 0.18 |

A plateau from 18 to 22 (0.53-0.69 in 2015-26, 0.79-0.95 in 2015-20); the
rule is not knife-edge, but 16 and 25 are clearly worse. 20 is the long-run
median of the VIX; "stressed = VIX above its typical level" is the regime.

## 12:10 UTC - the VIX > 20 switch, beta-hedged

| | 2006-14 | 2015-20 | 2021-26 |
|---|---|---|---|
| all names, as traded | 0.24 | 0.95 | 0.33 |
| all names, beta-hedged (trailing 252-day beta) | **0.16** | **0.63** | **0.25** |
| top 300, as traded | 0.13 | 0.92 | 0.18 |
| top 300, beta-hedged | 0.04 | 0.61 | 0.10 |

The only configuration of the night that stays positive in all three
sub-periods after hedging its rebound beta: a small (0.2-0.6 Sharpe,
1-5% a year at unit gross) crisis-rebound alpha. Running the full
robustness / bootstrap battery on it.

## 12:30 UTC - robustness battery for the VIX > 20 switch

- **All 18 design variants positive in both periods**: 2006-14 0.10-0.48,
  2015-26 0.04-0.71 (vs the HMM switch, which had several negative cells).
  21-day rebalance is best (0.57-0.71 in 2015-26); 10-day is cost-heavy.
- Headline (composites, 21 days, all names): 0.27 / 0.95 / 0.33 by
  sub-period; correlation with the market 0.06 / -0.10 / -0.04.
- **Bootstrap, 2015-26** (21-day blocks, 2,000 draws): Sharpe 90% interval
  [0.27, 1.06], P(Sharpe < 0) = 0.3%; gain over plain monthly reversal median
  +0.58, P(no gain) = 1.7%. 2004-14: [-0.28, 0.79], P(< 0) = 20%.
- Good years (as traded, unit gross): 2020 +22%, 2019 +10%, 2015 +9%, 2008
  +6%, 2024 +6%, 2022 +5%; worst 2026 to date -5.6%.
- Still: beta-hedged it is 0.16 / 0.63 / 0.25 (see 12:10), and the threshold
  is a hand-chosen round number that happens to sit at the VIX's median.

## 12:45 UTC - the book with the VIX > 20 switch (25% cap per strategy)

| inverse-vol, 10% vol target | 2006-14 | 2015-26 | return/yr 15-26 | worst DD 15-26 |
|---|---|---|---|---|
| 8 ETF sleeves | 1.01 | 0.91 | 9.6% | -17% |
| + pairs | 1.05 | 0.96 | 9.7% | -17% |
| + VIX > 20 switch | 0.97 | 1.05 | 11.0% | -17% |
| + pairs + VIX > 20 switch | 1.03 | **1.11** | 10.6% | -15% |
| + stock book + pairs + VIX > 20 switch | 1.04 | 1.10 | 10.2% | **-13%** |

Same shape as with the HMM switch, slightly better in the check period.

## 13:00 UTC - execution delay (VIX > 20 switch, all names, monthly)

| trade ... after the signal | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| next open (as everywhere above) | 0.24 | 0.95 | 0.33 | 0.69 |
| one day later | 0.14 | 1.04 | 0.22 | 0.69 |
| two days later | 0.02 | 0.93 | 0.12 | 0.57 |

Not fragile to a day's delay in the check period; the already-weak 2006-14
edge is. Monthly signals should not depend on same-day execution, and these
do not.

## Closing note

Everything above is in `research_night/` on the user's branch: code (runs
against Arjun's `claude/keen-tesla-shs956`), 90+ result files, this log,
`REPORT.md` and the stability review. Not done: a point-in-time (survivorship-
free) re-run of the switch, which needs Alpaca keys; anything intraday or
news-based (encrypted data not available); GBM in the live-pipeline
comparison (did not finish in 2 hours).

## 13:10 UTC - pairs is a stressed-market strategy too

| Arjun's pairs book (unlevered) | 2006-14 | 2015-20 | 2021-26 | 2015-26 | return/yr 15-26 |
|---|---|---|---|---|---|
| constant | 0.85 | 0.71 | 0.76 | 0.72 | 0.8% |
| only when VIX > 20 (two days earlier) | 0.89 | 0.64 | 0.89 | 0.68 | 0.6% |
| only when VIX <= 20 | 0.09 | 0.29 | 0.28 | 0.28 | 0.2% |
| **x2 when VIX > 20** | 0.89 | 0.70 | 0.90 | 0.74 | 1.4% |
| x3 when VIX > 20 | 0.90 | 0.69 | 0.92 | 0.73 | 2.1% |

Almost all of pairs' Sharpe is earned when the VIX is above 20 (spreads blow
out and mean-revert); in calm markets it is ~0.1-0.3. Doubling its size in
stress keeps the Sharpe and nearly doubles the return - a mild, consistent
improvement, and the same lesson as the switch: in this universe the
cross-sectional edges are crisis edges.

## 14:10 UTC - GBM runs stopped again

The six-model live backtests with refits every 126 days were also stopped at
the 2-hour limit without output. Last attempt: yearly refits and 100k training
rows per GBM fit, both arms alike (`config/light_gbm*.yaml`). If this does not
finish either, the GBM comparison stays open; the four-model comparison and
Arjun's own full run both say the same thing about the daily book.

## 14:20 UTC - three more checks with the VIX > 20 regime

1. **Arjun's daily stock book is not a stress strategy.** Its net returns
   (backtest/daily.csv): traded only when VIX > 20: 0.28 / -0.41 / 0.30 by
   sub-period; only when VIX <= 20: 0.36 / 0.43 / 0.08; as is 0.44 / 0.06 /
   0.27. Unlike the monthly signals, the daily factor-neutral book does *worse*
   in stress (its costs and impact rise with volatility). The regime lever
   does not rescue it; it should be stopped, not re-timed.
2. **A long-only version for a small account**: in months with VIX > 20, buy the
   momentum losers (equal-weighted composite), hedge with the market; hold
   nothing otherwise. Hedged 1:1 against the equal-weight universe: Sharpe
   0.52 / 0.83 / 0.59 (2015-26 0.71), 6.1% a year at unit gross, worst drawdown
   -12%. Unhedged it is 0.97 / 17.8% / -22% but that is mostly the market
   rebounding (long market in stress alone: 0.93 / 11.7%). SPY-hedged versions
   and a concentrated top-decile version follow.
3. **Switch at a 10% vol target**: 2015-26 Sharpe 0.77, 8.6% a year, worst
   drawdown -14%, worst month -5.6%; but 2004-14 drawdown -26%. At unit gross:
   4.5% a year, 6.6% vol, -9% drawdown.

## 14:30 UTC - the long-only "losers in stress" line, hedged with SPY: handle with care

| long losers when VIX > 20, all names | 2006-14 | 2015-20 | 2021-26 | 2015-26 | ret/yr 15-26 | maxDD 15-26 | maxDD 06-14 |
|---|---|---|---|---|---|---|---|
| hedged 1:1 with the equal-weight universe | 0.52 | 0.83 | 0.59 | 0.71 | 6.1% | -12% | - |
| hedged 1:1 with SPY | 0.28 | 0.54 | 0.36 | 0.46 | 8.2% | -21% | -37% |
| hedged with SPY x trailing beta | 0.44 | 1.01 | 0.77 | 0.89 | 16.0% | -22% | **-49%** |
| top-decile losers, SPY x beta | 0.46 | 1.01 | 0.76 | 0.89 | 18.9% | -27% | -56% |

- Yearly returns of the beta-matched line: 2008 -1%, **2009 +66%**, 2016 +20%,
  2019 +20%, **2020 +83%**, 2021 +19%, 2025 +22%, with -49% to -56% drawdowns
  inside 2008-09. This is the momentum crash seen from the long side: buying
  the biggest losers in a crisis loses violently while the crisis deepens and
  pays enormously in the rebound. The 2020 and 2009 numbers are also exactly
  where survivorship bias is largest (today's 1,000 largest names include the
  ones that crashed and recovered). A SPY hedge does not remove the small-cap
  and high-beta exposure of the losers; the equal-weight-universe hedge does,
  and that version (0.5-0.8 Sharpe, ~6% a year, -12% drawdown) is the honest
  one. Not a $10k-account strategy in its SPY-hedged form.

## 14:40 UTC - timing inside the crisis does not help

Splitting "VIX > 20" into "VIX still near its 63-day high" and "VIX falling
from it": the hedged long-losers line is 0.12 / 0.65 / 0.12 near the peak and
0.46 / 0.51 / 0.52 once the VIX is falling; the signed switch 0.03 and 0.35
(2015-26) respectively vs 0.68 for the whole stressed period. Both halves
contribute and neither can be dropped; the plain rule stays.
