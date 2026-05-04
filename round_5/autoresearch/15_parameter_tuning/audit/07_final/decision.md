# Phase G — final decision

## Candidates (sorted by fold_min, then Sharpe)

| candidate           |  n_pairs | day2    | day3    | day4    | total_3day | fold_min | fold_median | sharpe | max_dd |
|:--------------------|---------:|--------:|--------:|--------:|-----------:|---------:|------------:|-------:|-------:|
| v_final             |      166 | 520,225 | 465,320 | 450,479 |  1,436,024 |  450,479 |     465,320 |  13.03 | 27,243 |
| v_drop_harmful_only |      128 | 489,823 | 456,258 | 446,200 |  1,392,280 |  446,200 |     456,258 |  20.32 | 24,766 |
| v_conservative      |      119 | 460,960 | 419,783 | 445,834 |  1,326,576 |  419,783 |     419,783 |  21.23 | 36,775 |
| v_replatueau        |       89 | 450,814 | 418,008 | 381,333 |  1,250,154 |  381,333 |     418,008 |  11.99 | 20,099 |

Sources:
- v_final: `07_assembly/algo1_tuned.py`
- v_drop_harmful_only: built here, `audit/07_final/algo1_drop_harmful_only.py`
- v_conservative: `audit/05_conservative/algo1_conservative.py`
- v_replatueau: built here, `audit/07_final/algo1_replatueau.py`

## Decision rule (mission)
**Ship the variant with the highest fold_min PnL, breaking ties by Sharpe.**
Day-5 floor = fold_min (the worst observed day).

## Winner: **v_final** (`algo1_tuned.py`, unchanged)
- fold_min: **450,479**
- fold_median: 465,320
- 3-day total: 1,436,024
- Sharpe (3-day): 13.03
- n_pairs: 166

`v_final` wins on the strict mission rule by **4,279** PnL on fold_min (≈ +0.95%
above runner-up).

## Why the audit ships v_final and rejects v_conservative

The audit verifies that the **+353K uplift over baseline is mostly REAL**, not
overfit:

1. **Phase A (per-product attribution)**: 54% of the uplift (191K of 353K) comes
   from 5 products that have lower variance AND higher fold_min than baseline:
   PEBBLES_XS (+59.8K, fold_min +27.6K), SNACKPACK_CHOCOLATE (+39.6K,
   fold_min +13.7K), SNACKPACK_RASPBERRY (+36.6K — gained with **0 added
   pairs**, purely from cap/skew param changes), MICROCHIP_CIRCLE (+29.7K,
   fold_min +10.4K), SNACKPACK_VANILLA (+26.1K, fold_min +11.5K). All 5
   improved on every fold simultaneously — robust gains.

2. **Phase B (pair LOO)**: The aggressive 127 added pairs are mostly inert or
   net-positive. Only 38 instances (mapping to 10 unique (a,b) signatures) are
   "HARMFUL" by the LOO criterion. Joint removal of all 38 (`v_drop_harmful_only`)
   loses 44K total PnL, which is FAR less than the 131K "naive sum of LOO
   uplifts" predicted — meaning the harmful pairs are mostly duplicates that
   substitute for each other.

3. **Phase C (pair stability)**: The β-shift criterion (>30% between day-2-fit
   and full-stitch-fit) flags 82/166 pairs as unstable, BUT Phase E and Phase F
   show that dropping these pairs HURTS PnL. The strategy depends on
   short-window mean-reversion, not strict cointegration — the β shifts are
   real and the tilts still pay.

4. **Phase D (variance)**: The Sharpe drop 63→13 is concentrated in 10
   products (90.9% of the variance increase). OXYGEN_SHAKE_CHOCOLATE
   (+7.8K xday std) and PEBBLES_XL (+7.5K) are the main contributors. But
   capping these (Phase E v_conservative) HURTS PnL more than it helps Sharpe
   for the day-5 floor.

5. **Phase F (re-plateau)**: Re-running the pair-count sweep with the
   stability filter yielded no N where fold_min beats v_final. Best was
   N_used=80 at fold_min 381K — 69K below v_final.

The audit decision is explicitly justified, not default-accepted.

## Honourable mention: v_drop_harmful_only

`v_drop_harmful_only` is a strong runner-up that is **strictly more robust**
than v_final on every dimension except raw fold_min:

- fold_min only **4,279 lower** (1% drop)
- Sharpe **+56% higher** (20.32 vs 13.03)
- Max drawdown **-2,477 lower** (24,766 vs 27,243)
- Per-day std **-12K lower** (~17K vs ~30K)
- 5th-percentile day-5 projection (Normal-fit q05): **433K vs 429K — HIGHER**

If the user prefers a tighter PnL distribution at the cost of 1% fold_min, ship
`v_drop_harmful_only`. The mission's strict rule keeps v_final.

## Variants that fail clearly
- `v_conservative` (fold_min 419,783): -30K below v_final. Adding caps on
  PANEL_1X4/UV_VISOR_YELLOW/OXYGEN_SHAKE_CHOCOLATE leaves money on the table.
- `v_replatueau` (fold_min 381,333): -69K below v_final. The β-shift filter
  removes too many productive pairs.

## Files
- `algo1_day5.py`             — chosen ship algo (= `algo1_tuned.py`)
- `algo1_drop_harmful_only.py` — runner-up, robustness-optimised alternative
- `algo1_replatueau.py`       — Phase F-derived variant (rejected)
- `candidates.csv`            — full comparison table
- `pnl_projection.csv`, `pnl_projection.md` — day-5 bands
