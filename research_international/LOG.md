# International research log (from 23 Oct 2026)

Question: does the US finding - 12-month stock momentum pays when the VIX is
low and reverses when it is high, so a monthly momentum book flipped short
when VIX > 20 earns ~0.6 / 0.7 / 0.2 Sharpe (2006-14 / 2015-20 / 2021-26) -
hold on other exchanges, and in Asian financials in particular?

## Data

- Universes: current constituents of each market's main index, from Wikipedia
  (Japanese Wikipedia for the Nikkei 225 by sector; Chinese Wikipedia for the
  Taiwan 50). 1,760 stocks in 21 markets, 308 financials:
  Japan 225 (20 fin.), Hong Kong 85 (10), HK H-shares 50 (10), China CSI 300
  (50), Korea KOSPI 200 (22), Taiwan 50 (11), Singapore STI 30 (4), Australia
  ASX 200 (38), India NIFTY 50 + Next 50 (24), Malaysia KLCI 30 (6), Thailand
  SET50 (12), New Zealand NZX 50 (12); UK FTSE 100 (29), Germany DAX 40 (6),
  France CAC 40 (5), Switzerland SMI 20 (5), Netherlands AEX 25 (6), Spain IBEX
  35 (7), Italy FTSE MIB 40 (12), Sweden OMXS30 (7), Canada TSX 60 (12).
- Prices: Yahoo daily OHLCV 2000-, local currency, adjusted for dividends and
  splits; plus each market's index, the US VIX, local volatility indices where
  Yahoo has them, and 29 US-listed country ETFs.
- Same survivorship caveat as the US work, stronger here: today's index
  members only, and some markets (Korea, India, China) have a lot of index
  turnover.

## First look (smoke test, before the full run)

Hong Kong: plain 12-month momentum works without any flip (Sharpe 0.48 /
0.80 / 0.32 by sub-period, break-even 165 bp) and the VIX flip *hurts*
(0.45 / -0.55 / 0.57). Hong Kong momentum's 21-day IC stays positive in
stressed markets (0.035 vs 0.055 calm) - it does not crash the way US
momentum does. The US pattern is not automatically universal.

## Full run, 21 markets (all books staggered over 7 start days, net of local costs and taxes)

### 1. The invariant holds everywhere, in a weaker form

21-day rank IC of the momentum signals (12-1, residual, 52-week high), calm
(VIX <= 20) vs stressed (VIX > 20) markets:

- **Momentum is weaker in stress in all 21 markets** (stress minus calm IC
  -0.004 in Switzerland to -0.085 in Canada).
- It turns outright **negative** in stress in 10 of 21: Canada, Malaysia,
  Taiwan, India, Korea, UK, Germany, France, Japan, Sweden.
- It stays **positive** in stress in Hong Kong, HK H-shares, China, New
  Zealand, Thailand, Spain, Switzerland, Australia, Italy (IC +0.006 to +0.037).
- 21-day reversal is stronger in stress in 19 of 21 markets.

So the US finding ("momentum reverses in stress") is the strong end of a
universal pattern ("momentum weakens in stress"). In greater China and
Hong Kong momentum simply works through crises.

### 2. 12-month momentum is a robust signal outside the US

Same sign in all four sub-periods with |t| > 2: mom_12_1 in 15 of 21 markets
at 21 days (19 of 21 at 5 days), residual momentum 14 / 17. In the US survivor
universe it was "noise" unconditionally. Short-term reversal (rev_5d) robust
in 17 of 21 at 5 days. Low-vol and low-beta robust almost nowhere.

### 3. The momentum flip by market (Sharpe 2006-14 / 2015-20 / 2021-26)

Positive in 2006-14 in 19 of 21 markets. Consistently positive in all three:
Canada 0.70 / 0.84 / 0.58, Korea 0.67 / 0.79 / 0.19, India 0.52 / 0.90 / 0.06,
UK 0.41 / 0.51 / 0.34, Netherlands 0.47 / 0.24 / 0.40, France 0.36 / 0.16 /
0.47, Italy 0.34 / 0.48 / 0.48, Singapore 0.39 / 0.88 / 0.58, Malaysia 0.10 /
0.76 / 1.09, Australia 1.25 / 0.61 / 0.15. Fails in Hong Kong (-0.58 in
2015-20), HK H-shares, China (2015-20), Thailand, New Zealand, Spain -
exactly the markets where momentum stays positive in stress.

### 4. The honest cross-market book

Per market, choose flip or plain momentum by which was better in **2006-14
only**; equal-risk combine; report 2015-26:

| book across 21 markets | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| chosen per market on 2006-14 (15 flip, 6 plain) | 1.32 | **1.26** | **0.96** | **1.12** |
| flip in every market | 0.99 | 0.58 | 0.73 | 0.64 |
| never flip anywhere | 0.43 | 0.82 | 0.78 | 0.80 |

The 2006-14 choice picked plain momentum for Hong Kong, HK H-shares, New
Zealand, Singapore, Spain, Thailand - mostly the markets where momentum does
not crash - and the choice held up out of sample. Unit gross: ~4% a year at
3% volatility (21 nearly uncorrelated books), so ~3x gross for a 10%-vol book.

### 5. Long-only, index-hedged (where shorting is restricted)

