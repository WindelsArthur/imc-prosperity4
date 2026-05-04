# PANEL_1X2

**Final 3-day PnL: -456**  ·  mode = `MM`

## Universe stats (day-2)
- spread_p50 = 12  ·  mid_std = 590  ·  bucket = `WEAK_DRIFT`
- ADF p = 0.741  ·  KPSS p = 0.01  ·  OU half-life = 3067.2
- AR(1)-on-Δmid coef = 0.001  (p = 0.895)
- lattice_ratio = 0.145

## Phase 1 — best FV (composite-z ranked)
- FV: `quad_500`  ·  IC|abs| = 0.016  ·  half-life = 49.32  ·  res/spread = 3.69

## Phase 2 — best in-sim threshold config (taker)
- FV `quad_500`  ·  z_in=2.50  z_out=0.00  sizing=fixed
- pnl_A (day-3 OOS) = +0  ·  pnl_B (day-4 OOS) = +2635  ·  avg_daily = +1318
- min_sharpe across folds = 0.00

## Chosen runtime config
```
{
  "mode": "MM",
  "alpha_skew": 0.0,
  "beta_inv": 0.2,
  "max_size": 10,
  "spread_offset": 1
}
```

## Why default MM
No qualifying TAKER (Phase 2 sim required pnl_A > 0 AND pnl_B > 0). Inside-spread quoting with inventory skew earned positive PnL in v3 backtest after the in-spread clamp fix; we keep the simple passive variant.

## Failure modes / robustness
- Loss appears when sustained directional drift exceeds the half-spread → captures bid then sells lower.
- match-mode delta `worse` vs `all`: <1% — execution-mode robust.

## Expected day-5 PnL
≈ -152 (= total / 3, given walk-forward stability).
