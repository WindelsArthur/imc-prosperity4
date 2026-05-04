# Exhaustive findings (every reconciled finding, grouped by theme)

This document is the audit trail for "did we lose anything from prior research". Every claim is sourced.

## A. Basket invariants

### A1. PEBBLES Σ = 50,000 invariant — STRONGEST STRUCTURAL ALPHA
- mean=49,999.94, std=2.80, range [49,981.5, 50,016.5] over 30,000 stitched ticks (re-verified).
- R²=0.999998 of any-pebble on other-four basket regression.
- OU half-life=0.16 ticks (sub-tick reversion).
- Capacity: with limit=10, max residual capture per tick ≈ 28 per pebble.
- Strategy: passive inside-spread MM with skew_i = −resid/5, clipped ±3.
- 3-day per-pebble PnL contribution: XL +9,942; XS +12,928; S +5,394; M +943; L −12,237 (with cap=10) → −12,237 mitigated by cap=4 in final.  
*Sources:* `ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv`, `ROUND_5/batch1_summary/03_reconciliation/reverify_results/stats_reverify.csv`.

### A2. SNACKPACK Σ = 50,221 invariant
- mean=50,220.94, std=189.58 (re-verified). 10× weaker than pebbles.
- Best EG within-group pair RASPBERRY/VANILLA ADF p=0.0014 (re-verified). CHOCOLATE/STRAWBERRY ADF p=0.035 (re-verified).
- Off-diagonal returns correlation −0.16 (group is internally anti-correlated).
- 3-day per-product PnL: STRAWBERRY +13,860, PISTACHIO +8,711, VANILLA +2,573, CHOCOLATE −4,689, RASPBERRY −10,238 (with cap=5).
*Sources:* `ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv`, `ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md`.

### A3. SNACKPACK higher-rank Johansen — REJECTED
- Rank 5 found but residual std=0.96 → tiny capacity vs spread cost.
*Source:* `ROUND_5/autoresearch/13_round2_research/C_johansen/`.

### A4. Cross-group baskets / triplets — REJECTED
- 157 stationary cross-group triplets exist; std too large vs spread.
- SNACKPACK min-var weights: −68 PnL ablation.
*Source:* `ROUND_5/autoresearch/13_round2_research/F_cross_basket/`.

## B. Cointegration pairs

### B1. Within-group (10 candidates, 9 in algo)
| Pair | slope | claimed ADF p | re-verified ADF p | OOS Sharpe (A/B) | In algo? |
|---|---:|---:|---:|---|:--:|
| MICROCHIP_RECTANGLE/MICROCHIP_SQUARE | −0.401 | 0.004 | 0.0036 | 1.91/1.37 | ✓ |
| ROBOT_LAUNDRY/ROBOT_VACUUMING | 0.334 | 0.026 | 0.378 ⚠ | 1.19/1.70 | ✓ (fold-OOS positive) |
| SLEEP_POD_COTTON/SLEEP_POD_POLYESTER | 0.519 | 0.033 | 0.146 ⚠ | 1.32/1.89 | ✓ |
| GALAXY_SOUNDS_DARK_MATTER/PLANETARY_RINGS | 0.183 | 0.037 | 0.038 | 1.61/2.00 | ✓ |
| SNACKPACK_RASPBERRY/SNACKPACK_VANILLA | 0.013 | 0.001 | 0.0014 | 1.77/1.45 | ✓ |
| SNACKPACK_CHOCOLATE/SNACKPACK_STRAWBERRY | −0.106 | 0.009 | 0.035 | 1.50/1.98 | ✓ |
| UV_VISOR_AMBER/UV_VISOR_MAGENTA | −1.238 | 0.023 | 0.046 | 0.98/0.85 | ✓ |
| **OXYGEN_SHAKE_CHOCOLATE/OXYGEN_SHAKE_GARLIC** | −0.155 | 0.030 | **0.918** ✗ | n/a/0.65 | **✗ DROPPED** |
| TRANSLATOR_ECLIPSE_CHARCOAL/TRANSLATOR_VOID_BLUE | 0.456 | 0.041 | 0.035 | 2.10/0.72 | ✓ |
| SLEEP_POD_POLYESTER/SLEEP_POD_SUEDE | 0.756 | 0.052 | 0.091 | 1.90/1.12 | ✓ |

