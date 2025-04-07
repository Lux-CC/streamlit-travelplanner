import streamlit as st
import pydeck as pdk
from menu import menu_with_redirect
from lib.mapping import fetch_osm_boundary


def create_view_state(coords, zoom=14, pitch=0):
    """Create a PyDeck ViewState object."""
    center_lon = sum([pt[0] for pt in coords]) / len(coords)
    center_lat = sum([pt[1] for pt in coords]) / len(coords)

    return pdk.ViewState(
        latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=pitch
    )


def create_boundary_layer(geojson_data):
    """Create a GeoJSON layer for district boundaries."""
    return pdk.Layer(
        "GeoJsonLayer",
        data=geojson_data,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color="[255, 0, 0, 255]",
        line_width_min_pixels=3,
    )


def render_map(view_state, layer):
    """Render the map with the given view state and layer."""
    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v10",
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>{name}</b>", "style": {"color": "black"}},
        )
    )


def display_district_boundaries(place):
    """Main function to display district boundaries for a given place."""
    geojson_data = fetch_osm_boundary(place)

    if not geojson_data or not geojson_data["features"]:
        st.error("❌ Could not find boundaries for that place.")
        return

    coords = geojson_data["features"][0]["geometry"]["coordinates"][0]

    view_state = create_view_state(coords)
    layer = create_boundary_layer(geojson_data)
    render_map(view_state, layer)


menu_with_redirect()

st.title("🗾 Draw Tokyo District Boundaries")
place = st.text_input(
    "Enter an area name (e.g., Asakusa, Shibuya, Akihabara)", "Asakusa"
)

if place:
    display_district_boundaries(place)
