# Theme: Per-product mean-reversion (mr_study)

## Source
Standalone study at `ROUND_5/autoresearch/mr_study/`. 50 products × 45 fair-value families × parameter grid. Phase 0 → universe stats. Phase 1 → 4500 (prod, FV, fold) IC/half-life/ADF rows. Phase 2 → 37,200 numba-JIT taker simulations. Phase 4 → strict qualifying (pnl_A>0 ∧ pnl_B>0 ∧ min_sharpe ≥ 0.5) gives 6 products + 1 relaxed = 7 TAKERs. Phase 6 → single-file `strategy_mr.py` with TAKER + MM + IDLE modes.

## Headline (mr_v6)
Total profit: **399,636** (engine), **283,223** final 3-day. Average daily OOS PnL: ~95K. Sharpe 0.93. Mode split: 7 TAKER, 35 MM, 8 IDLE.

## TAKER products (7)

| Product | FV family | z_in | z_out | mr_v6 PnL | v3 PnL | Δ (mr_v6 − v3) |
|---|---|---:|---:|---:|---:|---:|
| ROBOT_DISHES | rolling_mean w=50 | 2.5 | 0.5 | +11,219 | −2,982 | **+14,201** |
| PEBBLES_M | rolling_quadratic w=2000 | 1.0 | 0.1 | +9,103 | +943 | +8,160 |
| SLEEP_POD_POLYESTER | range_mid w=500 | 1.75 | 0.1 | +8,049 | +4,040 | +4,009 |
| ROBOT_MOPPING | rolling_quadratic w=500 | 1.25 | 0.0 | +10,225 | +994 | **+9,231** |
| PEBBLES_XS | rolling_quadratic w=500 | 1.25 | 0.1 | +15,016 | +12,928 | +2,088 |
| OXYGEN_SHAKE_CHOCOLATE | rolling_linreg w=500 | 1.0 | 0.0 | +8,864 | +4,867 | +3,997 |
| PEBBLES_L | rolling_median w=100 | 1.5 | 0.1 | +9,434 | −12,237 | **+21,671** |

Total uplift if all TAKERs additive: +63K. But v3 already integrates basket invariants and pair overlays that interact with these — the actual additive uplift will be smaller.

## IDLE products (8)
ROBOT_IRONING, MICROCHIP_RECTANGLE, TRANSLATOR_SPACE_GRAY, GALAXY_SOUNDS_PLANETARY_RINGS, SLEEP_POD_SUEDE, SLEEP_POD_LAMB_WOOL, GALAXY_SOUNDS_SOLAR_FLAMES, UV_VISOR_MAGENTA. mr_v6 chose to skip — chronic MM losers with too much directional drift.

## MM with signal-skew (2)
OXYGEN_SHAKE_EVENING_BREATH (alpha_skew=1.5), SNACKPACK_CHOCOLATE (alpha_skew=1.0) using `ar_diff p=1`. mr_v6 found these mildly additive on top of MM.

## Why mr_v6 ≠ v3 on raw PnL
mr_v6 = 399K, v3 = 733K. Difference = 334K = the value of basket-invariant + 30 cointegration overlays that mr_v6 doesn't run. **mr_study's value is the per-product TAKER thresholds, not the total PnL.**

## Decision for final algo
- **Phase H ablation candidates:** add TAKER mode for the 4 products with highest mr_v6 vs v3 delta:
  1. PEBBLES_L: +21.7K (chronic v3 loser)
  2. ROBOT_DISHES: +14.2K (chronic v3 loser, strong AR(1))
  3. ROBOT_MOPPING: +9.2K (cap=4 in v3 but still tiny PnL)
  4. PEBBLES_M: +8.2K
- For each, test whether TAKER trade INSIDE basket-invariant skew is additive or substitutive (likely partial overlap because TAKER and basket both bias the same direction).
- IDLE products in v3 already underperform; trying IDLE adds 0 to PnL but reduces drawdown (test in Phase H stress).

## Expected PnL contribution
+10K to +30K over v3 if 2-3 TAKERs additively combine. Phase H ablation will measure exactly.
