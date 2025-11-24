# src/utils_geo.py

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

import pytz
from timezonefinder import TimezoneFinder

# Astral v3 imports
from astral import LocationInfo
from astral.sun import sun, azimuth

from streamlit_javascript import st_javascript


# ------------------------------------------------------------
# Timezone helpers
# ------------------------------------------------------------

_tf = TimezoneFinder()

def get_timezone_from_coords(lat: float, lon: float) -> str:
    """
    Returns an IANA timezone string for given coordinates.
    If lookup fails, fallback to America/New_York.
    """
    try:
        tz = _tf.timezone_at(lat=lat, lng=lon)
        if tz:
            return tz
    except Exception:
        pass
    return "America/New_York"


def format_local_time(dt_utc: datetime, tzname: str) -> str:
    """
    Format a UTC datetime into local time like '4:16 PM EST'.
    """
    try:
        tz = pytz.timezone(tzname)
    except Exception:
        tz = pytz.timezone("America/New_York")

    dt_local = dt_utc.astimezone(tz)
    return dt_local.strftime("%-I:%M %p %Z")


# ------------------------------------------------------------
# Auto azimuth at sunset
# ------------------------------------------------------------

def get_auto_azimuth(lat: float, lon: float, date_obj) -> float:
    """
    Compute sun azimuth at local sunset using Astral v3.
    Returns degrees (0=N, 90=E, 180=S, 270=W).
    """
    tzname = get_timezone_from_coords(lat, lon)
    tz = pytz.timezone(tzname)

    location = LocationInfo("", "", tzname, lat, lon)

    s = sun(location.observer, date=date_obj, tzinfo=tz)
    sunset_local = s["sunset"]

    # Astral v3 azimuth()
    az = azimuth(location.observer, sunset_local)
    return float(az)


# ------------------------------------------------------------
# Browser geolocation (immediate)
# ------------------------------------------------------------

def get_browser_location_immediate() -> Tuple[Optional[float], Optional[float]]:
    """
    Immediately requests browser geolocation.
    Returns (lat, lon) or (None, None) if user denies or unavailable.
    """
    coords = st_javascript(
        """
        new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({lat: null, lon: null});
            } else {
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                    () => resolve({lat: null, lon: null})
                );
            }
        })
        """
    )

    if isinstance(coords, dict):
        lat = coords.get("lat")
        lon = coords.get("lon")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            return float(lat), float(lon)

    return None, None
