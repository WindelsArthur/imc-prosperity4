"""Per-product distilled MR parameters.

Each entry: {
    "mode": "TAKER" | "MM" | "IDLE",
    "fv": {"family": str, "params": dict},   # FV spec when needed
    "sigma": float,                          # rolling std of residual on training data
    "rule": {"z_in": float, "z_out": float, "sizing": str, "sizing_gamma": float,
             "z_stop": float | None, "time_stop": int | None,
             "alpha_skew": float, "beta_inv": float},   # MM-only
}

This file is kept as the single source of truth for runtime params. Edit
PARAMS to change behaviour; never mutate at runtime.
"""
from __future__ import annotations

from typing import Any, Dict


# Default MM params (used unless product overrides)
DEFAULT_MM = {
    "mode": "MM",
    "alpha_skew": 0.0,    # passive only — no signal skew
    "beta_inv": 0.2,      # inventory skew strength
    "max_size": 10,       # max quote size at each side
    "spread_offset": 1,   # post at best+offset / ask-offset (1 = inside)
}

# Signal-skewed MM (for products with strong AR(1) on diffs)
_MM_SKEW = {
    "OXYGEN_SHAKE_EVENING_BREATH": {
        "mode": "MM",
        "alpha_skew": 1.5,
        "beta_inv": 0.5,
        "max_size": 10,
        "spread_offset": 1,
        "fv_family": "ar_diff", "fv_params": {"p": 1},
    },
    "SNACKPACK_CHOCOLATE": {
        "mode": "MM",
        "alpha_skew": 1.0,
        "beta_inv": 0.3,
        "max_size": 10,
        "spread_offset": 1,
        "fv_family": "ar_diff", "fv_params": {"p": 1},
    },
}


# Phase-2 strict-qualifying TAKER configs:
#   sigma values come from train-fold residual std on the chosen FV (combined
#   day 2+3 calibration for day-5 freezing — here we approximate using the
#   fold-A sigma reported in grid_pivot.parquet).
_TAKER = {
    "ROBOT_DISHES": {
        "mode": "TAKER",
        "fv_family": "rolling_mean", "fv_params": {"w": 50},
        "sigma_fallback": 50.0,
        "z_in": 2.5, "z_out": 0.5, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
    "PEBBLES_M": {
        "mode": "TAKER",
        "fv_family": "rolling_quadratic", "fv_params": {"w": 2000},
        "sigma_fallback": 50.0,
        "z_in": 1.0, "z_out": 0.1, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
    "SLEEP_POD_POLYESTER": {
        "mode": "TAKER",
        "fv_family": "range_mid", "fv_params": {"w": 500},
        "sigma_fallback": 50.0,
        "z_in": 1.75, "z_out": 0.1, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
    "ROBOT_MOPPING": {
        "mode": "TAKER",
        "fv_family": "rolling_quadratic", "fv_params": {"w": 500},
        "sigma_fallback": 50.0,
        "z_in": 1.25, "z_out": 0.0, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
    "PEBBLES_XS": {
        "mode": "TAKER",
        "fv_family": "rolling_quadratic", "fv_params": {"w": 500},
        "sigma_fallback": 50.0,
        "z_in": 1.25, "z_out": 0.1, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
    "OXYGEN_SHAKE_CHOCOLATE": {
        "mode": "TAKER",
        "fv_family": "rolling_linreg", "fv_params": {"w": 500},
        "sigma_fallback": 30.0,
        "z_in": 1.0, "z_out": 0.0, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
    "PEBBLES_L": {
        "mode": "TAKER",
        "fv_family": "rolling_median", "fv_params": {"w": 100},
        "sigma_fallback": 50.0,
        "z_in": 1.5, "z_out": 0.1, "sizing": "fixed", "sizing_gamma": 0.0,
        "z_stop": None, "time_stop": None,
    },
}


# Products to IDLE (chronic MM losers — too much directional drift for inside-spread MM)
_IDLE_LIST = [
    "ROBOT_IRONING",                  # AR-skew failed; tight spread (6) loses
    "MICROCHIP_RECTANGLE",            # MM lost 13K
    "TRANSLATOR_SPACE_GRAY",          # MM lost 12K
    "GALAXY_SOUNDS_PLANETARY_RINGS",  # MM lost 7.2K
    "SLEEP_POD_SUEDE",                # MM lost 6.6K
    "SLEEP_POD_LAMB_WOOL",            # MM lost 5.3K
    "GALAXY_SOUNDS_SOLAR_FLAMES",     # MM lost 3.4K
    "UV_VISOR_MAGENTA",               # MM lost 3.2K
]


def get_params() -> Dict[str, Dict[str, Any]]:
    """Return per-product config dict. Unknown products default to MM."""
    from utils_local import ROUND5_PRODUCTS
    idle_set = set(_IDLE_LIST)
    out = {}
    for p in ROUND5_PRODUCTS:
        if p in _TAKER:
            out[p] = dict(_TAKER[p])
        elif p in _MM_SKEW:
            out[p] = dict(_MM_SKEW[p])
        elif p in idle_set:
            out[p] = {"mode": "IDLE"}
        else:
            out[p] = dict(DEFAULT_MM)
    return out
