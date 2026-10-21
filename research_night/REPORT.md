# Overnight research report: 21 October 2026

A second pass over Arjun's quant-trading research, run on the same data
(1,000 US stocks, daily prices 2000-2026, rebuilt from Yahoo) with the same
rules he used: 2006-2014 is for choosing, 2015-2026 is only for checking;
every model is refit walk-forward; costs are measured bid-ask spreads plus 1 bp.
Everything here is in `research_night/` (code, reports, the running log
`night_lab_log.md`, and a review of his existing outputs in
`stability_report.md`). Draft - numbers may be refined before 11:00.

## The short version

1. **The market's one stable pattern is a sign pattern, not a level.** When
   volatility is high, stocks that fell bounce back (reversal works) and
   momentum stocks crash. When volatility is low, momentum works and reversal
   does nothing. This held in every sub-period 2004-2026. Nothing else in the
   44-signal library is both strong and stable.
2. **Arjun's daily reversal system is dead on costs, not on signal.** The
   gross edge is still there (half of what it was); daily rebalancing costs
   eat it. Trading monthly instead, and switching between reversal and
   momentum by regime, gives a modest, market-neutral strategy that pays in
   crises: net Sharpe about **0.3 (2006-14) / 0.4 (2015-26)** versus **-0.04 /
   0.09** for monthly reversal alone. It is not a 1.0-Sharpe strategy, and it
   was flat in 2022-2026.
3. **The best regime model is the simplest.** A 2-state hidden Markov model on
   the VIX, the yield-curve slope and GARCH volatility. 88 variants were tried
   (more states, fat-tailed emissions, sticky transitions, jump counts as a
   Poisson symptom, GARCH-standardised symptoms, dispersion, breadth): none
   beat it, most were worse, and none of them is a better *market timer* than
   plain volatility targeting.
4. **Two bugs in the existing research.** (a) The Poisson jump model's
   "-2.2 deviance explained" is a standardisation bug (a feature that is
   constant before 2015 gets divided by ~1e-12), not a finding; the models
   actually rank future jumpers well (rank IC 0.11). (b) The `downside_beta`
   signal is broken and sits at the top of `best_correlations.csv` through
   its pairs. Also, every "1st period" table in his research covers 2001-2014,
   not 2006-2014 as documented, and 2001-2005 flatters reversal a lot.
5. **Adding the switch and his `pairs` strategy to the ETF book raises its
   Sharpe from 1.01 / 0.91 to 1.07 / 1.10**, because those two earn in exactly
   the stressed markets where every ETF sleeve loses (switch Sharpe 0.82 in
   stress; the trend sleeves -0.2 to -0.5). Regime-*tilting* the ETF sleeves
   themselves does not help.

## What was built

| module | what it does |
|---|---|
| `lab_prep` | builds the market, factor model and all 44 signals once and caches them (4 min), so experiments run in seconds |
| `regime_lab` | 88 HMM variants (symptom sets x emissions x states x sticky), walk-forward, scored on *money*: market timing vs vol-managed, reversal sizing, reversal/momentum switch |
| `jump_lab` | Poisson and negative-binomial GLMs for next-month jump counts; walk-forward, rank-standardised features, market-rate offset; tested as alpha and as a risk filter |
| `invariants_lab` | every signal's 5- and 21-day IC in four sub-periods, trend test, regime dependence; classifies invariant / decaying / regime-dependent / noise |
| `switch_lab`, `switch_robust` | the monthly reversal-momentum switch, with every design choice varied and a block-bootstrap interval |
| `book_lab` | regime-aware capital allocation across all of Arjun's strategies, with vol-tercile and VIX-tercile "dumb regimes" as the bar to clear |

They import from Arjun's `claude/keen-tesla-shs956` branch (the research
package), so they need that branch merged into this one to run.
`research_night/patch/` holds the small change that lets his live pipeline use
the 2-state macro HMM (`config/regime_macro.yaml`), tested end to end on the
synthetic demo; the real-data comparison against the current 3-state model is
in the "Live pipeline" section below once it finishes.

## Findings in more detail