In calm markets long the top momentum quintile, in stress long the bottom
quintile, minus the equal-weighted market: Korea 0.91 / 1.06 / 0.47, Taiwan
0.93 / 0.65 / 0.46, Singapore 0.75 / 0.83 / 1.00, Australia 1.68 / 0.99 /
0.43, India 0.65 / 0.65 / 0.44, Malaysia 0.14 / 1.11 / 1.38, UK 0.45 / 0.58
/ 0.50, Canada 0.84 / 1.05 / 0.87. Important for India (no cash shorting)
and Korea (short-sale bans). The hedge here is the equal-weight universe; a
real index future is cap-weighted - checked next.

### 6. Local volatility is a worse regime gauge than the US VIX

Using each market's own 21-day volatility above its long-run median instead
of the VIX is worse in most markets (UK 0.41 -> 0.04 in 2006-14, Australia
1.25 -> -0.15, Malaysia, Spain, Italy, NZ all worse). The global stress gauge
is the US VIX.

### 7. Asian financials: no

Financials-only books are small (10-50 names per market) and unstable:
pooled country-neutral Asian financials, momentum flip 0.02 / 0.44 / 0.05;
never flipped -0.78 / 0.52 / 0.46. Financials-only long-only versions work in
Korea, Australia, India (0.5-1.0 in 2015-26) and fail in Japan, Hong Kong,
Taiwan, Italy. Bank stocks move together on rates and credit; there is too
little cross-sectional dispersion for momentum. Not recommended as a
separate book.

### 8. Country ETFs: no

Cross-country momentum on 25 US-listed country ETFs: 0.01 / -0.52 / 0.60
plain, 0.04 / -0.23 / 0.19 flipped. Nothing.

### Data quality

99% of tickers downloaded. High share of zero-return days in Thailand (21%),
Malaysia, New Zealand (19%), Singapore (14%), Australia (13%): illiquid
names; the tradable filter drops stretches with 8 of 10 days unchanged.
Australia (267), Korea (135), New Zealand (128), India (107) have the most
>40% daily moves (small caps, rights issues); suspected bad prints that fully
reverse the next day are removed. Early-sample universes are thin in the
Netherlands (14 names in 2006) and Switzerland (16).

## Second layer (corrected: per-market choice now matched exactly; beta lag 3 days)

### Universal rules across markets (equal risk, unit gross per market; Sharpe 2006-14 / 2015-20 / 2021-26)

| all 21 markets | 2006-14 | 2015-20 | 2021-26 | 2015-26 | costs x2, 2015-26 |
|---|---|---|---|---|---|
| plain momentum | 0.43 | 0.82 | 0.78 | 0.80 | 0.63 |
| flip short in stress | 0.99 | 0.58 | 0.73 | 0.64 | 0.26 |
| **flat in stress (no position when VIX > 20)** | **1.58** | **1.19** | **1.06** | **1.13** | **0.80** |
| chosen per market on 2006-14 | 1.32 | 1.26 | 0.96 | 1.12 | 0.73 |

| Asia-Pacific (12 markets) | 2006-14 | 2015-20 | 2021-26 | 2015-26 | costs x2 |
|---|---|---|---|---|---|
| plain momentum | 0.78 | 1.18 | 1.04 | 1.11 | 0.89 |
| flip | 1.16 | 0.63 | 0.87 | 0.75 | 0.26 |
| **flat in stress** | **1.78** | **1.49** | **1.30** | **1.38** | **0.99** |
| chosen per market on 2006-14 | 1.58 | 1.77 | 1.20 | 1.46 | 1.01 |

Europe + Canada (9): flat in stress 0.68 / 0.57 / 0.48; plain 0.01 / 0.28 / 0.28.

- **Flat in stress is the right international rule**: it needs no per-market
  choice, matches the invariant (momentum weakens in stress everywhere but
  only reverses in some markets), has the lowest drawdown (-5%), and is the
  most robust to costs (0.80 at double costs vs 0.26 for the flip, which
  pays twice the turnover on each sign change).
- In the US the flip still beats flat (0.65 / 0.68 / 0.20 vs 0.22 / 0.38 /
  0.06), because US momentum genuinely reverses in stress.
- Bootstrap (21-day blocks): all-21 flat-in-stress 90% intervals [0.83,
  2.43] / [0.32, 2.02] / [0.40, 1.94]; Asia-Pacific [1.09, 2.57] / [0.60,
  2.28] / [0.59, 2.22]. Positive in every sub-period at the 99% level.
- Leave one market out: 1.02-1.19 for 2015-26 (dropping New Zealand,
  Singapore or Malaysia hurts most). Average pairwise correlation of the 21
  market books 0.15 - that is where the high combined Sharpe comes from.
- Scale: ~3% a year at 3% volatility at unit gross; a 10%-vol version needs
  ~3x gross across 21 markets.

### The survivorship trap, measured

Today's index members, equal-weighted, against their own cap-weighted index
(beta-hedged): Sharpe 1.06 / 1.20 / 1.28, **11% a year**. That is not alpha;
it is what "being in the index today" implies about the past. The long-only
momentum book hedged with the index future (1.18 / 1.33 / 1.38, 15% a year)
is almost entirely this premium and is discarded. Hedging against the
equal-weighted universe instead (both legs survivors) removes it: long-only
flat-in-stress, equal-weight-hedged, 1.64 / 1.51 / 1.13 across 21 markets,
1.86 / 1.87 / 1.50 in Asia-Pacific.

A note on direction of the bias for the momentum books: survivorship removes
the losers that kept losing, which flatters *buying* past losers (the
stressed leg of the flip) and hurts *shorting* them (the calm leg of plain
momentum). The flat-in-stress rule holds nothing in stress, so it avoids the
part of the book survivorship flatters most. A point-in-time test follows.

