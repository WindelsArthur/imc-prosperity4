# Parameter decisions — algo1_tuned

## Tier 1 (universal) — REVERT TO BASELINE

LHS (n=50) + TPE (n=40) + plateau analysis (24 cells) found **0 configurations** passing the joint gates (a)+(b)+(c)+(e) vs the locked baseline.

| Param | Baseline kept | Plateau width | Fold votes | Why |
|---|---|---|---|---|
| PAIR_TILT_DIVISOR | 3.0 | wide (1.5-6.0 all viable) | 5/5 | LHS+TPE optima clustered at div ∈ {1.7-3.5}, all with median ≤ baseline's 363,578 |
| PAIR_TILT_CLIP | 7.0 | wide (5-12 viable) | 5/5 | Lower clip (5-6) drops PnL; higher clip (10-12) gives slight median drop with mean uplift but fails gate (b) |
| INV_SKEW_BETA | 0.20 | broad (0.10-0.30 viable) | 5/5 | Beta is robust; small shifts don't change PnL meaningfully |
| QUOTE_BASE_SIZE_CAP | 8 | broad (6-10 viable) | 5/5 | Both 6 and 10 give similar PnL; 8 is plateau center |
| FAIR_QUOTE_GATE | 0.25 | tight (0-0.5 viable) | 5/5 | Hardcoded 0.25 in make() — kept as-is |

**Best LHS candidate (rejected on gate b)**: lhs_011 with div=1.81, clip=10.56, beta=0.135, qbsc=6, gate=0.13. Mean 370,642 (+8,608), but median 362,839 (-739) → fails (b) by 0.2%. Fold-min HIGHER than baseline (362,839 vs 354,448) — interesting robustness profile but not strict gate-pass.

**Reason for revert**: The R4 baseline parameters were already R4 sweep winners. Tier-1 search confirms: baseline sits on a robust plateau and **no neighbor uniformly dominates**. Reverting to baseline is the conservative-correct choice per the gate.

## Tier 2 group-scoped — STRONG UPLIFT

### PEBBLES block (+16K stand-alone uplift; broad plateau)

| Param | Old | New | Plateau width | Decision |
|---|---|---|---|---|
| PEBBLES_SKEW_DIVISOR | 5.0 | **8.0** | 6 cells identical at DIVISOR=8 across CLIP ∈ {2,3,5} and BIG_SKEW ∈ {2.5,3.5} | Loosened |
| PEBBLES_SKEW_CLIP | 3.0 | **5.0** | Within-plateau tie | Loosened |
| PEBBLES_BIG_SKEW | 1.8 | **3.5** | At BIG_SKEW=3.5, aggressive cross never fires | Effectively disabled |

### SNACKPACK block (+114K stand-alone uplift)

| Param | Old | New | Decision |
|---|---|---|---|
| SNACKPACK_SKEW_DIVISOR | 5.0 | 5.0 | Kept |
| SNACKPACK_SKEW_CLIP | 5.0 | **3.0** | **Tightened** |
| SNACKPACK_BIG_SKEW | 3.5 | 3.5 | Kept (effectively disabled) |

### QUOTE_AGGRESSIVE_SIZE — IRRELEVANT

| Param | Old | New | Note |
|---|---|---|---|
| QUOTE_AGGRESSIVE_SIZE | 2 | 1 | All values 1-5 give IDENTICAL PnL because both BIG_SKEW thresholds are now high enough that aggressive cross never fires. Picked 1 as nominal. |

**Both basket-invariant skews were OVER-aggressive in baseline.** Loosening lets cross-group pair tilts dominate, where the actual PnL signal lives. Plateau is broad — robust.

## Tier 3 per-product caps — MIXED

| Product | Old | New | Δ median (this product alone) | Decision |
|---|---:|---:|---:|---|
| SLEEP_POD_LAMB_WOOL | 3 | **10** | +7,751 | Cap REMOVED — was profitable bleeder under new Tier-2 |
| UV_VISOR_MAGENTA | 4 | 4 | — | Reverted |
| PANEL_1X2 | 3 | 3 | — | Reverted |
| TRANSLATOR_SPACE_GRAY | 4 | 4 | — | Reverted |
| ROBOT_MOPPING | 4 | **2** | +2,910 | Tightened — true bleeder confirmed |
| PANEL_4X4 | 4 | 4 | — | Reverted |
| GALAXY_SOUNDS_SOLAR_FLAMES | 4 | 4 | — | Reverted |
| SNACKPACK_RASPBERRY | 5 | **10** | (uplift) | Cap REMOVED |
| SNACKPACK_CHOCOLATE | 5 | **10** | (uplift) | Cap REMOVED |
| PEBBLES_L | 4 | 4 | — | Reverted |

**Sleep-pod / snackpack cap releases reflect that these products were originally bleeders under baseline Tier-2, but the new looser Tier-2 makes them PROFITABLE.** The "Phase B bleeder" calibration from R2 was tuned to a v3-era algo and is stale.

## Tier 4 pair count — DOMINANT LEVER

| Param | Old | New | Δ |
|---|---:|---:|---:|
| N_PAIRS (cross-group) | 30 | **157** | +178K incremental over Tier-2+3 |
| RANK_METHOD | combined_pnl | combined_pnl | tied with combined_sharpe at N=157 since all pass-filter pairs are included |

**PnL increases monotonically with N** — no capacity collision observed up to N=157 (the entire ADF<.05 + min_fold_sharpe≥0.7 surviving pool). Sharpe drops to 13.0 (more variance) but median PnL +101K. fold_min jumps from 391K → 450K (+58K).

| N | rank | fold_median | fold_min | 3-day | maxDD |
|---:|---|---:|---:|---:|---:|
| 20 | combined_pnl | 327,695 | 297,026 | 967,586 | 26,323 |
| 30 | combined_sharpe | 346,464 | 346,464 | 1,051,344 | 32,223 |
| 50 | combined_sharpe | 386,666 | 354,812 | 1,139,010 | 30,526 |
| 75 | combined_sharpe | 416,293 | 376,312 | 1,217,824 | 33,050 |
| 100 | combined_sharpe | 449,358 | 402,732 | 1,327,736 | 31,886 |
| 150 | combined_pnl | 463,882 | 451,367 | 1,437,532 | 27,757 |
| **157** | **combined_pnl** | **465,320** | **450,479** | **1,436,024** | **27,243** |

N=150 is essentially identical to N=157. The plateau is wide; we ship N=157 for completeness.