### Invariants and monovariants (what is stable, what drifts)

*5-day horizon.* 11 of 44 signals are invariant (same sign in 2004-09,
2010-14, 2015-20, 2021-26; |t| > 3; no trend): all the short-term reversal
variants plus peer-gap, close-location and volume-price correlation. Nothing
in momentum, volatility, volume, seasonality or microstructure qualifies.
The reversal IC fell from 0.022 to 0.012 over 22 years; the slope is -0.005 per
decade with t = -1.4 - a drift, not a death. Every reversal signal is 2-3x
stronger in the top volatility tercile.

*21-day horizon.* Only one signal is unconditionally invariant. Eleven are
regime-dependent: reversal/RSI/Bollinger/illiquidity have IC near zero in calm
markets and 0.02-0.04 in stressed ones; momentum, 52-week high, low beta, low
vol and trend are +0.02 in calm and -0.04 to -0.06 in stress. The two
families cancel unconditionally, which is why the research's monthly models
look like noise.

*Market structure.* Volatility, dispersion, average correlation and market
autocorrelation show no trend 2004-2026. Jumps per day drift up slightly
(15 -> 18). The only strong monovariant is the number of tradable names
(540 -> 950): the universe is today's survivors filling in - the survivorship
bias Arjun flagged, and it flatters every result here.

### The regime model (HMM)

- Market timing: zero of 88 variants beat a plain 10%-vol-targeted exposure
  in both periods (median gain -0.29 Sharpe). Crash-probability skill 0.00-0.02;
  volatility forecasts never beat last month's realised vol. Same as Arjun
  found; Student-t emissions, sticky transitions and a 4th state change nothing.
- Daily (non-overlapping) symptoms, with or without the signed return, make
  the HMM learn 1-3 day "big day / small day" states, not regimes. Regimes
  need slow inputs: the VIX level, rolling vol, the term spread.
- The only consistent economic use is as a **dial between reversal and
  momentum**. The VIX + term-spread 2-state model was the top variant by
  2004-14 score *and* held up in 2015-26. Its stressed state: ~35-42% of
  days, 28% annualised vol, lasts ~33 days, reversal IC 0.025 vs 0.007 calm,
  momentum IC -0.03 vs +0.02 calm.
- Honest limits: the HMM does not separate signal regimes more sharply than a
  trailing-vol tercile (mean IC spread 0.021 vs 0.028); its value is
  persistence (fewer switches). Three regime proxies were tried and one was
  consistent across both periods, so selection risk is real.

### Poisson / GLM jump models

- Jump propensity is very predictable across stocks: rank correlation of
  predicted vs realised next-21-day jump counts 0.09-0.11 (t 20-28) in both
  periods. Ranking features within each day and using the trailing market jump
  rate as an exposure offset fixes calibration (0.78 -> 1.01 predicted /
  realised). Negative binomial equals Poisson for the mean.
- As an alpha signal it is weak (net Sharpe 0.13 / 0.42 at a 20-day
  smoothing) and partly a high-volatility tilt that only pays in a survivor
  universe. As a *risk filter* it hurts: dropping the 10-20% most jump-prone
  stocks from the reversal book cuts its gross Sharpe from 1.18 to 0.90 -
  jump risk is where reversal alpha lives.

### The switch (what to trade)

Two monthly-rebalanced long/short books: reversal (rev_21d + Bollinger +
RSI) and momentum (12-1 month + residual momentum + 52-week high). Capital
goes to each in proportion to its predicted IC (regime probabilities x
per-regime IC learned on the training block); a book with a negative
predicted IC is traded the other way (short momentum in stress).

| all 1,000 names, net | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| monthly reversal alone | -0.04 | 0.16 | 0.01 | 0.09 |
| 50/50 reversal / momentum | -0.40 | -0.12 | -0.11 | -0.12 |
| **switch, VIX + term HMM** | **0.27** | **0.77** | -0.09 | **0.42** |
| switch, vol terciles | -0.20 | 0.82 | 0.26 | 0.59 |

