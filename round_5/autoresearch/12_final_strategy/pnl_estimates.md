# PnL Estimates — Round 5

Backtests run with `prosperity4btest` against
`ROUND_5/autoresearch/10_backtesting/data/round5/` (mirror of `ROUND_5/Data/`).
Position limit = 10 enforced for every product via `--limit ...:10` flags.

## Per-day backtest (training set)

| Day  | Total PnL | Max DD abs | Match modes diverge? |
|------|-----------|------------|----------------------|
| 5-2  | 124,893   | 26,980     | no                   |
| 5-3  | 105,220   | 30,772     | no                   |
| 5-4  | 166,636   | 20,244     | no                   |
| Σ234 | **396,749** | – | – |

Strategy is fully passive — `--match-trades worse` and `--match-trades all`
return identical PnL.

`prosperity4btest --merge-pnl` Sharpe = 4.22.

## Day-5 forecast band

| Scenario      | Per-day PnL | Notes                                              |
|---------------|-------------|----------------------------------------------------|
| Low           | ≈ 105,000   | matches the worst training day (5-3)               |
| Base / mean   | ≈ 132,000   | mean of training days                               |
| High          | ≈ 170,000   | matches best training day (5-4)                     |

Tail risks that could push below the low:
- Day-5 sine phase differs from training (especially MICROCHIP_OVAL,
  UV_VISOR_AMBER, SLEEP_POD_POLYESTER).
- One-sided drift in basket residuals (most likely on SNACKPACK).
- An unseen macro regime change that the inventory-skew controller cannot
  absorb fast enough.

## Per-product 3-day cumulative (`--match-trades worse`)

Top 15 winners and bottom 5 losers of the strategy across days 2–4
(parsed from `10_backtesting/results/walk_forward_summary.csv`):

| product                          | 3-day PnL |
|----------------------------------|-----------|
| PEBBLES_XL                       | 50,715    |
| PANEL_1X4                        | 29,536    |
| MICROCHIP_RECTANGLE              | 26,299    |
| OXYGEN_SHAKE_CHOCOLATE           | 24,785    |
| SNACKPACK_STRAWBERRY             | 22,855    |
| ROBOT_LAUNDRY                    | 21,504    |
| OXYGEN_SHAKE_EVENING_BREATH      | 20,865    |
| UV_VISOR_AMBER                   | 19,988    |
| GALAXY_SOUNDS_PLANETARY_RINGS    | 18,164    |
| SLEEP_POD_POLYESTER              | 18,065    |
| PANEL_2X4                        | 18,014    |
| SLEEP_POD_COTTON                 | 17,491    |
| TRANSLATOR_VOID_BLUE             | 16,806    |
| PEBBLES_S                        | 15,783    |
| GALAXY_SOUNDS_BLACK_HOLES        | 14,942    |
| …                                | …         |
| GALAXY_SOUNDS_SOLAR_FLAMES       | −8,237    |
| SNACKPACK_CHOCOLATE              | −16,417   |
| ROBOT_MOPPING                    | −17,174   |
| PANEL_1X2                        | −18,729   |
| SLEEP_POD_LAMB_WOOL              | −24,199   |
| SNACKPACK_RASPBERRY              | −31,946   |

The bottom-5 losers are products where the basket-residual or pair-skew
overlay pulls quotes in the wrong direction during a one-sided run.
A reasonable follow-up is to clip the skew when |residual| > 2σ rather than
ride it.

## Reproduce

```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/autoresearch/12_final_strategy/strategy.py \
    5-2 5-3 5-4 \
    --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
