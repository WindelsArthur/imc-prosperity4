# Phase 1 — ROBOT_DISHES dedicated handler — findings

## Verdict: **SHIPS** (log-pair-only variant)

The dedicated-handler hypothesis is **PARTIALLY confirmed**:
- log-pair tilts (4 novel log-space pairs from `log_study/06_oos_validation`)
  add real, robust alpha when ROBOT_DISHES is removed from the global
  additive `pair_skew`. **+10,500 fold_min, +20,803 ROBOT_DISHES 3-day.**
- AR(1) overlay using the documented φ=-0.232 *hurts* on its own (1d cells
  fold_min DROP to ~438K, -7,856 vs baseline). It does not damage the
  combined 1b cells enough to fail the gate, but it does not contribute
  uplift either.

## Winner: `1c_c10_b0.6`

```
log_clip       = 10   (per-pair price-space dollar clip on log-pair tilt)
inv_beta_dishes = 0.6 (vs global 0.20) — keeps inventory tight despite the
                       new tilt vocabulary
USE_AR1        = False
USE_LOG        = True
```

| metric | baseline | winner | Δ |
|---|---:|---:|---:|
| fold_min | 446,200 | **456,700** | +10,500 |
| fold_median | 456,258 | 461,788 | +5,530 |
| fold_mean | 460,959 | 467,332 | +6,372 |
| total_3day | 1,392,280 | 1,410,995* | +18,715 |
| Sharpe | 20.32 | 22.90 | +2.58 |
| max_dd | 24,766 | 25,580 | +814 (1.03×) |
| ROBOT_DISHES 3d | 26,201 | **47,004** | +20,803 |

(*total_3day estimated from per-day decomposition; the per-fold values
are the test-day PnLs and are reproduced exactly.)

### Per-fold deltas (all positive, gate (c) satisfied)

| fold | baseline | winner | Δ |
|---|---:|---:|---:|
| F1 (day3) | 456,258 | 461,788 | +5,530 |
| F2 (day4) | 446,200 | 456,700 | +10,500 |
| F3 (day3) | 456,258 | 461,788 | +5,530 |
| F4 (day2) | 489,823 | 494,604 | +4,781 |
| F5 (day3) | 456,258 | 461,788 | +5,530 |

All 5 gates pass:
- (a) mean +6,372 ≥ +2,000 ✓
- (b) median +5,530 ≥ 0 ✓
- (c) every fold ≥ +4,781 ✓
- (d) fold_min +10,500 ≥ 0 ✓
- (e) max_dd 1.03× ≤ 1.20× ✓
- target dishes_3d +20,803 ≥ 0 ✓

96 of 116 sweep cells pass the strict gate (1b: 80/80, 1c: 16/16, 1d: 0/20).

## Why log-pair-only beats log-pair + AR(1)

The diagnostic showed that ROBOT_DISHES AR(1) on Δmid is **regime-shifted**:

| day | n | φ (AR(1)) | R² | var(Δmid) |
|---|---:|---:|---:|---:|
| 2 | 9,998 | -0.0009 | 0.00% | 93 |
| 3 | 9,998 | -0.0041 | 0.00% | 100 |
| 4 | 9,998 | **-0.2904** | 8.4% | **755** |
| pooled | 29,996 | -0.2317 | 5.4% | 316 |

The pooled φ=-0.232 cited in prior research is **entirely Day-4** (which has
8× the variance of Days 2/3 and a structural mean-reverting regime). Days
2/3 are essentially random walks. Applying a Day-4-fitted coef as a
constant overlay across all days adds noise in F1, F3, F4, F5 and
under-prepares for the actual Day-4 magnitude. The result: 1d (AR(1)-only)
delivers **negative** Δfold_min in every cell.

## Why log-pairs work

The 4 novel log-space pairs were independently OOS-validated in
`log_study/06_oos_validation/ship_list_dedup.csv` with all 5 folds positive:

| pair | β_log | α_log | isolated_5fold |
|---|---:|---:|---:|
| PEBBLES_S – ROBOT_DISHES | -1.4245 | 22.214 | 18,991 |
| ROBOT_DISHES – PANEL_2X4 | 0.7853 | 1.885 | 17,304 |
| GALAXY_SOUNDS_BLACK_HOLES – ROBOT_DISHES | 1.2349 | -2.030 | 13,529 |
| ROBOT_DISHES – SNACKPACK_STRAWBERRY | 1.2191 | -2.101 | 12,158 |

**Sum (isolated): 61,983.** The combined Δ on top of the baseline is
+20,803 on ROBOT_DISHES — significantly less than 62K because the existing
PEBBLES_XL→ROBOT_DISHES global pair (which is *removed* in this variant
from contributing to ROBOT_DISHES) was already capturing some of the same
information. The 1c handler gets clean attribution: it is the only source
of pair-skew on ROBOT_DISHES.

## Why β_dishes = 0.6 (3× the global)

`b0.6` cells consistently outperform `b0.20` cells in 1c (e.g. 1c_c10_b0.6
Δfm=+10,500 vs 1c_c10_b0.2 Δfm=+9,910). The new log-pair tilt is more
aggressive than the global pair-skew, so ROBOT_DISHES inventory turns over
faster — a stronger inv_skew β prevents the dedicated handler from holding
out positions too long. β=0.6 ≈ 1 dollar of fair-value pull per 2 units of
inventory at lim=10, i.e. fully bleeds inventory in ~3 ticks of mean
reversion.

## Output artefacts

- `01_diagnostic.md` — Step 1a diagnostic
- `02_run_sweep.py` — sweep runner (116 cells)
- `03_apply_gate.py` — strict gate evaluator
- `04_combined_handler.py` — winner algo (= 1c_c10_b0.6 assembled)
- `_dishes_template.py` — template used by sweep
- `ablation.csv` — every cell × full per-fold metrics
- `ablation_with_gate.csv` — with per-cell gate verdict
- `winner.json` — winner row JSON

Reproduce winner:
```
imcp/bin/prosperity4btest cli \\
  ROUND_5/autoresearch/post_audit/01_robot_dishes_specialised/04_combined_handler.py \\
  5-2 5-3 5-4 --merge-pnl --no-progress --match-trades worse \\
  $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
