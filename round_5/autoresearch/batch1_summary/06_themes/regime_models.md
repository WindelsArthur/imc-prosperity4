# Theme: Regime models (HMM, Kalman β, GARCH, Markov-VECM)

## Definition
Conditional models that switch parameters based on a latent regime variable (Markov-switching VAR/VECM) or update parameters online (Kalman filter on the cointegration β, GARCH on volatility).

## Reconciled findings (mostly deferred)
- **Round 2 Phase H (Regime-conditional cointegration)**: Markov-switching VECM and Kalman β were **SKIPPED for time** in round 2. Listed as DEFERRED.  
  *Source:* `ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md`.
- **Round 3 Phase H (regime conditioning) and Phase I (lead-lag with regime)**: also DEFERRED.  
  *Source:* `ROUND_5/autoresearch/14_lag_research/O_submit/findings_v3.md`.

## Day-of-day instability flag (KS p < 1e-9)
Products where days 2/3/4 distributions differ significantly:
- ROBOT_DISHES, OXYGEN_SHAKE_CHOCOLATE, MICROCHIP_OVAL, MICROCHIP_SQUARE, UV_VISOR_AMBER, SLEEP_POD_POLYESTER, MICROCHIP_TRIANGLE, OXYGEN_SHAKE_EVENING_BREATH, PANEL_1X4, GALAXY_SOUNDS_BLACK_HOLES.

These products have either drifting levels (MICROCHIP_OVAL sine-like) or true regime shifts (OXYGEN_SHAKE_CHOCOLATE — see ADF reverify failure).

*Source:* `ROUND_5/autoresearch/04_statistical_patterns/`, `ROUND_5/autoresearch/11_findings/exploitable_patterns.md` § 6.

## Implicit regime adaptation in v3
- **inv_skew = −pos·0.2** acts as a soft regime-conditional pricing controller. When the market regime changes and inventory accumulates one-sided, inv_skew biases the quote to encourage the opposite-side fill.
- **PROD_CAP** for the 9 bleeders effectively shrinks the regime-sensitivity of the strategy on the products most exposed to it.
- **Per-pair tilt clipping** at ±3 prevents an unbounded skew when a pair's residual goes through a regime shift (e.g., OXYGEN_SHAKE_CHOCOLATE/GARLIC).

## Decision for final algo
- **No explicit regime model.** Implicit handling via inv_skew + PROD_CAP + tilt-clipping is preserved.
- **Phase H test:** for the 3 within-group pairs that failed full-stitch ADF (LAUNDRY/VAC, COTTON/POLY, POLY/SUEDE), tighten the tilt-clip to ±2 (vs ±3) to reduce regime-shift sensitivity.

## Expected PnL contribution
0 from explicit regime modelling. Implicit handling is part of the v3 baseline.
