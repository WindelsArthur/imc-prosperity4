# Post-audit decisions log

## Hypothesis verdicts

### Hypothesis 1: ROBOT_DISHES structural alpha — **PASS**

The dedicated-handler approach (ROBOT_DISHES removed from global pair_skew,
replaced by 4 novel log-pairs from `log_study/06_oos_validation`) yields
**+10,500 fold_min** uplift, **+20,803 ROBOT_DISHES 3-day**, with all 5
folds positive Δ.

Winning config: `1c_c10_b0.6` — log-pair-only (no AR(1) overlay), per-pair
clip=10 dollars, ROBOT_DISHES inv_skew_β=0.6 (vs global 0.20).

96 of 116 sweep cells passed the strict gate; the winner was chosen by
highest fold_min, tie-broken by Sharpe. AR(1)-only cells (1d) ALL FAILED
because the AR(1) signal is regime-shifted to Day 4 only (φ_d2=-0.001,
φ_d3=-0.004, φ_d4=-0.290) and applying the pooled coef as a constant
overlay across all days is harmful on Days 2/3.

Citations:
- `01_robot_dishes_specialised/01_diagnostic.md` — per-day AR(1) regime
- `01_robot_dishes_specialised/findings.md` — full sweep result
- `01_robot_dishes_specialised/winner.json` — chosen cell
- `01_robot_dishes_specialised/ablation.csv` — every cell
- `04_combined_assembly/algo1_post_audit_v01.py` — the assembled algo (Phase 1 only)

### Hypothesis 2: AR(1) MR as additive skew on priority products — **FAIL**

Cross-day-stability filter (same-sign across all 3 days, |mean φ| > 0.05)
admits 3 of 7 priority products: OXYGEN_SHAKE_EVENING_BREATH (φ=-0.115),
ROBOT_IRONING (φ=-0.118), OXYGEN_SHAKE_CHOCOLATE (φ=-0.080). The other 4
have AR(1) coefs an order of magnitude smaller and are noise.

Per-product α sweep over {0.5, 1.0, 1.5, 2.0}:
- OXYGEN_SHAKE_CHOCOLATE: zero effect at every α (skew below order gate).
- ROBOT_IRONING: zero effect at every α (skew below order gate).
- OXYGEN_SHAKE_EVENING_BREATH: -188 to -952 fold_min (overlay actively
  hurts).

Conclusion: the AR(1) skew magnitude `|φ · Δmid · α|` is bounded by
~|0.12 · 1 · 2| = 0.24 dollars — just below the maker's `fair > bid - 0.25`
threshold for products with |φ| ≤ 0.12. The hypothesis is rejected as
formulated; using AR(1) as a TAKER signal would be a different study (out
of scope).

Citations:
- `02_mr_skew_overlay/findings.md`
- `02_mr_skew_overlay/per_product_alpha_sweep.csv`
- `02_mr_skew_overlay/per_product_decisions.csv` (all "✗ retained=False")
- `02_mr_skew_overlay/ar1_coefs_per_product.csv`

### Hypothesis 3: Drift-aware per-product inv_skew β — **PARTIAL**

10 KS-flagged products × 7 β values swept. **Zero cells pass the strict
5-gate as standalone changes** vs the baseline. However, two products
showed all-folds-positive partial uplift:

- **MICROCHIP_OVAL β=0.40** — Δfold_min=+1,232, mean=+1,857, all folds
  positive. Failed gate (a) (mean ≥ +2K) standalone.
- **SLEEP_POD_POLYESTER β=0.40** — Δfold_min=+1,292, mean=+1,857, all
  folds positive. Failed gate (a) standalone.

These two were promoted to Phase 4 combined assembly. When applied
**together** (no other changes), the combined Δfold_min=+2,525, mean=+2,476
— gate (a) clears with margin. When applied **on top of Phase 1** (v04),
combined Δfold_min=+13,026, mean=+8,849 — gate (a) clears with large
margin. Both ride-along nicely with the Phase-1 handler.

Citations:
- `03_drift_aware_inv_skew/findings.md`
- `03_drift_aware_inv_skew/decisions_strict.csv` (all "✗ retained=False" standalone)
- `04_combined_assembly/full_ablation.csv` (v03 and v04 rows)

## Per-product MR-overlay decisions (Phase 2)

| product | best α | individual Δfold_min | retained_in_combined |
|---|:---:|---:|:---:|
| OXYGEN_SHAKE_CHOCOLATE | (any) | 0 | ✗ — overlay inert |
| ROBOT_IRONING | (any) | 0 | ✗ — overlay inert |
| OXYGEN_SHAKE_EVENING_BREATH | 0 (rejected) | -188 | ✗ — overlay harmful |
| PEBBLES_L | – | – | ✗ — failed cross-day filter |
| PEBBLES_M | – | – | ✗ — failed cross-day filter |
| PEBBLES_XS | – | – | ✗ — failed cross-day filter |
| ROBOT_MOPPING | – | – | ✗ — failed cross-day filter |

## Per-product β decisions (Phase 3, KS-flagged)

| product | chosen β (strict) | strict pass | combined v04 effect |
|---|:---:|:---:|---|
| ROBOT_DISHES | 0.20 | ✗ | (overridden by Phase-1 handler β=0.6) |
| OXYGEN_SHAKE_CHOCOLATE | 0.20 | ✗ | left at default |
| MICROCHIP_OVAL | 0.40 | ✗ standalone, ✓ combined | retained in v04 |
| MICROCHIP_SQUARE | 0.20 | ✗ no-op | left at default |
| UV_VISOR_AMBER | 0.20 | ✗ no-op | left at default |
| SLEEP_POD_POLYESTER | 0.40 | ✗ standalone, ✓ combined | retained in v04 |
| MICROCHIP_TRIANGLE | 0.20 | ✗ no-op | left at default |
| OXYGEN_SHAKE_EVENING_BREATH | 0.20 | ✗ harmful at lower β | left at default |
| PANEL_1X4 | 0.20 | ✗ no-op | left at default |
| GALAXY_SOUNDS_BLACK_HOLES | 0.20 | ✗ no-op | left at default |

## Why the gate strictness matters

The mission's strict 5-gate rejected 7 of 9 candidates that had positive
fold_min uplift but failed gate (a) (mean ≥ +2K) or gate (b) (median ≥
baseline). This filter is doing real work — many tempting "near-misses"
have positive fold_min but worse median or mean, indicating that the
β change shifted PnL between days rather than added genuine alpha. The two
products promoted to Phase 4 (MICROCHIP_OVAL=0.40, SLEEP_POD_POLYESTER=0.40)
both have all-folds-positive deltas — a stronger criterion than fold_min
alone.

## Final ship target

`ROUND_5/autoresearch/post_audit/04_combined_assembly/algo1_post_audit.py`
== `algo1_post_audit_v04.py`. Reproducible via:

```
imcp/bin/prosperity4btest cli \\
  ROUND_5/autoresearch/post_audit/04_combined_assembly/algo1_post_audit.py \\
  5-2 5-3 5-4 --merge-pnl --no-progress --match-trades worse \\
  $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```

Expected fold_min: 459,226. Expected 3-day total: 1,420,758.
