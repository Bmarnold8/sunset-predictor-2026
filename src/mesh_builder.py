# src/mesh_builder.py

import math
from typing import List, Dict, Optional

from src.config import (
    DISTANCE_BANDS,
    MESH_STEP_KM,
    MESH_MAX_DISTANCE_KM,
    PERP_OFFSET_DEFAULT_KM,
    PERP_OFFSET_BY_BAND_KM,
)

EARTH_RADIUS_KM = 6371.0

MeshPoint = Dict[str, object]  # simple alias for readability


# ---- Distance band classification ----

def _classify_distance_band(distance_km: float) -> Optional[str]:
    """
    Return the base band name for a given distance along the azimuth.
    e.g. 'Close', 'West', 'CloudHorizon', 'FarWest'

    Uses DISTANCE_BANDS from config.py:
        DISTANCE_BANDS = [
            ("Close",         0.0,   252.0),
            ("West",        252.0,   350.0),
            ("CloudHorizon", 350.0,  468.0),
            ("FarWest",     468.0,   935.0),
        ]
    """
    for name, d_min, d_max in DISTANCE_BANDS:
        if d_min <= distance_km < d_max:
            return name
    return None


# ---- Geodesic helper: project point given bearing + distance ----

def project_point(lat_deg: float, lon_deg: float, bearing_deg: float, distance_km: float):
    """
    Move from (lat_deg, lon_deg) along a great-circle by `distance_km`
    at `bearing_deg` (degrees clockwise from north).
    Returns (lat2_deg, lon2_deg).
    """
    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lon_deg)
    brng = math.radians(bearing_deg)

    d_over_r = distance_km / EARTH_RADIUS_KM

    sin_lat1 = math.sin(lat1)
    cos_lat1 = math.cos(lat1)

    sin_d_over_r = math.sin(d_over_r)
    cos_d_over_r = math.cos(d_over_r)

    sin_lat2 = sin_lat1 * cos_d_over_r + cos_lat1 * sin_d_over_r * math.cos(brng)
    lat2 = math.asin(sin_lat2)

    y = math.sin(brng) * sin_d_over_r * cos_lat1
    x = cos_d_over_r - sin_lat1 * sin_lat2
    lon2 = lon1 + math.atan2(y, x)

    # Normalize longitude to -180..+180
    lon2 = (lon2 + math.pi) % (2 * math.pi) - math.pi

    return math.degrees(lat2), math.degrees(lon2)


# ---- Mesh building ----

def build_narrow_mesh(
    start_lat: float,
    start_lon: float,
    azimuth_deg: float,
    step_km: float = MESH_STEP_KM,
    max_distance_km: float = MESH_MAX_DISTANCE_KM,
    use_band_perp_widths: bool = True,
    default_perp_offset_km: float = PERP_OFFSET_DEFAULT_KM,
) -> List[MeshPoint]:
    """
    Build a narrow 'ladder' mesh of coordinates using parameters from config.py.

    Group A: points along the azimuth (the spine).
    Group B: points perpendicular to the azimuth at each Group A point (the rungs).

    Each point has:
      - group: 'A' or 'B'
      - subgroup: e.g. 'GroupA_Close', 'GroupB_CloudHorizon'
      - distance_along_km
      - offset_perp_km (0 for A; +/- band width for B)
      - side: 'center', 'left', 'right'
      - index_along: integer step index (1, 2, 3, ...)
      - lat, lon

    Parameters:
      step_km: base step along azimuth (defaults to MESH_STEP_KM from config).
      max_distance_km: max distance along azimuth (defaults to MESH_MAX_DISTANCE_KM).
      use_band_perp_widths:
          If True, perpendicular offsets come from PERP_OFFSET_BY_BAND_KM[band]
          (falls back to default_perp_offset_km if band missing).
          If False, uses default_perp_offset_km for all bands.
      default_perp_offset_km:
          Fallback perpendicular offset if band-specific setting is not used/found.
    """
    points: List[MeshPoint] = []

    # How many steps along the azimuth?
    num_steps = int(max_distance_km // step_km)

    for k in range(1, num_steps + 1):
        distance_along_km = k * step_km

        # Classify this distance into a band
        band = _classify_distance_band(distance_along_km)
        if band is None:
            # Skip points outside defined bands, if any
            continue

        # Determine perpendicular width for this band
        if use_band_perp_widths:
            perp_offset_for_band = PERP_OFFSET_BY_BAND_KM.get(band, default_perp_offset_km)
        else:
            perp_offset_for_band = default_perp_offset_km

        # ---- Group A point (along azimuth) ----
        lat_a, lon_a = project_point(start_lat, start_lon, azimuth_deg, distance_along_km)

        subgroup_a = f"GroupA_{band}"

        point_a: MeshPoint = {
            "group": "A",
            "subgroup": subgroup_a,
            "distance_along_km": distance_along_km,
            "offset_perp_km": 0.0,
            "side": "center",
            "index_along": k,
            "lat": lat_a,
            "lon": lon_a,
        }
        points.append(point_a)

        # ---- Group B points (perpendicular to azimuth) ----

        # bearings for left/right relative to azimuth
        bearing_left = (azimuth_deg - 90.0) % 360.0
        bearing_right = (azimuth_deg + 90.0) % 360.0

        # Left point
        lat_left, lon_left = project_point(lat_a, lon_a, bearing_left, perp_offset_for_band)
        subgroup_b_left = f"GroupB_{band}"
        point_b_left: MeshPoint = {
            "group": "B",
            "subgroup": subgroup_b_left,
            "distance_along_km": distance_along_km,
            "offset_perp_km": -perp_offset_for_band,
            "side": "left",
            "index_along": k,
            "lat": lat_left,
            "lon": lon_left,
        }
        points.append(point_b_left)

        # Right point
        lat_right, lon_right = project_point(lat_a, lon_a, bearing_right, perp_offset_for_band)
        subgroup_b_right = f"GroupB_{band}"
        point_b_right: MeshPoint = {
            "group": "B",
            "subgroup": subgroup_b_right,
            "distance_along_km": distance_along_km,
            "offset_perp_km": perp_offset_for_band,
            "side": "right",
            "index_along": k,
            "lat": lat_right,
            "lon": lon_right,
        }
        points.append(point_b_right)

    return points
