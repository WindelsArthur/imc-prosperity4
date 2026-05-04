"""Multi-fold evaluation harness for algo1 hyperparameter tuning.

Critical finding (verified empirically in Phase 0): the current algo1 is
stateless across days under prosperity4btest — running day 3 standalone gives
the IDENTICAL per-day PnL as running 5-2 5-3 (merged). This means the "fold"
construct from the mission spec degenerates: each fold's test-PnL equals the
test day's standalone PnL regardless of train days.

Implication: we run each day ONCE, cache it, then compose folds from the cache.
3 backtests per config instead of 12. ~4x speedup.

The 5-fold protocol is honored literally (the fold/test mapping is preserved
for reporting), but per-fold PnL is computed from cached per-day PnL.

Public API
    render_algo(params, pairs=None, prod_cap=None) -> str
    run_day(algo_src, day, match_mode='worse', limit=10) -> DayResult
    eval_config(params, pairs=None, prod_cap=None, match_mode='worse',
                limit=10, cache_key=None) -> EvalResult
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Iterable

import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────
_HARNESS_DIR = Path(__file__).resolve().parent
_PT_DIR = _HARNESS_DIR.parent                                       # parameter_tuning/
_AUTORES = _PT_DIR.parent                                           # ROUND_5/autoresearch/
_REPO_ROOT = _AUTORES.parent.parent                                 # repo root
_TEMPLATE = _PT_DIR / "algo1.py"
_LIMIT_FLAGS_FILE = _AUTORES / "utils" / "limit_flags.txt"
_CLI = _REPO_ROOT / "imcp" / "bin" / "prosperity4btest"
_CACHE_DIR = _PT_DIR / "_harness" / ".day_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

with _LIMIT_FLAGS_FILE.open() as f:
    _LIMIT_FLAGS_RAW = f.read().strip().split()


def _limit_flags(limit: int) -> list[str]:
    if limit == 10:
        return _LIMIT_FLAGS_RAW
    return [re.sub(r":\d+$", f":{limit}", flag) for flag in _LIMIT_FLAGS_RAW]


# ── parsing ────────────────────────────────────────────────────────────────
_PNL_RE = re.compile(r"^([A-Z][A-Z0-9_]+):\s*([\-\d,]+)\s*$", re.MULTILINE)
_DAY_PNL_RE = re.compile(r"^Round\s+(\d+)\s+day\s+(\d+):\s*([\-\d,]+)\s*$", re.MULTILINE)
_TOTAL_RE = re.compile(r"^Total profit:\s*([\-\d,]+)\s*$", re.MULTILINE)
_DD_RE = re.compile(r"max_drawdown_abs:\s*([\-\d,]+)")
_SHARPE_RE = re.compile(r"sharpe_ratio:\s*([\-\d.eE+nan/]+)")


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


def _parse_merged_summary(stdout: str) -> dict:
    """Parse the 3-day merged stdout. Returns per-day pnl dict, per-product
    summed across days, final 3-day sharpe + maxDD."""
    per_day_pnl: dict[int, int] = {}
    for m in _DAY_PNL_RE.finditer(stdout):
        day = int(m.group(2))
        pnl = _to_int(m.group(3))
        per_day_pnl[day] = pnl
    # per-product: prosperity4btest prints per-product PnL block per day.
    # Sum all matches → 3-day per-product totals.
    per_product_3day: dict[str, int] = {}
    for m in _PNL_RE.finditer(stdout):
        name, val = m.group(1), m.group(2)
        if name == "Total":
            continue
        try:
            per_product_3day[name] = per_product_3day.get(name, 0) + _to_int(val)
        except ValueError:
            continue
    dd_m = _DD_RE.search(stdout)
    dd = _to_int(dd_m.group(1)) if dd_m else None
    sh_m = _SHARPE_RE.search(stdout)
    sh = None
    if sh_m and sh_m.group(1) not in ("n/a", "nan"):
        try:
            sh = float(sh_m.group(1))
        except ValueError:
            pass
    total_m = list(_TOTAL_RE.finditer(stdout))
    total_3day = _to_int(total_m[-1].group(1)) if total_m else None
    return {"per_day_pnl": per_day_pnl, "per_product_3day": per_product_3day,
            "max_drawdown_abs_3day": dd, "sharpe_3day": sh, "total_3day": total_3day}


def _parse_activities_pnl_per_day(log_path: Path) -> dict[int, np.ndarray]:
    """Extract per-day per-tick PnL INCREMENT series. The activities log column
    `profit_and_loss` is cumulative MTM PnL; we diff it to get per-tick deltas."""
    if not log_path.exists():
        return {}
    try:
        with log_path.open() as f:
            text = f.read()
    except OSError:
        return {}
    idx = text.find("Activities log:")
    if idx < 0:
        return {}
    rest = text[idx + len("Activities log:"):]
    end_idx = rest.find("Trade History:")
    if end_idx >= 0:
        rest = rest[:end_idx]
    lines = [ln for ln in rest.splitlines() if ln.strip()]
    if len(lines) < 2:
        return {}
    header = lines[0].split(";")
    try:
        day_col = header.index("day")
        ts_col = header.index("timestamp")
        pnl_col = header.index("profit_and_loss")
    except ValueError:
        return {}
    # accumulate cumulative pnl by (day, timestamp)
    by_day_ts: dict[int, dict[int, float]] = {}
    for ln in lines[1:]:
        parts = ln.split(";")
        if len(parts) <= max(day_col, ts_col, pnl_col):
            continue
        try:
            d = int(parts[day_col])
            t = int(parts[ts_col])
            p = float(parts[pnl_col])
        except ValueError:
            continue
        by_day_ts.setdefault(d, {})
        by_day_ts[d][t] = by_day_ts[d].get(t, 0.0) + p
    out: dict[int, np.ndarray] = {}
    for d, ts_map in by_day_ts.items():
        ts_sorted = sorted(ts_map)
        cumulative = np.array([ts_map[t] for t in ts_sorted], dtype=np.float64)
        # diff → per-tick increment; first tick increment is the first cumulative value
        if len(cumulative) == 0:
            continue
        increments = np.empty_like(cumulative)
        increments[0] = cumulative[0]
        increments[1:] = np.diff(cumulative)
        out[d] = increments
    return out


# ── algo template rendering ────────────────────────────────────────────────
_TEMPLATE_TEXT = _TEMPLATE.read_text()

_TUNABLE_KEYS = (
    "PEBBLES_SKEW_DIVISOR", "SNACKPACK_SKEW_DIVISOR",
    "PEBBLES_SKEW_CLIP", "SNACKPACK_SKEW_CLIP",
    "PEBBLES_BIG_SKEW", "SNACKPACK_BIG_SKEW",
    "PAIR_TILT_DIVISOR", "PAIR_TILT_CLIP",
    "INV_SKEW_BETA", "QUOTE_BASE_SIZE_CAP", "QUOTE_AGGRESSIVE_SIZE",
)


def render_algo(
    params: Optional[dict] = None,
    *,
    pairs: Optional[list] = None,           # full ALL_PAIRS list; None = template default
    prod_cap: Optional[dict] = None,        # None = template default
    fair_quote_gate: Optional[float] = None,  # None = template default (0.25)
    use_lagged_signal: bool = False,        # True → use mids[t-1] (latency stress)
) -> str:
    """Return modified algo source with parameters injected."""
    src = _TEMPLATE_TEXT
    p = params or {}

    for key in _TUNABLE_KEYS:
        if key in p:
            v = p[key]
            v_str = repr(float(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else repr(v)
            # only replace integer-valued caps if they look like ints in source
            if key in ("QUOTE_BASE_SIZE_CAP", "QUOTE_AGGRESSIVE_SIZE"):
                v_str = str(int(v))
            src = re.sub(
                rf"^{key}\s*=\s*[\d.\-]+",
                f"{key} = {v_str}",
                src, count=1, flags=re.MULTILINE,
            )

    if prod_cap is not None:
        cap_lines = []
        for k, v in prod_cap.items():
            cap_lines.append(f'    "{k}": {int(v)},')
        cap_block = "PROD_CAP = {\n" + "\n".join(cap_lines) + "\n}"
        src = re.sub(
            r"PROD_CAP\s*=\s*\{[^}]*\}",
            lambda _m: cap_block,
            src, count=1, flags=re.DOTALL,
        )

    if pairs is not None:
        # Replace COINT_PAIRS list with empty, CROSS_GROUP_PAIRS with the full pairs list
        # Cleanest: leave COINT_PAIRS but override ALL_PAIRS = pairs.
        pair_lines = []
        for tup in pairs:
            a, b, slope, intercept = tup[:4]
            pair_lines.append(f'    ("{a}", "{b}", {slope}, {intercept}),')
        pairs_block = "ALL_PAIRS = [\n" + "\n".join(pair_lines) + "\n]"
        src = re.sub(
            r"ALL_PAIRS\s*=\s*COINT_PAIRS\s*\+\s*CROSS_GROUP_PAIRS",
            pairs_block,
            src, count=1,
        )

    if fair_quote_gate is not None:
        # Replace the 0.25 in the make() function
        g = float(fair_quote_gate)
        src = src.replace(
            "if size_buy  and fair > bid_px - 0.25: orders.append(Order(prod, bid_px, size_buy))",
            f"if size_buy  and fair > bid_px - {g}: orders.append(Order(prod, bid_px, size_buy))",
        )
        src = src.replace(
            "if size_sell and fair < ask_px + 0.25: orders.append(Order(prod, ask_px, -size_sell))",
            f"if size_sell and fair < ask_px + {g}: orders.append(Order(prod, ask_px, -size_sell))",
        )

    if use_lagged_signal:
        # Inject a lag wrapper on _compute_mids: keep prev_mids in module-level dict.
        # Approach: stash mids in a module global and return prev tick's mids.
        lag_inject = (
            "_PREV_MIDS: Dict[str, float] = {}\n\n"
            "def _compute_mids_lagged(state: TradingState) -> Dict[str, float]:\n"
            "    global _PREV_MIDS\n"
            "    cur = {}\n"
            "    for p in ALL_PRODUCTS:\n"
            "        m = _mid(state.order_depths.get(p))\n"
            "        if m is not None:\n"
            "            cur[p] = m\n"
            "    out = dict(_PREV_MIDS) if _PREV_MIDS else dict(cur)\n"
            "    _PREV_MIDS = cur\n"
            "    return out\n"
        )
        src = src.replace(
            "def _compute_mids(state: TradingState) -> Dict[str, float]:",
            lag_inject + "\ndef _compute_mids(state: TradingState) -> Dict[str, float]:",
        )
        src = src.replace(
            "mids = _compute_mids(state)",
            "mids = _compute_mids_lagged(state)",
        )

    return src


# ── result types ───────────────────────────────────────────────────────────
@dataclass
class DayResult:
    day: int
    total_pnl: int
    per_tick_pnl: Optional[np.ndarray]      # per-tick INCREMENT PnL (already diffed)

    def to_dict_jsonable(self) -> dict:
        return {
            "day": self.day,
            "total_pnl": self.total_pnl,
        }


@dataclass
class EvalResult:
    days: dict[int, DayResult]                  # day → result
    folds: list[dict]                           # 5 folds with test PnL
    fold_pnls: list[int]                        # length 5
    fold_positive_count: int
    fold_min: int
    fold_max: int
    fold_mean: float
    fold_median: float
    bootstrap_q05: Optional[float]
    bootstrap_q50: Optional[float]
    bootstrap_q95: Optional[float]
    total_pnl_3day: int                         # sum of days 2+3+4
    sharpe_3day: Optional[float]
    max_dd_3day: Optional[int]
    per_product_3day: dict[str, int]            # summed across days
    cache_key: str

    def to_dict_jsonable(self) -> dict:
        return {
            "days": {str(k): v.to_dict_jsonable() for k, v in self.days.items()},
            "folds": self.folds,
            "fold_pnls": self.fold_pnls,
            "fold_positive_count": self.fold_positive_count,
            "fold_min": self.fold_min,
            "fold_max": self.fold_max,
            "fold_mean": self.fold_mean,
            "fold_median": self.fold_median,
            "bootstrap_q05": self.bootstrap_q05,
            "bootstrap_q50": self.bootstrap_q50,
            "bootstrap_q95": self.bootstrap_q95,
            "total_pnl_3day": self.total_pnl_3day,
            "sharpe_3day": self.sharpe_3day,
            "max_dd_3day": self.max_dd_3day,
            "per_product_3day": self.per_product_3day,
            "cache_key": self.cache_key,
        }


# ── 5-fold protocol (test days fixed; train days informational only since
# algo is stateless across days) ───────────────────────────────────────────
_FOLDS = [
    {"name": "F1", "train": [2],   "test": 3},
    {"name": "F2", "train": [2, 3], "test": 4},
    {"name": "F3", "train": [4],   "test": 3},
    {"name": "F4", "train": [3, 4], "test": 2},
    {"name": "F5", "train": [2, 4], "test": 3},
]


# ── runner ─────────────────────────────────────────────────────────────────
@dataclass
class MergedRunResult:
    per_day_pnl: dict[int, int]
    per_product_3day: dict[str, int]
    sharpe_3day: Optional[float]
    max_dd_3day: Optional[int]
    total_3day: int
    per_day_tick_pnl: dict[int, np.ndarray]   # per-tick INCREMENTS
    elapsed_s: float


def run_merged(
    algo_src: str,
    days: Iterable[int] = (2, 3, 4),
    *,
    match_mode: str = "worse",
    limit: int = 10,
    capture_ticks: bool = True,
    timeout: float = 600.0,
) -> MergedRunResult:
    """Run a single 3-day merged backtest and parse all needed metrics."""
    days_list = list(days)
    with tempfile.TemporaryDirectory(prefix="ptune_") as td:
        td_p = Path(td)
        algo_path = td_p / "algo.py"
        algo_path.write_text(algo_src)
        log_path = td_p / "out.log"

        day_specs = [f"5-{d}" for d in days_list]
        cmd = [
            str(_CLI), "cli", str(algo_path), *day_specs,
            "--merge-pnl", "--no-progress",
            "--match-trades", match_mode,
        ]
        if capture_ticks:
            cmd.extend(["--out", str(log_path)])
        else:
            cmd.append("--no-out")
        cmd.extend(_limit_flags(limit))

        t0 = time.time()
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=str(_REPO_ROOT),
        )
        elapsed = time.time() - t0

        if proc.returncode != 0:
            raise RuntimeError(
                f"merged backtest failed (rc={proc.returncode}): "
                f"{proc.stderr[:500]}\nSTDOUT-tail:{proc.stdout[-500:]}"
            )
        summary = _parse_merged_summary(proc.stdout)
        tick_per_day = _parse_activities_pnl_per_day(log_path) if capture_ticks else {}

    return MergedRunResult(
        per_day_pnl=summary["per_day_pnl"],
        per_product_3day=summary["per_product_3day"],
        sharpe_3day=summary["sharpe_3day"],
        max_dd_3day=summary["max_drawdown_abs_3day"],
        total_3day=summary["total_3day"] or 0,
        per_day_tick_pnl=tick_per_day,
        elapsed_s=elapsed,
    )


# ── top-level eval ─────────────────────────────────────────────────────────
def _config_hash(
    params: Optional[dict],
    pairs: Optional[list],
    prod_cap: Optional[dict],
    fair_quote_gate: Optional[float],
    match_mode: str,
    limit: int,
    use_lagged_signal: bool,
) -> str:
    payload = {
        "params": params or {},
        "pairs": pairs,
        "prod_cap": prod_cap,
        "fair_quote_gate": fair_quote_gate,
        "match_mode": match_mode,
        "limit": limit,
        "use_lagged_signal": use_lagged_signal,
    }
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def _block_bootstrap_pnl(
    per_tick_arrays: list[np.ndarray],
    block: int = 100,
    n_resamples: int = 1000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Block bootstrap of total PnL across days. Returns (q05, q50, q95)."""
    if not per_tick_arrays:
        return (float("nan"),) * 3
    series = [a for a in per_tick_arrays if a is not None and len(a) > 0]
    if not series:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    totals = np.empty(n_resamples, dtype=np.float64)
    for r in range(n_resamples):
        boot = 0.0
        for arr in series:
            n = len(arr)
            if n == 0:
                continue
            if n <= block:
                # too short for blocks; just resample with replacement
                boot += float(arr[rng.integers(0, n, size=n)].sum())
                continue
            n_blocks = (n + block - 1) // block
            starts = rng.integers(0, n - block + 1, size=n_blocks)
            chunks = [arr[s:s + block] for s in starts]
            samp = np.concatenate(chunks)[:n]
            boot += float(samp.sum())
        totals[r] = boot
    return (
        float(np.quantile(totals, 0.05)),
        float(np.quantile(totals, 0.50)),
        float(np.quantile(totals, 0.95)),
    )


