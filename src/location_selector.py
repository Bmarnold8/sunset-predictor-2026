# src/location_selector.py

from src.locations import LOCATIONS, get_location

def choose_location_interactive():
    """Prompt the user to choose a saved location and return (name, lat, lon)."""
    print("Available locations:")
    for name in LOCATIONS.keys():
        print(f" - {name.capitalize()}")

    user_choice = input("Enter a location name: ").strip()

    try:
        coords = get_location(user_choice)
        return user_choice.lower(), coords["lat"], coords["lon"]
    except ValueError as e:
        print(e)
        return None, None, None