### Combined with the US book (equal-risk sleeves, 25% cap, 10% vol)

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | ret/yr | worst DD | worst month |
|---|---|---|---|---|---|---|---|
| ETF sleeves alone | 0.87 | 0.85 | 0.96 | 0.90 | 9.5% | -15.0% | -8.2% |
| US book (ETF + pairs x2 + US flip) | 1.15 | 1.19 | 0.98 | 1.09 | 11.1% | -11.9% | -6.8% |
| **US book + international flat-in-stress** | **1.48** | **1.49** | **1.11** | **1.30** | 10.7% | **-9.9%** | **-5.4%** |

The international sleeve correlates 0.28 with the US flip (same VIX trigger)
and ~0 with the ETF book and pairs.

### Point-in-time membership test (NIFTY 50, DAX)

Membership was rebuilt on every date from the Wikipedia change tables, with
names resolved to Yahoo tickers. Resolved: 73/95 NIFTY names and 29/48 DAX
names. Former members with no price history stay unresolved and are counted
as missing:
- NIFTY: 2-6 of 50 missing per year in 2006-14, 0-4 after 2015.
- DAX: 4-8 of ~38 missing in 2000-07, 0-1 after 2012.

Net Sharpe, today's members vs point-in-time members:

| book | survivors 2006-14 | PIT 2006-14 | survivors 2015-26 | PIT 2015-26 |
|---|---|---|---|---|
| NIFTY plain | -0.05 | 0.19 | 0.19 | 0.01 |
| NIFTY flip VIX>20 | 0.16 | 0.26 | 0.72 | 0.78 |
| NIFTY flat in stress | 0.12 | 0.39 | 0.57 | 0.47 |
| DAX plain | -0.15 | -0.10 | 0.10 | 0.26 |
| DAX flip VIX>20 | 0.37 | 0.23 | -0.06 | 0.06 |
| DAX flat in stress | 0.25 | 0.12 | 0.06 | 0.26 |

Survivorship does not systematically inflate the momentum books. The
changes go both ways and are about the size of the noise in a ~40-name
single-market book. The regime rules (flip, flat) keep their ranking against
plain under point-in-time membership in both markets out of sample.

Caveats:
- Only two indices were tested.
- The names still missing are exactly the delisted and acquired companies,
  whose effect cannot be measured with free data.
- The stronger survivorship result is the earlier one: the 11%/yr
  equal-weight-vs-index premium. That bias lives in the hedge, not in the
  momentum ranking.

### Asian financials, pooled and country-neutral (first full pass)

Universe: 211 index-member financials across 11 Asia-Pacific markets
(median 186 tradable since 2015). Signals are z-scored within each market's
financials, and returns are measured relative to that market's financials
average.

Stock selection, ICs:
- Short-term reversal has by far the strongest IC: rev_5d at 5 days 0.044
  (t 11.6). But it decays in every period (0.065, 0.047, 0.038, 0.016), and
  the rev_5d and rev_21d books lose money after costs and next-open
  execution: -1.04 and -0.80 Sharpe in 2015-26.
- Residual momentum has a positive IC in all four IC periods (21-day 0.015 /
  0.003 / 0.047 / 0.023). The momentum books still fail the 2006-14
  selection test: plain -0.60, flat -0.25, flip 0.13. Out of sample: plain
  0.44, flat 0.64, flip 0.41.
- Size (small minus big, by ADV) and Amihud illiquidity are positive in all
  three periods: size 0.21 / 0.95 / 0.38, Amihud 0.36 / 1.14 / 0.38. But they
  earn only 2-3%/yr. They are also the signals survivorship flatters most:
  the small, illiquid financials that are still in an index today are the
  ones that did not fail. I would not trade these without point-in-time data.

Sector timing (financials minus their market over the next 21 days; linear
model on VIX, VIX change, term spread and the sector's own trend; fit on
2004-14):
- Out-of-sample correlation 0.076, hit rate 53.7%.
- Timing book: 0.26 / 0.62 / -0.01.
- Not usable. The sign of the sector's relative return is rate-driven:
  financials badly lag 2015-20 (-1.74 Sharpe when held against the market)
  and lead 2021-26 (+0.76). The model had no real rate series, because the
  cached macro file lacks a 10-year yield. That is the next thing to fix.

## Third layer: 20 new exchanges and every listed Asia-Pacific financial

### Data added

- `deep_universe.py`: Yahoo equity screener by region and industry.
  - 1,341 Asia-Pacific financials across 12 markets, one line per company,
    split into 14 industries (regional and diversified banks; life, P&C and
    other insurers; capital markets; credit services; ...).
  - 1,976 names in 20 exchanges never used before:
    - Emerging: Indonesia, Vietnam, Pakistan, Brazil, Mexico, Chile, South
      Africa, Turkey, Saudi Arabia, Kuwait, Qatar, Poland, Greece.
    - Developed: Israel, Norway, Denmark, Finland, Belgium, Austria, Portugal.
  - Foreign lines (BDRs, Mexico's SIC, Thai DRs, Vienna's global segment)
    are removed.
  - The Philippines has no Yahoo price history and is not covered.
- `macro_data.py`: OECD 10-year and 3-month rates for 30 countries (FRED),
  each used only from the 15th of the following month; US 10y/2y daily; 31
  USD crosses.
- Frictions for the new markets were added to `intl_lab.FRICTIONS`. These are
  rough, and the stamp or transaction taxes are included.

### Pre-registered test (written before any new-market result was seen)

The rule is fixed by the first 21 markets: momentum composite, 21-day
rebalance, 7 staggered cohorts, next-open execution, local costs, and no
position while the US VIX is above 20 ("flat in stress").

