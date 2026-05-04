# Phase 0 — data sanity & product universe

## Environment
- `prosperity4btest` resolves to `imcp/bin/prosperity4btest` (venv-shipped binary).
- `utils.backtester.run_backtest` import OK.
- No-op smoke backtest over `5-2 5-3 5-4` with `--match-trades worse`: returncode 0, total_pnl 0, drawdown 0, 50 product entries. **Wall-clock 14.2s.** Confirms the matching pipeline + `--limit=PRODUCT:10` flags.

## Data shape
- 3 days available: 2, 3, 4. 10,000 ticks/day @ step 100. 50 products × 10k = 500,000 rows per day.
- Columns: bid/ask 1/2/3 with volumes, mid_price, profit_and_loss. NaNs only on bid/ask 3 levels (sparse depth).
- Spread (BBO) median across products: 6 (ROBOT_IRONING) → 18 (SNACKPACK_STRAWBERRY). Mid std: 169 (SNACKPACK_RASPBERRY) → 1830 (MICROCHIP_SQUARE).

## Per-product universe → `product_universe.csv`
50 rows. Stats from day-2 (training fold). Every product still gets the full sweep — bucket is a priority hint only.

| bucket | count | criterion |
| --- | --- | --- |
| DETERMINISTIC | 2 | lattice_ratio < 0.05 OR ADF p < 1e-6 |
| INCREMENT_MR | 1 | AR(1) on Δmid coef < −0.05 (and not deterministic) |
| WEAK_DRIFT | 47 | rest |

DETERMINISTIC: `OXYGEN_SHAKE_EVENING_BREATH` (lattice_ratio 0.0151, AR1_diff −0.174), `ROBOT_IRONING` (0.0210, −0.162). Confirms the round-3/4 priors.

INCREMENT_MR: `OXYGEN_SHAKE_CHOCOLATE` (AR1_diff −0.121).

## Signal landscape (priors confirmed)
- Mid prices look unit-root for all 50: ADF p < 0.05 only for `MICROCHIP_CIRCLE` (0.015) and `UV_VISOR_RED` (0.035); the rest fail to reject. KPSS p ≈ 0.01 across the board → both tests reject stationarity for nearly everything.
- DFA-Hurst on the level ≈ 1.40–1.58 → consistent with random-walk-like cumulation (Hurst on increments ≈ 0.4–0.6 expected; computed but not surfaced as primary metric).
- Day-pair distributional KS on increments: most pairs reject (p ≪ 0.05), so day-2-only fits will miss regime drift; walk-forward refit on each fold is mandatory.

## Implications for Phase 1
- Pure level-MR FV (rolling mean) will be useless for most products — the price level is non-stationary. Focus instead on:
  1. Microstructure FVs (microprice, OFI-corrected mid, spread-aware imbalance) that capture short-horizon revert-to-fair behaviour.
  2. Lattice-snap FV for the two deterministic products.
  3. Markov-conditional mean / AR(p) one-step on diff space — exploits the negative lag-1 autocorr of Δmid for the INCREMENT_MR product.
  4. Inside-spread MM (rule J) is still the workhorse — every product gets it as a fallback floor.

## Backtest cost budget
- 14.2s/run baseline → ~30–40s for active traders. 100 backtests ≈ 50–70 min. Use a fast in-process simulator for the sweeps; reserve real backtests for shortlist validation.
