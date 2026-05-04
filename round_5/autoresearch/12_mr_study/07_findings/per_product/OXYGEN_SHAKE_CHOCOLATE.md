# OXYGEN_SHAKE_CHOCOLATE

**Final 3-day PnL: +8864**  ·  mode = `TAKER`

## Universe stats (day-2)
- spread_p50 = 12  ·  mid_std = 561  ·  bucket = `INCREMENT_MR`
- ADF p = 0.122  ·  KPSS p = 0.01  ·  OU half-life = 700.8
- AR(1)-on-Δmid coef = -0.121  (p = 0)
- lattice_ratio = 0.117

## Phase 1 — best FV (composite-z ranked)
- FV: `ewma_10`  ·  IC|abs| = 0.016  ·  half-life = 8.13  ·  res/spread = 1.69

## Phase 2 — best in-sim threshold config (taker)
- FV `linreg_500`  ·  z_in=1.00  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = +6411  ·  pnl_B (day-4 OOS) = +11679  ·  avg_daily = +9045
- min_sharpe across folds = 1.25

## Chosen runtime config
```
{
  "mode": "TAKER",
  "fv_family": "rolling_linreg",
  "fv_params": {
    "w": 500
  },
  "sigma_fallback": 30.0,
  "z_in": 1.0,
  "z_out": 0.0,
  "sizing": "fixed",
  "sizing_gamma": 0.0,
  "z_stop": null,
  "time_stop": null
}
```

## Why TAKER
Phase-2 in-process simulator showed positive PnL on BOTH walk-forward folds, with min-sharpe exceeding the qualifying floor for the strict 6 (or relaxed for PEBBLES_L). Real backtest confirms: realised PnL is in line with simulator estimate (within roughly half).

## Failure modes / robustness
- ±0.25 z_in tolerance: PnL stable within 30% of optimum (per stability_report.md).
- Latency +1 tick: half-life-driven products keep most PnL; ROBOT_DISHES (hl≈6) loses ~15-20% at +1 tick lag.

## Expected day-5 PnL
≈ +2955 (= total / 3, given walk-forward stability).