def eval_config(
    params: Optional[dict] = None,
    *,
    pairs: Optional[list] = None,
    prod_cap: Optional[dict] = None,
    fair_quote_gate: Optional[float] = None,
    match_mode: str = "worse",
    limit: int = 10,
    use_lagged_signal: bool = False,
    days: Iterable[int] = (2, 3, 4),
    capture_ticks: bool = True,
    cache: bool = True,
    n_bootstrap: int = 1000,
) -> EvalResult:
    """Run multi-fold eval (one merged 3-day backtest, then compose 5 folds)."""
    days_t = tuple(days)
    chash = _config_hash(params, pairs, prod_cap, fair_quote_gate,
                         match_mode, limit, use_lagged_signal)
    cache_path = _CACHE_DIR / f"{chash}_l{limit}_m{match_mode}.json"

    merged: Optional[MergedRunResult] = None
    if cache and cache_path.exists():
        try:
            d = json.loads(cache_path.read_text())
            tick_blob_path = cache_path.with_suffix(".npz")
            ticks_blob = np.load(tick_blob_path) if tick_blob_path.exists() else None
            tick_per_day = {}
            if ticks_blob is not None:
                for key in ticks_blob.files:
                    if key.startswith("d"):
                        tick_per_day[int(key[1:])] = ticks_blob[key]
            merged = MergedRunResult(
                per_day_pnl={int(k): v for k, v in d["per_day_pnl"].items()},
                per_product_3day=d["per_product_3day"],
                sharpe_3day=d.get("sharpe_3day"),
                max_dd_3day=d.get("max_dd_3day"),
                total_3day=d["total_3day"],
                per_day_tick_pnl=tick_per_day,
                elapsed_s=d.get("elapsed_s", 0.0),
            )
        except Exception:
            merged = None

    if merged is None:
        algo_src = render_algo(params, pairs=pairs, prod_cap=prod_cap,
                               fair_quote_gate=fair_quote_gate,
                               use_lagged_signal=use_lagged_signal)
        merged = run_merged(
            algo_src, days=days_t, match_mode=match_mode, limit=limit,
            capture_ticks=capture_ticks,
        )
        if cache:
            try:
                cache_path.write_text(json.dumps({
                    "per_day_pnl": merged.per_day_pnl,
                    "per_product_3day": merged.per_product_3day,
                    "sharpe_3day": merged.sharpe_3day,
                    "max_dd_3day": merged.max_dd_3day,
                    "total_3day": merged.total_3day,
                    "elapsed_s": merged.elapsed_s,
                    "params": params, "prod_cap": prod_cap,
                    "fair_quote_gate": fair_quote_gate,
                    "match_mode": match_mode, "limit": limit,
                    "use_lagged_signal": use_lagged_signal,
                    "n_pairs": (len(pairs) if pairs else None),
                }, default=str))
                if merged.per_day_tick_pnl:
                    np.savez_compressed(
                        cache_path.with_suffix(".npz"),
                        **{f"d{d}": v for d, v in merged.per_day_tick_pnl.items()},
                    )
            except Exception as e:
                print(f"[harness] cache write failed: {e}")

    # build day_results
    day_results = {
        d: DayResult(
            day=d,
            total_pnl=merged.per_day_pnl.get(d, 0),
            per_tick_pnl=merged.per_day_tick_pnl.get(d),
        )
        for d in days_t
    }

    # compose folds
    folds_out = []
    fold_pnls = []
    for fk in _FOLDS:
        test_d = fk["test"]
        pnl = day_results[test_d].total_pnl
        folds_out.append({
            "name": fk["name"],
            "train": fk["train"],
            "test": test_d,
            "test_pnl": pnl,
        })
        fold_pnls.append(pnl)

    fp_arr = np.array(fold_pnls, dtype=np.float64)
    fold_pos = int((fp_arr > 0).sum())

    # bootstrap on per-tick INCREMENT series
    per_tick_list = [v for v in merged.per_day_tick_pnl.values() if v is not None and len(v) > 0]
    if per_tick_list and capture_ticks and n_bootstrap > 0:
        q05, q50, q95 = _block_bootstrap_pnl(per_tick_list, block=100, n_resamples=n_bootstrap)
    else:
        q05 = q50 = q95 = float("nan")

    return EvalResult(
        days=day_results,
        folds=folds_out,
        fold_pnls=fold_pnls,
        fold_positive_count=fold_pos,
        fold_min=int(fp_arr.min()),
        fold_max=int(fp_arr.max()),
        fold_mean=float(fp_arr.mean()),
        fold_median=float(np.median(fp_arr)),
        bootstrap_q05=q05,
        bootstrap_q50=q50,
        bootstrap_q95=q95,
        total_pnl_3day=int(merged.total_3day),
        sharpe_3day=merged.sharpe_3day,
        max_dd_3day=merged.max_dd_3day,
        per_product_3day=merged.per_product_3day,
        cache_key=chash,
    )