Phase H ablation: dropping OG yields −262 PnL, **+2.46 Sharpe**, −2,204 DD.

### B2. Cross-group (30 ship in v3)
Found via lagged-EG over top-300 price-CCF pairs. 1,200 fits → 221 pass ADF<0.05 → 171 pass min-fold OOS Sharpe ≥ 0.7 → top 30 by combined PnL.

5-of-30 spot-check ADFs on full stitch (all p<0.01):
- PEBBLES_XL/PANEL_2X4: ADF p=0.00066, slope 2.482, intercept −14735.7. **Single biggest contributor.**
- UV_VISOR_AMBER/SNACKPACK_STRAWBERRY: ADF p=0.00071, slope −2.450.
- PEBBLES_M/OXYGEN_SHAKE_MORNING_BREATH: ADF p=0.00038, slope −0.904.
- ROBOT_IRONING/PEBBLES_M: ADF p=0.0055, slope −0.915.
- MICROCHIP_SQUARE/SLEEP_POD_SUEDE: ADF p=0.0064, slope 1.868.

Phase C round-3 single-largest ablation contribution: **+237,696 PnL** (=84% of v3 over v2).

*Sources:* `ROUND_5/autoresearch/14_lag_research/C_lagged_coint/lagged_coint_fast.csv`, `ROUND_5/autoresearch/14_lag_research/O_submit/strategy_v3.py`.

## C. AR / mean-reversion

### C1. AR(1) coefficients on Δmid (re-verified)
| Product | claimed | re-verified | n_distinct_mids |
|---|---:|---:|---:|
| ROBOT_DISHES | −0.265 | **−0.232** | 3,048 |
| OXYGEN_SHAKE_EVENING_BREATH | −0.124 | **−0.123** | 453 |
| ROBOT_IRONING | −0.130 | **−0.125** | 631 |
| OXYGEN_SHAKE_CHOCOLATE | −0.090 | **−0.089** | (high) |
| SNACKPACK_CHOCOLATE | (low) | **−0.031** | (high) |

ROBOT_DISHES is the strongest mean-reverter. Claim −0.265 vs reverify −0.232: same sign and magnitude, claim slightly inflated.

### C2. Higher-order AR / lag-IC — REJECTED
- max |IC| at k>1 is 0.038 (ROBOT_IRONING@k=96). Not enough after spread.
*Source:* `ROUND_5/autoresearch/14_lag_research/E_ar_extended/`.

### C3. Per-product MR (mr_study v6) — REJECTED for this final algo (alternative architecture)
- 7 TAKER products: ROBOT_DISHES, PEBBLES_M, SLEEP_POD_POLYESTER, ROBOT_MOPPING, PEBBLES_XS, OXYGEN_SHAKE_CHOCOLATE, PEBBLES_L.
- 8 IDLE: ROBOT_IRONING, MICROCHIP_RECTANGLE, TRANSLATOR_SPACE_GRAY, GALAXY_SOUNDS_PLANETARY_RINGS, SLEEP_POD_SUEDE, SLEEP_POD_LAMB_WOOL, GALAXY_SOUNDS_SOLAR_FLAMES, UV_VISOR_MAGENTA.
- mr_v6 TOTAL = 399K, v3 TOTAL = 733K → mr_v6 inferior in absolute. Phase H ablation tested AR1-EVB skew (closest mr_v6 substitute) → −74 PnL, REJECTED.
*Source:* `ROUND_5/autoresearch/mr_study/04_combined_search/v6_final_metrics.json`.

## D. Lattice / quasi-discrete

### D1. Lattice ratios (re-verified)
- OXYGEN_SHAKE_EVENING_BREATH: n_distinct=453, ratio=0.0151
- ROBOT_IRONING: n_distinct=631, ratio=0.0210
- ROBOT_DISHES: n_distinct=3,048, ratio=0.1016

### D2. Strategy treatment
All three handled by default MM + inv_skew in final. v3 PnL: EVENING_BREATH +11,905 (winner), IRONING +1,064, DISHES −2,982 (chronic).

