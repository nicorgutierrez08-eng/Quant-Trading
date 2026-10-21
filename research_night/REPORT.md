# Overnight research report: 21 October 2026

A second pass over Arjun's quant-trading research, run on the same data
(1,000 US stocks, daily prices 2000-2026, rebuilt from Yahoo) with the same
rules he used: 2006-2014 is for choosing, 2015-2026 is only for checking;
every model is refit walk-forward; costs are measured bid-ask spreads plus 1 bp.
Everything here is in `research_night/` (code, reports, the running log
`night_lab_log.md`, and a review of his existing outputs in
`stability_report.md`). Written between 01:00 and 07:00 EDT; the log has the
chronology and every intermediate number.

## The short version

1. **The market's one stable pattern is a sign pattern, not a level.** When
   volatility is high, stocks that fell bounce back (reversal works) and
   momentum stocks crash. When volatility is low, momentum works and reversal
   does nothing. This held in every sub-period 2004-2026. Nothing else in the
   44-signal library is both strong and stable.
2. **Arjun's daily reversal system is dead on costs, not on signal.** The
   gross edge is still there (half of what it was); daily rebalancing costs
   eat it. The tradable form of the pattern in point 1 turned out to be the
   simplest one: **hold a monthly momentum book, and hold it short whenever
   the VIX is above 20.** Nothing is fitted. Net Sharpe **0.61 / 1.06 / 0.37**
   in 2006-14 / 2015-20 / 2021-26 (6.2% a year at unit gross, worst drawdown
   -11%); **0.50 / 0.85 / 0.29 after hedging** the market beta it carries in
   rebounds. It is robust to the threshold (18-22), the universe, a day's
   execution delay, doubled costs, and works for each momentum signal on its
   own. A learned reversal/momentum switch (the first version of this idea)
   was worse in every sub-period (0.24 / 0.95 / 0.33). This is a real,
   modest crisis-rebound edge - "momentum with a crash hedge" - not a
   strategy to build an account on; its two +30% years (2009, 2020) are the
   two great rebounds in a survivor universe.
3. **The best regime model is the simplest, and the simplest is not an HMM.**
   Of 88 HMM variants (more states, fat-tailed emissions, sticky transitions,
   jump counts as a Poisson symptom, GARCH-standardised symptoms, dispersion,
   breadth, macro inputs) the best was a 2-state model on the VIX, the
   yield-curve slope and GARCH volatility. But the rule "stressed when the
   VIX is above 20" matches its states 84% of the time and does better in the
   check period (switch Sharpe 0.24 / 0.95 / 0.33 by sub-period vs the HMM's
   0.27 / 0.77 / -0.09); "VIX above its long-run median" does better still
   after 2015 (0.91 / 0.43) but misses 2008. None of them is a better *market
   timer* than plain volatility targeting. The regime that matters is the
   level of the VIX; the machinery around it added nothing.
4. **Two bugs in the existing research.** (a) The Poisson jump model's
   "-2.2 deviance explained" is a standardisation bug (a feature that is
   constant before 2015 gets divided by ~1e-12), not a finding; the models
   actually rank future jumpers well (rank IC 0.11). (b) The `downside_beta`
   signal is broken and sits at the top of `best_correlations.csv` through
   its pairs. Also, every "1st period" table in his research covers 2001-2014,
   not 2006-2014 as documented, and 2001-2005 flatters reversal a lot.
5. **Adding his `pairs` strategy and the switch to the ETF book raises its
   Sharpe from 1.01 / 0.91 to about 1.06 / 1.05** (with a 25% cap per
   strategy; 1.07 / 1.10 uncapped) and cuts the worst drawdown from -17% to
   -13%, because those two earn in exactly the stressed markets where every ETF
   sleeve loses. Regime-*tilting* the ETF sleeves themselves does not help.

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

*Is the edge decaying monotonically?* No. Reversal's 5-day IC (x10,000) by
5-year block: rev_5d 222 / 200 / 123 / 120 / 164; peer_gap 181 / 135 / 105 /
99 / 121. It halved by 2014-18 and has recovered since 2024. It moves with
market volatility rather than dying. The *monthly* versions are what has
been weak lately (2024-26 IC near zero or negative), which is the switch's
flat 2021-26 seen from the signal side.

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
- Its blind spot: the term spread that made it catch 2007-08 kept it in the
  "stressed" state through 2023 (73% of days) and much of 2024-25 while the
  VIX sat at 13-20 and momentum ran - the inverted yield curve, not market
  stress. That is where the switch lost money in 2023-24. Dropping the term
  spread fixes 2023 (stressed share 73% -> 18%, 2021-26 Sharpe -0.09 -> 0.24)
  but loses 2007-08 (2006-14 Sharpe 0.27 -> -0.11). Three stress cycles in
  the sample are too few to settle how much weight a slow macro input should
  get; treat the regime switch as 0.2-0.5 Sharpe in crises with a
  model-choice risk of about +-0.3.
