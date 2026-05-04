"""Thin wrapper around the prosperity4btest CLI.

We do not implement matching ourselves — the upstream backtester
(https://github.com/nabayansaha/imc-prosperity-4-backtester, PyPI:
``prosperity4btest``) is the source of truth. This module just builds the
CLI invocation, runs it via subprocess, parses the printed PnL summary, and
saves both the raw log and a tidy CSV under
``ROUND_5/autoresearch/10_backtesting/results/``.

Public API
    run_backtest(algo_path, days, *, data_dir=None, run_name=None,
                 extra_flags=None, executable=None) -> dict
"""
from __future__ import annotations

import csv
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .round5_products import LIMIT_FLAGS

# ── paths ──────────────────────────────────────────────────────────────────

_AUTORES = Path(__file__).resolve().parents[1]                      # ROUND_5/autoresearch/
_REPO_ROOT = Path(__file__).resolve().parents[3]                    # repo root
_RESULTS_DIR = _AUTORES / "10_backtesting" / "results"
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Default CLI: prefer the venv-shipped binary, fall back to PATH.
_DEFAULT_EXEC_CANDIDATES: list[Path | str] = [
    _REPO_ROOT / "imcp" / "bin" / "prosperity4btest",
    "prosperity4btest",
]


def _resolve_executable(executable: Optional[str | Path]) -> str:
    if executable is not None:
        return str(executable)
    for cand in _DEFAULT_EXEC_CANDIDATES:
        if isinstance(cand, Path) and cand.exists():
            return str(cand)
        if isinstance(cand, str):
            # let subprocess search PATH for plain strings
            return cand
    raise FileNotFoundError("prosperity4btest CLI not found; "
                            "install with `pip install -U prosperity4btest --break-system-packages`")


# ── output parsing ─────────────────────────────────────────────────────────

# Each per-product line looks like `PEBBLES_L: 12,345`. Total is `Total profit: 209,924`.
_PNL_RE = re.compile(r"^([A-Z][A-Z0-9_]+):\s*([\-\d,]+)\s*$", re.MULTILINE)
_TOTAL_RE = re.compile(r"^Total profit:\s*([\-\d,]+)\s*$", re.MULTILINE)
_DD_RE = re.compile(r"max_drawdown_abs:\s*([\-\d,]+)")
_CALMAR_RE = re.compile(r"calmar_ratio:\s*([\-\d.eE+]+)")
_SHARPE_RE = re.compile(r"sharpe_ratio:\s*([\-\d.eE+nan/]+)")


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


def _parse_summary(stdout: str) -> dict:
    """Pull per-product PnL plus aggregate risk metrics out of stdout."""
    per_product: dict[str, int] = {}
    for m in _PNL_RE.finditer(stdout):
        name, val = m.group(1), m.group(2)
        if name == "Total":
            continue
        try:
            per_product[name] = _to_int(val)
        except ValueError:
            continue

    total_matches = list(_TOTAL_RE.finditer(stdout))
    total = _to_int(total_matches[-1].group(1)) if total_matches else None

    dd_m = _DD_RE.search(stdout)
    dd = _to_int(dd_m.group(1)) if dd_m else None

    calmar_m = _CALMAR_RE.search(stdout)
    calmar = float(calmar_m.group(1)) if calmar_m else None

    sharpe_m = _SHARPE_RE.search(stdout)
    sharpe_raw = sharpe_m.group(1) if sharpe_m else None
    sharpe: Optional[float] = None
    if sharpe_raw and sharpe_raw not in ("n/a", "nan"):
        try:
            sharpe = float(sharpe_raw)
        except ValueError:
            sharpe = None

    return {
        "per_product": per_product,
        "total_pnl": total,
        "max_drawdown_abs": dd,
        "calmar_ratio": calmar,
        "sharpe_ratio": sharpe,
    }


# ── result type ────────────────────────────────────────────────────────────

