import streamlit as st
import pydeck as pdk
from menu import menu_with_redirect
from lib.mapping import fetch_multiple_points


def create_point_layer(locations):
    """Create a scatter plot layer for locations."""
    return pdk.Layer(
        "ScatterplotLayer",
        data=locations,
        get_position=["lon", "lat"],
        get_color=[255, 0, 0],  # Red points
        get_radius=75000,  # Size of points
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
    )


def calculate_view_bounds(locations):
    """Calculate the optimal view state to show all points."""
    if not locations:
        return pdk.ViewState(latitude=0, longitude=0, zoom=1)

    lats = [loc["lat"] for loc in locations]
    lons = [loc["lon"] for loc in locations]

    center_lat = (max(lats) + min(lats)) / 2
    center_lon = (max(lons) + min(lons)) / 2

    # Calculate zoom level based on the spread of points
    lat_diff = max(lats) - min(lats)
    lon_diff = max(lons) - min(lons)
    max_diff = max(lat_diff, lon_diff)

    # Adjust zoom based on the spread
    if max_diff < 1:
        zoom = 10
    else:
        zoom = max(1, min(10, 180 / (max_diff * 4)))

    return pdk.ViewState(
        latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=0, bearing=0
    )


def render_map(locations):
    """Render the map with all locations."""
    if not locations:
        return

    view_state = calculate_view_bounds(locations)
    layer = create_point_layer(locations)

    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v10",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={
                "html": "<b>{name}</b>",
                "style": {"backgroundColor": "steelblue", "color": "white"},
            },
        )
    )


def process_location_input(location_input: str) -> None:
    """Process the location input and display the map with found locations."""
    locations_list = [loc.strip() for loc in location_input.split("\n") if loc.strip()]

    if not locations_list:
        return

    with st.spinner("Finding locations..."):
        locations = fetch_multiple_points(locations_list)

        if locations:
            render_map(locations)

            # Display locations found/not found
            found_places = {loc["name"] for loc in locations}
            not_found = set(locations_list) - found_places

            if not_found:
                st.warning("Could not find these locations: " + ", ".join(not_found))
        else:
            st.error("Could not find any of the specified locations.")


menu_with_redirect()

st.title("🗺️ World View")

default_locations = """Tokyo
New York
London
Sydney"""

location_input = st.text_area(
    "Enter cities or countries (one per line):",
    value=default_locations,
    height=150,
    help="Enter one location per line",
)

if location_input:
    process_location_input(location_input)
