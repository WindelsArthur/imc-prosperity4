# Round 5 — Findings

## Headline numbers

| Metric                                | Value                  |
|--------------------------------------|------------------------|
| Strategy total PnL, days 2–4 (worse) | **396,749**            |
| Per-day mean / min / max             | 132,250 / 105,220 / 166,636 |
| `prosperity4btest --merge-pnl` Sharpe| **4.22**               |
| Max drawdown (worst day)             | 30,772 (≈ 26.9 %)      |
| Match-mode band (worse vs all)       | 0 — strategy is fully passive |

Day 5 PnL projection (1 day): low ≈ **105K**, mid ≈ **132K**, high ≈ **170K**.

## Top 15 exploitable patterns (ranked by expected day-5 PnL contribution)

1. **PEBBLES sum-to-50,000 invariant.** Empirical: `Σ_i mid_i ∈ [49,981, 50,016]`,
   std 2.8, OU half-life **0.16 ticks**. Each pebble individually has spread
   ~13 so the residual cannot be lifted by crossing; instead we skew passive
   inside-spread quotes by `-resid/5` per pebble. 3-day strategy PnL on the
   five pebbles together = **+55K**. PEBBLES_XL alone = 50,715.
   *Evidence:* `05_cross_product/groups/pebbles/basket_residual.csv` (R²=0.999998).

2. **SNACKPACK basket** (sum ≈ 50,221, std 190). Far weaker than pebbles but
   still surfaces a 0.7–1.1 OOS-Sharpe signal in Phase 8. Used as a smaller
   skew on top of MM.

3. **MICROCHIP_RECTANGLE × MICROCHIP_SQUARE** cointegration, slope −0.40,
   ADF p=0.004, walk-forward Sharpe 1.0–2.1. 3-day combined PnL +35K.
   *Evidence:* `05_cross_product/all_pair_cointegration.csv`.

4. **GALAXY_SOUNDS_DARK_MATTER × GALAXY_SOUNDS_PLANETARY_RINGS**, slope 0.18,
   ADF p=0.04, Sharpe 1.5–2.0.

5. **ROBOT_LAUNDRY × ROBOT_VACUUMING**, slope 0.33, ADF p=0.026, Sharpe 1.2–1.7.

6. **SLEEP_POD_COTTON × SLEEP_POD_POLYESTER**, slope 0.52, ADF p=0.033,
   Sharpe 1.3–1.9.

7. **OXYGEN_SHAKE_EVENING_BREATH (lattice + AR(1))**. Only **453 distinct
   mids** across 30,000 ticks (lattice ratio 0.015). AR(1) coefficient
   −0.124 with phi stable across days. 3-day MM PnL +20.9K.

8. **ROBOT_IRONING (lattice + AR(1))**. 631 distinct mids, AR(1)=−0.13,
   gzip ratio 0.087 (very compressible). 3-day MM PnL +14.5K.

9. **ROBOT_DISHES (deep AR)**. Best AR-BIC p=9, AR(1)=−0.265 — lag-1
   reversion is strong but day-of-day distributions differ wildly
   (KS p ≈ 0). Strategy treats it as plain MM with inventory skew.

10. **OXYGEN_SHAKE_CHOCOLATE / OXYGEN_SHAKE_GARLIC** cointegration,
    slope −0.16, ADF p=0.03.

11. **UV_VISOR_AMBER × UV_VISOR_MAGENTA** cointegration, slope −1.24,
    ADF p=0.023.

12. **TRANSLATOR_ECLIPSE_CHARCOAL × TRANSLATOR_VOID_BLUE** cointegration,
    slope 0.46, ADF p=0.04.

13. **SNACKPACK_RASPBERRY × SNACKPACK_VANILLA** cointegration, ADF p=0.0013
    (best cointegration in the universe).

14. **MICROCHIP_OVAL & UV_VISOR_AMBER deterministic-sine fits**. R² ≥ 0.96
    for `A·sin(ωt+φ)+ct+d` across the whole 30,000-tick stitched series
    (period = 30,000). Currently exploited only via inventory-skew MM; an
    explicit sine fair-value extension is the obvious follow-up if day 5
    continues the same phase.

15. **Generic inside-spread MM at best_bid+1 / best_ask-1** with inventory
    skew applied to all 50 products. This is the workhorse: per-tick spread
    capture is the dominant PnL contributor in absolute terms.

## Critical data observation

**Counterparty fields (`buyer`, `seller`) are EMPTY in every row of every
trades_round_5_day_*.csv file.** The autoresearch prompt assumed they would
be present; they are not. Phase 3 bot-detection is therefore impossible at
the per-counterparty level. Aggregate signed-flow IC is ~0.01 — flow is not
informed. See `00_data_inventory/inventory.md`.

## Reproducing

```
prosperity4btest cli ROUND_5/autoresearch/12_final_strategy/strategy.py \
    5-2 5-3 5-4 --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```

Expected total profit: 396,749.
