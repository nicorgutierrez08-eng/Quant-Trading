# Research backlog

Ideas queued for the overnight research loop. Each wave is pushed as a commit
with a `[zoo: ...]` / `[research: ...]` tag, runs in GitHub Actions on real
data, and adds its results to `research/zoo/best_correlations.csv` on the
`results` branch. Ticked = pushed.

## Signals (ideas lab, `qtrade/research/ideas.py`)

- [x] **Wave 1**: momentum variants (vol-scaled, frog-in-the-pan, consistency,
  peer-relative, time-series), trend shape (MA gap, MACD, distance from high),
  volatility change, skewness, co-skewness, illiquidity change, OBV divergence,
  fundamentals (earnings/revenue growth, ROE, leverage, net issuance, R&D, cash)
- [x] **Wave 2**: seasonality (stock's same-calendar-month return over 1-10
  years, weekday, pre-holiday), overnight momentum (overnight returns persist),
  52-week low, nominal price level, volume-spike continuation vs reversal,
  earnings-surprise revisions (change in SUE), network (correlation-neighbour) momentum;
  public data: FINRA short volume, SEC insider buying (net and cluster), filing delays
- [x] **Wave 3-4**: interactions found to stick (momentum x 52-week high,
  reversal x momentum, reversal x HMM stress) as single signals; rank and
  nonlinear transforms of the best signals; signal decay-adjusted blends

## Models (model zoo, `qtrade/research/zoo.py`)

- [x] 21 base families x 4 signal sets x 1/5/21 days
- [x] 13 more families (random forest, robust/early-stopped boosting, PLS,
  Bayesian ridge, SVR, kernel bandwidths, decayed/expanding/regime ridge,
  stacking) and a 63-day horizon for all
- [x] Other targets: factor-residual returns, volatility-scaled returns,
  top/bottom-decile classification
- [x] Feature engineering: sticky pairs and the best ideas as inputs; two-stage
  lasso-selection then boosting

## Strategies (`qtrade/research/strategies.py`)

- [x] Market timing, cross-asset trend/risk parity, sector momentum, stock
  factors, pairs, earnings premium
- [x] Momentum crash protection (vol-scaled, macro-timed); sector- and beta-neutral and
  vol-scaled factor books; ETF pair trades; a risk-parity blend of the
  momentum and reversal books
- [x] Intraday (5-minute data): opening drive, last-half-hour momentum,
  overnight-intraday reversal

## Not yet covered (added after review)

- [x] Free public data loaders: FRED macro, S&P 500 changes, FINRA short volume, SEC insider trades, all US stocks incl. delisted (Alpaca)
- [x] Survivorship-free universe study: signal ICs on a point-in-time top-1000 (with delisted stocks) vs today's survivors, 2017-2026
- [x] Intraday-derived daily signals: realized skew/kurtosis, jump share, first/last half-hour moves
- [x] News text: novelty, event types (M&A, FDA, guidance, lawsuit, offering, analyst), event study by type
- [x] Index events: S&P 500 additions/removals around the effective date
- [x] Macro: FRED states for market timing and momentum-crash protection
- [x] Broad trend following (~30 ETFs: commodities, currencies, rates, countries), volatility premium (VIX term structure), sector seasonality
- [x] Ledoit-Wolf covariance and mean-variance across strategies; capacity vs AUM; open- vs close-auction execution
- [x] Sequence models on raw return histories; online model weighting; sizing by model disagreement
- [ ] Not possible with free data: options (implied vol, skew), analyst revisions, borrow fees, supply chains, 13F (large)

## Added overnight

- [x] Ideas wave 5: news-event signals from the event study (buybacks, lawsuits, M&A, net upgrades, dividend raises, CEO changes) — in-sample by construction, judge with care
- [x] Ideas report IC for 2015-20 and 2021-26 separately (an honest split for news signals)
- [x] Intraday model zoo (gross edge, for direct exchange access): 20 signals x 6 models x 5 horizons on 5-minute bars, monthly walk-forward, net shown at 0.5 / 1 / 2.34 bp