Predictions for the 20 new exchanges:
1. The momentum IC is lower in stress than in calm in at least 14 of the 20.
2. The equal-risk flat-in-stress book across the 20 has a positive Sharpe in
   both 2015-20 and 2021-26.
3. Over 2015-26 it beats the never-flipped (plain) book.

If prediction 2 fails, the 21-market result was partly luck in which markets
were chosen.

### Result of the pre-registered test: all three predictions pass

| prediction | outcome |
|---|---|
| momentum IC weaker in stress in at least 14 of 20 | **20 / 20** weaker (negative in stress only in Brazil) |
| flat-in-stress positive in 2015-20 and 2021-26 | **2.10 and 2.19** |
| flat beats plain over 2015-26 | **2.13 vs 1.64** |

Equal-risk books over the 20 new exchanges (net of local costs):

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | ret/yr | maxDD |
|---|---|---|---|---|---|---|
| plain | 1.39 | 1.14 | 2.39 | 1.64 | 4% | -8% |
| flip VIX>20 | 0.85 | 1.64 | 0.66 | 1.23 | 3% | -11% |
| **flat in stress** | **1.39** | **2.10** | **2.19** | **2.13** | 3% | -3% |
| flat, costs x2 | 1.13 | 1.61 | 1.59 | 1.59 | 3% | -4% |
| long-only flat, EW-hedged | 1.40 | 1.99 | 2.09 | 2.03 | 3% | -3% |
| original 21, flat (for comparison) | 1.58 | 1.19 | 1.06 | 1.13 | 3% | -5% |
| **all 41, flat** | 1.43 | 1.69 | 1.67 | 1.68 | 3% | -3% |

- Emerging (13) 0.90 / 1.57 / 1.88; developed (7) 1.18 / 1.95 / 1.58.
- The bootstrap 5th percentile is above 0 in every period (2015-26: [1.57, 2.74]).
- Leave one out: 2.00-2.27. Kuwait is the only market with a negative
  book (-0.48), and dropping it raises the total.
- Moving the VIX trigger (not pre-registered) changes little: 17.5 / 25 /
  30 give 1.94 / 2.00 / 1.81.
- Average pairwise correlation among the 20 is 0.02, so the high aggregate
  Sharpe is diversification across many ~0.6-Sharpe books. The 20 correlate
  0.46 with the original 21.
- The flip, which won in the US, loses to flat here as well, and it is the
  most cost-sensitive (0.55 at double costs).

### Why I don't believe the 2.1, and what survives

`new_exchanges_robust.py`:
- **Not a stale-price artefact.** Executing one day later than allowed
  gives the same result (2.11 vs 2.13). Stale opens are 1-9% of days.
- **Both legs earn.** Against the equal-weighted market, the long leg makes
  +1.9%/yr (Sharpe 2.8) and the short leg +2.1%/yr (2.1). Selecting on
  today's size biases *against* the short leg (the shorted losers in the
  sample are the ones that recovered), so survivorship is unlikely to
  explain the short leg's profit.
- **Costs are the real risk.** At triple costs the book drops to 1.04 (all
  20) and 1.33 (14 borrowable). The 6 markets where single stocks cannot be
  borrowed (Indonesia, Vietnam, Pakistan, Saudi Arabia, Kuwait, Qatar) earn
  0.96 at normal cost, 0.02 at triple cost, and 0.02 in 2006-14. **Only the
  14 borrowable markets are tradable as long/short:** 1.99 / 2.23 / 2.11,
  and 1.33 at triple cost.
- **Liquid half only:** 1.73 (all 20), 1.50 (14 borrowable).
- **Capacity is small.** Holding at most 10% of a day's traded value per
  name in the liquid half gives roughly $376M gross across all 20, mostly
  in Brazil ($104M), Turkey ($88M), South Africa and Saudi Arabia (~$36M
  each). The Nordics, Poland, Greece and Chile are $0.3-7M each. This is a
  personal-account strategy, not a fund strategy.

My honest estimate for the 14 borrowable markets after real-world
slippage is a Sharpe of about 1, not 2.

### Combined with the US book (same blend as before: inverse vol, 25% cap, 10% vol)

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | ret/yr | maxDD | worst month |
|---|---|---|---|---|---|---|---|
| US book | 1.15 | 1.19 | 0.98 | 1.09 | 11.1% | -11.9% | -6.8% |
| US + original 21 | 1.48 | 1.49 | 1.11 | 1.30 | 10.7% | -9.9% | -5.4% |
| **US + original 21 + new 20 (separate sleeves)** | **1.81** | **1.97** | **1.67** | **1.83** | 10.0% | -7.9% | -3.8% |
| US + all 41 as one sleeve | 1.31 | 1.58 | 1.19 | 1.40 | 11.0% | -8.7% | -4.0% |

Treat this with the same discount as above. The new-20 sleeve gets a 25%
weight because its measured volatility is tiny, and it is the sleeve most
likely to be worse live (costs, capacity, borrow).

### Every listed Asia-Pacific financial (`asia_fin_deep.py`)

