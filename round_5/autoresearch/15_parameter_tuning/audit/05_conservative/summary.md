# Phase E — conservative variant

- HARMFUL dropped: 38
- HIGHLY UNSTABLE dropped (β>50%, idx≥39): 12
- Overlap (HARMFUL ∩ UNSTABLE): 3
- Extra caps added: {'PANEL_1X4': 5, 'UV_VISOR_YELLOW': 5, 'OXYGEN_SHAKE_CHOCOLATE': 4}

## Variants compared

| variant                 |   n_pairs | caps_added                                                          |   day2 |   day3 |   day4 |   total_3day |   fold_min |   fold_median |   fold_mean |   sharpe_3day |   max_dd |
|:------------------------|----------:|:--------------------------------------------------------------------|-------:|-------:|-------:|-------------:|-----------:|--------------:|------------:|--------------:|---------:|
| v_full_tuned            |       166 | {}                                                                  | 520225 | 465320 | 450479 |      1436024 |     450479 |        465320 |      473333 |       13.0284 |    27243 |
| v_drop_harmful          |       128 | {}                                                                  | 489823 | 456258 | 446200 |      1392280 |     446200 |        456258 |      460959 |       20.3167 |    24766 |
| v_drop_harmful_unstable |       119 | {}                                                                  | 487888 | 437722 | 446256 |      1371865 |     437722 |        437722 |      449462 |       17.0367 |    32174 |
| v_conservative          |       119 | {"PANEL_1X4": 5, "UV_VISOR_YELLOW": 5, "OXYGEN_SHAKE_CHOCOLATE": 4} | 460960 | 419783 | 445834 |      1326576 |     419783 |        419783 |      433229 |       21.2302 |    36775 |

## Ship rule (CONSERVATIVE vs full TUNED)
- median ≥ tuned_median - 30K? **False** (419,783 vs 435,320)
- sharpe ≥ 30? **False** (sharpe = 21.23)
- fold_min ≥ tuned_fold_min? **False** (419,783 vs 450,479)
- **OVERALL: KEEP TUNED**