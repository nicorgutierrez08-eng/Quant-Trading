# Overnight research log

Running notes from the overnight research loop: what was launched, what came
back, and what it means. Newest first. Full results: `research/` on the
`results` branch.

## 2026-10-21 03:50 UTC: everything not yet covered is now launched

Built, tested on synthetic data, and pushed to run on real data:
- **Public data loaders:** FRED macro, S&P 500 changes, FINRA daily short volume, SEC insider trades, every US stock incl. delisted (Alpaca)
- **Ideas wave 2:** short volume (level and change), insider net and cluster buying, filing delays, correlation-network momentum, calendar-month seasonality, overnight momentum, 52-week low, nominal price, volume-spike continuation, earnings-surprise revisions
- **Ideas wave 3:** daily signals from 5-minute bars (realized skewness and kurtosis, jump share, first/last half hour, realized-vol ratio)
- **Survivorship study:** point-in-time top-1000 incl. delisted stocks vs today's survivors, 2017-2026
- **Events:** 15 headline-classified news types, novel vs stale news, S&P 500 additions/removals
- **Strategies wave 2:** ~30-ETF trend following, volatility premium, sector seasonality, macro timing of market and momentum, momentum crash protection, Ledoit-Wolf optimisation across strategies, capacity to $1B, open vs close execution
- **Model zoo:** sequence models on raw histories; online IC-weighted ensemble; disagreement-sized ensemble

Still open in the backlog: sector/beta-neutral factor books, ETF pair trades, intraday strategies, other training targets, interaction signals as features.
Not possible with free data: options, analyst revisions, borrow fees, supply chains.

## 2026-10-21 03:00 UTC: loop started

Launched:
- model zoo, wave 1: 21 families x 4 signal sets x 1/5/21 days (12 jobs)
- model zoo, wave 2: 13 more families at 1/5/21/63 days + all families at 63 days (8 jobs)
- ideas lab, wave 1: 20 new signals (momentum variants, trend shape, volatility, liquidity, fundamentals) at 1/5/21/63 days
- strategy zoo (rerun after a bug fix): ~20 non-reversal strategies and a diversified book

Findings so far:
- Strongest tradable signal pair: 12-month momentum + 52-week high. Net Sharpe 0.49 (2004-14) / 0.59 (2015-26), break-even 39-46 bp (~10x cost).
- Real spreads match the cost model (1.6 bp for liquid names; 5-8x wider at the open).
- Reversal IC is 2-3x larger in HMM-stressed markets, but trading only then doesn't add net profit.
- GARCH beats the rolling window for stock volatility (146/150 stocks), but scaling the whole book by volatility hurts.
- Jumps cluster (variance/mean 24); jump storms are predictable (7-day half-life); no-news up-jumps reverse twice as much as news-driven ones.

## 04:00 UTC
- Pushed ideas wave 4 (combination signals: momentum + 52w high, reversal + residual momentum, momentum trio, reversal within winners) and a zoo `targets` group (ridge/GBM on factor-residual and vol-scaled targets, top/bottom-decile logistic). Synthetic runs clean; real-data run triggered via `[zoo: ...]` tag.
- Strategy zoo wave 2 (real data): **diversified book of 16 strategies chosen on 2006-14 → net Sharpe 1.29 / 0.85 (2015-26), max DD -17%**, vs reversal book alone 0.44 / 0.16. Inverse-vol weights beat Ledoit-Wolf mean-variance out of sample (0.85 vs 0.76). Best single legs in 2015-26: SPY vol-managed 0.84, cross-asset momentum 0.78, pairs 0.72 (corr with SPY 0.23), risk parity 0.70, broad 12m trend 0.54 (corr with SPY -0.01). Short vol works but with -66% to -95% drawdowns. Losers: sector seasonality, low vol, earnings premium, 52w-high alone, sector momentum.
- Execution: 5-day reversal does better filled at the next open (0.07-0.09) than the next close (-0.03); 1-day residual reversal loses either way once costs are in.
- Capacity: momentum goes from 0.05 to -0.16 (2015-26) between $10k and $1B, so it's fine at retail size.
- FRED timed out from the runners → added a Yahoo fallback (5ddc44b) and started the strategies study again.

## 04:20 UTC
- Event study (fixed first day, real data 2015-26): buyback headlines **+33 bp next open→close (t 6.6), +37 bp at 21 days**; analyst upgrades +4.5 bp (t 3.2); M&A headlines drift **-22 bp over 21 days (t -3.2)**; lawsuit/probe news *reverses* **+76 bp over 21 days (t 3.6)**; CEO changes -38 bp day 1. Stale news reverses more than novel news (-22 bp at 21 days, t -2.6), matching Tetlock.
- Survivorship (Alpaca, 14,736 stocks incl. 1,954 delisted, 2017-26): on a point-in-time universe, **momentum is stronger** (21d IC 0.035 vs 0.005 on survivors) and so is low vol; **illiquidity/size look worse** (amihud bias +0.039, size +0.025: their apparent edge was survivorship); reversals slightly overstated (+0.01-0.02).
- Fixed: survivorship JSON keys, S&P change table lookup, research workflow failing on untagged pushes (451d5df).
- New: neutral/vol-scaled factor books + ETF pairs + momentum/reversal risk parity (06019fa); intraday strategies (9e1406f); zoo `features` group: sticky-pair products, best ideas, lasso→GBM (8b6c5a5); ideas wave 5 news events.
