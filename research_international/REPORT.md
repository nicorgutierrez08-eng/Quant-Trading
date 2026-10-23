# International extension: 41 exchanges and every listed Asia-Pacific financial

*Written 23-24 October 2026. This is a separate model from Arjun's US work
and from `research_night/`, and it changes none of their code. The running
log with every intermediate number, including the dead ends, is `LOG.md`.
The code is in `code/` and the result tables are in `reports/`.*

The question: the US finding was "12-month momentum pays when the VIX is
low and crashes when it is high". Does it hold on other exchanges, and in
Asian financials in particular? If it does, how should it be traded?

Same discipline as the US work:
- 2006-14 is for choosing; 2015-20 and 2021-26 are for checking.
- Every book is averaged over 7 staggered start days of the monthly cycle.
- Trades execute at the next open.
- Costs are local: spread tiers by liquidity, plus stamp/transaction taxes,
  plus 1 bp slippage.
- The 20 new exchanges were tested against predictions written down before
  their results were seen.

## The short version

1. **"Momentum weakens when the VIX is high" is a property of stock markets,
   not of the US.**
   - In each of 41 markets, the IC of 12-month momentum is lower when the
     US VIX is above 20 than when it is below.
   - That covers the original 21 and all 20 new exchanges, and the 20 were
     a pre-registered test.
   - It turns negative in 11 of the 41. The US is the extreme case: there it
     reverses hard.
2. **Outside the US the right trade is to step aside, not to flip.**
   - The book holds momentum when the VIX is at or below 20 and holds
     nothing above it.
   - Flipping short, which is best in the US, loses to stepping aside in
     every group of markets, and it is twice as cost-sensitive.
   - Nothing in the rule is fitted.
3. **The out-of-sample test passed, by more than I expected.** On the 20
   exchanges never used to build the rule, all three pre-registered
   predictions held:
   - Momentum is weaker in stress in 20 of 20.
   - The book is positive in both test periods: 2.10 and 2.19.
   - It beats plain momentum: 2.13 vs 1.64 over 2015-26.
4. **But the 2.1 is not a number to plan on.** It comes from 20
   near-uncorrelated books (average pairwise correlation 0.02), each worth
   about 0.6, at about 2% volatility each. The checks:
   - Six markets cannot be shorted, and there the book earns nothing at
     realistic costs.
   - At triple costs the tradable 14 fall to 1.33.
   - Capacity is a few hundred million dollars at most, mostly Brazil and
     Turkey.
   - My honest estimate for the tradable version is a Sharpe around 1.
5. **Added to the US book, the conservative version still helps a lot.**
   Using only borrowable markets, every international cost doubled, and the
   blend unchanged:
   - Sharpe 1.87 / 1.80 / 1.42 in 2006-14 / 2015-20 / 2021-26, against 1.15
     / 1.19 / 0.98 for the US book alone.
   - 9.4% a year, maxDD -9.1%, worst month -4.1%.
6. **Asian financials have no special edge.** Across every listed
   Asia-Pacific financial (1,341 names):
   - The same flat-in-stress momentum book works modestly in the liquid
     half: 0.92 over 2015-26. It is weak in 2006-14 (0.22).
   - The strongest stock-selection signals are low volatility and avoiding
     lottery stocks. But they live in names that cannot be shorted, and
     using them as a long-only filter was tested and **failed**.
   - Rates do not time the sector.
   - What is stable is an exposure: since 2015, Asian banks gain 2-10%
     against their market per +100bp on the US 10-year, in every market.
7. **Survivorship.** Every universe here is "listed today", which biases
   the results. Measured three ways (point-in-time rebuild, synthetic
   markets, breadth check), it does not explain the momentum results. In
   simulation, selecting today's largest survivors *lowers* momentum Sharpe
   by about 0.15-0.2 per market. It
   *does* explain two things that looked like edges:
   - the equal-weight-vs-index "premium" (11% a year);
   - the small-cap and illiquidity premia in financials, which reverse sign
     once the full listing is used.
   Details below.

## 1. Data

| set | names | markets | source |
|---|---|---|---|
| index members (first pass) | 1,760 (308 financials) | 21: 12 Asia-Pacific, 8 Europe, Canada | Wikipedia constituent lists (Japanese and Chinese Wikipedia for Nikkei 225 and Taiwan 50) |
| new exchanges | 1,976 | 20: Indonesia, Vietnam, Pakistan, Brazil, Mexico, Chile, South Africa, Turkey, Saudi Arabia, Kuwait, Qatar, Poland, Greece, Israel, Norway, Denmark, Finland, Belgium, Austria, Portugal | Yahoo equity screener, 120 largest domestic companies; Wikipedia KSE-100; hand lists for Vietnam and Austria |
| Asia-Pacific financials | 1,341, by industry | 12 | Yahoo screener by region and industry |
| rates, FX | 87 series | 30 countries | FRED (OECD 10y and 3m, monthly, used from the 15th of the next month; US 10y/2y daily), Yahoo FX |
| prices | daily OHLCV 2000-2026 | | Yahoo, adjusted for dividends and splits |