- Today (20 Oct 2026) the model reads calm: P(stressed) 0.01, VIX 18, curve
  +1.1%. The switch's current rebalance is 38% reversal / 62% momentum.

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

### The momentum flip (the simplest tradable form)

Hold the momentum composite (12-1 month momentum + residual momentum +
52-week high, equal-weighted z-scores, rebalanced every 21 days); when the
VIX is above 20 at the rebalance, hold it short. Net of measured costs:

| all 1,000 names | 2006-14 | 2015-20 | 2021-26 | 2015-26 | return/yr 15-26 | worst DD 15-26 |
|---|---|---|---|---|---|---|
| as traded | 0.61 | 1.06 | 0.37 | 0.76 | 6.2% | -11% |
| beta-hedged | 0.50 | 0.85 | 0.29 | 0.59 | 4.6% | -18% |
| threshold 18 / 22 | 0.38 / 0.73 | 1.05 / 0.95 | 0.49 / 0.10 | 0.80 / 0.58 | | |
| top 300 names | 0.53 | 0.93 | 0.20 | 0.61 | 5.8% | -14% |
| one-day delay / costs x2 | 0.59 / 0.51 | 1.08 / 0.99 | 0.29 / 0.29 | 0.73 / 0.68 | | |
| each momentum signal alone | 0.51-0.58 | 0.87-1.09 | 0.24-0.49 | 0.60-0.75 | | |

Turnover 0.035 a day, break-even 77 bp. For scale: the same momentum book
*never* flipped is -0.47 / -0.28 / -0.16 - in this universe long/short
momentum loses in every sub-period, and the flip is the whole difference.
Every fixed rule that shorts momentum in stress beat the IC-learned switch
below; adding reversal to the stressed
leg added nothing once short-momentum was there. The learned switch is kept
below as the record of how the result was reached.

### The switch (the first version, learned weights)

Two monthly-rebalanced long/short books: reversal (rev_21d + Bollinger +
RSI) and momentum (12-1 month + residual momentum + 52-week high). Capital
goes to each in proportion to its predicted IC (regime probabilities x
per-regime IC learned on the training block); a book with a negative
predicted IC is traded the other way (short momentum in stress).

| all 1,000 names, net | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| monthly reversal alone | -0.04 | 0.16 | 0.01 | 0.09 |
| 50/50 reversal / momentum | -0.40 | -0.12 | -0.11 | -0.12 |
| switch, VIX + term HMM (best of 88 HMMs) | 0.27 | 0.77 | -0.09 | 0.42 |
| **switch, "VIX > 20"** | 0.24 | **0.95** | **0.33** | **0.69** |
| switch, VIX above its long-run median | -0.26 | 0.91 | 0.43 | 0.70 |
| switch, vol terciles | -0.20 | 0.82 | 0.26 | 0.59 |

The VIX > 20 rule is robust between 18 and 22 (0.53-0.69 for 2015-26) and
clearly worse at 16 or 25.

- Break-even cost 32-44 bp (plain reversal: 11 bp); turnover 0.04 a day;
  correlation with the market -0.08.
- Good years: 2008 (+14.7%), 2015, 2019-2021. Flat 2022-2026 (2024: -5.6%).
  It is a crisis strategy; it does nothing in calm trending years.
- Beta: dollar-neutral but not beta-neutral. In stressed months it buys
  high-beta losers and sells low-beta winners (beta 0.28 in 2015-20), so it is
  net long when the market rebounds. Hedged with the trailing 252-day beta the
  HMM switch is 0.19 / 0.45 / -0.46 in 2006-14 / 2015-20 / 2021-26 and the
  VIX > 20 switch 0.16 / 0.63 / 0.25. Those are the numbers to carry.
- Bootstrap (21-day blocks, 2,000 draws) of the 2015-26 Sharpe. HMM switch:
  90% interval [0.00, 0.78], P(below zero) 4.8%, P(no gain over plain
  reversal) 6.2%. VIX > 20 switch: [0.27, 1.06], P(below zero) 0.3%, P(no
  gain) 1.7%. For 2004-14 the VIX > 20 switch's interval is [-0.28, 0.79]:
  one clear out-of-sample period, one murky selection period.
