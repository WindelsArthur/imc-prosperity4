# strategy_v3 — diff vs v2 (annotated)

The single change is the **`CROSS_GROUP_PAIRS` list**, populated from
Phase C's lagged-EG sweep over the top-300 high-correlation pairs from
Phase A. Each tuple is `(a, b, slope, intercept, residual_sd)` and gets
applied as a soft skew on both legs in the existing pair-overlay loop:

```python
spread_val = mids[a] - slope * mids[b] - intercept
tilt = max(-3.0, min(3.0, -spread_val / 8.0))
pair_skew[a] = pair_skew.get(a, 0.0) + tilt
pair_skew[b] = pair_skew.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)
```

The 30 cross-group cointegrating pairs (lag=1 EG, ADF p<0.05,
half-life ∈ [5,1000], min-fold OOS Sharpe ≥ 1.0) appended to v2's
within-group `COINT_PAIRS`:

```python
CROSS_GROUP_PAIRS = [
    ("PEBBLES_XL", "PANEL_2X4", 2.482, -14735.7, 200.0),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.450, 34144.0, 200.0),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.904, 19300.5, 200.0),
    ("UV_VISOR_YELLOW", "GALAXY_SOUNDS_DARK_MATTER", 1.584, -5239.0, 200.0),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.011, 20960.0, 200.0),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.868, -7693.0, 200.0),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.018, 20560.0, 200.0),
    ("SLEEP_POD_POLYESTER", "UV_VISOR_AMBER", -0.923, 19139.8, 200.0),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.538, 15490.3, 200.0),
    ("PEBBLES_S", "PANEL_2X4", -1.102, 21344.6, 200.0),
    ("ROBOT_IRONING", "PEBBLES_M", -0.915, 18096.1, 200.0),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.554, 4653.1, 200.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "UV_VISOR_YELLOW", 0.373, 6145.0, 200.0),
    ("SNACKPACK_STRAWBERRY", "SLEEP_POD_POLYESTER", 0.325, 6852.8, 200.0),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.217, 12289.6, 200.0),
    # … 15 more (full list in strategy_v3.py)
]
```

Everything else (PEBBLES sum-50,000, SNACKPACK sum-50,221, the 10
within-group cointegration pairs, PROD_CAP, generic MM at bb+1/ba-1,
inv_skew=−pos·0.2) is **unchanged from v2**.

Investigated and **rejected** for v3:
- Lead-lag (Phase B) — only PANEL_1X4→PANEL_1X2 lag 33 survived, ~6K total PnL across 3 days; not material vs the +200K from Phase C.
- Extended AR / lag-IC (Phase E) — peak |IC| beyond k=1 is 0.038 (ROBOT_IRONING@k=96); insufficient for any positive Sharpe after spread.
- Lagged OFI / cross-flow (Phase F) — top |IC| = 0.090 at k=1 (own ROBOT_IRONING) which is just the AR(1) reversion already captured by inv_skew.
- VAR / Granger (Phase D) — within-group lag structure essentially absent (max 1-2 significant edges per group at p<0.01).

Items deferred:
- Lead-lag with regime conditioning (Phase I)
- Markov-switching VECM / Kalman β (Phase H)
- Multi-lag basket invariants (Phase H')
- Crossed-pair triangulation (Phase K)
