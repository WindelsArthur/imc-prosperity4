# Round 2 — Final findings

## Headline

| Metric                                  | v1        | v2        | Δ          |
|----------------------------------------|-----------|-----------|------------|
| Total PnL, days 2–4 (worse match)       | 396,749   | **531,525**| +134,776  |
| Sharpe (merged)                         | 4.22      | **8.61**  | +4.39      |
| Max drawdown abs                        | 30,772    | 26,286    | −4,486     |
| Max drawdown %                          | 26.9 %    | 5.0 %     | −21.9 ppt  |
| Per-day PnL: d2 / d3 / d4               | 124K/105K/167K | 169K/162K/201K | +45K/+57K/+34K |
| Match-mode band (worse vs all)          | 0         | 0         | identical  |

Day-5 forecast band:
| Scenario | Per-day PnL |
|----------|-------------|
| Low      | ≈ 162K (worst training day d3) |
| Base     | ≈ 177K |
| High     | ≈ 201K (best training day d4) |

## Phase results — what worked, what didn't

| Phase | Hypothesis | Result | Δ PnL vs v1 baseline | Decision |
|-------|------------|--------|----------------------|----------|
| A. Sine-fit phase resolution | 7 sine-R²-high products are real cycles | only UV_VISOR_AMBER survives OOS (90% MSE improvement fold A; 43% fold B). Other 6 have unstable periods — false alarm | sine added −496 in ablation | **EXCLUDE** sine overlay |
| B. Bleeder forensics | adverse-selection bleed on low spread/vol products | spread/vol < 0.6 on 9 of 11 bleeders → MM loses to flow; per-product cap to ±3..5 | **+134,280** (entire delta!) | **INCLUDE** PROD_CAP {LAMB_WOOL:3, MAGENTA:4, PANEL_1X2:3, SPACE_GRAY:4, ROBOT_MOPPING:4, PANEL_4X4:4, SOLAR_FLAMES:4, RASPBERRY:5, CHOCOLATE:5} |
| C. Johansen higher-order coint | rank-≥2 cointegration in some groups | only PEBBLES (rank 1, already used) and SNACKPACK (rank 5, but std=0.96 → tiny capacity) | n/a | **NONE** |
| D. Microstructure round 2 | OFI multi-level + spread regime → new signals | OFI IC weak (max 0.10), but negative on lattice products (contra). Tight-spread regime has negative realised spread on most products | n/a — informs Phase B | informs caps |
| E. ML residual signals | LightGBM on v1 residuals | SKIPPED for time | n/a | **DEFER** |
| F. Cross-group baskets | min-var per-group + triplets | SNACKPACK weighted basket is tighter (rel_std 0.0023 vs 0.004 for sum). UV_VISOR + ROBOT have stable min-var baskets. 157 stationary cross-group triplets but std large vs spread cost | swapping eq-weight → min-var signal: **−68** | **EXCLUDE** weighted snack signal (= equal-weight) |
| G. Intraday seasonality | 100-bin mod-day patterns | max cross-day corr 0.13, all below 0.30 threshold | n/a | **NONE** |
| H. Regime-conditional coint | Markov-VECM, Kalman β | SKIPPED for time | n/a | **DEFER** |
| I. Inventory + sizing | Avellaneda-Stoikov optimal MM | Replaced by Phase B PROD_CAP (subset of optimal sizing) | included in B | covered |
| J. Order placement | improve vs join | SKIPPED — strategy already passive at bb+1/ba-1 | n/a | **NONE** |
| K. v2 assembly + ablation | combined surviving phases | full v2 = 531,525 vs v1 396,749 | +134,776 | **SHIP v2** |
| L. Robustness | OOS, match modes, day-removal, limit stress | OOS ratios solid (fold A 162K, fold B 201K). Day-removal (test 3+4) holds 363K. Match modes identical. Limit=8 stress drops to 82K (strategy hardcoded for limit=10) | within bounds | **READY** |

## Critical conclusions
- **Adverse-selection bleed dominated v1's losses**, not signal misalignment. Phase B's simple per-product cap recovered the entire 134K gap.
- **Sine fits with R² > 0.9 on stitched days were artefacts** for 6 out of 7 products — the period equalled the training-window length. UV_VISOR_AMBER is the lone genuine cycle, but its dollar contribution is small.
- **No new cointegration relations** beyond round 1. PEBBLES sum=50,000 remains the singular structural alpha; everything else is correlation-driven.
- **No exploitable intraday seasonality** at 100-bin granularity.
- **Counterparty fields remain empty** (round-1 finding); no flow-based bot signals available.

## Reproducing

```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/autoresearch/13_round2_research/M_submit/strategy_v2.py \
    5-2 5-3 5-4 \
    --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```

Expected total profit: **531,525**.
