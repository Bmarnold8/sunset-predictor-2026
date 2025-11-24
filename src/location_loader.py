# src/location_loader.py

"""
A simple loader module that provides a clean dictionary of saved locations
for Streamlit or any other non-interactive parts of the app.
"""

from src.locations import LOCATIONS

def load_locations():
    """
    Returns a dictionary of all saved locations.

    Example return structure:
    {
        "bedford": {"lat": 42.1234, "lon": -71.2345},
        "boston":  {"lat": 42.3601, "lon": -71.0589},
        ...
    }
    """
    return LOCATIONS