Coverage: 1,341 names with prices, 11 markets (New Zealand's 9 dropped);
median tradable 2015-26: Japan 152, India 155, Hong Kong 139, Australia 122,
China 99, Indonesia 75, Korea 73, Taiwan 48, Malaysia 30, Thailand 20,
Singapore 15.

Stock selection, pooled 21-day ICs (country-neutral):

| signal | IC | t | sign kept in all 4 periods | calm / stress |
|---|---|---|---|---|
| low_vol | 0.072 | 9.7 | yes | 0.075 / 0.066 |
| max_effect (avoid lottery stocks) | 0.058 | 10.2 | yes | 0.059 / 0.057 |
| high_52w | 0.045 | 6.0 | yes | 0.058 / 0.024 |
| mom_12_1 | 0.032 | 5.1 | yes | 0.041 / 0.017 |
| low_beta | 0.032 | 3.6 | yes | 0.042 / 0.014 |
| rev_5d | 0.020 | 3.9 | yes | 0.013 / 0.032 |
| size_proxy (small minus big) | **-0.019** | -2.9 | yes | |
| amihud (illiquid minus liquid) | **-0.029** | -4.7 | yes | |

- **The size and illiquidity "premia" from the index-only pass reverse.**
  They are negative in all four periods in the full listing, so the earlier
  positive result (size 0.69, Amihud 0.82 out of sample) was survivor
  selection, as suspected. Do not trade them.
- Low vol and MAX are the strongest and most stable signals in financials.
  Survivorship biases *against* them (the volatile names that blew up are
  missing), so they are probably understated. They are much weaker in the
  21 index universes (robust in only 3 and 2 markets), so the effect lives
  in the smaller, volatile names. Those are hard to short in Asia, which
  makes avoiding them (a long-only filter) the natural use; tested below.
- Industry-neutral scoring changes little.

Books (net, liquid half unless stated):
- Momentum, flat in stress: 0.22 / 0.90 / 0.95 (2015-26 0.92). Flip: 0.08 /
  1.01 / 0.37. Plain: 0.04 / 0.27 / 0.83.
  - Using all names makes every version worse (flat 0.45): the illiquid half
    costs more than it adds.
  - The rule's out-of-sample ordering (flat > flip > plain) holds again, but
    2006-14 is weak in financials specifically.
- Low vol: 0.80 / 0.19 / 0.98. MAX: 0.33 / 0.19 / 0.58. The low_beta book is
  flat (~0).
- Reversal books lose money after costs, despite positive ICs (rev_5d
  -0.47).
- Industry momentum (29 market x industry baskets): 0.70 in 2006-14, then
  about 0. It is dead.
- Lead-lag (big financials leading small ones in the same market and
  industry):
  - The pure lead signal (the big basket's past day) has IC 0.004, which is
    nothing.
  - "Big basket's 5-day return minus own 5-day return" has IC 0.034 (t 13.6)
    at 5 days. But that is mostly the stock's own short-term reversal, and
    it decays from 0.042 to 0.024.
  - The 21-day-hold book: 0.57 / 0.93 / -0.58. Not usable.

Rates (each group's return minus its market's, next 21 days):
- Lagged rate signals predict nothing. Univariate correlations are 0.02-0.07
  and unstable; the pooled 2004-14 model has out-of-sample correlation of
  -0.01 to 0.01; the timing books earn about 0.
- **A stable exposure, not a forecast.** Since 2015, Asian banks rise
  against their market when US 10-year yields rise, in every market and in
  both sub-periods. The move is about +2% to +10% relative return per
  +100bp, measured over 21-day windows: Japan +7.9% / +3.6%, Korea +10.5% /
  +6.0%, Hong Kong +4.3% / +4.7%. Before 2015 it was mixed and near zero.
  That is useful for hedging a financials book's rate exposure (or for
  expressing a rate view through banks), but it gives no timing edge.

### Pre-registered: a lottery filter for the long-only book (written before running)

Motivation: in Asian financials, low vol and MAX are the most stable signals
(ICs 0.07 / 0.06, same sign in all four periods), but the volatile names
they penalise cannot be shorted in most of Asia. So the test is to *avoid*
them.

Specification:
- Before picking the top momentum quintile in the long-only flat-in-stress
  book, drop every name in its market's top 30% by 63-day volatility or by
  21-day maximum daily return.
- The hedge is unchanged: the equal-weighted universe.
- Run on three universes: the original 21, the 20 new exchanges, and the
  pooled Asian financials (liquid half).

Prediction: the filtered book has a higher 2015-26 Sharpe than the
unfiltered one in all three universes, and a maxDD that is no worse.

**Result: the prediction fails.** The lottery filter hurts the momentum book
in both broad universes:

| universe | unfiltered | filtered | markets where the filter helps |
|---|---|---|---|
| original 21 (2006-14 / 2015-26) | 1.64 / 1.30 | 0.69 / 0.23 | 2 of 21 |
| 20 new exchanges | 1.40 / 2.03 | 0.56 / 0.78 | 1 of 20 |
| Asia-Pacific financials, liquid half | -0.22 / 0.39 | -0.70 / 0.77 | - |

The filter helps only in Asian financials after 2015, and hurts there in
2006-14. Momentum winners are often the volatile names, so filtering them
out removes much of the premium. **Don't use it.**

A post-hoc diagnostic hedging with the trailing beta (applied only while
invested) gives the same ranking: filtered 1.24 vs unfiltered 1.70 on the
original 21, and 2.17 vs 2.88 on the new 20. But it also inflates *every*
book (unfiltered 1.30 → 1.70) because the beta is below 1. That leaves the
book net long a survivor-only universe, which drifts upward in-sample (the
same survivor premium as before). Beta-hedged numbers on survivor universes
are not trustworthy. The 1:1 equal-weight hedge remains the honest
construction.

### The conservative combined number (`conservative_combo.py`)

Assumptions:
- Only the 14 borrowable new exchanges are used.
- Every international market is charged **double** its estimated costs.
- The blend is unchanged.

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | ret/yr | vol | maxDD | worst month |
|---|---|---|---|---|---|---|---|---|
| US book | 1.15 | 1.19 | 0.98 | 1.09 | 11.1% | 10.2% | -11.9% | -6.8% |
| US + original 21 (costs x2) | 1.40 | 1.40 | 1.02 | 1.21 | 10.0% | 8.2% | -10.1% | -5.5% |
| US + original 21 + 14 new (costs x1) | 2.08 | 2.02 | 1.70 | 1.87 | 10.8% | 5.8% | -8.6% | -4.0% |
| **US + original 21 + 14 new (costs x2)** | **1.87** | **1.80** | **1.42** | **1.62** | 9.4% | 5.8% | -9.1% | -4.1% |
| US + 35 markets as one sleeve (costs x2) | 1.43 | 1.50 | 1.10 | 1.31 | 10.5% | 8.0% | -9.5% | -4.5% |

Sleeves alone at double costs:
- original 21: 1.20 / 0.87 / 0.74
- 14 new: 1.65 / 1.86 / 1.63

Realised volatility (5.8%) sits below the 10% target because the 3x
leverage cap binds. The international sleeves run at about 2% volatility at
unit gross. Capacity (see above) limits this to a small account.

### Breadth check (`breadth_check.py`)

The original 21 are index large caps (20-60 names in most of Europe); the
new exchanges are the 120 largest companies. Restricting each new exchange
to its 30 largest:

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| new 20, all 120 | 1.39 | 2.10 | 2.19 | 2.13 |
| new 20, largest 30 | 0.90 | 1.82 | 1.30 | 1.58 |
| 14 borrowable, all 120 | 1.99 | 2.23 | 2.11 | 2.17 |
| 14 borrowable, largest 30 | 1.63 | 1.82 | 1.02 | 1.46 |

Breadth explains part of the gap: mid caps add momentum, as in the
literature. Even large caps alone (1.46-1.58) beat the original 21 (1.13).
The rest is diversification: the 20 new books correlate 0.02 on average,
against 0.15 among the original 21.

### Survivorship, calibrated by simulation (`survivorship_sim.py`, 32 markets)

Setup:
- Each synthetic market has 600 stocks and zero momentum by construction.
- Market and idiosyncratic volatility follow the real VIX path, with
  Student-t shocks.
- Half the stocks list on random dates.
- A stock dies after a 90% fall from its peak; the crash day is recorded.
- The universe is the 120 largest stocks alive at the end, the screener's
  construction. The books are the same, gross of costs.

Mean 2015-26 Sharpe per simulated market:

| book | today's 120 largest survivors | all stocks, point in time | paired bias (± s.e.) |
|---|---|---|---|
| plain | -0.30 | -0.08 | **-0.22 ± 0.06** |
| flat in stress | -0.23 | -0.07 | **-0.16 ± 0.06** |
| flip | -0.01 | -0.02 | +0.02 ± 0.05 |

**Selecting on today's size biases momentum *down*, by about 0.15-0.2 of
Sharpe per market.** Losers that later recovered make it into the
universe and hurt the short leg, and losers that died are missing. The flip
is unbiased because its stressed leg *buys* losers, which the same
selection flatters. The point-in-time universe stays near zero, as it
should.

So the momentum results on the screener universes are, if anything,
understated by this mechanism. The simulation does not cover other
survivorship channels, such as index additions or data vendors dropping
dead tickers entirely. Together with the point-in-time rebuild (NIFTY,
DAX: no systematic effect), survivorship is not the explanation for the
momentum results.

### Pre-registered: pairs trading inside Asia-Pacific financials (written before running)

The rule is the US pairs sleeve's rule, unchanged:
- Each year, take the 5 most correlated pairs (daily returns over the past
  252 days, correlation > 0.6) inside each market x industry group (banks,
  insurance, capital markets, credit).
- Use only the liquid half of each market at the formation date.
- Trade the log-price spread on a 60-day z-score: enter at |z| > 2, exit at
  |z| < 0.5 or after 21 days.
- Execute at the **next open**, net of local costs.
- Weight pairs equally within each market, and markets equal-risk.

Prediction: a positive net Sharpe in both 2015-20 and 2021-26. The
same-close version (the US convention) is reported for comparison only.

**Result: pairs in Asian financials fail.** Net, next-open execution,
equal-risk across 11 markets: 0.39 / **-0.62 / -0.85**. The same-close
version is no better (0.57 / -0.51 / -0.72), and doubling in stress does not
help (-0.61 / -0.63). The bootstrap puts 2021-26 below zero with 98%
probability. By market, 2015-26:
- mildly positive: Japan 0.22, Australia 0.23, Indonesia 0.37;
- clearly negative: Taiwan -1.11, Hong Kong -0.71, Korea -0.53, Thailand
  -0.51.

The relative-value edge between Asian financials has gone since 2015: the
spreads keep diverging instead of reverting.

### Check on the US book: does Arjun's pairs sleeve survive next-open execution?

`strategies.pairs_strategy` trades at the same close that produced the
z-score. `us_pairs_execution.py` reruns the identical rule (same clusters,
formation and costs). The same-close rerun matches strategy_returns.csv
with correlation 0.997.

| US pairs | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| same close (original) | 0.85 | 0.79 | 0.77 | 0.77 |
| next open | 0.63 | 0.78 | 0.72 | 0.74 |
| one day late (close of i+1) | 0.42 | 0.66 | 0.53 | 0.60 |

The US pairs edge is robust to execution, losing about a quarter of its
Sharpe with a full day's delay. The conservative combined book is unchanged
with next-open pairs: 1.75 / 1.78 / 1.48 (2015-26 1.64 vs 1.63). So US
pairs work and Asian-financials pairs do not. That is a real difference
between markets, not an execution artefact.

### Year by year: US book vs the conservative combined book (sum of daily returns, %)

| year | US book | US + original 21 + 14 new, costs x2 |
|---|---|---|
| 2007 | 7.0 | 5.3 |
| 2008 | 16.5 | 18.5 |
| 2009 | 24.4 | 17.7 |
| 2010 | 7.1 | 4.4 |
| 2011 | 4.8 | 6.0 |
| 2012 | 12.7 | 8.9 |
| 2013 | 20.2 | 18.0 |
| 2014 | 3.8 | 5.6 |
| 2015 | 8.6 | 18.5 |
| 2016 | -1.0 | **-4.4** |
| 2017 | 22.9 | 11.6 |
| 2018 | -2.4 | 1.9 |
| 2019 | 19.9 | 9.3 |
| 2020 | 27.1 | 29.8 |
| 2021 | 11.8 | 12.3 |
| 2022 | -7.4 | **-3.0** |
| 2023 | 13.0 | 5.3 |
| 2024 | 16.1 | 17.9 |
| 2025 | 12.4 | 6.7 |
| 2026 (to Oct) | 9.7 | 4.2 |

The combined book has two losing years (2016, 2022) against three for the
US book. It gives up some of the strong US years (2017, 2019, 2023) in
exchange for smaller losses. Its biggest years, 2008-09 and 2020, are crisis
and rebound years, as in the US work, so a large share of the long-run
return depends on such episodes recurring. 2016 is the international
sleeve's worst year.

### Pre-registered: broad Asia-Pacific universes (written before running)

New data: the 400 largest domestic companies by market cap on each major
Asia-Pacific exchange (Japan, Korea, Taiwan, Hong Kong, China, India,
Australia; Singapore, Malaysia and Thailand up to what the screener has),
from the Yahoo screener. The original Asia-Pacific universes were index
large caps.

The rule is unchanged (flat in stress).

Prediction:
- The equal-risk book over these broad universes has a positive Sharpe in
  2015-20 and 2021-26.
- Its 2015-26 Sharpe is at least the index version's (1.38 for the 12
  Asia-Pacific index universes), because mid caps add momentum, as on the
  new exchanges.

