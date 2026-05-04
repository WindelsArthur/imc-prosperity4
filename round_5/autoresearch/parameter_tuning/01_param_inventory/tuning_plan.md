# Tuning Plan & Search Budget

## Total compute budget
~24s per merged 3-day backtest. Available: ~30 hours wall-clock single-threaded.
Parallelize with joblib across 8 cores → effective ~10-12s/config.

Hard cap on configs across all phases: ~3,000 (≈10 wall-clock hours @ 12s ea).

## Phase budget allocation

| Phase | Configs | Description |
|---|---|---|
| 2a Tier-1 LHS coarse | 100 | Latin Hypercube over 5D Tier-1 cube |
| 2b Tier-1 TPE | 150 | Optuna multivariate TPE on top of LHS |
| 2c Tier-1 plateau | 5×9=45 | 1D sweep around TPE optimum, per param |
| 2d Tier-1 bootstrap | 5 | Top-5 candidates, full bootstrap re-eval |
| 3a PEBBLES grid | 7×6×5=210 | Reduced cube |
| 3b SNACKPACK grid | 7×6×5=210 | Reduced cube |
| 3c QUOTE_AGGR_SIZE | 5 | 1D sweep |
| 4a PROD_CAP per-product | 8×10=80 | Sweep cap ∈ {2..10} per product |
| 4b new-cap candidates | 8×5=40 | Sweep on 5 weakest uncapped products |
| 4c pair-specific clips | 5×5=25 | Top-5 pairs, clip ∈ {3,5,7,10,15} |
| 5 N_PAIRS sweep | 8×3=24 | N ∈ {20,30,50,75,100,125,150,171} × 3 ranking methods |
| 6 stress battery | 50+15+1+1+3 ≈ 70 | LHS perturb + match/lat/lim/day-removal |
| 7 ablation v00..v05 | 6 | Final additive ablation |
| Total | ~970 | |

Realistic 12s wall-clock per config → ~3.2 hours. Comfortable.

## Strategy notes
- Tier-1 dominates expected uplift — most aggressive search budget.
- Tier-2 is full grid (210 cells per group) since it's fast and the cubes are small.
- Tier-3 per-product sweeps trivially parallel; ~80 configs.
- N_PAIRS may dominate if structural — included as Phase 5.
- Stress battery: ~70 configs. Critical, do not skip.

## What can be cut if compute runs short
- Tier-1 TPE 150→80 trials.
- Phase 4c (pair-specific clips) — lowest expected gain.
- Phase 6 LHS perturbation 50→20.

NEVER cut Phase 6 limit-8 stress or day-removal stress.
