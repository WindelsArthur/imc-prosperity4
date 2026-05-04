"""Shared utilities for the algo1_tuned robustness audit.

Stateless-algo trick: per-day per-product PnL is identical regardless of which
days are merged. So we:
  - run a single 3-day merged backtest (--merge-pnl)
  - parse the per-day stdout blocks → dict[day -> dict[product -> pnl]]
  - compose 5 folds: F1=F3=F5=day3, F2=day4, F4=day2

This lets each candidate algo be evaluated with ONE backtest of ~30s.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── paths ──────────────────────────────────────────────────────────────────
_AUDIT_DIR = Path(__file__).resolve().parent
_PT_DIR = _AUDIT_DIR.parent                                             # parameter_tuning/
_AUTORES = _PT_DIR.parent                                               # ROUND_5/autoresearch/
_REPO_ROOT = _AUTORES.parent.parent                                     # repo root
_LIMIT_FLAGS_FILE = _AUTORES / "utils" / "limit_flags.txt"
_CLI = _REPO_ROOT / "imcp" / "bin" / "prosperity4btest"

with _LIMIT_FLAGS_FILE.open() as f:
    LIMIT_FLAGS = f.read().strip().split()

# 5-fold protocol, identical to harness/_FOLDS.
FOLDS = [
    {"name": "F1", "train": [2],     "test": 3},
    {"name": "F2", "train": [2, 3],  "test": 4},
    {"name": "F3", "train": [4],     "test": 3},
    {"name": "F4", "train": [3, 4],  "test": 2},
    {"name": "F5", "train": [2, 4],  "test": 3},
]
DAYS = (2, 3, 4)


# ── parsing ────────────────────────────────────────────────────────────────
_DAY_HEADER_RE = re.compile(
    r"^Backtesting .*\.py on round (\d+) day (\d+)\s*$", re.MULTILINE
)
_PNL_RE = re.compile(r"^([A-Z][A-Z0-9_]+):\s*([\-\d,]+)\s*$", re.MULTILINE)
_DAY_PNL_RE = re.compile(r"^Round\s+(\d+)\s+day\s+(\d+):\s*([\-\d,]+)\s*$",
                         re.MULTILINE)
_TOTAL_RE = re.compile(r"^Total profit:\s*([\-\d,]+)\s*$", re.MULTILINE)
_SHARPE_RE = re.compile(r"sharpe_ratio:\s*([\-\d.eE+nan/]+)")
_DD_RE = re.compile(r"max_drawdown_abs:\s*([\-\d,]+)")


def _to_int(s: str) -> int:
    return int(s.replace(",", ""))


@dataclass
class MergedResult:
    per_day_pnl: dict[int, int]                            # day -> total
    per_day_per_product: dict[int, dict[str, int]]         # day -> {product -> pnl}
    sharpe_3day: Optional[float]
    max_dd_3day: Optional[int]
    total_3day: int
    elapsed_s: float
    fold_pnls: dict[str, int] = field(default_factory=dict)
    fold_min: int = 0
    fold_median: float = 0.0
    fold_mean: float = 0.0

    def __post_init__(self):
        # compose folds
        for fk in FOLDS:
            self.fold_pnls[fk["name"]] = self.per_day_pnl.get(fk["test"], 0)
        vals = list(self.fold_pnls.values())
        if vals:
            sv = sorted(vals)
            self.fold_min = sv[0]
            n = len(vals)
            self.fold_median = sv[n // 2] if n % 2 == 1 else (sv[n // 2 - 1] + sv[n // 2]) / 2.0
            self.fold_mean = sum(vals) / n


def parse_merged_stdout(stdout: str) -> MergedResult:
    """Parse a `--merge-pnl` stdout into per-day per-product PnL.

    The stdout has, per day:
        Backtesting <algo> on round <r> day <d>
        ...possibly logger output...
        PRODUCT_A: 12,345
        PRODUCT_B: -3,456
        ...
        Total profit: 12,345
    Then a final "Profit summary" with `Round R day D: PNL` lines.
    """
    # Find each "Backtesting ... day D" header position, then parse the next
    # PRODUCT block until the next header or final "Profit summary".
    headers = list(_DAY_HEADER_RE.finditer(stdout))
    per_day_per_product: dict[int, dict[str, int]] = {}
    for i, m in enumerate(headers):
        day = int(m.group(2))
        start = m.end()
        end = headers[i + 1].start() if (i + 1) < len(headers) else stdout.find("Profit summary", start)
        if end < 0:
            end = len(stdout)
        block = stdout[start:end]
        prod_map: dict[str, int] = {}
        for pm in _PNL_RE.finditer(block):
            name, val = pm.group(1), pm.group(2)
            if name in ("Total", "Round"):
                continue
            try:
                prod_map[name] = _to_int(val)
            except ValueError:
                continue
        per_day_per_product[day] = prod_map

    per_day_pnl: dict[int, int] = {}
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
    algo_path: str | Path,
    *,
    days: tuple = DAYS,
    match_mode: str = "worse",
    timeout: float = 600.0,
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
    return res


def run_algo_text(
    algo_src: str,
    *,
    days: tuple = DAYS,
    match_mode: str = "worse",
    timeout: float = 600.0,
) -> MergedResult:
    """Like run_algo but for an in-memory algo source string."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=str(_AUDIT_DIR)
    ) as tf:
        tf.write(algo_src)
        tmp_path = Path(tf.name)
    try:
        return run_algo(tmp_path, days=days, match_mode=match_mode, timeout=timeout)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


# ── pair-set rendering ─────────────────────────────────────────────────────
def render_with_pairs(template_src: str, pairs: list[tuple]) -> str:
    """Replace ALL_PAIRS in algo1_tuned.py with the given list of pairs.

    The tuned source has a literal `ALL_PAIRS = [...]` block (line ~ALL_PAIRS).
    We rewrite it. Each pair is (a, b, slope, intercept).
    """
    lines = ["ALL_PAIRS = ["]
    for tup in pairs:
        a, b, slope, intercept = tup[0], tup[1], tup[2], tup[3]
        lines.append(f'    ("{a}", "{b}", {slope}, {intercept}),')
    lines.append("]")
    block = "\n".join(lines)

    # Match `ALL_PAIRS = [` ... matching `]` — we use a non-greedy match across
    # multiple lines; the file has only one ALL_PAIRS literal.
    pattern = re.compile(r"^ALL_PAIRS\s*=\s*\[.*?^\]\s*$", re.MULTILINE | re.DOTALL)
    new_src, n = pattern.subn(block, template_src, count=1)
    if n != 1:
        raise RuntimeError(f"ALL_PAIRS substitution failed (n={n})")
    return new_src
