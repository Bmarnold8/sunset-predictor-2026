# src/locations.py

LOCATIONS = {
    "bedford": {"lat": 42.4868, "lon": -71.2768},
    "home":    {"lat": 42.329516, "lon": -71.036679},
    "boston":  {"lat": 42.3601, "lon": -71.0589},
}

def get_location(name: str):
    """Return a location dict {'lat': ..., 'lon': ...} if it exists."""
    key = name.lower()
    if key in LOCATIONS:
        return LOCATIONS[key]
    raise ValueError(f"Location '{name}' not found. Try one of: {', '.join(LOCATIONS.keys())}")

