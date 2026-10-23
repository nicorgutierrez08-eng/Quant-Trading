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
