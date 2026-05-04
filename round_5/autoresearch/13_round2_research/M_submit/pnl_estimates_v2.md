# PnL Estimates v2 — Round 5

## Per-day backtest (training set, `--match-trades worse`)

| Day  | v1 PnL  | v2 PnL  | Δ          |
|------|---------|---------|------------|
| 5-2  | 124,893 | 168,887 | +43,994    |
| 5-3  | 105,220 | 162,030 | +56,810    |
| 5-4  | 166,636 | 200,608 | +33,972    |
| Σ234 | **396,749** | **531,525** | **+134,776** |

Sharpe (merged): 4.22 → 8.61.
Max drawdown abs: 30,772 → 26,286.
Max drawdown %: 26.9 → 5.0.
Match-mode band (worse vs all): 0 — fully passive.

## Day-5 forecast band

| Scenario | Per-day PnL | Notes                                                  |
|----------|-------------|--------------------------------------------------------|
| Low      | ≈ 162,000   | matches v2's worst training day (5-3)                   |
| Base     | ≈ 177,000   | mean of training days                                   |
| High     | ≈ 201,000   | matches v2's best training day (5-4)                    |

## Robustness

| Test                                  | v2 result            |
|---------------------------------------|----------------------|
| Walk-forward fold A (test d3)         | 162,030               |
| Walk-forward fold B (test d4)         | 200,608               |
| Day-removal (train d2 only, test d3+d4) | 362,638              |
| Match-mode worse vs all               | identical             |
| Limit=10 (prescribed)                 | 531,525               |
| Limit=8 stress                        | 82,485 (strategy is wired for limit=10; 30K rejected orders) |

## Reproduce

```bash
imcp/bin/prosperity4btest cli \
    ROUND_5/autoresearch/13_round2_research/M_submit/strategy_v2.py \
    5-2 5-3 5-4 \
    --merge-pnl --match-trades worse --no-progress \
    --data ROUND_5/autoresearch/10_backtesting/data \
    $(cat ROUND_5/autoresearch/utils/limit_flags.txt)
```
