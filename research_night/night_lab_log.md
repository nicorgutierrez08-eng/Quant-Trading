# Night lab log (2026-10-21, 01:00-11:00 EDT)

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