**Result: passes, narrowly.** Flat in stress, equal-risk, on the 10
Asia-Pacific markets that have both a broad and an index universe:

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 |
|---|---|---|---|---|
| broad top 400: flat in stress | 2.14 | 1.53 | 1.34 | **1.42** |
| index members, same 10 markets: flat | 1.76 | 1.32 | 1.19 | 1.24 |
| broad, liquid half | 2.09 | 1.79 | 1.44 | 1.58 |
| broad, liquid half, costs x2 | 1.78 | 1.42 | 1.15 | 1.26 |
| index, liquid half, costs x2 | 0.86 | 0.62 | 0.95 | 0.79 |
| broad: plain / flip | 1.50 / 1.59 | 0.87 / 1.12 | 1.21 / 0.75 | 1.05 / 0.94 |

- Both test periods are positive, with bootstrap 5th percentiles of 0.60
  and 0.63.
- 2015-26 is 1.42, against 1.38 for the 12 index universes and 1.24 for the
  same 10.
- Breadth helps most in India (1.35 vs 0.57) and Malaysia (1.53 vs 0.70),
  and in the liquid half at double costs (1.26 vs 0.79).
- Japan's momentum is about zero in either version (0.12 / 0.13). That is
  consistent with the long-standing finding that momentum does not pay in
  Japan; a Japan sleeve adds nothing but costs.
