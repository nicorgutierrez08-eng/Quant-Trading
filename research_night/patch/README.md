# Macro regime option for the live pipeline

Files to drop into Arjun's `claude/keen-tesla-shs956` branch:

- `macro_state.py` -> `qtrade/features/macro_state.py` (new): the HMM symptoms
  that won the regime lab (GARCH vol, standardised market return, dispersion,
  correlation, breadth, log VIX, 10y-3m term spread).
- `regime_macro.diff`: adds `features: rolling|macro` to `RegimeConfig`
  (`qtrade/config.py`) and makes `pipeline.build_research` use the macro
  symptoms when selected.
- `regime_macro.yaml` -> `config/regime_macro.yaml`: `n_states: 2`,
  `features: macro`. Run with `python -m qtrade --config config/regime_macro.yaml backtest`.

The macro symptoms need the FRED/Yahoo macro cache (`qtrade.data.public.load_fred`),
which the research workflow already builds.
