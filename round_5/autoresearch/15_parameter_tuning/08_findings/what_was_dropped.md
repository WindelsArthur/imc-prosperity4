# Configurations dropped during tuning

This document lists configs that **looked attractive on a single metric** but failed the joint gate. They are dropped for a reason — beating baseline on one number while losing on another is a classic overfitting signature.

## Tier-1 LHS (50 configs + baseline)

- 8 configs beat baseline mean by ≥ +2K (gate a)
- 0 configs beat baseline median (gate b)
- All 51 configs have 5/5 folds positive (gate c)
- **0 configs pass gates (a)+(b)+(c) jointly** → revert

Notable rejected configs:
- `lhs_011` (div=1.81, clip=10.56, beta=0.135): mean +8,608, fold_min +8,391 (HIGHER than baseline) — **but** fold_median -740. Fails gate (b) by 0.2%. Strict median gate kills an otherwise-robust candidate.
- `lhs_017` (div=2.75, clip=9.59, beta=0.212, gate=0.76): mean +6,476, median -648. Same pattern.
- `lhs_023` (div=6.01, clip=8.54, beta=0.335): Sharpe 73.7 (HIGHER than baseline 63), mean -531, median -5,366. High Sharpe but lower PnL. Sharpe alone is misleading when PnL is the goal.

## Tier-1 TPE (40 trials seeded from LHS top-10)

TPE pushed toward `(div=1.7, clip=11.6, beta=0.12, qbsc=6, gate=0.59)` — aggressive low-divisor / high-clip region. Best fold_median 362,930 (still < baseline 363,578). Only 1 trial tied or beat baseline median, none passed all gates.

## Tier-1 plateau analysis

24 cells across 5 univariate sweeps (anchored at TPE optimum). 6 cells beat baseline median INDIVIDUALLY but failed joint gate. None of the plateau cells satisfied "neighbors within ±10% all pass" (gate f) when measured against baseline — the plateau is a robust valley, not a peak above baseline.

## Tier-2 PEBBLES (36 cells)

- 22 cells beat baseline median
- 10 cells failed mean uplift gate
- All 36 had 5/5 folds positive
- **Winner**: DIVISOR=8/CLIP=5/BIG_SKEW=3.5 with broad plateau (6 identical cells)

Notable: configs with PEBBLES_BIG_SKEW = 1.0 (more aggressive cross threshold) consistently underperformed — meaning the aggressive cross was a HURT, not help. The new BIG_SKEW=3.5 effectively disables it.

## Tier-2 SNACKPACK (27 cells)

- 15 cells beat baseline median
- 0 failed mean uplift
- All 27 had 5/5 folds positive
- **Winner**: DIVISOR=5 / CLIP=3 / BIG_SKEW=3.5

Tightening CLIP from 5 → 3 was the key move. The baseline allowed too-large skew adjustments on SNACKPACK basket residuals.

## Tier-3 PROD_CAP

70 cells (10 products × 7 caps each). Most products had no clear uplift — 6 of 10 reverted.

Dropped:
- All "uplift" candidates with `delta_median < 1000` were rejected (per the +1K incremental gate).
- Configs that improved the swept-product's PnL but degraded fold_min were rejected.

## Tier-4 N_PAIRS

14 cells (7 N values × 2 ranking methods).

- N=20: median 327K (worse than baseline)
- N=30: median 346K (still worse than v_final's component baseline)
- N=50, 75, 100, 125, 150, 157: monotonic increase
- **No peak/decline observed** — the mission's hypothesis "PnL likely peaks then declines as low-Sharpe pairs add noise" was NOT supported by the data

Dropped: N ≤ 100 with combined_sharpe ranking (all underperform combined_pnl ranking at same N).

## Phase 6 stress

No configurations were dropped during stress; but the **limit-8 stress flagged a structural fragility** in v_final: PnL drops to 24% of headline (340K) when limits are reduced by 20%. The mission allows shipping with documented fragility (since PnL stays positive and is 6.9× better than baseline at limit-8). 

If a more limit-robust variant is needed, drop to N=100 pairs (1,328K headline, expected limit-8 ~315K = 24% retention as well — limit-8 is a structural feature, not configuration-dependent).