- Singapore's broad universe is mostly tiny names: the full universe gives
  0.09, the liquid half 1.29.
- Flat beats flip again (1.42 vs 0.94).

## Fourth layer: South America

### Data

`south_america_universe.py`:

| universe | names | notes |
|---|---|---|
| Brazil | 296 | the 400 largest domestic listings, collapsed to one line per company; BDRs and real-estate/investment funds removed |
| Chile | 62 | every domestic listing in the screener |
| Argentina | 62 | every listing with peso accounts (CEDEARs drop out) |
| Colombia | COLCAP, 20 companies | one share class each, the most traded |
| Peru | S&P/BVL Peru General, ~36 companies | one share class each, the most traded |
| South American financials | 74 | by industry |
| South American companies listed in New York | 61 | hand list, 18 financials |

- The screener has nothing for Colombia, Peru or Venezuela. Venezuela is
  left out.
- Brazil (as the top 120) and Chile were already among the 20 new
  exchanges, so they are **not** fresh out-of-sample. Argentina, Colombia,
  Peru, the broader Brazil and the New York ADR set are.
- Colombia and Peru are tiny (20-36 names), so their single-market books
  will be noisy.
- Costs: the same tiered spreads (10/20/40 bp for Argentina, Colombia and
  Peru; 4/8/15 for the ADRs). Within-market terciles probably understate
  the cost of Brazil's smallest names, so the liquid half and multiplied
  costs are reported.

### Pre-registered predictions (written before any South American result was seen)

The rule is unchanged: flat in stress (no position while the US VIX is
above 20), monthly, staggered, next-open, local costs.

1. Momentum's IC is lower in stress than in calm in all 5 local markets
   (Brazil broad, Chile, Argentina, Colombia, Peru).
