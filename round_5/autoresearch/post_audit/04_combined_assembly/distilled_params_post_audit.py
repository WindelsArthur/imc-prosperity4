"""Distilled parameter changes vs the audit's algo1_drop_harmful_only.py baseline.

This is a single-source-of-truth of every NEW tunable in algo1_post_audit_v04
relative to the post-audit baseline.

Reproduce v04 by patching algo1_drop_harmful_only.py with:
  1. Remove ROBOT_DISHES from the global pair_skew dict (skip both `out[a]=…`
     and `out[b]=…` updates when either is "ROBOT_DISHES" — see
     `01_robot_dishes_specialised/_dishes_template.py:_pair_skews_all`).
  2. Add `_dishes_log_pair_skew(mids)` that sums the 4 novel log-pairs into
     a price-space dollar tilt for ROBOT_DISHES, with per-pair clip.
  3. Add ROBOT_DISHES dedicated branch in `_fair`: use DISHES_INV_BETA, add
     the dedicated log-pair skew.
  4. Add `OTHER_BETA_MAP` for non-DISHES products.
"""

# ── 4 truly novel log-space pairs (from log_study Phase-6 ship_list_dedup) ─
DISHES_LOG_PAIRS = [
    # (i, j, beta_log, alpha_log) — residual = log(mid_i) - β log(mid_j) - α
    ("PEBBLES_S",                "ROBOT_DISHES",         -1.424539615179072,  22.21380995919832),
    ("ROBOT_DISHES",             "PANEL_2X4",             0.7852940330682344,  1.885458055632914),
    ("GALAXY_SOUNDS_BLACK_HOLES","ROBOT_DISHES",          1.234892829761178,  -2.0303511860381143),
    ("ROBOT_DISHES",             "SNACKPACK_STRAWBERRY",  1.2191408531743275, -2.100596770515793),
]

# ── Phase 1 dedicated-handler params (winner: 1c_c10_b0.6) ─────────────────
DISHES_AR1_COEF  = -0.232  # documented pooled coef; not used (USE_AR1=False)
DISHES_AR1_ALPHA = 0.0     # AR(1) overlay disabled (1d cells all failed)
DISHES_LOG_CLIP  = 10      # per-pair price-space dollar clip on log-pair tilt
DISHES_INV_BETA  = 0.6     # inv_skew β for ROBOT_DISHES alone (vs global 0.20)
DISHES_USE_AR1   = False
DISHES_USE_LOG   = True

# ── Phase 3 per-product β overrides (non-DISHES) ───────────────────────────
OTHER_BETA_MAP = {
    "MICROCHIP_OVAL":     0.40,   # was 0.20 — Phase 3 partial
    "SLEEP_POD_POLYESTER": 0.40,  # was 0.20 — Phase 3 partial
}

# ── Untouched constants (from algo1_drop_harmful_only.py) ──────────────────
INV_SKEW_BETA           = 0.20  # global default
PAIR_TILT_DIVISOR       = 3.0
PAIR_TILT_CLIP          = 7.0
PEBBLES_SUM_TARGET      = 50000.0
SNACKPACK_SUM_TARGET    = 50221.0
PEBBLES_SKEW_DIVISOR    = 8.0
SNACKPACK_SKEW_DIVISOR  = 5.0
PEBBLES_SKEW_CLIP       = 5.0
SNACKPACK_SKEW_CLIP     = 3.0
PEBBLES_BIG_SKEW        = 3.5
SNACKPACK_BIG_SKEW      = 3.5
QUOTE_BASE_SIZE_CAP     = 8
QUOTE_AGGRESSIVE_SIZE   = 2
POSITION_LIMIT          = 10

# Per-product strict caps (preserved from baseline)
PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 10,
    "UV_VISOR_MAGENTA":     4,
    "PANEL_1X2":            3,
    "TRANSLATOR_SPACE_GRAY": 4,
    "ROBOT_MOPPING":        2,
    "PANEL_4X4":            4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4,
    "SNACKPACK_RASPBERRY": 10,
    "SNACKPACK_CHOCOLATE": 10,
    "PEBBLES_L":            4,
}
