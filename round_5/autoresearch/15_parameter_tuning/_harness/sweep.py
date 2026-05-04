"""Parallel sweep utility built on top of harness.eval_config."""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Callable, Iterable, Optional

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .harness import eval_config, EvalResult


def _row_from_result(cfg_id: int, params: dict, res: EvalResult, extras: Optional[dict] = None) -> dict:
    row = {
        "cfg_id": cfg_id,
        **{f"p_{k}": v for k, v in params.items()},
        "fold_mean": res.fold_mean,
        "fold_median": res.fold_median,
        "fold_min": res.fold_min,
        "fold_max": res.fold_max,
        "fold_pos": res.fold_positive_count,
        "fold_pnls": res.fold_pnls,
        "total_3day": res.total_pnl_3day,
        "sharpe": res.sharpe_3day,
        "max_dd": res.max_dd_3day,
        "boot_q05": res.bootstrap_q05,
        "boot_q50": res.bootstrap_q50,
        "boot_q95": res.bootstrap_q95,
        "cache_key": res.cache_key,
    }
    if extras:
        row.update(extras)
    return row


def _eval_one(cfg_id: int, params: dict, kwargs: dict, extras: Optional[dict] = None) -> dict:
    t0 = time.time()
    try:
        res = eval_config(params=params, **kwargs)
        row = _row_from_result(cfg_id, params, res, extras)
        row["elapsed_s"] = time.time() - t0
        row["error"] = ""
        return row
    except Exception as e:
        return {
            "cfg_id": cfg_id,
            **{f"p_{k}": v for k, v in params.items()},
            "elapsed_s": time.time() - t0,
            "error": f"{type(e).__name__}: {e}\n{traceback.format_exc()[-500:]}",
        }


def parallel_sweep(
    configs: list[dict],
    out_path: Path,
    *,
    n_jobs: int = 6,
    eval_kwargs: Optional[dict] = None,
    progress_every: int = 5,
    extras_fn: Optional[Callable[[int, dict], dict]] = None,
) -> pd.DataFrame:
    """Run eval_config on each params dict in `configs`, in parallel.

    Returns DataFrame and also writes to `out_path` (CSV).
    """
    eval_kwargs = eval_kwargs or {}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[sweep] {len(configs)} configs, n_jobs={n_jobs}")
    t0 = time.time()
    rows = Parallel(n_jobs=n_jobs, backend="loky", verbose=0)(
        delayed(_eval_one)(
            i, p, eval_kwargs,
            extras_fn(i, p) if extras_fn else None,
        )
        for i, p in enumerate(configs)
    )
    elapsed = time.time() - t0

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"[sweep] done in {elapsed:.1f}s ({elapsed/max(len(configs),1):.1f}s/config)")
    print(f"[sweep] wrote {out_path} ({len(df)} rows)")
    return df
