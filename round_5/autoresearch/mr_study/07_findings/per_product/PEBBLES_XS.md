# PEBBLES_XS

**Final 3-day PnL: +15016**  ·  mode = `TAKER`

## Universe stats (day-2)
- spread_p50 = 9  ·  mid_std = 1450  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.794  ·  KPSS p = 0.01  ·  OU half-life = 3213.0
- AR(1)-on-Δmid coef = -0.008  (p = 0.42)
- lattice_ratio = 0.270

## Phase 1 — best FV (composite-z ranked)
- FV: `ar5_dx`  ·  IC|abs| = 0.021  ·  half-life = 0.10  ·  res/spread = 1.41

## Phase 2 — best in-sim threshold config (taker)
- FV `quad_500`  ·  z_in=1.25  z_out=0.10  sizing=fixed
- pnl_A (day-3 OOS) = +7706  ·  pnl_B (day-4 OOS) = +12052  ·  avg_daily = +9879
- min_sharpe across folds = 0.92

## Chosen runtime config
```
{
  "mode": "TAKER",
  "fv_family": "rolling_quadratic",
  "fv_params": {
    "w": 500
  },
  "sigma_fallback": 50.0,
  "z_in": 1.25,
  "z_out": 0.1,
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
≈ +5005 (= total / 3, given walk-forward stability).
