"""Data loaders for ROUND_5.

Locates `prices_round_5_day_{day}.csv` and `trades_round_5_day_{day}.csv`,
parses with pandas, and caches a parquet copy under `data_views/` so subsequent
calls are cheap. The CSV files use `;` as the delimiter, matching the
Prosperity convention.

Public API
    load_prices(day: int)      -> pd.DataFrame
    load_trades(day: int)      -> pd.DataFrame
    load_all()                 -> dict with keys 'prices', 'trades', each
                                  a dict day -> DataFrame
    available_days()           -> sorted list of days for which prices exist
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

# ── path resolution ────────────────────────────────────────────────────────

_ROUND_DIR = Path(__file__).resolve().parents[2]            # ROUND_5/
_AUTORES = Path(__file__).resolve().parents[1]              # ROUND_5/autoresearch/
_CACHE = _AUTORES / "data_views"
_CACHE.mkdir(exist_ok=True)

# Roots searched, in order, for raw CSVs. The first existing file wins.
_SEARCH_ROOTS: List[Path] = [
    _ROUND_DIR / "Data",                                    # ROUND_5/Data/
    _ROUND_DIR / "data",                                    # ROUND_5/data/
    Path("/Users/arthurwindels/Documents") / "08_DEV" / "Prosperity4" /
        "IMC-Prosperity-4-Belmonte" / "ROUND_5" / "Data",
    Path("/mnt/user-data/ROUND_5/Data"),
    Path("/mnt/user-data") / "ROUND_5" / "Data",
]


def _find_file(filename: str) -> Path:
    """Search the configured roots for a given basename."""
    for root in _SEARCH_ROOTS:
        candidate = root / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Could not locate {filename!r} in any of: "
        + ", ".join(str(r) for r in _SEARCH_ROOTS)
    )


# ── prices ─────────────────────────────────────────────────────────────────

_PRICE_DTYPES = {
    "day": "int64",
    "timestamp": "int64",
    "product": "string",
    "bid_price_1": "Float64",
    "bid_volume_1": "Int64",
    "bid_price_2": "Float64",
    "bid_volume_2": "Int64",
    "bid_price_3": "Float64",
    "bid_volume_3": "Int64",
    "ask_price_1": "Float64",
    "ask_volume_1": "Int64",
    "ask_price_2": "Float64",
    "ask_volume_2": "Int64",
    "ask_price_3": "Float64",
    "ask_volume_3": "Int64",
    "mid_price": "Float64",
    "profit_and_loss": "Float64",
}


def load_prices(day: int, *, refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) the prices file for one R5 day."""
    cache = _CACHE / f"prices_r5_d{day}.parquet"
    if cache.exists() and not refresh:
        return pd.read_parquet(cache)

    src = _find_file(f"prices_round_5_day_{day}.csv")
    df = pd.read_csv(src, sep=";")
    for col, dtype in _PRICE_DTYPES.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except (TypeError, ValueError):
                pass
    df.to_parquet(cache, index=False)
    return df


# ── trades ─────────────────────────────────────────────────────────────────

_TRADE_DTYPES = {
    "timestamp": "int64",
    "buyer": "string",
    "seller": "string",
    "symbol": "string",
    "currency": "string",
    "price": "Float64",
    "quantity": "Int64",
}


def load_trades(day: int, *, refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) the trades file for one R5 day."""
    cache = _CACHE / f"trades_r5_d{day}.parquet"
    if cache.exists() and not refresh:
        return pd.read_parquet(cache)

    src = _find_file(f"trades_round_5_day_{day}.csv")
    df = pd.read_csv(src, sep=";")
    for col, dtype in _TRADE_DTYPES.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except (TypeError, ValueError):
                pass
    df.to_parquet(cache, index=False)
    return df


# ── bulk ───────────────────────────────────────────────────────────────────

def available_days(roots: Optional[Iterable[Path]] = None) -> List[int]:
    """Return the sorted list of day-indexes for which a prices file exists."""
    roots = roots or _SEARCH_ROOTS
    found = set()
    for root in roots:
        if not root.exists():
            continue
        for p in root.glob("prices_round_5_day_*.csv"):
            try:
                found.add(int(p.stem.split("_")[-1]))
            except ValueError:
                continue
    return sorted(found)


def load_all(*, refresh: bool = False) -> Dict[str, Dict[int, pd.DataFrame]]:
    """Load every (day, kind) in one shot. Returns {'prices': {d: df}, 'trades': {d: df}}."""
    days = available_days()
    return {
        "prices": {d: load_prices(d, refresh=refresh) for d in days},
        "trades": {d: load_trades(d, refresh=refresh) for d in days},
    }