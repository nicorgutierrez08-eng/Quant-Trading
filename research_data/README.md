# Research data

Everything the research produced, as plain CSV and Markdown, for anyone who
wants to check the results or improve the model. Refresh it from the latest
GitHub Actions runs with:

```bash
bash scripts/export_research_data.sh
```

## Ground rules used throughout

- **Two periods.** 2006-2014 ("1st", "2006_14") is used to choose things;
  2015-2026 ("2nd", "2015_26") is only used to check them. Anything chosen
  by looking at 2015-2026 is labelled as in-sample where it appears.
- **Walk-forward.** Every model is refit yearly on the previous 5 years and
  forecasts the following year only.
- **Costs** come from measured Alpaca bid-ask spreads by liquidity tier
  (`studies/spreads*.csv`) plus 1 bp of slippage; "break-even" is the
  one-way cost at which a strategy stops making money, in basis points.
- **IC** is the daily cross-sectional rank correlation between a forecast and
  the next N days' returns (N = `horizon_days`). An IC of 0.02 is useful.
- **Universe:** today's ~1,000 most traded US stocks. This flatters some
  signals (survivorship bias) — see `studies/survivorship.md` and the
  `survivorship_prone` column.

## Where to start

| File | What it is |
|---|---|
| `zoo/best_correlations.csv` | **The main table.** Every signal, signal pair and fitted model, ranked by its IC in the *weaker* of the two periods. |
| `zoo/README.md` | Summary of ~550 fitted models: which families work, pros and cons, whether period-1 winners stayed winners, the luck hurdle. |
| `studies/ALL_STUDIES.md` | All study write-ups in one document. |
| `studies/strategies.md` | 40+ strategies beyond stock reversal (trend, risk parity, pairs, factors, volatility premium), with correlations. |
| `studies/multi.md` | The multi-strategy book (ETF sleeves + stock book) as it will trade. |
| `backtest/README.md` | Full backtest of the stock book (2004-2026) with charts. |

## `zoo/best_correlations.csv` columns

| Column | Meaning |
|---|---|
| `what` | `signal`, `pair` (two signals summed or multiplied) or `model` |
| `name`, `family` | what it is; ideas are tagged `idea:<theme> (wave N)` |
| `horizon_days` | forecast horizon: 1, 5, 21 or 63 trading days |
| `ic_2006_14`, `ic_2015_26`, `t_*` | mean daily IC and its t-statistic in each period |
| `ic_2015_20`, `ic_2021_26` | the same split inside 2015-2026, for signals that only exist from 2015 (news) |
| `years_positive` | share of calendar years with a positive IC |
| `breakeven_bp_*`, `net_sharpe_*` | trading it as a long/short book (models and ideas) |
| `same_sign_both_periods`, `weaker_period_ic` | the ranking key: did it keep working, and how strongly at worst |
| `survivorship_prone` | size/illiquidity-type signals that look better on today's survivors than they were |

A negative IC that is stable in both periods is just as useful: trade it the
other way.

## Folders

- `zoo/` — model zoo. `zoo_all_strategies.csv` has every model x signal set x
  horizon x smoothing x universe combination (~3,000+ rows) with ICs, Sharpe
  and break-even costs; `parts/` holds the raw per-group results
  (`zoo_<group>_h<horizon>.csv`).
- `studies/` — one file set per study:
  - `edge*` signal ICs, decay and break-even costs; `alt*` fundamental and news signals
  - `combos*`, `stability.csv` signal pairs and which ones kept their sign
  - `conditional*` when each signal works (regimes, volatility, news days)
  - `poisson*` jump clustering (INGARCH, Hawkes, Poisson HMM) and jump-based signals
  - `hmm*` market-regime model variants and calibration
  - `strategies*`, `strategy_returns.csv` daily net returns of every strategy;
    `strategy_correlations.csv`
  - `multi*` ETF sleeves + stock book; `intraday*` intraday strategies
  - `events.md`, `news_events.csv` returns after each type of news; `survivorship*`
  - `spreads*` measured bid-ask spreads by liquidity tier, time of day and year
- `backtest/` — the reference stock-book backtest (`daily.csv`: daily returns,
  exposure and turnover; `signal_ic.csv`; `model_comparison.csv`; charts) and
  `all_runs.csv`, a one-line summary of every backtest variant tried.

## Raw data

The raw inputs are **not** here, because their licences do not allow
redistribution:

- Daily prices: Yahoo Finance — anyone can download them with
  `python -m qtrade download`.
- 5-minute and 1-minute bars, news: Alpaca (free account) — anyone can rebuild
  them with their own Alpaca keys: `python -m qtrade intraday --timeframe 5Min --symbols 1000`
  and `python -m qtrade news`. The repository's own copies are stored encrypted.
- Macro series: FRED (free API key) or the Yahoo stand-ins in `qtrade/data/public.py`.

Datasets that *can* be shared openly — SEC fundamentals, SEC insider
transactions and S&P 500 index changes — are published unencrypted to the
GitHub release **public-data** by the `publish-public-data` workflow.

## Reproducing everything

1. `pip install -r requirements.txt`
2. `python -m qtrade universe && python -m qtrade download`
3. `python -m qtrade.research --tasks edge,combos,strategies,multi` (any of
   quality, spreads, edge, alt, poisson, conditional, combos, garch, glm,
   strategies, multi, events, survivorship, intraday, hmm)
4. `python -m qtrade.research.zoo --group tree --horizon 5` (groups: simple,
   linear, tree, nn, extra, ideas, seq, online, targets, features)

Or push a commit with `[research: edge,combos]` / `[zoo: tree@5,21]` in its
message and GitHub Actions runs it on real data; results land on the
`results` branch.