2. The equal-risk flat-in-stress book over the 5 is positive in both
   2015-20 and 2021-26.
3. It beats plain momentum over 2015-26.
4. The same rule on the New York ADR set (one cross-section, USD,
   borrowable) has a positive 2015-26 Sharpe.

Not predicted:
- **South American financials:** no special edge expected (Asia found
  none); descriptive only.
- **Commodity lead-lag:** expected to show **no** tradable edge at 1-5 day
  horizons, because US commodity futures settle before São Paulo, Santiago
  and Lima close. An IC above 0.02 with t > 3 in both halves would surprise
  me.

### Results (`south_america.py`)

**All four predictions pass, but this is the weakest region so far, and
only part of it is tradable.**

| prediction | outcome |
|---|---|
| momentum weaker in stress in all 5 | **5 / 5**; none turns negative in stress |
| 5-market flat book positive in 2015-20 and 2021-26 | **0.75 and 1.43** (bootstrap: 8% chance 2015-20 is below 0) |
| flat beats plain over 2015-26 | **1.11 vs 0.98**, narrowly |
| ADR flat book positive over 2015-26 | **0.41** (country-neutral 0.57), but weak: the bootstrap gives a 26% / 12% chance that 2015-20 / 2021-26 is below 0 |

Momentum IC calm / stress: Brazil 0.082 / 0.062, Chile 0.073 / 0.021,
Argentina 0.037 / 0.021, Colombia 0.073 / 0.032, Peru 0.039 / 0.019, ADRs
0.039 / 0.003.

Books, net Sharpe:

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | maxDD 15-26 |
|---|---|---|---|---|---|
| 5 markets: plain | 1.14 | 0.33 | 1.60 | 0.98 | -18% |
| 5 markets: flip | 0.79 | 0.77 | 0.63 | 0.70 | -13% |
| **5 markets: flat in stress** | **1.09** | **0.75** | **1.43** | **1.11** | -10% |
| 5 markets: flat, costs x2 / x3 | 0.93 / 0.77 | 0.39 / 0.03 | 1.13 / 0.83 | 0.78 / 0.46 | |
| 5 markets: flat, liquid half | 0.88 | 1.10 | 0.88 | 0.99 | -9% |
| 5 markets: flat, one day late | 1.08 | 0.80 | 1.44 | 1.14 | -10% |
| 3 fresh (Argentina, Colombia, Peru): flat | 0.50 | 0.70 | 0.35 | 0.50 | -9% |
| 3 fresh: flat, costs x2 / x3 | 0.35 / 0.21 | 0.40 / 0.09 | 0.11 / -0.12 | 0.24 / -0.02 | |
| Brazil + Chile: flat | 1.17 | 0.31 | 1.97 | 1.13 | -17% |
| ADRs (58 NY listings), pooled: flat | 0.65 | 0.30 | 0.55 | 0.41 | -25% |
| ADRs, country-neutral: flat | 0.31 | 0.28 | 0.88 | 0.57 | -17% |
| ADRs, country-neutral: flat, costs x3 | 0.16 | 0.14 | 0.74 | 0.43 | |

What to make of it:
- **Brazil's edge is in its small names.**
  - Broad (296 names) flat in stress: 0.97 over 2015-26.
  - Its 120 largest only: 0.30. The earlier top-120 universe: 0.18.
  - Liquid half: 0.55.
  - Small Brazilian stocks are exactly where the tiered cost model (5-20
    bp) is least trustworthy (27% of stock-days have zero volume), so most
    of the 0.97 should be treated as unproven. The 2015-20 weakness (0.28)
    is Brazil's 2015-16 recession.
- **Argentina, Colombia and Peru are not tradable as local long/short.**
  - Shorting is impractical in all three.
  - The books are small (median 54, 18 and 17 names).
  - Peru's data is stale: 33% zero-return days.
  - Their edge disappears at triple costs (-0.02).
- **The ADR route works on paper but adds nothing.** The ADR book is
  real-money tradable (USD, borrowable, costs x3 still 0.43
  country-neutral), but at 7-11% volatility and ~0.4-0.6 Sharpe it is a
  weak sleeve. Added to the conservative combined book at double costs, it
  *lowers* the Sharpe (2015-26 1.62 → 1.56; worst month -4.1% → -5.6%),
  because it correlates about 0.2 with the international sleeves and is
  noisy. **Don't add it.**
- Both legs earn; the short leg earns slightly more (5 markets: long 1.14,
  short 1.39 against the equal-weighted market). Executing a day late
  changes nothing.
- Leave one out (2015-26): 0.76 (without Brazil) to 1.15 (without Peru).
  Brazil carries the region.

**South American financials** (Brazil 26, Chile 15, Argentina 10; Colombia
and Peru have too few names): pooled momentum IC 0.06 (t 3.2), and
low-vol / MAX ICs of about 0.045, all with the same signs as in Asia. But
with a median of 34 names the books are weak (flat in stress 0.51 / 0.14 /
0.59). There is no special edge, as expected.

**Commodity lead-lag: no edge, as predicted.**
- The commodity-implied move (trailing betas to copper, oil, gold, silver,
  soybeans, coffee and sugar, times the commodities' returns) has an IC of
  about 0 at 1 day and is slightly *negative* at 5 days (-0.010).
- "Implied minus own 5-day return" scores 0.028 at 5 days. But the control,
  the stock's own 5-day reversal alone, scores 0.032. The commodity part
  adds nothing; it is short-term reversal.
- As expected, South American prices already contain the day's commodity
  move by their close.