- Robust to design choices: for the VIX > 20 rule all 18 variants (10/21/42-day
  rebalance x 3 book compositions x 2 universes) are positive in both periods
  (0.10-0.48 and 0.04-0.71); 21-day rebalancing is best, 10-day too costly.
  The HMM switch had several negative cells. Trading one day late leaves
  2015-26 unchanged (0.69); two days late gives 0.57.
- Cost stress: at twice the measured spreads 2015-26 is 0.60, at three times
  0.51 (the thin 2006-14 edge is gone at 3x). Monthly turnover is why it
  survives where the daily book does not.
- Not a few lucky names: 60% of stocks contributed positively in 2015-26, the
  top 10 names are 15% of the P&L (dropping them: Sharpe 0.93 -> 0.82 in
  2015-20), net sector exposures stay within +-2% of gross, and the gains come
  from cyclicals (discretionary, industrials, energy, real estate); health care
  is the one losing sector.
- Where the money comes from (one leg at a time): **shorting momentum in
  stressed markets** - buying the stocks that fell most, selling the ones that
  rose most, i.e. the classic momentum crash - is the strongest and most
  stable leg (Sharpe 0.81 / 0.75 / 0.03 in 2006-14 / 2015-20 / 2021-26).
  Reversal in stress is second (0.49 / 0.48 / -0.21); momentum in calm third
  (0.37 / 0.74 / -0.14). Reversal in calm markets *loses* after costs in every
  period, so the "invariant" reversal edge is really a stressed-market effect.
- For a small account: trading only the top and bottom decile by signal
  (about 30 longs and 30 shorts in the 300 most liquid names) keeps the Sharpe
  (-0.05 / 0.86 / 0.21 by sub-period, 0.57 for 2015-26) and runs at ~10%
  volatility unlevered. Shorting is still required for the stressed-regime leg.
- A warning about long-only versions: "buy the losers in stress" looks like a
  1.0-Sharpe, 20%-a-year line in 2015-26, but owning the *whole* market in the
  same stressed months gives 1.06 and 15.7% - the regime is flagged after the
  fall, so it caught the rebounds of 2016, 2019, 2020 and 2023 (and would have
  sat through 2008: 0.50 in 2006-14). The losers' alpha over the market is a
  modest 0.80 / 0.83 / 0.15 Sharpe by sub-period. Hedge it or don't count it.
  With the VIX > 20 rule and a 1:1 hedge against the equal-weight universe the
  long-only version is 0.52 / 0.83 / 0.59 (about 6% a year, -12% worst
  drawdown) - the most consistent hedged line of the night. Hedging with SPY
  instead looks far better (16% a year) but hides -50% drawdowns inside 2008-09
  and +66% / +83% years in 2009 / 2020: that is the momentum crash from the
  long side plus survivorship bias, not a strategy.

### Multi-strategy book

