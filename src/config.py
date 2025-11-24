# src/config.py

"""
Configuration constants for Sunset Predictor 2026.
Universal / backwards-compatible with all mesh_builder versions.
"""

# ------------------------------------------------------------
# Mesh spacing and extents
# ------------------------------------------------------------
MESH_STEP_KM = 75.0
MESH_MAX_DISTANCE_KM = 900.0

# Default perpendicular width (left/right)
PERP_OFFSET_DEFAULT_KM = 75.0


# ------------------------------------------------------------
# Distance bands along azimuth (subgrouping)
# ------------------------------------------------------------
# Format: (base_subgroup_name, min_km_inclusive, max_km_exclusive)
DISTANCE_BANDS = [
    ("Close",          0.0, 252.0),
    ("West",         252.0, 350.0),
    ("CloudHorizon", 350.0, 468.0),
    ("FarWest",      468.0, 936.0),
]


# ------------------------------------------------------------
# Per-band perpendicular offsets
# (some mesh versions use these to widen/narrow by distance)
# ------------------------------------------------------------
PERP_OFFSET_BY_BAND_KM = {
    "Close":         PERP_OFFSET_DEFAULT_KM,
    "West":          PERP_OFFSET_DEFAULT_KM,
    "CloudHorizon":  PERP_OFFSET_DEFAULT_KM,
    "FarWest":       PERP_OFFSET_DEFAULT_KM,
}


# ------------------------------------------------------------
# Timezone fallback (only used if lookup fails)
# ------------------------------------------------------------
DEFAULT_TIMEZONE_NAME = "America/New_York"
