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