How the universes were cleaned:
- Foreign cross-listings are removed by requiring local-currency accounts:
  Brazilian BDRs, Mexico's SIC, Thai DRs, and Vienna's global segment
  (which is why Austria is a hand list).
- Dual share classes are collapsed to one line per company.
- The Philippines is missing because Yahoo has no prices for it.

## 2. The invariant

21-day rank IC of the momentum signals (12-1 month, residual, 52-week high)
when the US VIX is at or below 20 ("calm") and above 20 ("stress"):

| | weaker in stress | negative in stress |
|---|---|---|
| original 21 | 21 / 21 | 10 / 21 |
| new 20 (pre-registered) | 20 / 20 | 1 / 20 (Brazil) |

Momentum keeps working through stress in Hong Kong and China, Australia,
New Zealand, Thailand, southern Europe and most emerging markets. It
reverses in Canada, Malaysia, Taiwan, India, Korea, the UK, Germany,
France, Japan and Sweden. 12-1 month momentum by itself is a robust signal
in 15 of the original 21 markets (same sign in all four sub-periods,
|t| > 2), unlike in the US survivor universe.

Local volatility indices (India VIX, Australia's A-VIX) make worse regime
gauges than the US VIX.

## 3. The books

Net Sharpe, equal-risk across markets (inverse trailing volatility):

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | maxDD 15-26 |
|---|---|---|---|---|---|
| original 21: plain momentum | 0.43 | 0.82 | 0.78 | 0.80 | -8% |
| original 21: flip (short when VIX > 20) | 0.99 | 0.58 | 0.73 | 0.64 | -12% |
| **original 21: flat in stress** | **1.58** | **1.19** | **1.06** | **1.13** | -5% |
| original 21: flat, costs x2 | 1.20 | 0.87 | 0.74 | 0.80 | -5% |
| Asia-Pacific 12: flat | 1.78 | 1.49 | 1.30 | 1.38 | -5% |
| Europe + Canada 9: flat | 0.68 | 0.57 | 0.48 | 0.53 | -8% |
| new 20: plain | 1.39 | 1.14 | 2.39 | 1.64 | -8% |
| new 20: flip | 0.85 | 1.64 | 0.66 | 1.23 | -11% |
| **new 20: flat in stress** | **1.39** | **2.10** | **2.19** | **2.13** | -3% |
| new 20: flat, costs x3 | 0.87 | 1.11 | 0.96 | 1.04 | -5% |
| new 14 borrowable: flat | 1.99 | 2.23 | 2.11 | 2.17 | -3% |
| new 14 borrowable: flat, costs x3 | 1.32 | 1.49 | 1.15 | 1.33 | -5% |
| new 6 not borrowable: flat | 0.02 | 0.84 | 1.12 | 0.96 | -5% |
| all 41: flat | 1.43 | 1.69 | 1.67 | 1.68 | -3% |

Each market's book runs at about 2-3% volatility at unit gross and makes
about 3% a year. The aggregate Sharpe is high because the markets barely
correlate with one another.

Robustness of the new-20 book:
- Bootstrap (21-day blocks): the 5th percentile is above zero in every
  period.
- Leaving out any one market gives 2.00-2.27.
- Executing a day late changes nothing (2.11).
- Both legs earn: the long leg makes +1.9%/yr and the short leg +2.1%/yr
  against the equal-weighted market.
- A VIX trigger of 17.5, 25 or 30 gives 1.94, 2.00 or 1.81.

Long-only versions (top momentum quintile, out of the market in stress,
minus the equal-weighted universe) do about as well: 1.30 on the original
21 and 2.03 on the new 20, over 2015-26. That matters where shorting is
impossible, but the equal-weighted hedge itself needs a basket short or a
future.

## 4. Combined with the US book

The blend is the one used before: inverse-volatility sleeves, a 25% cap
per sleeve, a 10% volatility target (3x leverage cap) and 2-day lags.

| book | 2006-14 | 2015-20 | 2021-26 | 2015-26 | ret/yr | vol | maxDD | worst month |
|---|---|---|---|---|---|---|---|---|
| US book (ETF sleeves + pairs + US flip) | 1.15 | 1.19 | 0.98 | 1.09 | 11.1% | 10.2% | -11.9% | -6.8% |
| + original 21 (costs x2) | 1.40 | 1.40 | 1.02 | 1.21 | 10.0% | 8.2% | -10.1% | -5.5% |
| + original 21 + 14 borrowable new (costs x1) | 2.08 | 2.02 | 1.70 | 1.87 | 10.8% | 5.8% | -8.6% | -4.0% |
| **+ original 21 + 14 borrowable new (costs x2)** | **1.87** | **1.80** | **1.42** | **1.62** | **9.4%** | 5.8% | **-9.1%** | **-4.1%** |

The bold line is the one I would plan around, and even it should be
discounted. The new-exchange sleeve gets its 25% weight because its
measured volatility is tiny. It is also the sleeve most exposed to things a
backtest cannot see:
- borrow recalls and short-sale bans (Turkey banned shorting in 2020 and
  2023);
- spreads in thin names;
- capacity: holding at most 10% of a day's traded value in each
  liquid-half name gives about $376M gross across all 20 exchanges, and
  only $0.3-7M in each of the Nordics, Poland, Greece and Chile.

## 5. Asia-Pacific financials

Pooled across 11 markets (New Zealand's 9 names are too few), signals are
scored within each market, and returns are measured against the market's
own financials.

**Stock selection.** 21-day ICs over 2004-26:

| signal | IC | t | same sign in all 4 periods |
|---|---|---|---|
| low volatility | 0.072 | 9.7 | yes |
| avoid lottery stocks (21-day max return) | 0.058 | 10.2 | yes |
| 52-week high | 0.045 | 6.0 | yes |
| 12-1 momentum | 0.032 | 5.1 | yes |
| 5-day reversal | 0.020 | 3.9 | yes |
| small minus big | **-0.019** | -2.9 | yes |
| illiquid minus liquid (Amihud) | **-0.029** | -4.7 | yes |

**Books, liquid half, net:**
- Momentum flat in stress: 0.22 / 0.90 / 0.95. Flip: 0.08 / 1.01 / 0.37.
  Plain: 0.04 / 0.27 / 0.83.
- Low vol: 0.80 / 0.19 / 0.98. MAX: 0.33 / 0.19 / 0.58.
- The reversal books lose after costs.

**Dead ends:**
- Industry momentum (29 market x industry baskets) worked before 2015 and
  is flat since.
- "Big financials lead small ones": the pure lead signal has IC 0.004.
- Sector timing from VIX, the term spread and local or US rate changes:
  out-of-sample correlation about 0.
- Pairs trading inside market x industry groups, using the US pairs rule:
  pre-registered, failed. Net 0.39 / -0.62 / -0.85, the same at the same
  close.
  - The US pairs sleeve itself survives next-open execution (0.63 / 0.78 /
    0.72, vs 0.85 / 0.79 / 0.77 at the same close).
  - So this is a real difference between markets.
- A lottery filter on the long-only momentum book: pre-registered, failed.
  It hurts in both broad universes (1.30 → 0.23, 2.03 → 0.78).

**What survived but is not a forecast: banks' rate exposure.** Each 21-day
window's bank return relative to the market, per +100bp on the US 10-year:

| | 2004-09 | 2010-14 | 2015-20 | 2021-26 |
|---|---|---|---|---|
| Japan | -1.2% | -2.0% | +7.9% | +3.6% |
| Korea | -0.7% | +2.7% | +10.5% | +6.0% |
| Hong Kong | -1.1% | +1.3% | +4.3% | +4.7% |
| Australia | -5.9% | +2.3% | +4.1% | +4.0% |
| India | +3.2% | -3.9% | +4.5% | +3.7% |

All nine bank markets are positive in both post-2015 periods. Use this to
hedge a financials book's rate exposure, or to express a rate view through
banks. It does not time anything.

**Earlier pass, now overturned.** On index members only, small and
illiquid financials looked like an edge (out-of-sample 0.69 and 0.82). On
the full listing both signs reverse in every period. The first result was
survivor selection: the small financials still in an index today are the
ones that grew into it.

## 6. Survivorship, measured

Every universe is "listed today", and three checks bear on it:

1. **Point-in-time membership** (NIFTY 50 and DAX, rebuilt from their
   change tables).
   - The momentum books move both ways and by about the noise. NIFTY flip
     over 2015-26 is 0.72 on today's members and 0.78 point-in-time; DAX
     flat is 0.06 and 0.26.
   - The regime rules keep their ranking against plain momentum.
2. **Synthetic markets with zero momentum** (`survivorship_sim.py`, 32
   markets of 600 stocks).
   - Volatility follows the real VIX path; stocks list at random and die
     after a 90% fall.
   - The universe is the 120 largest stocks alive at the end, exactly the
     screener's construction.
   - This selection *lowers* momentum Sharpe per market: plain -0.22 ±
     0.06, flat in stress -0.16 ± 0.06, flip +0.02 ± 0.05 (2015-26, paired
     against the point-in-time universe of the same simulated market).
     Losers that recovered are kept and hurt the short leg, and losers
     that died are dropped.
   - So the screener universes, if anything, understate the momentum
     books.
3. **Breadth** (`breadth_check.py`): the new exchanges use the 120
   largest companies, while the original 21 use index large caps.
   Restricting the new exchanges to their 30 largest names cuts
   flat-in-stress from 2.13 to 1.58 (2015-26; borrowable 14: 2.17 to
   1.46).
   - Mid caps add momentum, which explains part of the gap.
   - Large caps alone still beat the original 21 (1.13).
   - The rest is diversification: the new markets correlate 0.02 with each
     other, against 0.15 among the original 21.

What survivorship *does* distort, and is excluded here:
- Long-only books hedged with the cap-weighted index. They mostly earn the
  equal-weight-vs-index survivor premium (11% a year, Sharpe about 1.2).
  That is why every long-only number here is hedged with the
  equal-weighted universe.
- Small-cap and illiquidity signals (section 5).
- Any beta-adjusted hedge below 1, which leaves the book net long a
  survivor universe that drifts upward in-sample.

## 7. What I would do with this

- **Trade:** flat-in-stress momentum, monthly, staggered, in the 35
  borrowable markets (the original 21 plus the 14 new ones).
  - Start with the liquid half of each market.
  - Run it as separate sleeves next to the US book.
- **Size:** for planning, about half the backtested Sharpe. Keep gross
  within capacity (Nordics, Poland, Greece and Chile at a few million
  dollars each).
- **Don't trade:**
  - the flip outside the US;
  - long-only books hedged with index futures, unless you accept that most
    of the backtest is survivor premium;
  - small-cap or illiquidity tilts;
  - reversal books;
  - sector timing;
  - pairs inside Asian financials;
  - the six non-borrowable markets as long/short.
- **Next data that would most change the conclusions:**
  - point-in-time constituents (a paid source: Refinitiv, Bloomberg or
    Compustat Global);
  - borrow availability and fees by market;
  - real historical spreads instead of the tiered estimates.

## Reproducing

From a working directory holding `data/` (first pass) and `data2/` (deep
data):

```
python research_international/code/universes.py --out data/universe.csv
python research_international/code/download.py --universe data/universe.csv --out data/prices
python research_international/code/intl_lab.py --prices data/prices --universe data/universe.csv --out reports/intl
python research_international/code/summarize.py --lab reports/intl --prices data/prices --out reports/intl
python research_international/code/intl_more.py --prices data/prices --universe data/universe.csv --out reports/intl_more \
    --choice reports/intl/market_choice.csv --us-flip <US flip daily> --us-etf <multi_daily.csv> --us-strategies <strategy_returns.csv>
python research_international/code/point_in_time.py --prices data/prices --universe data/universe.csv --out reports/pit
python research_international/code/asia_financials.py --prices data/prices --universe data/universe.csv --macro <fred.parquet> --out reports/asia_fin

python research_international/code/deep_universe.py --out data2
python research_international/code/macro_data.py --out data2/macro.parquet
python research_international/code/download.py --universe data2/universe_asia_financials.csv --out data2/prices_fin
python research_international/code/download.py --universe data2/universe_new_markets.csv --out data2/prices_new
python research_international/code/new_exchanges.py --prices data2/prices_new --universe data2/universe_new_markets.csv \
    --old-prices data/prices --old-universe data/universe.csv --out reports/new_exchanges --us-flip ... --us-etf ... --us-strategies ...
python research_international/code/new_exchanges_robust.py --prices data2/prices_new --universe data2/universe_new_markets.csv --macro data2/macro.parquet --out reports/new_exchanges
python research_international/code/breadth_check.py --prices data2/prices_new --universe data2/universe_new_markets.csv --out reports/new_exchanges
python research_international/code/asia_fin_deep.py --fin-prices data2/prices_fin --fin-universe data2/universe_asia_financials.csv \
    --mkt-prices data/prices --mkt-universe data/universe.csv --macro data2/macro.parquet --out reports/asia_fin_deep
python research_international/code/lottery_filter.py --old-prices data/prices --old-universe data/universe.csv --new-prices data2/prices_new \
    --new-universe data2/universe_new_markets.csv --fin-prices data2/prices_fin --fin-universe data2/universe_asia_financials.csv --out reports/lottery
python research_international/code/conservative_combo.py --old-prices data/prices --old-universe data/universe.csv --new-prices data2/prices_new \
    --new-universe data2/universe_new_markets.csv --out reports/conservative --us-flip ... --us-etf ... --us-strategies ...
python research_international/code/survivorship_sim.py --vix-from data2/prices_new/_series/adj_close.parquet --sims 8 --seed-start 0 --out reports/survivorship_sim
```

The US inputs come from Arjun's repo and `research_night/`:
`reports/momentum_flip/momentum_flip_staggered_daily.csv`,
`research_data/studies/multi_daily.csv` and
`research_data/studies/strategy_returns.csv`.
