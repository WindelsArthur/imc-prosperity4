# Phase B — Lead-Lag Validation

- Candidates from Phase A: 100
- After OOS filter (min-fold Sharpe ≥ 0.7): 5
- After stable-lag filter (decay near peak): 2

## Top survivors (min-fold Sharpe ≥ 0.7)

| i                      | j                   |   lag | group_i      | group_j   |   peak_rho |      fA_ic |   fA_sharpe |   fA_hit |   fA_pnl |      fB_ic |   fB_sharpe |   fB_hit |   fB_pnl |   decay_minus1 |   decay_plus1 |   decay_minus2 |   decay_plus2 |   min_fold_sharpe | decay_stability   |
|:-----------------------|:--------------------|------:|:-------------|:----------|-----------:|-----------:|------------:|---------:|---------:|-----------:|------------:|---------:|---------:|---------------:|--------------:|---------------:|--------------:|------------------:|:------------------|
| OXYGEN_SHAKE_MINT      | PEBBLES_XL          |    60 | oxygen_shake | pebbles   |  0.0205143 | 0.0145026  |    1.58312  | 0.494919 |   4725.5 | 0.0175863  |    1.46388  | 0.495825 |   4353   |       0.711913 |     -0.796164 |      -1.03797  |      0.75169  |          1.46388  | False             |
| OXYGEN_SHAKE_CHOCOLATE | PEBBLES_XS          |    39 | oxygen_shake | pebbles   |  0.0218834 | 0.0308321  |    2.51736  | 0.485743 |   3711   | 0.00837826 |    1.14261  | 0.468173 |   1646.5 |      -1.66945  |      1.8249   |       0.483318 |     -1.07176  |          1.14261  | True              |
| PANEL_1X4              | PANEL_1X2           |    33 | panel        | panel     |  0.0212866 | 0.00675181 |    0.962399 | 0.476319 |    791   | 0.00887612 |    1.24626  | 0.473008 |   1140   |       0.703936 |      0.633149 |       0.819709 |      0.564826 |          0.962399 | True              |
| PEBBLES_M              | SNACKPACK_PISTACHIO |    13 | pebbles      | snackpack | -0.0230434 | 0.00961235 |    1.13276  | 0.470859 |    588   | 0.00594401 |    0.855413 | 0.470859 |    437   |      -0.935069 |     -0.147768 |       0.99439  |     -0.295702 |          0.855413 | False             |
| MICROCHIP_RECTANGLE    | PANEL_1X2           |    47 | microchip    | panel     |  0.0259671 | 0.0108932  |    0.83233  | 0.478899 |    687.5 | 0.00399063 |    1.2382   | 0.481813 |   1137.5 |      -1.03334  |     -0.350974 |      -0.228072 |     -1.23774  |          0.83233  | False             |
