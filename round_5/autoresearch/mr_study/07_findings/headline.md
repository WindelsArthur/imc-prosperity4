# MR Study — Headline

## Day-5 PnL projection

| scenario | Total profit (engine) | Final 3-day PnL | Drawdown | Sharpe | Calmar |
| --- | ---:| ---:| ---:| ---:| ---:|
| **mid (`--match-trades worse`)** | **399,636** | **283,223** | 69,390 | 0.93 | 5.76 |
| upper (`--match-trades all`)     | 402,669     | 283,301     | 69,390 | 0.94 | 5.80 |
| lower (mid − 1σ assumption)      | ~340,000    | ~240,000    |    —   |   —  |   —  |

For day-5 specifically, all three days (2/3/4) become training data; the FV
state warms up over the first ~2,000 ticks of day-2 and then operates
fully calibrated for the rest. Expected day-5 PnL is in the **80–100K
range** based on the day-3/day-4 deltas (98K and 93K respectively, both
OOS).

## Comparison vs round-2 baseline

- ROUND-2 walk-forward baseline (per task brief): **+396K Total profit** over
  3 days.
- This MR-only strategy: **+399.6K Total profit** over 3 days.
- **Net beat: ≈ +3.6K.** Below the ≥15K target.

I did not hit the +15K bar. The honest reason is that the round-5 universe
is dominated by unit-root-like processes (47/50 fail ADF stationarity at
5% on day-2 mid; 49/50 fail KPSS) — the level-MR alpha is small. The
exploitable structure is overwhelmingly **microstructure** (inside-spread
quoting + inventory skew) rather than persistent residual mean-reversion.
A multi-strategy ensemble that adds momentum / cross-product / option-arb
signals on top should comfortably beat the baseline; this study delivers
the MR layer of that ensemble.

## Top 10 contributors (final 3-day PnL)

| rank | product | mode | FV | per-product PnL |
| ---:| --- | --- | --- | ---:|
| 1 | PEBBLES_S                  | MM    | — (default)             | +22,195 |
| 2 | PEBBLES_XS                 | TAKER | rolling_quadratic w=500 | +15,016 |
| 3 | GALAXY_SOUNDS_BLACK_HOLES  | MM    | — (default)             | +14,828 |
| 4 | ROBOT_DISHES               | TAKER | rolling_mean w=50       | +11,219 |
| 5 | PEBBLES_XL                 | MM    | — (default)             | +10,865 |
| 6 | UV_VISOR_AMBER             | MM    | — (default)             | +10,718 |
| 7 | MICROCHIP_CIRCLE           | MM    | — (default)             | +10,358 |
| 8 | ROBOT_MOPPING              | TAKER | rolling_quadratic w=500 | +10,225 |
| 9 | TRANSLATOR_VOID_BLUE       | MM    | — (default)             | +10,199 |
| 10| GALAXY_SOUNDS_SOLAR_WINDS  | MM    | — (default)             |  +9,320 |

Top-10 sum: **+125K** ≈ 44% of total final PnL.

## IDLE products (with reasons)

| product | reason |
| --- | --- |
| ROBOT_IRONING                 | strongest Phase-1 signal (IC 0.10) but spread=6 too tight; aggressive taker pays half-spread bigger than residual; signal-skewed MM tested negative (-2.6K). Needs aggressive resting MM with bot-flow-aware fills, beyond MR scope. |
| MICROCHIP_RECTANGLE           | MM lost -13K with strong directional drift; no qualifying TAKER config in Phase 2. |
| TRANSLATOR_SPACE_GRAY         | MM lost -12K; no TAKER candidate. |
| GALAXY_SOUNDS_PLANETARY_RINGS | MM lost -7K; persistent drift across days. |
| SLEEP_POD_SUEDE               | MM lost -7K; mid jumps wider than spread. |
| SLEEP_POD_LAMB_WOOL           | MM lost -5K; same pattern. |
| GALAXY_SOUNDS_SOLAR_FLAMES    | MM lost -3K; fold-A taker had +1.5K but unstable. |
| UV_VISOR_MAGENTA              | MM lost -3K; spread=14 but mid std=614. |

## Where to push next

1. **ROBOT_IRONING / OXYGEN_SHAKE_EVENING_BREATH passive MR-MM**: post inside
   spread with strong signal skew on the AR(1) prediction; needs a bot-flow
   simulator that handles passive matching realistically. Expected +5–10K
   each.
2. **PEBBLES_M / SLEEP_POD_POLYESTER threshold finetune**: in-sim said
   +15K/+12K avg daily but realised only +9K/+8K. The discrepancy is the
   FV residual sigma being computed slightly differently online vs offline.
   Aligning these adds maybe +5K each.
3. **Re-enable IDLE'd products with tighter MM (smaller size, wider offset)**:
   the chronic losers are losing because the inside-spread fill volume is too
   high relative to the directional drift. Quoting at offset=2 (skip a
   level) and size=3 might convert -5K losses into +1K gains.
4. **Cross-day FV state freezing**: currently the FV warms up on day-2 in
   the live trader. Pre-baking the day-2-trained FV state into
   `distilled_params.py` would stabilise day-3/4 OOS slightly.

Estimated PnL of these four together: **+30–50K**, which would put us at
+330K final / +430K total — beating the +15K bar.

The ranking metric the task requested ("AVERAGE DAILY OOS PnL across two
walk-forward test days") for v6 is **(98 + 93) / 2 ≈ 95K/day**.
