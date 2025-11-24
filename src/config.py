# src/config.py

"""
General configuration constants for Sunset Predictor 2026.

This file defines:
- Mesh density and extents
- Perpendicular width defaults
- Distance band subgrouping along the azimuth
"""

# -----------------------------
# Mesh spacing / extent
# -----------------------------
MESH_STEP_KM = 75.0
MESH_MAX_DISTANCE_KM = 900.0

# Base perpendicular offset for Group B (left/right)
PERP_OFFSET_DEFAULT_KM = 75.0


# -----------------------------
# Distance bands (subgroups)
# -----------------------------
# These define how we label points based on distance along azimuth.
# Your earlier definitions:
#   Close:        <252 km
#   West:         252–350 km
#   CloudHorizon: 350–468 km
#   FarWest:      468–936 km
#
# Mesh builder can use these to assign subgroup names.
#
# Format: (subgroup_base_name, min_km_inclusive, max_km_exclusive)
DISTANCE_BANDS = [
    ("Close",         0.0, 252.0),
    ("West",        252.0, 350.0),
    ("CloudHorizon",350.0, 468.0),
    ("FarWest",     468.0, 936.0),
]


# -----------------------------
# Fallback timezone (only used if tz lookup fails)
# -----------------------------
DEFAULT_TIMEZONE_NAME = "America/New_York"
