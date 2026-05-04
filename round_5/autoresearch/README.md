# ROUND_5 Autoresearch

Discover and exploit the structural and statistical patterns in the Round 5 product set across days 2, 3, 4. Each numbered subfolder is a stage of the research pipeline — inventory → EDA → microstructure → trade flow → statistical pattern discovery → cross-product → cross-group → hidden patterns → signal construction → per-product strategy design → backtesting → findings → final strategy. Outputs of each stage are committed back into the corresponding folder so the chain stays auditable.

## Folder map

| Path | Purpose |
|------|---------|
| `00_data_inventory/` | File listing, schema check, sanity asserts on the raw CSVs |
| `01_eda/` | Descriptive stats, distributions — split by `per_product`, `per_group`, `global` |
| `02_microstructure/` | Order-book depth, spread, queue dynamics, tick autocorrelation |
| `03_trade_flow/` | Counterparty/buyer/seller analysis, aggressor inference, trade-imbalance signals |
| `04_statistical_patterns/` | Stationarity, mean reversion, regime, vol clustering, distribution checks |
| `05_cross_product/` | Within-group pair / basket relationships (cointegration, lead-lag) |
| `06_global_cross_group/` | Across-group relationships (e.g. options vs underlying, currency baskets) |
| `07_hidden_patterns/` | Anything not naturally captured by the above — calendar, intraday seasonality, hidden levels |
| `08_signals/` | Distilled trading signals: feature → expected edge → IC, half-life |
| `09_strategy_design/per_product/` | One markdown + python file per asset documenting the chosen strategy |
| `10_backtesting/` | Backtest harness invocations + per-config result JSONs in `results/` |
| `11_findings/` | Headline write-ups: `findings.md`, `per_group_findings.md`, `exploitable_patterns.md` |
| `12_final_strategy/` | Submitted algorithm (`strategy.py`) + expected PnL breakdown (`pnl_estimates.md`) |
| `notebooks/` | Exploratory `.ipynb`s — promoted findings get migrated to numbered folders |
| `plots/` | Saved figures (PNG/SVG) referenced from markdown |
| `logs/progress.md` | Append-only timeline of what's been investigated, decided, dropped |
| `data_views/` | Cached/derived dataframes (parquet) — built lazily by `utils/data_loader.py` |
| `utils/` | Shared helpers: data loading, plotting, statistics, backtester skeleton |

The numeric prefixes are chronological; `08_signals` and onward depend on the upstream stages being filled in. `notebooks/` and `plots/` are cross-cutting and don't follow the numbering.

## Backtesting

We do **not** roll our own matching engine. All backtests go through the upstream
[`prosperity4btest`](https://github.com/nabayansaha/imc-prosperity-4-backtester) CLI
(PyPI: `prosperity4btest`).

- The CLI is already available in this repo's venv at `imcp/bin/prosperity4btest`. If
  you ever lose it, reinstall with:

  ```
  pip install -U prosperity4btest --break-system-packages
  ```

- **Round-5 position limits = 10 per product** for all 50 products. The list and
  helper `LIMIT_FLAGS` (one `--limit=PRODUCT:10` per product) live in
  [`utils/round5_products.py`](utils/round5_products.py). Always pass these flags
  when invoking the CLI — the backtester defaults to higher limits otherwise.

- **Round-5 data**: bundled inside `prosperity4bt/resources/` once the upstream
  package has been updated for R5. Until then, pass `--data <path>` explicitly
  (e.g. `--data ROUND_5/Data`).

- The thin Python wrapper [`utils/backtester.py`](utils/backtester.py) exposes
  `run_backtest(algo_path, days, data_dir=None, ...)`. It builds the full CLI
  invocation (with `--merge-pnl`, `--no-progress`, all 50 limit flags, optional
  `--data <dir>`, `--out <path>`), captures stdout, parses the per-product PnL
  table, and writes both the raw log and a tidy CSV under
  `10_backtesting/results/<run_name>.{log,csv}`.

- Walk-forward day specs follow the upstream convention: `"5-2"`, `"5-3"`,
  `"5-4"` for individual days, or just `"5"` for all days in the round.

Example:

```python
from utils.backtester import run_backtest

result = run_backtest(
    algo_path="12_final_strategy/strategy.py",
    days=["5-2", "5-3", "5-4"],
    data_dir="ROUND_5/Data",
)
print(result.total_pnl, result.per_product)
```
