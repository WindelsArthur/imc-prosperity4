# SNACKPACK_CHOCOLATE

**Final 3-day PnL: +5017**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 17  ·  mid_std = 201  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.125  ·  KPSS p = 0.01  ·  OU half-life = 547.1
- AR(1)-on-Δmid coef = -0.024  (p = 0.0182)
- lattice_ratio = 0.063

## Phase 1 — best FV (composite-z ranked)
- FV: `ar1_dx`  ·  IC|abs| = 0.032  ·  half-life = 0.09  ·  res/spread = 0.32

## Phase 2 — best in-sim threshold config (taker)
- FV `median_50`  ·  z_in=2.50  z_out=0.50  sizing=fixed
- pnl_A (day-3 OOS) = -2132  ·  pnl_B (day-4 OOS) = +566  ·  avg_daily = -783
- min_sharpe across folds = -1.39

## Chosen runtime config
```
{
  "mode": "MM",
  "alpha_skew": 1.0,
  "beta_inv": 0.3,
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
≈ +1672 (= total / 3, given walk-forward stability).
