# web_app.py

import streamlit as st
from datetime import datetime, timedelta
import pytz

# Import your existing modules
from sunset2026_main import run_full_sunset_analysis
from location_loader import load_locations

st.set_page_config(
    page_title="Sunset Predictor 2026",
    page_icon="🌅",
    layout="centered",
)

st.title("🌅 Sunset Predictor 2026")
st.write("""
This tool analyzes cloud conditions west of your location—along and around the solar azimuth—to assess 
how atmospheric structure may influence sunset color.  
It uses data from **Open-Meteo**, your custom mesh builder, and your classification rules.
""")

# ------------------------------
# LOCATION & INPUT PANEL
# ------------------------------

locations = load_locations()

location_name = st.selectbox(
    "Choose a location:",
    list(locations.keys())
)

selected = locations[location_name]
lat = selected["lat"]
lon = selected["lon"]

azimuth_default = 270  # west-ish default
azimuth = st.slider("Azimuth (°)", 230, 310, azimuth_default)

st.write(f"**Coordinates:** {lat}, {lon}")

# ------------------------------
# RUN ANALYSIS BUTTON
# ------------------------------

if st.button("Run Tonight's Sunset Analysis"):
    with st.spinner("Fetching atmospheric data and analyzing mesh…"):
        try:
            report_text = run_full_sunset_analysis(
                lat=lat,
                lon=lon,
                azimuth=azimuth,
                date=None,          # use today by default
                verbose=True        # keep your explicit print style
            )

            # Show output in a scrollable text box
            st.subheader("📄 Sunset Report")
            st.text(report_text)

        except Exception as e:
            st.error(f"Error running analysis: {e}")

# ------------------------------
# FOOTER
# ------------------------------

st.write("---")
st.caption("Built with Streamlit • Powered by Open-Meteo • Created by Ben Arnold")
