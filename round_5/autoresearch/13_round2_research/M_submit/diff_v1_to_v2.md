# strategy_v2 — diff vs v1 (annotated)

```diff
+ # Per-product position cap (added in v2). Phase B identified 9 bleeders
+ # whose spread/vol < 0.6 → MM was being adversely selected by informed flow.
+ # Reducing each product's max position to ±3..±5 cuts the bleed without
+ # removing the spread-capture floor.
+ PROD_CAP = {
+     "SLEEP_POD_LAMB_WOOL": 3,    # v1: -24,199;  v2: -2,310   (+21,889)
+     "UV_VISOR_MAGENTA":    4,    # v1:  -7,001;  v2: -2,880   (+4,121)
+     "PANEL_1X2":           3,    # v1: -18,729;  v2:    509   (+19,238)
+     "TRANSLATOR_SPACE_GRAY": 4,  # v1:  -4,820;  v2: -5,039   (−219, neutral)
+     "ROBOT_MOPPING":       4,    # v1: -17,174;  v2:    994   (+18,168)
+     "PANEL_4X4":           4,    # v1:  -4,391;  v2:  3,116   (+7,507)
+     "GALAXY_SOUNDS_SOLAR_FLAMES": 4,  # v1: -8,237;  v2: 2,060 (+10,297)
+     "SNACKPACK_RASPBERRY": 5,    # v1: -31,946;  v2:  4,179   (+36,125)
+     "SNACKPACK_CHOCOLATE": 5,    # v1: -16,417;  v2:  4,776   (+21,193)
+ }

  POSITION_LIMIT = 10              # the actual hard limit from --limit flag

+ # NEW HELPER
+ def _cap(prod):
+     return PROD_CAP.get(prod, POSITION_LIMIT)
```

In the per-product loop, the buy/sell capacity is now the tighter of the
master limit and the product cap:

```diff
- buy_cap = POSITION_LIMIT - pos
- sell_cap = POSITION_LIMIT + pos
+ cap = _cap(p)
+ buy_cap = min(POSITION_LIMIT - pos, cap - pos)
+ sell_cap = min(POSITION_LIMIT + pos, cap + pos)
```

And the order size is capped at `min(8, cap)` (was a flat 8):

```diff
- size_buy = min(8, buy_left)
+ base_size = min(8, cap)
+ size_buy  = min(base_size, buy_left)
```

Everything else (PEBBLES sum-50,000 basket, SNACKPACK sum-50,221 basket
with equal weights, the 10 cointegration pair overlays, inside-spread
MM at bb+1/ba-1, inv_skew = -pos*0.2) is unchanged.

Items investigated and **rejected** for v2 (with their ablation deltas):
- UV_VISOR_AMBER sine overlay → −496
- SNACKPACK min-var weighted basket (Phase F) → −68
- Adding PEBBLES_L cap → marginal (+92 PnL but Sharpe drops 8.6 → 7.2)
- Adding ROBOT_DISHES cap → −9,477
- Adding GALAXY_PLANETARY_RINGS cap → −9,267

Items deferred (run out of compute budget before validation):
- LightGBM residual signals (Phase E)
- Markov-switching VECM / Kalman β (Phase H)
- Multi-level quote depth tapering (Phase J)
