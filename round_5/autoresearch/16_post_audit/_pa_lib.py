"""Shared utilities for the post-audit alpha extraction.

Wraps the audit's _audit_lib runner so that we can run any algo file (or in-memory
text) and receive parsed per-day per-product PnL with composed 5 folds.

5-fold protocol (identical to audit/_audit_lib.py):
  F1 = test on day 3, F2 = test on day 4, F3 = test on day 3,
  F4 = test on day 2, F5 = test on day 3.
  fold_min = min over the 5 fold test PnLs.

Conventions
- match_mode default is "worse" (mission rule for headline).
- Per-fold PnL is the *test-day* total PnL (per-day stateless backtest is
  sufficient because the algo is stateless across days under merge_pnl).
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ── paths ──────────────────────────────────────────────────────────────────
_PA_DIR = Path(__file__).resolve().parent
_AUTORES = _PA_DIR.parent
_REPO_ROOT = _AUTORES.parent.parent
_LIMIT_FLAGS_FILE = _AUTORES / "utils" / "limit_flags.txt"
_CLI = _REPO_ROOT / "imcp" / "bin" / "prosperity4btest"
_LOGS_DIR = _PA_DIR / "data_views" / "backtest_logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

with _LIMIT_FLAGS_FILE.open() as f:
    LIMIT_FLAGS = f.read().strip().split()

# 5-fold protocol identical to parameter_tuning/audit/_audit_lib.py
FOLDS = [
    {"name": "F1", "train": [2],     "test": 3},
    {"name": "F2", "train": [2, 3],  "test": 4},
    {"name": "F3", "train": [4],     "test": 3},
    {"name": "F4", "train": [3, 4],  "test": 2},
    {"name": "F5", "train": [2, 4],  "test": 3},
]
DAYS = (2, 3, 4)


# ── parsing ────────────────────────────────────────────────────────────────
_DAY_HEADER_RE = re.compile(r"^Backtesting .*\.py on round (\d+) day (\d+)\s*$", re.MULTILINE)
_PNL_RE = re.compile(r"^([A-Z][A-Z0-9_]+):\s*([\-\d,]+)\s*$", re.MULTILINE)
_DAY_PNL_RE = re.compile(r"^Round\s+(\d+)\s+day\s+(\d+):\s*([\-\d,]+)\s*$", re.MULTILINE)
_TOTAL_RE = re.compile(r"^Total profit:\s*([\-\d,]+)\s*$", re.MULTILINE)
_SHARPE_RE = re.compile(r"sharpe_ratio:\s*([\-\d.eE+nan/]+)")
_DD_RE = re.compile(r"max_drawdown_abs:\s*([\-\d,]+)")


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


@dataclass
class MergedResult:
    per_day_pnl: dict                                      # day -> total
    per_day_per_product: dict                              # day -> {product -> pnl}
    sharpe_3day: Optional[float]
    max_dd_3day: Optional[int]
    total_3day: int
    elapsed_s: float
    fold_pnls: dict = field(default_factory=dict)
    fold_min: int = 0
    fold_median: float = 0.0
    fold_mean: float = 0.0

    def __post_init__(self):
        for fk in FOLDS:
            self.fold_pnls[fk["name"]] = self.per_day_pnl.get(fk["test"], 0)
        vals = list(self.fold_pnls.values())
        if vals:
            sv = sorted(vals)
            self.fold_min = sv[0]
            n = len(vals)
            self.fold_median = sv[n // 2] if n % 2 == 1 else (sv[n // 2 - 1] + sv[n // 2]) / 2.0
            self.fold_mean = sum(vals) / n

    def per_product_total_3day(self) -> dict:
        out: dict = {}
        for d, pmap in self.per_day_per_product.items():
            for p, v in pmap.items():
                out[p] = out.get(p, 0) + v
        return out


def parse_merged_stdout(stdout: str) -> MergedResult:
    headers = list(_DAY_HEADER_RE.finditer(stdout))
    per_day_per_product: dict = {}
    for i, m in enumerate(headers):
        day = int(m.group(2))
        start = m.end()
        end = headers[i + 1].start() if (i + 1) < len(headers) else stdout.find("Profit summary", start)
        if end < 0:
            end = len(stdout)
        block = stdout[start:end]
        prod_map: dict = {}
        for pm in _PNL_RE.finditer(block):
            name, val = pm.group(1), pm.group(2)
            if name in ("Total", "Round"):
                continue
            try:
                prod_map[name] = _to_int(val)
            except ValueError:
                continue
        per_day_per_product[day] = prod_map

    per_day_pnl: dict = {}
    for m in _DAY_PNL_RE.finditer(stdout):
        per_day_pnl[int(m.group(2))] = _to_int(m.group(3))

    total_m = list(_TOTAL_RE.finditer(stdout))
    total_3day = _to_int(total_m[-1].group(1)) if total_m else 0

    sh_m = _SHARPE_RE.search(stdout)
    sharpe = None
    if sh_m and sh_m.group(1) not in ("n/a", "nan"):
        try:
            sharpe = float(sh_m.group(1))
        except ValueError:
            sharpe = None

    dd_m = _DD_RE.search(stdout)
    dd = _to_int(dd_m.group(1)) if dd_m else None

    return MergedResult(
        per_day_pnl=per_day_pnl,
        per_day_per_product=per_day_per_product,
        sharpe_3day=sharpe,
        max_dd_3day=dd,
        total_3day=total_3day,
        elapsed_s=0.0,
    )


# ── runner ─────────────────────────────────────────────────────────────────
def run_algo(
    algo_path,
    *,
    days: tuple = DAYS,
    match_mode: str = "worse",
    timeout: float = 600.0,
    extra_flags: list = None,
    save_log_as: str = None,
) -> MergedResult:
    """Run a single 3-day merged backtest, return parsed result."""
    algo_path = Path(algo_path).resolve()
    day_specs = [f"5-{d}" for d in days]
    cmd = [
        str(_CLI), "cli", str(algo_path), *day_specs,
        "--merge-pnl", "--no-progress",
        "--match-trades", match_mode,
        "--no-out",
        *LIMIT_FLAGS,
    ]
    if extra_flags:
        cmd.extend(extra_flags)
    t0 = time.time()
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=str(_REPO_ROOT),
    )
    elapsed = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError(
            f"backtest failed (rc={proc.returncode}) for {algo_path}: "
            f"{proc.stderr[-500:]}"
        )
    res = parse_merged_stdout(proc.stdout)
    res.elapsed_s = elapsed
    if save_log_as:
        log_path = _LOGS_DIR / f"{save_log_as}.log"
        log_path.write_text(proc.stdout)
    return res


def run_algo_text(
    algo_src: str,
    *,
    days: tuple = DAYS,
    match_mode: str = "worse",
    timeout: float = 600.0,
    extra_flags: list = None,
    save_log_as: str = None,
) -> MergedResult:
    """Like run_algo but for an in-memory algo source string. Writes to a temp
    file in post_audit/ so that imports of `datamodel` resolve correctly."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=str(_PA_DIR)
    ) as tf:
        tf.write(algo_src)
        tmp_path = Path(tf.name)
    try:
        return run_algo(tmp_path, days=days, match_mode=match_mode,
                        timeout=timeout, extra_flags=extra_flags,
                        save_log_as=save_log_as)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


