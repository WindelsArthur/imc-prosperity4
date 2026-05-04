# ROUND 5 — Headline (one-page TL;DR)

## Final algo
`ROUND_5/batch1_summary/08_final_algo/strategy_final.py` + `distilled_params.py`. Single-file Trader with PEBBLES_L_CAP=4. Fully passive (no aggressive cross dependence). 781 input artefacts → 1,583 reconciled findings → 1 algo.

## 3-day backtest (--match-trades worse, walk-forward)
| Metric | strategy_final | round-3 v3 | round-2 v2 | round-1 v1 |
|---|---:|---:|---:|---:|
| Total PnL | **733,058** | 733,320 | 531,525 | 396,749 |
| Sharpe | **10.80** | 8.34 | 8.61 | 4.22 |
| Max DD | **21,786** | 23,990 | 26,286 | 30,772 |
| Match-mode band | 0 | 0 | 0 | 0 |

## Day-5 PnL projection (1 day)
- **Low ≈ 227K** (matches worst training day d4)
- **Base ≈ 244K** (mean of training days)
- **High ≈ 270K** (matches best training day d3)

## Top-10 mechanisms ranked by realised ablation contribution
| Rank | Mechanism | Δ PnL | Cumulative | Source phase |
|---|---|---:|---:|---|
| 1 | **30 cross-group cointegration pairs** (PEBBLES_XL/PANEL_2X4 etc) | +237,696 | 732,052 | round-3 Phase C |
| 2 | **PROD_CAP for 9 bleeders** (LAMB_WOOL=3, MAGENTA=4, …) | +68,186 | 471,570 | round-2 Phase B |
| 3 | **9 within-group cointegration pairs** (1 dropped post-reverify) | +57,234 | 494,356 | round-1 Phase 5 |
| 4 | inside-spread MM @ bb+1/ba-1 (foundation) | n/a (=baseline) | 401,540 | round-1 Phase 9 |
| 5 | **PEBBLES_L cap=4** (Phase H ablation) | +1,006 (Sharpe +1.97) | 733,058 | round-5 batch1 Phase H |
| 6 | inv_skew = −pos·0.2 | +1,844 | 403,384 | round-1 Phase 9 |
| 7 | PEBBLES Σ=50,000 invariant skew | +1,339 | 472,909 | round-1 Phase 5 |
| 8 | SNACKPACK Σ=50,221 invariant skew | (only useful with pairs) | – | round-1 Phase 5 |
| 9 | OG-pair drop (OXYGEN_SHAKE_CHOCOLATE/GARLIC) | −262 PnL but +2.46 Sharpe | – | round-5 batch1 Phase D |
| 10 | AR(1) signal-skew on EVENING_BREATH (REJECTED) | −74 | – | tested Phase H |

## Critical risks (day-5 specific)
1. **PEBBLES_XL ~ PANEL_2X4 slope drift** — single biggest cross-group contributor. Slope=2.482 calibrated on stitched 2+3+4. If day-5 introduces a regime shift, this pair could underperform; it remains tilt-clipped at ±3 to bound exposure.
2. **OXYGEN_SHAKE_CHOCOLATE day-of-day KS break** — pair removal mitigates. Still a participant in 4 cross-group pairs as GARLIC; tilt-clip handles.
3. **Day-of-day distribution shifts** for 10 KS-flagged products (ROBOT_DISHES, OXYGEN_SHAKE_CHOCOLATE, MICROCHIP_OVAL/SQUARE/TRIANGLE, UV_VISOR_AMBER, SLEEP_POD_POLYESTER, OXYGEN_SHAKE_EVENING_BREATH, PANEL_1X4, GALAXY_SOUNDS_BLACK_HOLES). Inv_skew=−pos·0.2 absorbs.
4. **Limit-stress fragility**: if positions limit drops below 10 (e.g. to 8), v3 numbers degrade sharply (per round-2 stress: 82K vs 532K). Same fragility carries over.

## Counterparty data
**Buyer/seller fields are EMPTY in every row of every R5 trades CSV.** No counterparty bot fingerprinting. Aggregate signed-flow IC ~0.01 — no informed flow signal. Confirmed across all 3 days.

## Reproducing
```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/batch1_summary/08_final_algo/strategy_final.py \
    5-2 5-3 5-4 --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
Expected total profit: **733,058**.
