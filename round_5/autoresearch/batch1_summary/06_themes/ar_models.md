# Theme: AR (auto-regressive) models

## Definition
Δmid_t = φ_1·Δmid_{t-1} + ... + ε_t. Negative φ_1 implies short-horizon mean reversion in price changes; large negative |φ_1| implies strong predictability of next-tick move.

## Re-verified AR(1) coefficients on Δmid (stitched 3 days)

| Product | claimed AR(1) | re-verified AR(1) | n_distinct_mids | mr_v6 mode |
|---|---:|---:|---:|---|
| ROBOT_DISHES | −0.265 | **−0.232** | 3,048 | TAKER |
| OXYGEN_SHAKE_EVENING_BREATH | −0.124 | **−0.123** ✓ | 453 | MM-skew |
| ROBOT_IRONING | −0.130 | **−0.125** ✓ | 631 | IDLE |
| OXYGEN_SHAKE_CHOCOLATE | −0.090 | **−0.089** ✓ | (high) | TAKER |
| SNACKPACK_CHOCOLATE | (low) | **−0.031** | (high) | MM-skew |

ROBOT_DISHES is the strongest mean-reverter in the universe by AR(1). The reverify came in slightly weaker than the round-1 claim (−0.232 vs −0.265) but the sign and magnitude are confirmed.

## Phase E (round 3) — extended AR / lag-IC
Beyond AR(1), exploration of higher-order AR / IC at lags k>1:
- 4 sign-switch products with non-trivial structure beyond AR(1).
- Max |IC| at k>1 is **0.038** (ROBOT_IRONING @ k=96).
- Insufficient to overcome spread cost. **No PnL** in v3.

*Source:* `ROUND_5/autoresearch/14_lag_research/E_ar_extended/`.

## Decision for final algo
- **Encode AR(1) reversion implicitly** via inv_skew = −pos·0.2 (a large adverse fill flips position; the reversion brings price back; closing earns spread).
- **Phase H test:** explicit `ar_diff p=1` signal skew on OXYGEN_SHAKE_EVENING_BREATH (mr_v6 logic) and SNACKPACK_CHOCOLATE.
- **Phase H test:** switch ROBOT_DISHES to TAKER mode (mr_v6 found +11.2K).

## Expected PnL contribution
v3's implicit AR(1) capture: ~5–10K (embedded in inv_skew). Upside if explicit AR-skew added: +5–15K from EVENING_BREATH alone.
