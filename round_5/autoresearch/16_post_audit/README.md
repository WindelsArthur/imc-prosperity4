# post_audit — three targeted alpha extractions

Three hypotheses tested on top of `algo1_drop_harmful_only.py` (audit's
robust runner-up; baseline for THIS study):

1. ROBOT_DISHES carries structural alpha (AR(1)=-0.232, 4 log-pairs novel,
   currently bleeding) that the global additive `pair_skew` architecture cannot
   capture. A dedicated specialised handler may unlock it.
2. AR(1) mean-reversion as ADDITIVE SKEW (not as a TAKER replacement) was never
   fairly tested across all priority products.
3. Drift-aware per-product `inv_skew` β (vs the global β=0.20) may help the 10
   KS-flagged products.

5-fold protocol identical to `parameter_tuning/audit/_audit_lib.py`
(F1=F3=F5=day3, F2=day4, F4=day2). Match mode `worse` for headline.

Decision metric: **fold_min** (highest), tie-broken by Sharpe.

## Layout

- `00_baseline_lock/` — locked baseline numbers
- `01_robot_dishes_specialised/` — Phase 1 (ROBOT_DISHES dedicated handler)
- `02_mr_skew_overlay/` — Phase 2 (AR(1) MR as additive skew)
- `03_drift_aware_inv_skew/` — Phase 3 (per-product β for KS-flagged products)
- `04_combined_assembly/` — Phase 4 (assembled algo + ablation v00..v04)
- `05_stress/` — Phase 5 (stress battery)
- `06_findings/` — Phase 6 (headline / decisions / dropped)
- `data_views/backtest_logs/` — raw stdout logs

`progress.md` is the running log (append only).
