# Handoff: Quant-Trading research (for you and your Claude)

Give this whole file to Claude (or any assistant) as your first message, then
let it read the repository. Everything referenced here is public; no keys or
passwords are in this file.

## 1. Where everything is

- **Repository (public):** https://github.com/ASCoding11/Quant-Trading
- **Branch with all the latest work:** `claude/keen-tesla-shs956`
  (not yet merged into `main`; `main` has an older version).
  ```bash
  git clone https://github.com/ASCoding11/Quant-Trading.git
  cd Quant-Trading
  git checkout claude/keen-tesla-shs956
  git fetch origin results     # raw outputs of every GitHub Actions run
  ```
- **Results, ready to read:** `research_data/` on that branch
  (start with `research_data/README.md`).
- **Raw outputs of every run:** the `results` branch (`research/runs/`,
  `research/zoo/`, `runs/` for backtests).
- **Public datasets** (SEC fundamentals, SEC insider trades, S&P 500
  changes): the GitHub release **public-data**.

## 2. Read in this order

1. `README.md`: what the system is and how it trades (daily, market-on-open
   orders; Alpaca *paper* account only).
2. `research_data/README.md`: conventions, every file and column.
3. `research_data/zoo/README.md`: about 550 forecasting models compared,
   with pros and cons.
4. `research_data/zoo/best_correlations.csv`: every signal, signal pair and
   model, ranked by its accuracy (IC) in the weaker of the two test periods.
5. `research_data/studies/strategies.md` and `research_data/studies/multi.md`:
   the 40+ strategy zoo and the multi-strategy book.
6. `docs/overnight_log.md`: a dated log of what was tried and found.
7. `qtrade/research/BACKLOG.md`: what has been done and what is still open.

## 3. Rules the research follows (please keep them)

- **Two periods.** 2006-2014 is used to choose; 2015-2026 is only used to
  check. Choosing signals by their 2015-2026 performance is look-ahead and
  makes results meaningless. Anything picked after seeing 2015-2026 is
  labelled "in-sample".
- **Walk-forward only.** Models refit yearly on the past 5 years; no weight or
  signal may use data from after the day it trades. Tests enforce this
  (`tests/test_invariants.py`, `tests/test_sleeves.py`).
- **Costs are real:** measured Alpaca bid-ask spreads by liquidity tier, plus
  1 bp of slippage, 3x wider at the open. Report net results and break-even
  cost, not just IC.
- **The luck hurdle.** With ~3,000 variants tried, the best 2006-2014 Sharpe
  expected from luck alone is up to ~2.1. A result has to survive 2015-2026 to
  count.
- **Survivorship.** The universe is today's ~1,000 most traded stocks, which
  flatters size and illiquidity signals (`studies/survivorship.md`).

## 4. What we found so far

Net Sharpe ratios, written as 2006-2014 / 2015-2026:

| What | Result |
|---|---|
| Stock reversal book (the original system) | 0.44 / 0.16: the edge has mostly faded after costs |
| ETF book (8 trend, risk-parity and timing strategies) | 0.93 / 0.93 |
| 50/50 ETF + stock book | 0.99 / 0.80, max drawdown -13% (2015-26) |
| Best stock model families | regime-switching ridge, gradient-boosted trees; median model loses money after costs |
| Picking the top 10 models by 2006-14 | Sharpe 0.35 -> 0.14: winners mostly don't repeat |
| Strongest stable stock signals | reversal combinations at 5 days (e.g. rev_1d + rev_21d, IC 0.018 / 0.017), R&D intensity at 63 days |
| Survivorship-free universe (with delisted stocks) | momentum is *stronger* (21-day IC 0.035 vs 0.005); size and illiquidity edges were mostly survivorship |
| News events (2015-26, in-sample) | buybacks +33 bp next day (t 6.6); lawsuit news reverses +76 bp over 21 days |
| Intraday 5-minute reversal | edge 1.25 bp vs cost 2.34 bp: loses money |

A few ETF strategies were dropped after seeing 2015-2026 (short volatility,
stock pairs, a 3-month trend that faded), so that period is not fully clean
for the ETF book.

## 5. Running things yourself

- **Locally:**
  ```bash
  pip install -r requirements.txt
  python -m pytest -q                               # tests
  python -m qtrade universe && python -m qtrade download
  python -m qtrade.research --tasks edge,strategies,multi
  python -m qtrade.research.zoo --group tree --horizon 5
  python -m qtrade.research.zoo --group ideas --horizon 5 --synthetic   # offline smoke test
  ```
- **On real data via GitHub Actions** (in your own fork): push a commit whose
  message contains `[research: edge,strategies]` or `[zoo: tree@5,21]`.
  Results go to the `results` branch.
- **New signal ideas:** add a function to `qtrade/research/ideas.py` with the
  `@idea("theme", wave)` decorator; the zoo's `ideas` group scores it in both
  periods automatically.

## 6. Data and keys (each person uses their own; never share keys in files)

| Needed for | What to get | Where it goes |
|---|---|---|
| Daily prices | nothing: Yahoo Finance, downloaded by the code | - |
| 5-minute bars, news, paper trading | free Alpaca account, **paper** API key and secret | env vars or repo secrets `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` |
| Macro series | free FRED API key (fred.stlouisfed.org/docs/api/api_key.html) | `FRED_API_KEY` |
| SEC data | your name and email | `SEC_USER_AGENT` |
| The repository's encrypted datasets (5-minute bars, news) | the `DATA_KEY` password, only if the owner chooses to share it **privately** | `DATA_KEY` |

Price data, 5-minute bars and news are licensed for personal use: don't
publish them unencrypted.

## 7. Open questions worth attacking

- Make the stock book worth its costs again: lower turnover, trade only the
  strongest signals, better execution.
- Fold the survivorship-free universe (Alpaca, 2016+) into the main backtest.
- Get an honest out-of-sample test for the news-event signals.
- Better weighting across the ETF book and the stock book than 1 / volatility.
- Remaining ideas: `qtrade/research/BACKLOG.md`.