- Break-even cost 32-44 bp (plain reversal: 11 bp); turnover 0.04 a day;
  correlation with the market -0.08.
- Good years: 2008 (+14.7%), 2015, 2019-2021. Flat 2022-2026 (2024: -5.6%).
  It is a crisis strategy; it does nothing in calm trending years.
- Bootstrap (21-day blocks) of the 2015-26 Sharpe: 90% interval [0.00, 0.78];
  probability it is really below zero 4.8%; probability it does not beat
  plain reversal 6.2%. Borderline, one out-of-sample period.
- Robust to design choices: 21- or 42-day rebalance, either book
  composition, either universe give 0.26-0.49 in 2015-26; 10-day rebalancing
  is too costly.

### Multi-strategy book

| inverse-vol weights, 10% vol | 2006-14 | 2015-26 |
|---|---|---|
| 8 ETF sleeves (Arjun's book) | 1.01 | 0.91 |
| + stock book | 1.00 | 0.91 |
| + regime switch | 0.99 | 0.99 |
| **+ regime switch + pairs** | **1.07** | **1.10** |
| + switch + pairs, 25% cap per strategy | 1.06 | 1.05 |

Regime-tilting the sleeves (HMM or terciles) never beats inverse-vol in both
periods: in stress every long-biased sleeve has Sharpe ~0, and vol targeting
already cuts exposure. The switch and `pairs` are the only strategies that
pay in stress, which is why adding them - rather than tilting - helps.

### Pairs (Arjun's best market-neutral strategy, tuned honestly)

72 configurations (pairs per cluster, entry/exit thresholds, holding limit,
z-score window). His parameters (5 pairs per cluster, enter at |z| > 2, exit
at 0.5, 21-day hold) are already the robust choice: 0.85 / 0.77 Sharpe. The
configuration that looks best on 2006-14 (25 pairs, enter at 1.5, hold 63
days: 1.02) collapses to 0.35 afterwards - more pairs per cluster are noise
and concentrate the book. Only a longer holding limit (63 days) is marginally
better in both periods (1.01 / 0.81). Leave it as it is. Note the unlevered
book has ~1% volatility and kurtosis ~46; it needs ~10x leverage to matter,
which is where the fat tails bite.

## What to change in Arjun's system (concrete)

1. **Replace the daily 5-day reversal stock book with the monthly switch.**
   The daily book is -0.5 net in both periods at measured costs; the monthly
   switch is +0.3 / +0.4 and market-neutral.
2. **Replace the 3-state rolling HMM with the 2-state VIX + term-spread +
   GARCH model** (`regime_lab` `macro`, K=2). The current model's switch would
   have looked useless in 2006-14 (-0.45) and great after; unstable.
3. **Add the switch as a sleeve of the ETF book**, with a per-strategy weight
   cap so inverse-vol does not over-allocate to it.
4. **Fix `poisson._poisson_glm`**: drop features constant in training (or
   floor the standard deviation); rank-standardise stock features per day;
   refit yearly. Fix or drop `downside_beta`.
5. **Report 2006-2014, not 2001-2014**, as the selection period in
   `edge.summarize` and everything built on it; 2001-2005 roughly doubles the
   apparent reversal edge.
6. Stop spending effort on: more states or fancier emissions for the HMM,
   HMM market timing, using jump intensity as a risk filter, and regime tilts
   of long-biased sleeves. None of them survived.

## Caveats

- Survivor universe (today's 1,000 most traded, 15+ years of history): every
  stock-level result is flattered, momentum results are distorted (2008
  crashers that rebounded), and the switch should be re-run on a point-in-time
  universe before real money. The code for that exists (`survivorship` study)
  but needs Alpaca keys, which this session did not have.
- One out-of-sample period, and the last five years of it were flat for the
  switch. 2,000-draw bootstrap puts the lower 5% bound at zero.
- Many things were tried tonight (88 HMM variants, 3 regime proxies, 18
  switch configurations). The headline picks were made on 2006-14 where
  possible, but the design space itself was explored with both periods
  visible.
- The encrypted intraday and news datasets were not available here, so
  nothing intraday or news-based was re-examined.
