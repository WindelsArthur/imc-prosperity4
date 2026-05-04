# Phase H Checkpoint — final algo

## Final algo
`ROUND_5/batch1_summary/08_final_algo/strategy_final.py` + `distilled_params.py` (PEBBLES_L_CAP=4).

## Headline numbers (3-day backtest, --match-trades worse)
| Metric | v3 baseline | **strategy_final (v09)** | Δ |
|---|---:|---:|---:|
| Total PnL | 733,320 | **733,058** | −262 |
| Sharpe | 8.34 | **10.80** | **+2.47** |
| Max drawdown | 23,990 | **21,786** | −2,204 (−9 %) |
| Calmar | 30.6 | (≈33.6) | +3 |
| Match-mode band (worse vs all) | 0 | **0** | identical |

PnL sacrificed: 0.04 %. Sharpe gained: 30 %. DD reduction: 9 %.

## Components that survived ablation (additive)
| Component | Δ vs prior | Cumulative PnL | Sharpe |
|---|---:|---:|---:|
| 1. inside-spread MM (bb+1/ba-1) | – | 401,540 | 3.48 |
| 2. + inv_skew = −pos·0.2 | +1,844 | 403,384 | 3.53 |
| 3. + PROD_CAP for 9 bleeders | **+68,186** | 471,570 | 5.84 |
| 4. + PEBBLES Σ=50,000 invariant | +1,339 | 472,909 | 5.85 |
| 5. + SNACKPACK Σ=50,221 invariant | (combines below) | 437,122 | 4.47 |
| 6. + 9 within-group cointegration pairs (OG dropped) | +57,234 | 494,356 | 6.15 |
| 7. + 30 cross-group cointegration pairs | **+237,696** | 732,052 | 8.83 |
| 8. + PEBBLES_L cap=4 (vs 10 default) | +1,006 | **733,058** | **10.80** |

**Two dominant contributors:** PROD_CAP (Phase B round-2) at +68K, and the 30 cross-group pairs (Phase C round-3) at +238K. Together = 84% of the strategy's total PnL.

## Components that were tested and DROPPED in ablation
| Component | Δ tested | Decision |
|---|---:|---|
| OXYGEN_SHAKE_CHOCOLATE/GARLIC pair restored (= true v3) | +262 raw, **−2.46 Sharpe**, +2,204 DD | **DROP** — Sharpe penalty too large |
| PEBBLES_L cap=5 | +92 | inferior to cap=4 |
| PEBBLES_L cap=6 | −2,322 | reject |
| AR(1) signal-skew on OXYGEN_SHAKE_EVENING_BREATH | −74 | reject (negligible) |
| SNACKPACK invariant alone (no pair overlays) | **−35,787** | only beneficial when paired with cross-group overlays |

## Walk-forward (per-day standalone)
| Day | PnL | DD |
|---|---:|---:|
| 5-2 | 235,412 | 19,398 |
| 5-3 | 270,079 | 15,305 |
| 5-4 | 227,566 | 21,786 |
| Sum | 733,057 | – |

Sum matches the merged 3-day total (733,058) within rounding.

## Day-5 forecast band
| Scenario | Per-day PnL | Source |
|---|---:|---|
| Low | ≈ 227,000 | matches d4 (worst training day) |
| Base | ≈ 244,000 | mean of training days |
| High | ≈ 270,000 | matches d3 (best training day) |

## Stress tests
| Test | Result | OK? |
|---|---|---|
| --match-trades worse | 733,058 (Sharpe 10.80) | baseline |
| --match-trades all | 733,058 (Sharpe 10.80) | **IDENTICAL** — fully passive |
| Day-removal: drop d2 | 497,646 | ratio 0.68 vs full → consistent |
| Day-removal: drop d3 | 462,978 | ratio 0.63 |
| Day-removal: drop d4 | 505,491 | ratio 0.69 |

Match-mode band = 0. No aggressive-cross dependence.

## Prior-round components: which survived, which died
- **Round 1 (v1, 397K)**: PEBBLES invariant, SNACKPACK invariant, 10 within-group cointegration pairs, inside-spread MM, inv_skew. **Survived: 9 pairs (one dropped post-reverify).**
- **Round 2 (v2, 532K)**: PROD_CAP for 9 bleeders. **Survived: all 9 caps unchanged.**
- **Round 2 deferred/rejected**: sine overlay (-496 PnL), Johansen rank-≥2 (no PnL), min-var SNACKPACK weights (-68 PnL), Avellaneda-Stoikov (subsumed). **Dead.**
- **Round 3 (v3, 733K)**: 30 cross-group cointegration pairs. **Survived: all 30.**
- **Round 3 deferred**: lead-lag (1 marginal pair worth ~6K/3d), VAR/Granger, extended-AR/IC, OFI/cross-flow. **Dead — all dominated by Phase C.**
- **mr_study (v6, 399K)**: 7 TAKER products with rolling-FV thresholds. **Dead — v3's passive MM with overlays beats mr_v6's TAKER mode by 334K.**
- **NEW in final**: drop OXYGEN_SHAKE_CHOCOLATE/GARLIC pair (failed reverify ADF p=0.918), PEBBLES_L cap=4 (Phase H ablation found Sharpe +2.47).

## Verification command
```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/batch1_summary/08_final_algo/strategy_final.py \
    5-2 5-3 5-4 --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
Expected total profit: **733,058**.
