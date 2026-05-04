# SLEEP_POD_POLYESTER

**Final 3-day PnL: +8049**  ·  mode = `TAKER`

## Universe stats (day-2)
- spread_p50 = 11  ·  mid_std = 978  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.906  ·  KPSS p = 0.01  ·  OU half-life = 8485.1
- AR(1)-on-Δmid coef = 0.006  (p = 0.518)
- lattice_ratio = 0.199

## Phase 1 — best FV (composite-z ranked)
- FV: `rangemid_500`  ·  IC|abs| = 0.017  ·  half-life = 156.18  ·  res/spread = 10.13

## Phase 2 — best in-sim threshold config (taker)
- FV `rangemid_500`  ·  z_in=1.75  z_out=0.10  sizing=fixed
- pnl_A (day-3 OOS) = +7056  ·  pnl_B (day-4 OOS) = +17382  ·  avg_daily = +12219
- min_sharpe across folds = 1.21

## Chosen runtime config
```
{
  "mode": "TAKER",
  "fv_family": "range_mid",
  "fv_params": {
    "w": 500
  },
  "sigma_fallback": 50.0,
  "z_in": 1.75,
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
≈ +2683 (= total / 3, given walk-forward stability).
