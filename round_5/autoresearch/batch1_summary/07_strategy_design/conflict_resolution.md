# Conflict resolution per product

Cross-references against `03_reconciliation/conflicts.jsonl`.

## c001 — ROBOT_LAUNDRY/ROBOT_VACUUMING ADF
- Reverify: ADF p=0.378 (claimed 0.026). Pair non-stationary on full stitch.
- Decision: **KEEP** the within-group pair. Both fold-OOS Sharpes positive (1.19/1.70). v3 PnL on the legs is +4,074 / +423 — pair contributes meaningfully via skew.
- Risk mitigation: inv_skew + ±3 tilt clip already prevents unbounded exposure.

## c002 — SLEEP_POD_COTTON/SLEEP_POD_POLYESTER ADF
- Reverify: ADF p=0.146 (claimed 0.033).
- Decision: **KEEP**. Fold-OOS Sharpes 1.32/1.89. v3 leg PnL +9,177 / +4,040.

## c003 — OXYGEN_SHAKE_CHOCOLATE/OXYGEN_SHAKE_GARLIC ADF
- Reverify: ADF p=**0.918** (claimed 0.030). Pair is non-stationary; OXYGEN_SHAKE_CHOCOLATE has KS p≈0 day-of-day.
- Decision: **DROP** this within-group pair from final algo. CHOCOLATE keeps default MM + inv_skew (or optional Phase H test of mr_v6 ar_diff skew).
- Both legs participate in 4 cross-group pairs each — those are robust and KEPT.

## c004 — SLEEP_POD_POLYESTER/SLEEP_POD_SUEDE ADF
- Reverify: ADF p=0.091 (claimed 0.052). Both above 0.05 threshold.
- Decision: **KEEP**. Fold-OOS Sharpes positive (1.90/1.12).

## c005 — SNACKPACK_CHOCOLATE/SNACKPACK_STRAWBERRY ADF
- Reverify: ADF p=0.035 (claimed 0.009). Both <0.05.
- Decision: **KEEP**.

## c006 — v3 vs v3_per_product totals
- 733,320 vs 556,430. Reverified v3=733,320 (`reverify_v3.csv`).
- Decision: **BASELINE = 733,320**. v3_per_product was a different ablation config.

## c007 — Sine overlay
- v2 ablation: −496 PnL even on UV_VISOR_AMBER (the only OOS survivor).
- Decision: **DROP sine entirely**. No sine overlay in final algo.

## c008 — PEBBLES_L cap
- v2 found cap=5 → +92 PnL but Sharpe 8.6→7.2.
- v3 PEBBLES_L PnL = −12,237 (chronic loser).
- Decision: **TEST** in Phase H ablation. mr_v6 TAKER yields +9,434, suggesting cap or mode change could be net positive.

## c009 — mr_v6 TAKER mode for 7 products
- mr_v6 = 399K total, v3 = 733K total. mr_v6 inferior in absolute terms.
- Decision: **TEST** layering 2-3 highest-Δ TAKERs (PEBBLES_L, ROBOT_DISHES, ROBOT_MOPPING) on top of v3's basket+pair structure. Reject any that fail to add ≥+2K/day.

## c010 — counterparty fields empty
- Confirmed empty across all 3 days, all products.
- Decision: **IGNORE** all counterparty-conditional claims. No buyer/seller-based signals.
