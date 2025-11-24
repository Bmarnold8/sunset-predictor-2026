# src/open_meteo_client.py

from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Dict

import requests

BASE_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = "cloud_cover_low,cloud_cover_mid,cloud_cover_high"


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _ensure_utc_hour(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware in UTC and rounded down to the nearest hour.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware and in UTC (got naive datetime)")

    dt_utc = dt.astimezone(timezone.utc)
    # Floor to the hour: minutes/seconds -> 0
    return dt_utc.replace(minute=0, second=0, microsecond=0)


def _to_iso_hour(dt: datetime) -> str:
    """
    Convert a UTC datetime to the ISO 8601 hour format expected by Open-Meteo
    for start_hour / end_hour, e.g. '2025-11-17T20:00'.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    dt_utc = dt.astimezone(timezone.utc)
    # Drop seconds/micros; Open-Meteo accepts 'YYYY-MM-DDTHH:MM'
    return dt_utc.strftime("%Y-%m-%dT%H:%M")


# -------------------------------------------------------------------
# Sunset time (UTC)
# -------------------------------------------------------------------

def get_sunset_utc(lat: float, lon: float, target_date: date) -> datetime:
    """
    Get the sunset time (as a UTC-aware datetime) for a given location and date,
    using Open-Meteo's daily 'sunset' field.

    Parameters
    ----------
    lat, lon : float
        Latitude and longitude of the location.
    target_date : date
        The calendar date for which you want the sunset time.
        Typically this is your local date at the location.

    Returns
    -------
    datetime (timezone.utc)
        The sunset time in UTC for that date and location.

    Raises
    ------
    RuntimeError
        If the API response is missing expected data.
    """
    date_str = target_date.strftime("%Y-%m-%d")

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "sunset",
        "timezone": "UTC",
        "start_date": date_str,
        "end_date": date_str,
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "daily" not in data:
        raise RuntimeError("Open-Meteo response missing 'daily' key")

    daily = data["daily"]
    times = daily.get("time")
    sunsets = daily.get("sunset")

    if not (times and sunsets):
        raise RuntimeError("Open-Meteo daily data missing 'time' or 'sunset'")

    if len(sunsets) == 0:
        raise RuntimeError("No sunset data returned for the requested date")

    # Use the first (and only) sunset entry
    sunset_str = sunsets[0]  # e.g. "2025-11-17T21:20" or "...Z"

    # Handle optional 'Z' suffix
    if sunset_str.endswith("Z"):
        sunset_dt = datetime.fromisoformat(sunset_str.replace("Z", "+00:00"))
    else:
        sunset_dt = datetime.fromisoformat(sunset_str)

    # Treat as UTC
    sunset_dt = sunset_dt.replace(tzinfo=timezone.utc)
    return sunset_dt


# -------------------------------------------------------------------
# Cloud profile around sunset (Option A, Version A)
# -------------------------------------------------------------------

def get_cloud_profile_option_a(
    lat: float,
    lon: float,
    t_before: datetime,
    t_at: datetime,
    t_after: datetime,
) -> Dict[str, float]:
    """
    Fetch low/mid/high cloud cover from Open-Meteo for three UTC timestamps:

      - t_before: 1 hour before sunset
      - t_at:      sunset
      - t_after:   1 hour after sunset

    All datetimes must be timezone-aware and represent instants in UTC.
    The function will:

      1. Round each time down to the nearest hour (UTC).
      2. Request hourly cloud_cover_low/mid/high for the range [min, max].
      3. Match the returned data to those three hours.
      4. Return a dict with keys:
         low_before, mid_before, high_before,
         low_at,     mid_at,     high_at,
         low_after,  mid_after,  high_after
    """
    # 1. Normalize all target times to UTC hourly instants
    targets_raw = {
        "before": t_before,
        "at": t_at,
        "after": t_after,
    }

    targets_hours: Dict[str, datetime] = {
        label: _ensure_utc_hour(dt) for label, dt in targets_raw.items()
    }

    # Determine the time window to request
    start_dt = min(targets_hours.values())
    end_dt = max(targets_hours.values())

    start_str = _to_iso_hour(start_dt)
    end_str = _to_iso_hour(end_dt)

    # 2. Build and send the Open-Meteo request
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_VARS,
        "start_hour": start_str,
        "end_hour": end_str,
        "timezone": "UTC",
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "hourly" not in data:
        raise RuntimeError("Open-Meteo response missing 'hourly' key")

    hourly = data["hourly"]

    times = hourly.get("time")
    low = hourly.get("cloud_cover_low")
    mid = hourly.get("cloud_cover_mid")
    high = hourly.get("cloud_cover_high")

    if not (times and low and mid and high):
        raise RuntimeError("Open-Meteo hourly data missing one or more cloud arrays")

    if not (len(times) == len(low) == len(mid) == len(high)):
        raise RuntimeError("Mismatched lengths in hourly time/cloud arrays")

    # 3. Build a mapping from datetime -> index
    parsed_times: Dict[datetime, int] = {}
    for idx, t_str in enumerate(times):
        # Open-Meteo returns times like "2025-11-17T20:00"
        # or occasionally with 'Z' suffix
        if t_str.endswith("Z"):
            dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(t_str)
        # Treat as UTC
        dt = dt.replace(tzinfo=timezone.utc)
        parsed_times[dt] = idx

    # 4. For each target label, find the matching hour and extract values
    result: Dict[str, float] = {}

    for label, dt in targets_hours.items():
        idx = parsed_times.get(dt)
        if idx is None:
            raise RuntimeError(
                f"No hourly data returned for requested time {dt.isoformat()} ({label})"
            )

        result[f"low_{label}"] = float(low[idx])
        result[f"mid_{label}"] = float(mid[idx])
        result[f"high_{label}"] = float(high[idx])

    return result
