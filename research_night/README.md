# research_night

An overnight research pass (21 Oct 2026) over Arjun's quant-trading system,
on the same data and with the same walk-forward / two-period rules.

Start with **`REPORT.md`**. Then:

| file / folder | what it is |
|---|---|
| `REPORT.md` | the findings and recommendations, with the honest numbers |
| `night_lab_log.md` | chronological log of every experiment, including the ones that failed and the earlier figures that later checks revised |
| `stability_report.md` | review of Arjun's existing research outputs (model zoo, pairs, strategies, decay) and the data artefacts in them |
| `code/` | the research modules: `lab_prep` (cache), `regime_lab` (88 HMM variants), `jump_lab` (Poisson GLMs), `invariants_lab`, `switch_lab`, `switch_robust`, `book_lab`, `pairs_lab`, `momentum_flip` |
| `patch/` | the macro-regime option for the live pipeline (`macro_state.py`, `regime_macro.diff`, configs) |
| `reports/` | every run's markdown and CSV output (one folder per run) |

The code imports Arjun's research package, so it runs on his
`claude/keen-tesla-shs956` branch (not yet merged here). Typical use there:

```bash
python -m qtrade download                       # daily prices (Yahoo)
python -m qtrade.research.lab_prep              # cache market, factors, signals (4 min)
python -m qtrade.research.momentum_flip         # the headline strategy and its robustness table
python -m qtrade.research.regime_lab --quick    # the HMM sweep
python -m qtrade.research.jump_lab              # Poisson / negative-binomial jump models
python -m qtrade.research.invariants_lab        # stable / decaying / regime-dependent signals
```

One-paragraph summary: the only stable structure in the data is that
cross-sectional stock momentum works when the VIX is low and reverses when it
is high. Trading that as a monthly momentum book whose sign flips when the VIX
is above 20 gives a Sharpe of roughly 0.6 / 0.7 / 0.2 in 2006-14 / 2015-20 /
2021-26 (staggered, net of costs), nothing fitted. No HMM beat the VIX
threshold; no regime model beat volatility targeting as a market timer;
Arjun's daily reversal book loses after costs under any regime model and
should be retired; adding his pairs book and the flip to his ETF book takes it
from about 0.9 to about 1.1 Sharpe with a smaller worst drawdown. Everything
is on a survivor universe and should be re-run point-in-time before real
money.