| inverse-vol weights, 10% vol, 25% cap per strategy | Sharpe 2006-14 | Sharpe 2015-26 | return/yr 2015-26 | worst drawdown 2015-26 |
|---|---|---|---|---|
| 8 ETF sleeves (Arjun's book) | 1.01 | 0.91 | 9.6% | -17% |
| + stock book | 1.00 | 0.91 | 9.5% | -15% |
| + pairs | 1.05 | 0.96 | 9.7% | -17% |
| + regime switch | 0.99 | 0.99 | 10.3% | -17% |
| **+ pairs + regime switch (HMM)** | **1.06** | **1.05** | 9.9% | -15% |
| + pairs + regime switch (VIX > 20) | 1.03 | **1.11** | 10.6% | -15% |
| + stock book + pairs + switch (VIX > 20) | 1.04 | 1.10 | 10.2% | **-13%** |
| (uncapped, + pairs + HMM switch) | 1.07 | 1.10 | | |

The improvement is in risk, not return: the same ~10% a year with a smaller
worst loss, because the two new sleeves earn when the ETF sleeves lose.

Put together as three components at roughly equal risk (Arjun's ETF book,
his pairs book sized 2x when VIX > 20, the VIX > 20 switch; pairwise
correlations -0.04 to 0.06), scaled to 10% volatility:

| | 2006-14 | 2015-20 | 2021-26 | return/yr 2015-26 | worst drawdown | worst month |
|---|---|---|---|---|---|---|
| ETF book alone | 0.87 | 0.85 | 0.96 | 9.5% | -15% | -8.2% |
| ETF + pairs (x2 in stress) + learned switch | 1.02 | 1.28 | 1.15 | 12.4% | -12.6% | -7.3% |
| **ETF + pairs (x2 in stress) + momentum flip** | **1.11** | **1.43** | **1.12** | **13.3%** | **-11.2%** | -7.4% |

Worst years 2018 -3.3%, 2022 -2.6%, 2016 -2.0%; best 2019 and 2020 +27%;
2025 +19%, 2026 to date +9.5%. This blend is long equities through the ETF
book and the switch's rebound beta; it is not market-neutral.

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

Pairs is a crisis strategy too: its Sharpe is 0.89 / 0.64 / 0.89 by
sub-period when the VIX is above 20 and 0.09 / 0.29 / 0.28 when it is not.
Doubling its size when VIX > 20 keeps the Sharpe (0.89 / 0.70 / 0.90) and
nearly doubles the return - a mild, consistent improvement.

### Live pipeline: the two regime models head to head

Arjun's actual backtest (`python -m qtrade backtest`), run twice with the
fast models (ridge, regime_ridge, ic_weighted), once with the current 3-state
rolling HMM and once with the 2-state VIX + term-spread HMM
(`config/regime_macro.yaml`):

| four models (ridge, regime_ridge, kernel_ridge, ic_weighted) | current 3-state | 2-state macro |
|---|---|---|
| regime_ridge Sharpe / mean IC | -0.24 / 0.009 | -0.20 / **0.012** |
| ensemble Sharpe 2004-14 / 2015-20 / 2021-26 | 0.47 / -0.67 / -0.66 | 0.47 / -0.70 / -0.71 |
| frictionless ensemble Sharpe | 0.83 | 0.91 |

The better regime model improves the regime-conditional forecast (IC up a
third) but cannot save the daily book: at 16x annual turnover and measured
spreads it loses about 0.7 Sharpe a year after 2015 under either HMM. Nor
can the VIX rule: unlike the monthly signals, his daily factor-neutral book
does *worse* when the VIX is above 20 (-0.41 in 2015-20) than below it
(+0.43), because its costs and impact rise with volatility. (The
runs including GBM did not finish in the 2-hour limit; Arjun's own full run
shows the same second-half sign with GBM.) Same conclusion as the labs -
replace the daily book, don't re-tune it.

## What to change in Arjun's system (concrete)

1. **Stop trading the daily 5-day reversal stock book.** It is -0.5 net in
   both periods at measured costs under any regime model. If a stock book is
   wanted, the monthly momentum flip on "VIX > 20" is the candidate (0.61 /
   1.06 / 0.37 as traded; 0.50 / 0.85 / 0.29 beta-hedged) - a crisis-rebound
   sleeve, sized as such, not the core. Re-run it on a point-in-time universe
   before trusting the 2009 and 2020 numbers.
2. **Drop the HMM for the regime; use the VIX.** "Stressed when VIX > 20"
   (or above its long-run median) does what the best of 88 HMM variants does,
   with nothing to fit. If an HMM is kept for the regime_ridge model, the
   2-state VIX + term-spread + GARCH one (`config/regime_macro.yaml`) is the
   least bad; know its blind spot (an inverted yield curve reads as stress,
   as in 2023) and that the current 3-state rolling model's switch would have
   looked useless in 2006-14 (-0.45) and great after.
3. **Add `pairs` to the ETF book first, the switch second**, both with a
   per-strategy weight cap so inverse-vol does not over-allocate to them.
   Size pairs up (about 2x) when the VIX is above 20; that is where it earns.
   The three together at equal risk: Sharpe 1.02 / 1.28 / 1.15 by sub-period,
   12.4% a year at 10% volatility, worst drawdown -12.6% (ETF book alone:
   0.87 / 0.85 / 0.96, 9.5%, -15%).
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
- The live-pipeline comparison could not include GBM (the two six-model runs
  did not finish in two hours); it was run with the four other models.

## Where everything is

- `research_night/REPORT.md` - this document.
- `research_night/night_lab_log.md` - the chronological log with every
  intermediate table, including the ones that did not make it here.
- `research_night/stability_report.md` - the review of Arjun's existing
  research outputs (zoo, pairs, strategies, decay), with its data artefacts.
- `research_night/code/` - the seven research modules (run on Arjun's
  `claude/keen-tesla-shs956` branch); `research_night/patch/` - the macro
  regime option for his live pipeline.
- `research_night/reports/` - every run's markdown and CSV output.