@dataclass
class BacktestResult:
    run_name: str
    algo_path: Path
    days: list[str]
    cmd: list[str]
    returncode: int
    elapsed_s: float
    log_path: Path
    csv_path: Path
    per_product: dict[str, int] = field(default_factory=dict)
    total_pnl: Optional[int] = None
    max_drawdown_abs: Optional[int] = None
    calmar_ratio: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    stderr: str = ""

    def to_dict(self) -> dict:
        return {
            "run_name": self.run_name,
            "algo_path": str(self.algo_path),
            "days": self.days,
            "returncode": self.returncode,
            "elapsed_s": self.elapsed_s,
            "log_path": str(self.log_path),
            "csv_path": str(self.csv_path),
            "per_product": self.per_product,
            "total_pnl": self.total_pnl,
            "max_drawdown_abs": self.max_drawdown_abs,
            "calmar_ratio": self.calmar_ratio,
            "sharpe_ratio": self.sharpe_ratio,
        }


# ── main entrypoint ────────────────────────────────────────────────────────

def run_backtest(
    algo_path: str | Path,
    days: Iterable[str] | str,
    *,
    data_dir: Optional[str | Path] = None,
    run_name: Optional[str] = None,
    extra_flags: Optional[Iterable[str]] = None,
    executable: Optional[str | Path] = None,
    merge_pnl: bool = True,
    timeout: float = 600.0,
) -> BacktestResult:
    """Run prosperity4btest on `algo_path` over the given day specs.

    Args:
        algo_path: Path to the algorithm .py file.
        days: One day spec or a list. Each spec is "<round>-<day>" (e.g. "5-2",
              "5-3", "5-4") or just "<round>" (all days in the round).
        data_dir: Optional data dir to pass via --data. If None, the bundled
                  resources inside prosperity4bt are used.
        run_name: Used as the basename for the .log and .csv. Defaults to a
                  timestamp-prefixed slug.
        extra_flags: Any additional CLI flags appended verbatim.
        executable: Override the prosperity4btest binary path.
        merge_pnl: If True, pass --merge-pnl (cross-day PnL aggregation).
        timeout: Seconds before subprocess is killed.

    Returns:
        BacktestResult with per-product PnL, total, drawdown, and paths.
    """
    algo_path = Path(algo_path).resolve()
    if not algo_path.exists():
        raise FileNotFoundError(f"Algo not found: {algo_path}")

    days_list = [days] if isinstance(days, str) else list(days)
    if not days_list:
        raise ValueError("At least one day spec is required")

    if run_name is None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        run_name = f"{ts}_{algo_path.stem}_{'_'.join(days_list)}"

    log_path = _RESULTS_DIR / f"{run_name}.log"
    csv_path = _RESULTS_DIR / f"{run_name}.csv"

    cli = _resolve_executable(executable)
    cmd: list[str] = [cli, "cli", str(algo_path), *days_list]
    if merge_pnl:
        cmd.append("--merge-pnl")
    cmd.append("--no-progress")
    cmd.extend(["--out", str(log_path)])
    if data_dir is not None:
        cmd.extend(["--data", str(Path(data_dir).resolve())])
    cmd.extend(LIMIT_FLAGS)
    if extra_flags:
        cmd.extend(extra_flags)

    t0 = time.time()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=_REPO_ROOT,
    )
    elapsed = time.time() - t0

    summary = _parse_summary(proc.stdout)

    # Prosperity also writes its own .log file via --out. We append the parsed
    # stdout here for redundancy in case --out misses anything.
    if not log_path.exists():
        log_path.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr)

    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product", "pnl"])
        for p, v in sorted(summary["per_product"].items()):
            w.writerow([p, v])
        if summary["total_pnl"] is not None:
            w.writerow(["__total__", summary["total_pnl"]])
        if summary["max_drawdown_abs"] is not None:
            w.writerow(["__max_drawdown_abs__", summary["max_drawdown_abs"]])
        if summary["calmar_ratio"] is not None:
            w.writerow(["__calmar__", summary["calmar_ratio"]])
        if summary["sharpe_ratio"] is not None:
            w.writerow(["__sharpe__", summary["sharpe_ratio"]])

    return BacktestResult(
        run_name=run_name,
        algo_path=algo_path,
        days=days_list,
        cmd=cmd,
        returncode=proc.returncode,
        elapsed_s=elapsed,
        log_path=log_path,
        csv_path=csv_path,
        per_product=summary["per_product"],
        total_pnl=summary["total_pnl"],
        max_drawdown_abs=summary["max_drawdown_abs"],
        calmar_ratio=summary["calmar_ratio"],
        sharpe_ratio=summary["sharpe_ratio"],
        stderr=proc.stderr,
    )