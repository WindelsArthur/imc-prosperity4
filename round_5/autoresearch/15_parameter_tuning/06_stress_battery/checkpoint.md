# Phase 6 (Stress Battery) Checkpoint

## Headline stress results
### match_mode
| mode   |   lagged |   limit |   day |   fold_median |   fold_mean |   fold_min |   total_3day |   max_dd |   pnl |
|:-------|---------:|--------:|------:|--------------:|------------:|-----------:|-------------:|---------:|------:|
| worse  |      nan |     nan |   nan |        465320 |      473333 |     450479 |  1.43602e+06 |    27243 |   nan |
| all    |      nan |     nan |   nan |        465320 |      473333 |     450479 |  1.43602e+06 |    27243 |   nan |

### latency
|   mode | lagged   |   limit |   day |   fold_median |   fold_mean |   fold_min |   total_3day |   max_dd |   pnl |
|-------:|:---------|--------:|------:|--------------:|------------:|-----------:|-------------:|---------:|------:|
|    nan | False    |     nan |   nan |        465320 |      473333 |     450479 |  1.43602e+06 |    27243 |   nan |
|    nan | True     |     nan |   nan |        400222 |      420019 |     400222 |  1.29965e+06 |    28345 |   nan |

### limit
|   mode |   lagged |   limit |   day |   fold_median |   fold_mean |   fold_min |       total_3day |   max_dd |   pnl |
|-------:|---------:|--------:|------:|--------------:|------------:|-----------:|-----------------:|---------:|------:|
|    nan |      nan |      10 |   nan |        465320 |      473333 |     450479 |      1.43602e+06 |    27243 |   nan |
|    nan |      nan |       8 |   nan |        114069 |      113730 |      90058 | 340514           |    12106 |   nan |

### day_only
|   mode |   lagged |   limit |   day |   fold_median |   fold_mean |   fold_min |   total_3day |   max_dd |    pnl |
|-------:|---------:|--------:|------:|--------------:|------------:|-----------:|-------------:|---------:|-------:|
|    nan |      nan |     nan |     2 |           nan |         nan |        nan |          nan |      nan | 520225 |
|    nan |      nan |     nan |     3 |           nan |         nan |        nan |          nan |      nan | 465320 |
|    nan |      nan |     nan |     4 |           nan |         nan |        nan |          nan |      nan | 450479 |

### perturbation (LHS ±20%)
- n_samples: 15
- q05 fold_median: 411,039
- median fold_median: 465,045
- q95 fold_median: 470,436