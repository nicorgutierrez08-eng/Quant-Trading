"""Configuration: every tunable number in one place.

Defaults live in the dataclasses below; ``config/default.yaml`` mirrors them
and any YAML file passed with ``--config`` overrides only the keys it sets.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class UniverseConfig:
    size: int = 1000                 # number of companies to trade
    min_history_years: float = 15.0  # must have traded at least this long
    candidate_source: str = "ishares_r3000"  # ishares_r3000 | wikipedia | file
    universe_file: str | None = None # CSV with a 'ticker' column (source=file)
    min_price: float = 5.0           # skip penny stocks on a given day
    min_dollar_volume: float = 5e6   # 21-day median $ volume needed to trade


@dataclass
class DataConfig:
    start: str = "2000-01-01"
    end: str | None = None           # None = today
    cache_dir: str = "data"
    batch_size: int = 100            # tickers per yfinance request


@dataclass
class FactorConfig:
    n_factors: int = 15              # PCA eigenportfolios (Avellaneda-Lee)
    window: int = 252                # days of returns used for each PCA
    refit_every: int = 21            # re-estimate loadings monthly
    n_clusters: int = 20             # k-means peer groups on PCA loadings


@dataclass
class RegimeConfig:
    n_states: int = 3                # hidden market regimes
    refit_every: int = 252           # re-run Baum-Welch once a year
    min_history: int = 756           # 3 years before the first fit
    n_init: int = 5                  # random restarts for EM
    max_iter: int = 200
    temper: float = 1.0              # weight of each day's evidence (<1: less overconfident)
    align: bool = False              # keep regime labels fixed across refits (else sort by volatility)


@dataclass
class ModelConfig:
    horizon: int = 5                 # predict open(t+1) -> open(t+1+h), in days
    train_window: int = 1260         # 5 years rolling training window
    min_train: int = 756             # 3 years before first prediction
    retrain_every: int = 63          # quarterly walk-forward refits
    models: list[str] = field(default_factory=lambda: [
        "ridge", "elastic_net", "regime_ridge", "kernel_ridge", "gbm", "ic_weighted",
    ])
    ensemble: list[str] = field(default_factory=lambda: [
        "ridge", "regime_ridge", "kernel_ridge", "gbm", "ic_weighted",
    ])
    trade_model: str = "ensemble"    # which prediction the portfolio trades
    gbm_max_rows: int = 400_000      # subsample for gradient boosting
    rff_features: int = 256          # random Fourier features (kernel ridge)
    seed: int = 7
    signals: list[str] | None = None # None = every registered signal
    # keep only signals whose IC had the same sign in every part of the training
    # window (and a big enough t-stat); the rest are dropped at that refit
    select_stable: bool = False
    stable_splits: int = 3           # sub-periods of the training window that must agree
    stable_min_t: float = 2.0        # minimum |t| of the signal's IC over the whole window


@dataclass
class PortfolioConfig:
    target_vol: float = 0.10         # annualized volatility target
    max_gross: float = 2.0           # sum |w| cap: 2.0 = 100% long + 100% short (Reg T limit)
    max_weight: float = 0.02         # per-name cap as a fraction of equity
    kelly_fraction: float = 0.5      # half-Kelly cap on leverage
    ic_prior: float = 0.01           # prior daily IC for Bayesian shrinkage
    ic_prior_days: int = 252         # weight of that prior, in days
    ic_lookback: int = 252           # trailing window for realized IC
    forecast_halflife: float = 3.0   # days of exponential smoothing of the forecast (0 = off)
    max_names: int | None = None     # small accounts: hold only the N strongest names
    n_neutral_factors: int | None = None  # hedge only the first N PCA factors (None = all)
    whole_shares: bool = False       # round positions to whole shares (needs costs.aum = account size)
    weighting: str = "kelly"         # kelly (alpha / variance) | rank (proportional to score)
    factor_neutral: bool = True      # hedge PCA factors as well as net dollars
    cost_aversion: float = 1.0       # scales costs in the no-trade band (>1 trades less)
    trade_rate: float = 1.0          # extra partial adjustment toward target (1 = off)
    no_trade_band: float = 0.0002    # ignore trades smaller than 2 bp of equity
    regime_ic: bool = False          # estimate the forecast's IC separately for each HMM regime
    edge_scaling: float | None = None  # scale exposure by IC_hat / this (capped at 1); None = off
    drawdown_limit: float = 0.15     # cut risk after a 15% drawdown
    drawdown_scale: float = 0.5      # ...to half size until recovery


@dataclass
class CostConfig:
    aum: float = 10_000_000          # account size used for market impact
    commission_bps: float = 0.0      # Alpaca charges no commission
    slippage_bps: float = 1.0        # fill vs. official open price
    # half-spread by liquidity tier: (min 21-day median $ volume, half-spread bps)
    spread_tiers: list = field(default_factory=lambda: [
        [500e6, 1.5], [100e6, 3.0], [20e6, 6.0], [0.0, 12.0],
    ])
    impact_coef: float = 0.5         # square-root impact: c * sigma * sqrt(Q/ADV)
    borrow_bps_annual: float = 50.0  # stock-loan fee on short notional


@dataclass
class LiveConfig:
    dry_run: bool = True             # print orders instead of sending them
    order_type: str = "auto"         # auto | opg (market-on-open) | market
    min_order_value: float = 50.0    # skip orders smaller than this ($)
    capital_fraction: float = 1.0    # fraction of paper equity to deploy
    max_capital: float | None = None # never deploy more than this many dollars
    log_dir: str = "logs"


@dataclass
class MultiConfig:
    """ETF sleeves (``qtrade.portfolio.sleeves``) traded alongside the stock book."""
    enabled: bool = False
    etf_fraction: float = 0.5        # share of deployed capital for the ETF sleeves; the rest is the stock book
    sleeves: list = field(default_factory=lambda: ["spy_vol_managed", "cross_asset_mom", "spy_ma200",
                                                   "risk_parity", "spy_tsmom_12m", "broad_trend_12m",
                                                   "spy_turn_of_month", "multi_asset_trend"])
    target_vol: float = 0.10         # annualised volatility target for the ETF book
    max_gross: float = 1.5           # ETF book gross exposure cap (multiple of its capital)
    vol_window: int = 756            # days of sleeve returns behind the 1 / volatility weights
    history_start: str = "2004-01-01"


@dataclass
class AuctionConfig:
    """The auction trader (``qtrade.intraday.auction_live``): market-on-close in, market-on-open out."""
    strategies: list = field(default_factory=lambda: ["last30_fade", "overnight_persistence", "last_reaction"])
    gross: float = 2.0               # long + short as a multiple of capital
    frac: float = 0.2                # long the top fifth, short the bottom fifth
    capital: float | None = None     # dollars to trade (default: live.capital_fraction / live.max_capital)
    min_order_value: float = 25.0
    feed: str = "iex"                # today's 5-minute bars on the free plan
    earnings_per_event: float = 0.02  # last_reaction: capital per company reporting tonight (long or short)
    earnings_max_gross: float = 0.5   # ... capped in total on a busy night
    # the ADR book (qtrade.intraday.adr_book): Asian ADRs vs their home markets, open to close
    adr_enabled: bool = True          # research (2016-26 Alpaca bars): Sharpe 3.9 / 2.2 at 0 bp, 2.6 / 1.3 at 3 bp
    adr_mode: str = "premarket"       # "premarket": market-on-open with the pre-market price; "after_open": 9:35
    adr_gross: float = 0.5            # long + short as a multiple of capital (the overnight book is flat by then)
    adr_sign: float = 1.0             # +1: follow the home move the ADR hasn't priced yet (research direction)
    adr_min_residual: float = 0.0     # skip names whose residual is smaller than this (log return)
    adr_markets: list = field(default_factory=lambda: ["China", "Japan", "Korea", "India"])
    # true: the auction strategies are simulated in the Google Sheet (qtrade.intraday.auction_sheet); on Alpaca
    # the keeper only closes what is left open and sends nothing new, then stops its chain once the account is flat
    alpaca_flatten_only: bool = False


@dataclass
class IntradayConfig:
    """Intraday reversal strategy on N-minute bars (``qtrade.intraday``)."""
    store: str = "data/intraday/5min"  # per-symbol bar files (see `qtrade intraday`)
    bar_minutes: int = 5
    n_symbols: int = 500             # most liquid names in the store's symbols.csv
    start: str | None = None         # first day to load (None = everything)
    horizon_bars: int = 6            # forecast the next 6 bars (30 minutes)
    train_months: int = 12           # rolling training window, refit monthly
    min_train_months: int = 6
    ridge: float = 1e-3
    start_bar: int = 3               # first decision at the close of bar 3 (9:50 for 5-min bars)
    flat_bar: int = 74               # from the open of bar 75 (15:45) the book goes flat
    rebalance_every: int = 1         # trade every N bars (1 = every bar)
    gross: float = 2.0               # long + short as a multiple of capital
    n_side: int | None = 20          # names per side (None = the whole universe)
    cost_aversion: float = 1.0       # scales the no-trade band
    vol_days: int = 20               # days of history for volatility / volume baselines
    slippage_bps: float = 0.5
    # intraday orders cross the spread: half-spread by daily $ volume tier
    spread_tiers: list = field(default_factory=lambda: [
        [1e9, 1.0], [2e8, 2.0], [5e7, 4.0], [0.0, 8.0],
    ])
    impact_coef: float = 0.5
    aum: float = 10_000
    min_order_value: float = 25.0
    feed: str = "iex"                # live bars: the free plan's real-time feed


@dataclass
class Config:
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    data: DataConfig = field(default_factory=DataConfig)
    factors: FactorConfig = field(default_factory=FactorConfig)
    regime: RegimeConfig = field(default_factory=RegimeConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    portfolio: PortfolioConfig = field(default_factory=PortfolioConfig)
    costs: CostConfig = field(default_factory=CostConfig)
    live: LiveConfig = field(default_factory=LiveConfig)
    intraday: IntradayConfig = field(default_factory=IntradayConfig)
    multi: MultiConfig = field(default_factory=MultiConfig)
    auction: AuctionConfig = field(default_factory=AuctionConfig)
    report_dir: str = "reports"
    diagnostics: bool = True         # also backtest portfolio-construction variants

    # -- helpers ---------------------------------------------------------
    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def load(cls, path: str | Path | None = None, overrides: dict | None = None) -> "Config":
        cfg = cls()
        if path:
            with open(path) as fh:
                _merge(cfg, yaml.safe_load(fh) or {})
        if overrides:
            _merge(cfg, overrides)
        return cfg


def _merge(obj, updates: dict) -> None:
    for key, value in updates.items():
        if not hasattr(obj, key):
            raise KeyError(f"Unknown config key: {key}")
        current = getattr(obj, key)
        if dataclasses.is_dataclass(current) and isinstance(value, dict):
            _merge(current, value)
        else:
            setattr(obj, key, value)
