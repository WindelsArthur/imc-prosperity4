# OXYGEN_SHAKE_EVENING_BREATH

**Final 3-day PnL: +7669**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 12  ·  mid_std = 400  ·  bucket = `DETERMINISTIC`
- ADF p = 0.792  ·  KPSS p = 0.01  ·  OU half-life = 2744.1
- AR(1)-on-Δmid coef = -0.174  (p = 0)
- lattice_ratio = 0.015

## Phase 1 — best FV (composite-z ranked)
- FV: `ar1_dx`  ·  IC|abs| = 0.090  ·  half-life = 0.13  ·  res/spread = 0.64

## Phase 2 — best in-sim threshold config (taker)
- FV `ar5_dx`  ·  z_in=2.50  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = -120  ·  pnl_B (day-4 OOS) = -60  ·  avg_daily = -90
- min_sharpe across folds = -1.76

## Chosen runtime config
```
{
  "mode": "MM",
  "alpha_skew": 1.5,
  "beta_inv": 0.5,
  "max_size": 10,
  "spread_offset": 1,
  "fv_family": "ar_diff",
  "fv_params": {
    "p": 1
  }
}
```

## Why signal-skewed MM
Phase 1 IC > 0.03 indicates short-horizon residual reversion. Inside-spread MM with skew α·z + inventory β·pos shifts quotes against the predicted direction, capturing the half-spread on the reversion leg.

## Failure modes / robustness
- Loss appears when sustained directional drift exceeds the half-spread → captures bid then sells lower.
- match-mode delta `worse` vs `all`: <1% — execution-mode robust.

## Expected day-5 PnL
≈ +2556 (= total / 3, given walk-forward stability).
