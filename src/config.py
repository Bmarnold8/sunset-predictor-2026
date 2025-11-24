# src/config.py

# Mesh settings for the Sunset Project

# Distance bands along the azimuth (km)
# (label, min_inclusive, max_exclusive)
DISTANCE_BANDS = [
    ("Close",         0.0,   252.0),
    ("West",        252.0,   350.0),
    ("CloudHorizon", 350.0,  468.0),
    ("FarWest",     468.0,   935.0),
]

# Default mesh density along the azimuth
MESH_STEP_KM = 75.0
MESH_MAX_DISTANCE_KM = 900.0

# Perpendicular width (Group B)
# For now, everything uses the same width.
PERP_OFFSET_DEFAULT_KM = 75.0

# Optional: future-proofed per-band perpendicular widths
PERP_OFFSET_BY_BAND_KM = {
    "Close":         75.0,
    "West":          75.0,
    "CloudHorizon":  75.0,
    "FarWest":       75.0,
}
