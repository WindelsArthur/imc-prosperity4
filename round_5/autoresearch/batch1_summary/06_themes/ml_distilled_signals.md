# Theme: ML-distilled signals

## Definition
Lasso / GBM / Random Forest distillation of multi-feature predictors into a coefficient table that can be evaluated cheaply at runtime in pure Python (no sklearn at runtime per IMC submission rules).

## Reconciled findings (deferred)
- **Round 2 Phase E (ML residual signals — LightGBM on v1 residuals)**: **SKIPPED for time** in round 2. Listed as DEFERRED.
- **No ML signal has been trained or deployed** in v1, v2, or v3.

*Source:* `ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md` § Phase E.

## Why it isn't worth pursuing for day 5
- v3 already extracts +201K from cross-group pair-OLS, on top of v2's +134K from PROD_CAP. The total +336K v1→v3 came from very simple linear / position-cap mechanics.
- The remaining residuals after v3 are dominated by:
  - Day-of-day regime breaks (ML cannot help — non-stationary by construction).
  - Counterparty signal (which is empty — no buyer/seller info).
  - Higher-order lag structure (extended-AR Phase E found max |IC|=0.038 at k>1, insufficient for positive Sharpe after spread).
- A LightGBM trained on v1 residuals would either re-discover what v3 already encodes (cross-group pairs) or fit noise.

## Decision for final algo
- **No ML at runtime.** Per IMC rules and per the diminishing-returns argument above.

## Expected PnL contribution
0 (excluded).
