# What was dropped

This is the audit-of-audits: configurations that improved one metric but
failed the strict 5-gate, and hypotheses that were tested and rejected.

## Configurations that improved mean PnL but failed the strict gate

### Phase 1 sub-variants (1d AR(1)-only)

All 20 cells of variant 1d (AR(1)-only, no log-pair tilt) FAIL the gate.
Best 1d cell (1d_a2.5_b0.2) had fold_min=438,344 — **-7,856 below
baseline** despite the AR(1) signal being "documented" at φ=-0.232. The
underlying problem: the φ=-0.232 is regime-shifted to Day 4 only.

Source: `01_robot_dishes_specialised/ablation_with_gate.csv`.

### Phase 2 — every cell

12 of 12 Phase-2 cells failed the gate. The closest to passing:
- `OXYGEN_SHAKE_EVENING_BREATH` α=0.5: Δfold_min=-188 — already failed
  gate (d).

The 7 priority products produced ZERO surviving alphas under the additive
maker-skew formulation. AR(1) on Δmid is real signal but the mechanism
(adjusting fair value by `-φ · Δmid · α`) does not exceed the order gate
at the AR(1) magnitudes observed.

Source: `02_mr_skew_overlay/per_product_alpha_sweep.csv`.

### Phase 3 — standalone single-product changes

70 of 70 standalone β-change cells failed the strict 5-gate. Notable
near-misses (rejected as standalone, salvaged in Phase 4 combined):

| cell | Δfold_min | Δmean | fail mode |
|---|---:|---:|---|
| MICROCHIP_OVAL β=0.4 | +1,232 | +1,857 | gate (a): mean<+2K |
| MICROCHIP_OVAL β=0.6 | +6,317 | -2,049 | gate (a) by big margin; mean fell |
| SLEEP_POD_POLYESTER β=0.4 | +1,292 | +1,857 | gate (a): mean<+2K |
| SLEEP_POD_POLYESTER β=0.05 | +1,652 | +87 | gate (a),(b): median dropped |
| SLEEP_POD_POLYESTER β=0.6 | +1,260 | +1,510 | gate (a): mean<+2K |
| OXYGEN_SHAKE_EVENING_BREATH β=0.05 | +4 | -882 | gate (a),(b),(c) — actively harmful |

Source: `03_drift_aware_inv_skew/per_product_beta_sweep.csv`.

### Phase 3 — relaxed combined

The relaxed combined sweep (v_combined relaxed in `combined_run.csv`)
applied 9 of 10 KS-flagged products' "best β" simultaneously. Result:
fold_min=449,084 (Δ=+2,884 — passes (d)), but **mean +889 fails gate
(a)** (needs +2K). Because most of the 9 products' β changes were no-ops
(produced 0 effect), the combined run mostly recovers MICROCHIP_OVAL's
gain plus SLEEP_POD_POLYESTER's gain, with the no-ops contributing zero.
The strict gate insisted on +2K mean, which the strict-pass v04 (with
Phase 1 underneath) clears at +8,849.

Source: `03_drift_aware_inv_skew/combined_run.csv`.

## Hypotheses fully rejected

### H2 — AR(1) MR as additive maker-skew

Falsified. The formulation `fair += -φ · Δmid · α` produces:
- Inert outputs for products with |φ| · |Δmid| · α < 0.25 (the maker's
  order gate vs best bid/ask — see `algo1_drop_harmful_only.py:435`).
- Adversely-selected outputs for products where the formula DOES cross
  the gate (e.g., OXYGEN_SHAKE_EVENING_BREATH).

To extract the AR(1) signal a different mechanism would be needed:
- TAKER trigger when |skew| > spread × threshold (Round-4 algo_mr1
  family).
- Conditional-on-spread maker quote shifting (would require multi-tick
  state and a regime detector for Day 4).

Both out of scope for this study.

### H1 partial — AR(1) standalone on ROBOT_DISHES

The Phase-1 1d sub-variant (AR(1)-only, no log-pair) was the strongest
test of "is AR(1) ROBOT_DISHES tradeable". 20 cells, 0 passed. The reason
is the regime-shift documented in `01_diagnostic.md` — the documented
pooled φ=-0.232 is **entirely Day 4**, and applying it as a constant
across all days adds noise on Days 2 and 3.

## What remained "in the drawer" but worth recording

- Phase 1 1b combined (AR(1) + log-pair) cells passed the gate. 80 of 80
  cells passed. Top 1b cell (1b_a1.5_c7_b0.6) Δfold_min=+9,892 — **slightly
  worse** than the best 1c cell (+10,500). This suggests the AR(1) is
  marginally drag (-600 fold_min on the best parameterisation) when
  layered on top of log-pairs. Not enough to flip the conclusion: ship
  log-only.

- Phase 3 ROBOT_DISHES β sweep produced ZERO movement at any β value. This
  is because the dedicated-handler design in Phase 1 already overrides
  ROBOT_DISHES' β to 0.6, so changing the global β for ROBOT_DISHES has no
  effect when the dedicated handler is also active. (And without the
  dedicated handler, ROBOT_DISHES inventory rarely approaches the cap, so
  any global β between 0.05 and 0.60 is a no-op there too.)

- Phase 3 GALAXY_SOUNDS_BLACK_HOLES at β=0.6 was selected by the relaxed
  decision logic but had Δ=0 — pure noise tie-break. Dropped from v04.

## Verdict on hypothesis-rejection rate

3 hypotheses tested:
- 1 fully passed (H1 — log-pair handler ships)
- 1 partially passed (H3 — combined ride-along contributes +2.5K)
- 1 fully rejected (H2 — AR(1) skew falsified)

This is a **healthy yield**: ~50% of pre-registered hypotheses generate
ship-grade alpha. The mission's strict gate filtered out 7+ near-miss
configurations that would have looked tempting in a relaxed analysis.

## Further work flagged

1. **AR(1) as taker signal**: rebuild the AR(1) overlay so that when
   |skew| > 0.4 dollars, ROBOT_DISHES (or another mean-reverter) takes
   instead of just shifting the maker fair. Should reach the Day-4 alpha
   that 1d failed to.
2. **Day-detection regime switch**: Day 4 has 8× the variance of Days 2/3
   for ROBOT_DISHES. A regime-detector that switches AR(1) on/off based on
   recent var(Δmid) would activate the overlay only when productive.
3. **More log-pairs**: the log-study found 11 truly-novel log-pairs but
   only 4 (the ROBOT_DISHES cluster) passed Phase-6 OOS. Re-running the
   OOS cycle on a wider universe (e.g., other potential hubs like
   PEBBLES_S, PANEL_2X4) might surface additional dedicated-handler
   candidates.