# ── ablation gate ──────────────────────────────────────────────────────────
def passes_gate(
    candidate: EvalResult,
    baseline: EvalResult,
    *,
    pnl_uplift_min: float = 2000.0,
    require_all_folds_positive: bool = True,
    bootstrap_q05_no_worse: bool = True,
    dd_max_factor: float = 1.20,
) -> tuple[bool, dict]:
    """Apply gates (a)-(e) of the ablation gate.

    Returns (pass, details_dict). Plateau gate (f) and stress (g) checked elsewhere.
    """
    details = {}

    # (a) mean walk-forward avg-daily PnL ≥ baseline + 2K
    cand_mean_daily = candidate.fold_mean
    base_mean_daily = baseline.fold_mean
    a = cand_mean_daily >= base_mean_daily + pnl_uplift_min
    details["a_mean_uplift"] = (a, cand_mean_daily - base_mean_daily, pnl_uplift_min)

    # (b) median fold-PnL ≥ baseline median fold-PnL
    b = candidate.fold_median >= baseline.fold_median
    details["b_median"] = (b, candidate.fold_median, baseline.fold_median)

    # (c) strictly positive on every fold
    c = (candidate.fold_min > 0) if require_all_folds_positive else True
    details["c_all_pos"] = (c, candidate.fold_min)

    # (d) bootstrap q05 ≥ baseline q05
    if bootstrap_q05_no_worse and candidate.bootstrap_q05 is not None and baseline.bootstrap_q05 is not None:
        d = candidate.bootstrap_q05 >= baseline.bootstrap_q05
        details["d_q05"] = (d, candidate.bootstrap_q05, baseline.bootstrap_q05)
    else:
        d = True
        details["d_q05"] = (True, candidate.bootstrap_q05, baseline.bootstrap_q05)

    # (e) max DD ≤ 1.2× baseline
    if candidate.max_dd_3day is not None and baseline.max_dd_3day is not None:
        e = candidate.max_dd_3day <= baseline.max_dd_3day * dd_max_factor
        details["e_dd"] = (e, candidate.max_dd_3day, baseline.max_dd_3day * dd_max_factor)
    else:
        e = True
        details["e_dd"] = (True, candidate.max_dd_3day, None)

    return (a and b and c and d and e, details)
