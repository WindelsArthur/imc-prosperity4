# PnL Estimates — strategy_final

Backtests run with `prosperity4btest` against `ROUND_5/autoresearch/10_backtesting/data/round5/`. Position limit = 10 enforced for every product via `--limit ...:10` flags.

## Per-day backtest (training set, --match-trades worse)
| Day | PnL | Max DD |
|---|---:|---:|
| 5-2 | 235,412 | 19,398 |
| 5-3 | 270,079 | 15,305 |
| 5-4 | 227,566 | 21,786 |
| Σ234 | **733,058** | 21,786 |

`prosperity4btest --merge-pnl` Sharpe = **10.80**. Calmar ≈ 33.6.

Match-mode band: 0 (strategy is fully passive — `worse` and `all` identical).

## Day-5 forecast band
| Scenario | Per-day PnL | Notes |
|---|---:|---|
| Low | ≈ 227,000 | matches worst training day (d4) |
| Base | ≈ 244,000 | mean of training days |
| High | ≈ 270,000 | matches best training day (d3) |

## Tail risks (could push below the low)
- Day-5 cross-group cointegration relationships shifting (e.g. PEBBLES_XL ~ PANEL_2X4 slope drift).
- One-sided runs in PEBBLES_L (mitigated by cap=4) or SNACKPACK_RASPBERRY (mitigated by cap=5).
- Unseen day-of-day regime breaks in the 10 KS-flagged products (handled via inv_skew + tilt clip).

## Improvements vs prior baselines
| Baseline | PnL | Sharpe | Δ to final |
|---|---:|---:|---:|
| Round 1 v1 | 396,749 | 4.22 | +336,309 PnL, +6.58 Sharpe |
| Round 2 v2 (with PROD_CAP) | 531,525 | 8.61 | +201,533 PnL, +2.19 Sharpe |
| Round 3 v3 (= true baseline) | 733,320 | 8.34 | −262 PnL, **+2.47 Sharpe**, **−2,204 DD** |
| mr_study v6 | 399,636 | 0.93 | +333,422 PnL, **+9.87 Sharpe** |
| **strategy_final** | **733,058** | **10.80** | – |