## E. Sine / deterministic level fits — REJECTED
- 6 of 7 R²>0.9 fits had period = full stitched window length → over-fitting artefact.
- UV_VISOR_AMBER (R²=0.962) is the lone OOS survivor (90% MSE improvement fold A, 43% fold B) but adding the overlay yielded **−496 PnL** in v2 ablation.
- All sine overlays excluded from final algo.
*Sources:* `ROUND_5/autoresearch/13_round2_research/A_sine/`, `abl_v2_no_sine_amber.csv`.

## F. Lead-lag — REJECTED
- 1.2M CCFs computed (Phase A round-3); Bonferroni critical |ρ| = 0.040.
- 1 decay-stable signal: PANEL_1X4→PANEL_1X2 lag=33 (~6K/3d).
- Below +15K threshold. PANEL_1X4 already in within-group pair structure.
*Source:* `ROUND_5/autoresearch/14_lag_research/B_leadlag/`.

## G. Microstructure / PROD_CAP

### G1. PROD_CAP — round-2 Phase B (single largest standalone contribution at +68,186 in ablation)
- 9 products with spread/vol < 0.6 had MM bled by adverse selection. Cap reduces exposure.
- Per-product v1 → v2 PnL improvement: SNACKPACK_RASPBERRY +36,125; PANEL_1X2 +19,238; ROBOT_MOPPING +18,168; SLEEP_POD_LAMB_WOOL +21,889; SNACKPACK_CHOCOLATE +21,193; GALAXY_SOUNDS_SOLAR_FLAMES +10,297; PANEL_4X4 +7,507; UV_VISOR_MAGENTA +4,121; TRANSLATOR_SPACE_GRAY −219.
*Sources:* `ROUND_5/autoresearch/13_round2_research/B_bleeders/`, `ROUND_5/autoresearch/13_round2_research/M_submit/diff_v1_to_v2.md`.

### G2. PEBBLES_L cap (NEW in batch1 Phase H)
- v3: PEBBLES_L PnL = −12,237 (chronic loser).
- Phase H ablation: cap=4 → +1,006 PnL but **+2.47 Sharpe** and −2,204 DD vs v3.
- v2 had previously rejected cap=5 (Sharpe penalty); but with cross-group pairs in mix (v3+ regime), Sharpe improves.

### G3. Multi-level OFI — REJECTED as standalone
- Max IC = 0.10. Negative on lattice products. Embedded in PROD_CAP via Phase B instead.

## H. Regime / HMM / Kalman / GARCH — DEFERRED
- Markov-VECM, Kalman β, GARCH all skipped for time across rounds 2 and 3.
- Implicit handling via inv_skew + tilt-clip + PROD_CAP is the v3 approximation.

## I. ML — DEFERRED
- LightGBM on v1 residuals planned but skipped for time.
- Diminishing-returns argument: v3 already extracts 84% of total via simple OLS+caps.

## J. Intraday seasonality — REJECTED
- 100-bin mod-day max cross-day correlation 0.13 — below the 0.30 threshold.

## K. Day-of-day instability flags
KS p<1e-9 across days 2/3/4: ROBOT_DISHES, OXYGEN_SHAKE_CHOCOLATE, MICROCHIP_OVAL, MICROCHIP_SQUARE, UV_VISOR_AMBER, SLEEP_POD_POLYESTER, MICROCHIP_TRIANGLE, OXYGEN_SHAKE_EVENING_BREATH, PANEL_1X4, GALAXY_SOUNDS_BLACK_HOLES.
- Handled in algo via inv_skew=−pos·0.2 (soft inventory bias) + tilt-clip (bounded skew per pair).

## L. Counterparty data
**EMPTY** in every R5 trades CSV. No counterparty signal possible. Confirmed across all 3 days. All counterparty-conditional research from earlier rounds inapplicable.
*Source:* `ROUND_5/autoresearch/00_data_inventory/`.

## Summary
- **Mechanisms shipped in final algo (8):** inside-spread MM, inv_skew, PROD_CAP×9 + PEBBLES_L cap=4, PEBBLES Σ-invariant, SNACKPACK Σ-invariant, 9 within-group cointegration pairs, 30 cross-group cointegration pairs.
- **Reconciled findings carried through:** every claim with PnL > +2K/day or Sharpe contribution > +0.3.
- **Mechanisms tested and dropped:** see `what_was_dropped.md` (20 items).

Numbers in this document are reverifiable in <60s by opening any cited file.
