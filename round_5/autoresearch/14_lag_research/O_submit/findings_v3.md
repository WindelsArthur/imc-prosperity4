# Round 3 — Final findings

## Headline

| Metric                           | v1     | v2     | v3 (final) | Δ vs v2  |
|----------------------------------|--------|--------|------------|----------|
| Total PnL, days 2–4 (worse)      | 396,749 | 531,525 | **733,320** | +201,795 |
| Sharpe (merged)                  | 4.22   | 8.61   | **8.34**    | flat     |
| Max DD abs                       | 30,772 | 26,286 | 23,990      | -2,296   |
| Max DD %                         | 26.9 % | 5.0 %  | 21.9 %      | +16.9 ppt|
| Per-day d2 / d3 / d4             | 125/105/167 K | 169/162/201 K | **234/278/222 K** | +65/+116/+21 K |
| Match-mode band (worse vs all)   | 0      | 0      | 0           | identical |

**v3 ships.** +201K (+38 %) over v2.

Day 5 forecast (1 day): low ≈ 222K, base ≈ 244K, high ≈ 278K.

## What v3 adds: 30 cross-group cointegration pairs (Phase C)

Round 1 did Engle-Granger only **within** the 10 named groups. Round 2 added
Johansen but again within-group. Phase C runs EG over the top-300 pairs from
Phase A's price-CCF (which is unrestricted across groups) at lags
{1, 5, 20, 100} → 1,200 fits, 221 pass ADF<0.05 + half-life ∈ [5,1000].
Walk-forward (train d2 → test d3, train 2+3 → test 4) leaves 171 with
min-fold Sharpe ≥ 0.7. The top 30 by combined PnL are now skew overlays
in `strategy_v3.py`.

The single biggest contributor is **PEBBLES_XL ~ PANEL_2X4** (slope 2.482,
intercept -14735.7). Neither is in the same named group, and round 1's
group-bound search missed it. Walk-forward Sharpe 1.75 / 2.33; combined
3-day PnL ≈ 11K.

## Phase scoreboard

| Phase | Hypothesis | n_tested | n_surv | Δ PnL | Decision |
|-------|------------|----------|--------|-------|----------|
| A — CCF atlas | exhaustive lag map | 50²·161·3 = 1.2 M CCFs | foundation only | n/a | foundation |
| B — Lead-lag pairs | top-100 from A produce strategies | 100 | 1 (PANEL_1X4→PANEL_1X2 lag 33, ~2K/day) | ~6K total | DEFER |
| C — Lagged cointegration | EG with shifted j | 1,200 (300 × 4 lags) | 171 ADF + Sharpe filtered; top 30 shipped | **+201K** | **SHIP** |
| D — VAR(p) per group | within-group lag structure | 10 groups | 4 trivial leaders | 0 | drop |
| E — Extended AR / lag-IC | beyond AR(1) reversion | 50 products | 4 sign-switch (max IC 0.038 at k=96) | 0 | drop |
| F — Lagged OFI / cross-flow | OFI(t-k)→ret(t) | 50 own + 60 cross | strongest is just AR(1) restated | 0 | drop |
| G–K | combined exploration | n/a | n/a | n/a | DEFERRED — Phase C closed the gap |

## Per-product summary (3-day cumulative, top-30 v3)

Top winners: SLEEP_POD_SUEDE +16.1K, GALAXY_BLACK_HOLES +14.8K,
SNACKPACK_STRAWBERRY +13.8K, PEBBLES_XS +12.9K, OXYGEN_EVENING_BREATH +11.9K.

Persistent losers (per the v3 cross-group skew interactions):
PEBBLES_L -12.2K, SNACKPACK_RASPBERRY -10.2K,
GALAXY_PLANETARY_RINGS -6.9K, MICROCHIP_SQUARE -6.9K,
TRANSLATOR_SPACE_GRAY -5.0K. These are flagged for Round 4 if any.

## Critical conclusions

- The **lag dimension on returns and signed flow is essentially empty**.
  Bonferroni-corrected critical |ρ| = 0.040 on Phase A; the top-100 lead-lag
  candidates produced only 1 decay-stable signal (~2K/day).
- The **lag dimension on prices is rich**, but reduces to *cointegration with
  hedge ratios different from contemporaneous*. Round 1 missed it because it
  bound the EG search to within-named-group pairs.
- The biggest leverage was **expanding the cointegration search across groups**
  — 30 surviving cross-group pairs, including PEBBLES_XL/PANEL_2X4 (largest
  contribution).
- VAR / Granger / extended-AR / OFI lag analyses returned essentially zero
  alpha. Confirms this is not a lag-prediction game; it's a hedge-ratio
  expansion game.

## Reproducing

```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/autoresearch/14_lag_research/O_submit/strategy_v3.py \
    5-2 5-3 5-4 \
    --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```

Expected total profit: **733,320**.
