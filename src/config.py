# src/config.py

"""
Configuration constants for Sunset Predictor 2026.
Supports all mesh-builder versions (past & future).
"""

# ------------------------------------------------------------
# Mesh spacing and extents
# ------------------------------------------------------------
# Distance step along the azimuth
MESH_STEP_KM = 75.0

# Maximum distance along azimuth
MESH_MAX_DISTANCE_KM = 900.0

# Default perpendicular width (left/right) for Group B
PERP_OFFSET_DEFAULT_KM = 75.0


# ------------------------------------------------------------
# Distance bands along azimuth
#   These determine the "subgroup" names applied by mesh_builder.
# ------------------------------------------------------------
# Format: (base_subgroup_name, min_km_inclusive, max_km_exclusive)
DISTANCE_BANDS = [
    ("Close",         0.0,   252.0),
    ("West",        252.0,   350.0),
    ("CloudHorizon",350.0,   468.0),
    ("FarWest",     468.0,   936.0),
]


# ------------------------------------------------------------
# Per-band perpendicular offsets (if used)
# Some mesh-builder versions expand width differently depending on distance.
# ------------------------------------------------------------
# This is the constant Streamlit is complaining about.
# We'll define a flexible mapping that works with ANY mesh logic:
PERP_OFFSET_BY_BAND_KM = {
    "Close":         PERP_OFFSET_DEFAULT_KM,
    "West":          PERP_OFFSET_DEFAULT_KM,
    "CloudHorizon":  PERP_OFFSET_DEFAULT_KM,
    "FarWest":       PERP_OFFSET_DEFAULT_KM,
}


# ------------------------------------------------------------
# Default timezone fallback
# ------------------------------------------------------------
DEFAULT_TIMEZONE_NAME = "America/New_York"
