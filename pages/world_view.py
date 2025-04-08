import streamlit as st
import pydeck as pdk
from lib.langchain import extract_recommendations_from_text
from lib.langchain import fix_or_complete_location_data
from menu import menu_with_redirect
from lib.mapping import fetch_multiple_points
import json


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


def render_map(locations, placeholder_obj):
    """Render the map with all locations."""
    if not locations:
        return

    view_state = calculate_view_bounds(locations)
    layer = create_point_layer(locations)

    placeholder_obj.pydeck_chart(
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

    if not location_input:
        return

    map_placeholder = st.empty()

    st.subheader("Refine locations...")

    with st.spinner("Finding locations..."):
        locations, found_places, not_found_places = fetch_multiple_points(
            location_input
        )

        if locations:
            render_map(locations, map_placeholder)

            if not_found_places:
                st.warning(
                    "Could not find these locations: "
                    + ", ".join([place["place"] for place in not_found_places])
                )
        else:
            st.error("Could not find any of the specified locations.")


menu_with_redirect()

st.title("🗺️ World View")

default_locations = """You like diving, so Indonesia seems great. Also surfing is great in Bali. Avoid Java though!"""

travel_input = st.text_area(
    "Enter your travel plans",
    value=default_locations,
    height=150,
    help="Make sure it mentions cities and countries you want to visit",
)

if travel_input:
    # recommendations = extract_recommendations_from_text(travel_input)
    recommendations = json.loads(travel_input)
    recommendations = [
        {"index": i, **recommendation}
        for i, recommendation in enumerate(recommendations)
    ]
    fixed_recommendations = []
    for recommendation in recommendations:
        fixed_location = fix_or_complete_location_data(recommendation["location"])
        # add all fields of the recommendation but with fixed location
        fixed_recommendations.append({**recommendation, "location": fixed_location})

    with st.expander("Locations extracted from text"):
        if recommendations:
            st.dataframe(
                recommendations,
                hide_index=True,
            )
            st.dataframe(
                fixed_recommendations,
                hide_index=True,
            )
        else:
            st.warning("No locations were extracted from the text.")

    process_location_input(
        [
            {**recommendation["location"], "index": recommendation["index"]}
            for recommendation in fixed_recommendations
        ]
    )
