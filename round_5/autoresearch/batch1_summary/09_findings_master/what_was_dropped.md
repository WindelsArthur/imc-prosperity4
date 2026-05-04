# What was considered and excluded (with reasons)

This audit catalogues every signal, model, or feature that was investigated and **NOT** included in the final algo, with the citation chain that justifies each exclusion. The list is non-trivial: ~12 distinct mechanisms were rejected on solid grounds.

## Excluded — failed reverify
### 1. OXYGEN_SHAKE_CHOCOLATE / OXYGEN_SHAKE_GARLIC within-group cointegration pair
- **Claim:** ADF p=0.030 (round-1).
- **Reverify (Phase D):** ADF p=**0.918** on stitched 2+3+4 mids. Pair is non-stationary on full window; CHOCOLATE has KS p≈0 day-of-day distribution break.
- **Source:** `03_reconciliation/reverify_results/stats_reverify.csv` row WITHIN:OXYGEN_SHAKE_CHOCOLATE|OXYGEN_SHAKE_GARLIC.
- **Decision:** DROPPED from final algo. Both legs continue to participate in cross-group pairs, which spot-check at p<0.01.

## Excluded — failed walk-forward OOS (round-2 ablation results)
### 2. UV_VISOR_AMBER sine-fair-value overlay
- **Claim:** R²=0.962 over stitched 30k-tick window; 90% MSE improvement fold A, 43% fold B.
- **Ablation (Phase A round-2):** Adding the sine overlay yielded **−496 PnL** in v2's ablation despite the OOS-MSE win. The MSE gain doesn't translate to PnL because the inventory MM already absorbs the slow drift.
- **Source:** `ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md`, `abl_v2_no_sine_amber.csv`.
- **Decision:** DROPPED.

### 3. Sine fits on the other 6 high-R² products
MICROCHIP_OVAL (R²=0.974), GALAXY_SOUNDS_SOLAR_FLAMES, OXYGEN_SHAKE_GARLIC, SLEEP_POD_POLYESTER, SLEEP_POD_SUEDE, PEBBLES_XS, PEBBLES_XL.
- **Failure mode:** The fitted period equals the training-window length. Walk-forward MSE was worse than constant baseline.
- **Decision:** DROPPED at Phase A (round-2).

### 4. SNACKPACK min-var weighted basket (Phase F round-2)
- **Claim:** weighted basket has rel_std=0.0023 vs 0.004 for equal-weight Σ.
- **Ablation:** swapping equal-weight for min-var yielded **−68 PnL**.
- **Source:** `ROUND_5/autoresearch/13_round2_research/F_cross_basket/`, `abl_v2_no_snack_weights.csv`.
- **Decision:** DROPPED. Keep equal-weight Σ=50,221 invariant.

### 5. Cross-group min-var triplets (Phase F round-2)
- **Claim:** 157 stationary cross-group triplets exist.
- **Failure mode:** residual std too large vs spread cost.
- **Decision:** DROPPED.

## Excluded — dominated by simpler alternative
### 6. Lead-lag PANEL_1X4 → PANEL_1X2 lag=33
- **Claim:** 1 of 100 candidate lead-lag pairs survived decay-stability filter, ~2K/day ≈ 6K/3d.
- **Failure mode:** below the +15K PnL threshold for inclusion, and PANEL_1X4/1X2 already participate in within-group cointegration.
- **Source:** `ROUND_5/autoresearch/14_lag_research/B_leadlag/decision.md`, `findings_v3.md`.
- **Decision:** DROPPED.

