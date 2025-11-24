# src/web_app.py

import os
import sys
import streamlit as st
from datetime import date

# ---------------------------------------
# Ensure repo root is on sys.path so src.* imports work
# ---------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from streamlit_geolocation import streamlit_geolocation  # NEW

from src.location_loader import load_locations
from src.sunset2026_main import run_full_sunset_analysis
from src.utils_geo import get_auto_azimuth


st.set_page_config(
    page_title="Sunset Predictor 2026",
    page_icon="🌅",
    layout="centered",
)

st.title("🌅 Sunset Predictor 2026")
st.write("""
Select a location (saved, manual, or current), and this app will automatically compute the sunset azimuth
and analyze cloud conditions to explain tonight’s sunset potential.
""")

# ------------------------------------------------------------
# Session state init for browser location
# ------------------------------------------------------------
if "browser_lat" not in st.session_state:
    st.session_state.browser_lat = None
if "browser_lon" not in st.session_state:
    st.session_state.browser_lon = None


# ------------------------------------------------------------
# LOCATION INPUT (UI Style A)
# ------------------------------------------------------------
st.subheader("📍 Choose your location")

location_mode = st.radio(
    "Location source:",
    ["Saved location", "Enter coordinates manually", "Use my current location"]
)

lat = lon = None

if location_mode == "Saved location":
    saved_dict = load_locations()
    selected_name = st.selectbox("Select a saved location:", list(saved_dict.keys()))
    lat = saved_dict[selected_name]["lat"]
    lon = saved_dict[selected_name]["lon"]
    st.write(f"Coordinates: **{lat:.6f}, {lon:.6f}**")

elif location_mode == "Enter coordinates manually":
    lat = st.number_input("Latitude", format="%.6f")
    lon = st.number_input("Longitude", format="%.6f")
    st.write(f"Coordinates: **{lat:.6f}, {lon:.6f}**")

elif location_mode == "Use my current location":
    st.info("Press the button below. Your browser should ask permission to share location.")

    # This component renders its own button and returns a dict after click
    loc = streamlit_geolocation()

    # loc is either "No Location Info" (string) or a dict with latitude/longitude
    if isinstance(loc, dict):
        b_lat = loc.get("latitude")
        b_lon = loc.get("longitude")
        if isinstance(b_lat, (int, float)) and isinstance(b_lon, (int, float)):
            st.session_state.browser_lat = float(b_lat)
            st.session_state.browser_lon = float(b_lon)

    lat = st.session_state.browser_lat
    lon = st.session_state.browser_lon

    if lat is None or lon is None:
        st.warning("No location received yet. Click the button and allow location access.")
    else:
        st.success(f"Detected coordinates: **{lat:.6f}, {lon:.6f}**")


coords_ready = (lat is not None) and (lon is not None)


# ------------------------------------------------------------
# AZIMUTH SETTINGS
# ------------------------------------------------------------
st.subheader("☀️ Azimuth Settings")

auto_az = None
if coords_ready:
    auto_az = get_auto_azimuth(lat, lon, date.today())
    st.write(f"Auto-calculated sunset azimuth: **{auto_az:.1f}°**")

override = st.checkbox("Advanced: manually override azimuth")

manual_az = None
if override:
    manual_az = st.slider(
        "Manual azimuth (degrees)",
        0, 360,
        value=int(round(auto_az or 270))
    )

def final_azimuth():
    return manual_az if manual_az is not None else auto_az


# ------------------------------------------------------------
# RUN BUTTON
# ------------------------------------------------------------
if st.button("Run Tonight’s Sunset Analysis"):
    if not coords_ready:
        st.error("No valid coordinates selected. Please choose a location.")
    else:
        with st.spinner("Analyzing sunset conditions..."):
            report = run_full_sunset_analysis(
                lat=lat,
                lon=lon,
                azimuth_deg=final_azimuth(),
                target_date=date.today(),
            )
            st.subheader("📄 Sunset Report")
            st.text(report)

st.write("---")
st.caption("Built with Streamlit • Powered by Open-Meteo • Created by Ben Arnold")
