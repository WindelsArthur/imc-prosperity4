# Phase 3 — Drift-aware per-product inv_skew β — findings

## Verdict: **DOES NOT SHIP STANDALONE** (gate fails on every product)

10 KS-flagged products × 7 β values = 70 cells swept. **Zero cells pass the
strict 5-gate** as a standalone change vs the audit baseline. The hypothesis
that drift-prone products benefit from a tighter or looser inv_skew β
(vs the global 0.20) is **rejected** under the mission's strict criterion.

## Per-product strict-gate verdict

| product | best β | Δfold_min | Δmean | Δmedian | strict |
|---|---:|---:|---:|---:|:---:|
| ROBOT_DISHES | (any) | 0 | 0 | 0 | ✗ no-op |
| OXYGEN_SHAKE_CHOCOLATE | (any) | 0 | +56 | +94 | ✗ no-op |
| MICROCHIP_OVAL | 0.40 | +1,232 | **-2,049** | **-3,741** | ✗ b,a fail |
| MICROCHIP_SQUARE | (any) | 0 | 0 | 0 | ✗ no-op |
| UV_VISOR_AMBER | (any) | 0 | +102 | +170 | ✗ no-op |
| SLEEP_POD_POLYESTER | 0.05 | +1,652 | +87 | **-898** | ✗ a,b fail |
| MICROCHIP_TRIANGLE | (any) | 0 | 0 | 0 | ✗ no-op |
| OXYGEN_SHAKE_EVENING_BREATH | 0.05 | +4 | -882 | **-1,614** | ✗ a,b,c fail |
| PANEL_1X4 | (any) | 0 | -96 | -32 | ✗ no-op |
| GALAXY_SOUNDS_BLACK_HOLES | (any) | 0 | +25 | +42 | ✗ no-op |

## Two near-misses (potentially salvageable in Phase 4 combined)

### MICROCHIP_OVAL — β=0.40
- F1 ↑ +602, F2 ↑ +1,232, F3 ↑ +602, F4 ↑ +58, F5 ↑ +602
- All 5 folds positive — gate (c) ✓
- Mean +1,857 — gate (a) FAILS (needs ≥ +2K)
- Median +602 — gate (b) ✓
- fold_min +1,232 — gate (d) ✓
- **Hypothesis preserved as a partial signal:** β=0.40 improves the F2 floor
  by +1,232 with no fold regressing, but is single-handedly insufficient
  to pass the +2K mean threshold.

### SLEEP_POD_POLYESTER — β=0.40
- F1 +1,752, F2 +1,292, F3 +1,752, F4 +2,737, F5 +1,752 — **all positive**
- Mean +1,857, median +1,752, fold_min +1,292
- **Same gate-(a) shortfall** as MICROCHIP_OVAL.

These two products show genuine, all-folds-positive uplift but each only
~+1,300 fold_min and ~+1,800 mean — below the strict 2K mean threshold.
They are **candidates for inclusion in the Phase 4 combined assembly** on
top of the Phase-1 ROBOT_DISHES handler, where the Phase-1 mean uplift
(+6,372) already gives ample headroom for gate (a).

## Why most products were no-ops

The flagged products that show Δ=0 across the entire β sweep have inventory
that rarely approaches the cap (typically held within ±2 units), so the
inv_skew term `-pos · β` stays small (≤ 0.4 dollars even at β=0.20).
Changing β between 0.05 and 0.60 doesn't cross the order-gating threshold.
This is the same mechanism that made Phase 2's AR(1) skew inert.

## OXYGEN_SHAKE_EVENING_BREATH — actively harmful

`OXYGEN_SHAKE_EVENING_BREATH` β=0.05 reduces the inventory pull and worsens
the 3-day median by 1,614 — the product turns over too aggressively without
the inventory penalty to brake it. Confirms its KS-flag classification: it
NEEDS the global β=0.20 (or higher).

## Output artefacts

- `01_run_beta_sweep.py` — sweep runner (70 cells)
- `02_apply_strict_gate.py` — strict-gate evaluator
- `per_product_beta_sweep.csv` — every cell × full per-fold metrics
- `decisions.csv` — relaxed decision (no-ops mark as "retained")
- `decisions_strict.csv` — strict decision (zero retained)
- `retained_betas_strict.json` — empty
- `combined_run.csv` — relaxed combined run (fold_min +2,884, mean +889 — fails gate (a))
- `ablation.csv` — full sweep with baseline reference

## Action: defer to Phase 4

Phase 3 contributes ZERO standalone. Phase 4 will test whether
MICROCHIP_OVAL=0.40 and/or SLEEP_POD_POLYESTER=0.40 ride on top of the
Phase-1 handler without breaking it.