### 7. mr_v6 TAKER mode for 7 products
- **Claim:** 7 products earn +63K cumulative in mr_v6 TAKER mode; v3 doesn't use TAKER.
- **Comparison:** mr_v6 TOTAL = 399K, v3 TOTAL = 733K. Layering basket+pair overlays on passive MM dominates per-product TAKER selection.
- **Source:** `ROUND_5/autoresearch/mr_study/04_combined_search/v6_final_metrics.json`.
- **Decision:** DROPPED for ROBOT_MOPPING, SLEEP_POD_POLYESTER, OXYGEN_SHAKE_CHOCOLATE, PEBBLES_M, PEBBLES_XS (these are already winners in v3 with passive MM + cross-pair). PEBBLES_L and ROBOT_DISHES TAKER tested in Phase H ablation (see `08_final_algo/ablation.csv`).

### 8. Higher-rank Johansen cointegration (round-2 Phase C)
- **Claim:** rank-≥2 cointegration in some groups.
- **Result:** PEBBLES has rank 1 (already used as Σ=50,000); SNACKPACK has rank 5 but residual std=0.96 → tiny capacity.
- **Source:** `ROUND_5/autoresearch/13_round2_research/C_johansen/`.
- **Decision:** DROPPED.

### 9. Multi-level OFI signals
- **Claim:** multi-level OFI as a flow predictor.
- **Result:** max IC = 0.10; negative on lattice products. Embedded in PROD_CAP via Phase B bleeder analysis instead.
- **Source:** `ROUND_5/autoresearch/13_round2_research/D_micro/`.
- **Decision:** DROPPED as standalone signal.

### 10. Lagged OFI / cross-flow (round-3 Phase F)
- **Claim:** OFI(t-k) → ret(t) predictor.
- **Result:** strongest signal is just AR(1) restated (max |IC|=0.090 at k=1, own ROBOT_IRONING).
- **Decision:** DROPPED.

### 11. Extended AR / lag-IC (round-3 Phase E)
- **Claim:** AR-BIC selects p>1 for some products.
- **Result:** max |IC| at k>1 is **0.038** (ROBOT_IRONING@k=96). Insufficient after spread.
- **Decision:** DROPPED.

### 12. VAR / Granger within-group (round-3 Phase D)
- **Claim:** within-group VAR(p) lag structure.
- **Result:** 4 trivial leaders, no positive Sharpe.
- **Decision:** DROPPED.

### 13. Intraday seasonality (rounds 1+2 Phase G)
- **Claim:** 100-bin mod-day patterns.
- **Result:** max cross-day correlation 0.13, all below 0.30 threshold.
- **Decision:** DROPPED.

### 14. PEBBLES_L cap reduction
- **Claim:** chronic v3 loser at −12,237. Reducing cap should help.
- **Round-2 test:** cap=5 → +92 PnL but Sharpe 8.6→7.2 (worse).
- **Phase H test:** see `08_final_algo/ablation.csv` rows v08–v10. **Decision deferred to ablation outcome.**

## Deferred (run out of compute / inferior alternative existed)
### 15. LightGBM residual signals (Phase E round-2)
- SKIPPED for time. v3's pure-OLS approach found +201K vs the time it would take to train + integrate ML. Diminishing returns argument.

### 16. Markov-switching VECM / Kalman β (Phase H round-2 + 3)
- SKIPPED for time. Implicit handling via inv_skew + tilt-clip is a reasonable approximation.

### 17. Multi-lag basket invariants (Phase H' round-3)
- DEFERRED. PEBBLES Σ=50,000 already captures the strongest invariant.

### 18. Crossed-pair triangulation (Phase K round-3)
- DEFERRED.

### 19. Avellaneda-Stoikov optimal MM (Phase I round-2)
- Replaced by Phase B PROD_CAP, which is a special case of optimal sizing on bleeders.

### 20. Multi-level quote depth tapering (Phase J round-2)
- SKIPPED. Strategy already passive at bb+1/ba-1.

## Summary count
- **6** features failed reverify or OOS walk-forward and were dropped.
- **8** features dominated by simpler alternatives in the algo.
- **6** features deferred for compute / diminishing returns.

Total: **20 distinct candidates examined and rejected**, in addition to the components that did make it. This is the complete audit trail of "what was lost".
