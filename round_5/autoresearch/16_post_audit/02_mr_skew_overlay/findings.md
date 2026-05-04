# Phase 2 — AR(1) MR as additive skew — findings

## Verdict: **DOES NOT SHIP** (hypothesis falsified)

Adding `-φ · Δmid · α` to fair value as an additive skew (the formulation
the mission wanted re-tested across all priority products) shows zero
sustained alpha. The hypothesis is **rejected**.

## Step 2a — cross-day stability filter (3 of 7 survive)

| product | φ_d2 | φ_d3 | φ_d4 | mean φ | std φ | survives |
|---|---:|---:|---:|---:|---:|:---:|
| OXYGEN_SHAKE_EVENING_BREATH | -0.174 | -0.094 | -0.077 | -0.115 | 0.042 | ✓ |
| ROBOT_IRONING | -0.162 | -0.077 | -0.114 | -0.118 | 0.035 | ✓ |
| OXYGEN_SHAKE_CHOCOLATE | -0.121 | -0.008 | -0.111 | -0.080 | 0.051 | ✓ |
| PEBBLES_L | +0.006 | +0.002 | +0.012 | +0.007 | 0.004 | ✗ (mean too small) |
| PEBBLES_M | -0.001 | -0.010 | -0.004 | -0.005 | 0.004 | ✗ |
| PEBBLES_XS | -0.008 | -0.021 | -0.018 | -0.016 | 0.005 | ✗ |
| ROBOT_MOPPING | -0.019 | -0.012 | -0.004 | -0.012 | 0.006 | ✗ |

Filter rule: same-sign across all 3 days **AND** |mean φ| > 0.05. The dropped
products have AR(1) coefs an order of magnitude smaller and are
indistinguishable from random walks at tick frequency.

## Step 2b — per-product α sweep (all 12 cells fail the gate)

For the 3 surviving products, sweep α ∈ {0.5, 1.0, 1.5, 2.0}, holding all
others at baseline:

| product | α=0.5 | α=1.0 | α=1.5 | α=2.0 |
|---|---:|---:|---:|---:|
| OXYGEN_SHAKE_CHOCOLATE — Δfold_min | 0 | 0 | 0 | 0 |
| ROBOT_IRONING — Δfold_min | 0 | 0 | 0 | 0 |
| OXYGEN_SHAKE_EVENING_BREATH — Δfold_min | -188 | -188 | -328 | -952 |

`OXYGEN_SHAKE_CHOCOLATE` and `ROBOT_IRONING` cells produce **identical** PnL
to baseline at every α — the AR(1) skew is **inert** on these products.

`OXYGEN_SHAKE_EVENING_BREATH` is the only product where the overlay actually
changes orders, and it consistently REGRESSES fold_min.

## Why the overlay is inert / harmful

The skew magnitude is `|φ · Δmid · α|`. For the surviving products with
|φ| ≈ 0.08–0.12 and tick-level |Δmid| ≈ 1, even at α=2.0 the skew is at most
0.24 dollars. The trader's order gate is `fair > bid_px - 0.25` — i.e. a fair
that sits within 0.25 of the best bid. A 0.24-dollar shift is **just below**
the threshold that would flip an order, so for products where the integer mid
sits squarely between a bid/ask the AR(1) skew never crosses the gate.

For OXYGEN_SHAKE_EVENING_BREATH, where the skew DOES occasionally cross, the
direction is wrong: the overlay pulls the fair *toward* the recent move
(via the `-φ · Δmid` formulation with negative φ → +Δmid contribution),
biasing the maker into the next tick of momentum and adversely-selecting.

## Step 2c — combined run skipped

Zero retained products → no combined run. `combined_run.csv` not produced.

## Implication for the algo1_post_audit assembly

Phase 2 contributes NOTHING. The combined algo will skip this layer.
This is the **second-most-important finding of the post-audit study**: the
AR(1) signal documented in prior research is real but is **not tradeable
as an additive maker-skew** at this resolution and order-gate. To extract
it, one would need to either:
1. lower the `fair > bid - 0.25` gate to `bid - 0.50` (tested implicitly by
   Phase 1 cells with `1d` AR(1)-only — which lose -7,856 fold_min on
   ROBOT_DISHES too, suggesting the gate isn't the binding constraint), OR
2. use AR(1) as a **TAKER signal** (cross the spread when |φ·Δmid·α| is
   large), which is what Round-4's `algo_mr1` family attempted (out of
   scope for this study).

## Output artefacts

- `01_ar1_per_product.py` — Step 2a fitter
- `02_run_alpha_sweep.py` — Steps 2b/2c sweep
- `ar1_coefs_per_product.csv` — per-day per-product φ
- `per_product_alpha_sweep.csv` — 12 cells × full per-fold metrics
- `per_product_decisions.csv` — per-product verdict (all ✗)
- `ablation.csv` — baseline + all sweep cells