# ── parallel runner ────────────────────────────────────────────────────────
def run_many_text(specs, *, n_workers: int = 4, days: tuple = DAYS,
                  match_mode: str = "worse"):
    """Run many in-memory algo sources in parallel.

    specs: iterable of (label, algo_src). Returns dict {label: MergedResult or
    Exception}.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=n_workers) as exe:
        futs = {exe.submit(run_algo_text, src, days=days, match_mode=match_mode,
                           save_log_as=f"par_{label}"): label
                for label, src in specs}
        for fut in as_completed(futs):
            label = futs[fut]
            try:
                results[label] = fut.result()
            except Exception as e:
                results[label] = e
    return results


# ── ablation gate ──────────────────────────────────────────────────────────
def baseline_summary(res: MergedResult) -> dict:
    return {
        "fold_pnls": dict(res.fold_pnls),
        "fold_min": res.fold_min,
        "fold_median": res.fold_median,
        "fold_mean": res.fold_mean,
        "total_3day": res.total_3day,
        "sharpe_3day": res.sharpe_3day,
        "max_dd_3day": res.max_dd_3day,
    }


def ablation_gate(candidate: MergedResult, baseline: MergedResult,
                  K: int = 1000) -> dict:
    """Strict 5-gate ablation rule (gates a-e from the mission).

    (a) Mean fold PnL ≥ baseline + 2K
    (b) Median fold PnL ≥ baseline median
    (c) ALL 5 folds positive Δ vs baseline
    (d) Bootstrap 5%-quantile PnL ≥ baseline 5%-quantile (skipped, not enough
        independent fold samples — fold_min substitutes per mission)
    (e) MaxDD ≤ 1.20× baseline maxDD
    """
    cand_vals = [candidate.fold_pnls[f["name"]] for f in FOLDS]
    base_vals = [baseline.fold_pnls[f["name"]] for f in FOLDS]
    deltas = [c - b for c, b in zip(cand_vals, base_vals)]

    a = candidate.fold_mean >= baseline.fold_mean + 2 * K
    b = candidate.fold_median >= baseline.fold_median
    c = all(d > 0 for d in deltas)
    # Gate (d): bootstrap 5%-quantile of fold_min - approximate with min itself
    d = candidate.fold_min >= baseline.fold_min
    e = (
        candidate.max_dd_3day is None
        or baseline.max_dd_3day is None
        or candidate.max_dd_3day <= 1.20 * baseline.max_dd_3day
    )
    passed = bool(a and b and c and d and e)
    return {
        "gate_a_mean_2K": bool(a),
        "gate_b_median": bool(b),
        "gate_c_all_folds": bool(c),
        "gate_d_q05": bool(d),
        "gate_e_maxdd": bool(e),
        "passed": passed,
        "deltas": deltas,
        "delta_mean": candidate.fold_mean - baseline.fold_mean,
        "delta_median": candidate.fold_median - baseline.fold_median,
        "delta_fold_min": candidate.fold_min - baseline.fold_min,
        "max_dd_ratio": (candidate.max_dd_3day / baseline.max_dd_3day)
                        if (candidate.max_dd_3day and baseline.max_dd_3day) else None,
    }


def write_csv(rows: list, path) -> None:
    if not rows:
        return
    # union of all keys across all rows, preserving first-seen order
    keys: list = []
    seen: set = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def progress_log(msg: str) -> None:
    """Append a line to post_audit/progress.md with a timestamp."""
    p = _PA_DIR / "progress.md"
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with p.open("a") as f:
        f.write(f"- {ts} — {msg}\n")
