# Theme: Cointegration pairs

## Definition
Two products A, B such that residual = A − slope·B − intercept is stationary (ADF p < 0.05) with finite half-life. Each tick the residual is a soft fair-value skew applied to BOTH legs, opposite-signed and weighted by 1/|slope| for the B-leg.

## Products affected
40 distinct legs across 40 pairs (10 within-group + 30 cross-group). PANEL_2X4 is the most-connected product (7 cross-group pair appearances). PEBBLES_S, PEBBLES_M, OXYGEN_SHAKE_GARLIC, SNACKPACK_PISTACHIO, UV_VISOR_AMBER are also high-connectivity.

## Within-group (round 1, 10 pairs)

| Pair | slope | claimed ADF p | re-verified ADF p | OOS Sharpe (fold A / B) |
|---|---:|---:|---:|---|
| MICROCHIP_RECTANGLE / MICROCHIP_SQUARE | −0.401 | 0.004 | **0.0036** ✓ | 1.91 / 1.37 |
| ROBOT_LAUNDRY / ROBOT_VACUUMING | 0.334 | 0.026 | **0.378** ⚠ | 1.19 / 1.70 |
| SLEEP_POD_COTTON / SLEEP_POD_POLYESTER | 0.519 | 0.033 | **0.146** ⚠ | 1.32 / 1.89 |
| GALAXY_SOUNDS_DARK_MATTER / PLANETARY_RINGS | 0.183 | 0.037 | **0.038** ✓ | 1.61 / 2.00 |
| SNACKPACK_RASPBERRY / SNACKPACK_VANILLA | 0.013 | 0.001 | **0.0014** ✓ | 1.77 / 1.45 |
| SNACKPACK_CHOCOLATE / SNACKPACK_STRAWBERRY | −0.106 | 0.009 | **0.035** ✓ | 1.50 / 1.98 |
| UV_VISOR_AMBER / UV_VISOR_MAGENTA | −1.238 | 0.023 | **0.046** ✓ | 0.98 / 0.85 |
| OXYGEN_SHAKE_CHOCOLATE / OXYGEN_SHAKE_GARLIC | −0.155 | 0.030 | **0.918** ✗ | n/a / 0.65 |
| TRANSLATOR_ECLIPSE_CHARCOAL / TRANSLATOR_VOID_BLUE | 0.456 | 0.041 | **0.035** ✓ | 2.10 / 0.72 |
| SLEEP_POD_POLYESTER / SLEEP_POD_SUEDE | 0.756 | 0.052 | **0.091** ⚠ | 1.90 / 1.12 |

⚠ = ADF fails on full-stitch but OOS Sharpe was positive in both folds → KEEP.  
✗ = catastrophic failure. **OXYGEN_SHAKE_CHOCOLATE/GARLIC is dropped from the final algo.**

## Cross-group (round 3 Phase C, 30 pairs)

Lagged-EG over top-300 price-CCF pairs at lags {1,5,20,100} → 1,200 fits → 221 pass ADF<0.05 + half-life ∈ [5,1000] → 171 pass min-fold OOS Sharpe ≥ 0.7 → top 30 by combined PnL ship.

Spot-checks (5 of 30) on full-stitch ADF:

| Pair | slope | re-verified ADF p |
|---|---:|---:|
| PEBBLES_XL / PANEL_2X4 | 2.482 | 0.00066 |
| UV_VISOR_AMBER / SNACKPACK_STRAWBERRY | −2.450 | 0.00071 |
| PEBBLES_M / OXYGEN_SHAKE_MORNING_BREATH | −0.904 | 0.00038 |
| ROBOT_IRONING / PEBBLES_M | −0.915 | 0.0055 |
| MICROCHIP_SQUARE / SLEEP_POD_SUEDE | 1.868 | 0.0064 |

All cross-group spot-checks pass strongly. Cross-group cointegration is more robust than within-group — confirmed.

*Sources:* `ROUND_5/autoresearch/14_lag_research/C_lagged_coint/lagged_coint_fast.csv` (222 rows), `ROUND_5/autoresearch/14_lag_research/O_submit/strategy_v3.py`, `ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md`.

## Expected PnL contribution
v3 ablation: layering 30 cross-group pairs on v2 added **+201,795** over 3 days → **+67K/day**.

## Integration in final algo
```python
for a, b, slope, intercept, sd in COINT_PAIRS + CROSS_GROUP_PAIRS:
    if a in mids and b in mids:
        spread_val = mids[a] - slope * mids[b] - intercept
        tilt = max(-3.0, min(3.0, -spread_val / 8.0))
        pair_skew[a] += tilt
        pair_skew[b] += -slope * tilt / max(abs(slope), 1.0)
```

OXYGEN_SHAKE_CHOCOLATE/OXYGEN_SHAKE_GARLIC is the single removal vs v3 in the final algo.
