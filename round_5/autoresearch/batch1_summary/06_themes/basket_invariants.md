# Theme: Basket invariants

## Definition
A linear combination of group-member mids has constant or near-constant value across the entire training window. The residual reverts on a sub-tick timescale, so it is exploited as a short-horizon skew on inside-spread MM quotes rather than as a marketable cross.

## Products affected
- **PEBBLES** (PEBBLES_L, PEBBLES_M, PEBBLES_S, PEBBLES_XL, PEBBLES_XS): Σ mid = 50,000 ± 2.8.
- **SNACKPACK** (CHOCOLATE, PISTACHIO, RASPBERRY, STRAWBERRY, VANILLA): Σ mid = 50,221 ± 190.

## Reconciled findings
- **PEBBLES sum = 50,000 ± 2.8 (re-verified)**: mean=49,999.94, std=2.80, range [49,981.5, 50,016.5] over 30,000 stitched ticks. R² of any-pebble-on-other-four basket regression = 0.999998. OU half-life of basket residual = 0.16 ticks (effectively instantaneous reversion).  
  *Sources:* `ROUND_5/autoresearch/05_cross_product/groups/pebbles/basket_residual.csv`, `ROUND_5/autoresearch/11_findings/exploitable_patterns.md`, reverify in `ROUND_5/batch1_summary/03_reconciliation/reverify_results/stats_reverify.csv`.

- **SNACKPACK sum = 50,221 ± 190 (re-verified)**: mean=50,220.94, std=189.58, range [49,706, 50,625.5]. ~10× weaker than pebbles. Best EG within-group pair RASPBERRY/VANILLA ADF p=0.001 (re-verified at 0.0014).  
  *Sources:* `ROUND_5/autoresearch/05_cross_product/groups/snackpack/basket_residual.csv`, `ROUND_5/autoresearch/13_round2_research/M_submit/findings_v2.md`.

- **Phase C of round-2 Johansen**: PEBBLES has rank 1 (already used as sum=50,000); SNACKPACK has rank 5 but residual std=0.96 → tiny capacity — not exploitable as a higher-rank invariant.  
  *Source:* `ROUND_5/autoresearch/13_round2_research/C_johansen/`.

- **Cross-group basket attempts (Phase F round 2)**: SNACKPACK weighted basket has rel_std=0.0023 vs 0.004 for equal-weight, but swapping the equal-weight skew for weighted yielded −68 PnL in ablation. Other cross-group min-var baskets in UV_VISOR + ROBOT exist but std-vs-spread economics don't pay.  
  *Source:* `ROUND_5/autoresearch/13_round2_research/F_cross_basket/`.

## Expected PnL contribution (low / mid / high)
- PEBBLES: 50K / 55K / 60K per 3 days (across the 5 pebble products combined, after PROD_CAP).
- SNACKPACK: 0K / 9K / 20K per 3 days (high variance — STRAWBERRY +14K dominates a couple of bleeders).
- Combined: ~50–80K per 3 days = **17–27K / day**.

## Integration in final algo
```python
# In Trader.run():
PEBBLES_SUM_TARGET = 50000.0
if all(p in mids for p in PEBBLES):
    psum = sum(mids[p] for p in PEBBLES)
    resid = psum - PEBBLES_SUM_TARGET
    skew = max(-3.0, min(3.0, -resid / 5.0))
    for p in PEBBLES: pebble_skew[p] = skew

SNACKPACK_SUM_TARGET = 50221.0
if all(p in mids for p in SNACKPACKS):
    ssum = sum(mids[p] for p in SNACKPACKS)
    resid = ssum - SNACKPACK_SUM_TARGET
    skew = max(-5.0, min(5.0, -resid / 5.0))
    for p in SNACKPACKS: snack_skew[p] = skew
```

The skew is a soft fair-value tilt added to the inside-spread MM. Aggressive crossing only fires when basket residual exceeds ±1.8σ (PEBBLES) or ±3.5σ (SNACKPACK).
