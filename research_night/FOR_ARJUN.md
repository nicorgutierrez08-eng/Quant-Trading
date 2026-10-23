# For Arjun: how to take this into your repo

Everything is self-contained in this folder; nothing in it needs the
encrypted datasets. Your `claude/keen-tesla-shs956` branch is the base.

## 1. Get the folder

```bash
git remote add nico https://github.com/nicorgutierrez08-eng/Quant-Trading.git
git fetch nico claude/practical-ride-wggb8u
git checkout claude/keen-tesla-shs956
git checkout nico/claude/practical-ride-wggb8u -- research_night
```

(That branch's `main` is your `main` at 946f86e plus this folder, so a plain
merge also works: `git merge nico/claude/practical-ride-wggb8u`.)

## 2. Drop the code into place

```bash
cp research_night/code/*.py qtrade/research/
cp research_night/patch/macro_state.py qtrade/features/
cp research_night/patch/regime_macro.yaml research_night/patch/fast_refit*.yaml research_night/patch/light_gbm*.yaml config/
git apply research_night/patch/regime_macro.diff      # adds regime.features to config.py and pipeline.py
python -m pytest -q
```

## 3. Reproduce

```bash
python -m qtrade download                            # daily prices from Yahoo (~2 min)
python -m qtrade.research.lab_prep                   # cache market, factors, 44 signals (~4 min)
python -m qtrade.research.momentum_flip              # the headline strategy and its robustness table
python -m qtrade.research.invariants_lab --horizon 21
python -m qtrade.research.jump_lab
python -m qtrade.research.regime_lab --quick --workers 3
python -m qtrade.research.switch_robust --probs reports/regime_lab/probs/<any>.parquet
```

`research_night/reports/` has every output these produced here, so you can
diff. `night_lab_log.md` is the chronological record; `REPORT.md` the summary.

## 4. What to change in your system (short form; details in REPORT.md)

1. Retire the daily 5-day reversal book (negative after costs 2015-26 under
   any regime model, including with GBM).
2. Regime = "VIX > 20". No HMM beat it. If you keep `regime_ridge`, use
   `config/regime_macro.yaml` (2 states, VIX + term spread + GARCH).
3. Add `pairs` (x2 when VIX > 20) and the staggered momentum flip as sleeves
   next to the ETF book, capped per strategy.
4. `poisson._poisson_glm`: drop features constant in training (news_fast was
   all zeros before 2015 -> the -2.2 deviance); rank-standardise per day;
   refit yearly. Fix or drop `downside_beta`.
5. `edge.summarize`'s "1st" period is 2001-2014, not 2006-2014; 2001-05
   roughly doubles the apparent reversal edge in every edge/combos/poisson table.

## 5. What this did not do

No point-in-time universe (needs your Alpaca keys: the flip's stressed leg is
long high-vol names, exactly where survivorship flatters); no intraday or news
work (encrypted data not available here); GBM only in a lightened live run.
