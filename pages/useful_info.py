import streamlit as st
import pydeck as pdk
import pandas as pd

# Sample polygon data (lat/lon) for a few Tokyo districts (simplified outlines)
districts = pd.DataFrame({
    "name": ["Shibuya", "Shinjuku", "Asakusa"],
    "vibe": ["Trendy, youth-focused, nightlife", "Business hub meets bars", "Historical, traditional"],
    "info": [
        "Famous for the scramble crossing and fashion districts like Harajuku.",
        "Bustling area with skyscrapers, izakayas, and the busiest train station.",
        "Home to Senso-ji Temple, street food, and old-town Tokyo vibes."
    ],
    "center_lat": [35.659, 35.6938, 35.7148],
    "center_lon": [139.700, 139.7034, 139.7967],
    "polygon": [
        [[[139.695, 35.656], [139.705, 35.656], [139.705, 35.662], [139.695, 35.662]]],  # Shibuya
        [[[139.698, 35.69], [139.708, 35.69], [139.708, 35.697], [139.698, 35.697]]],     # Shinjuku
        [[[139.792, 35.712], [139.800, 35.712], [139.800, 35.718], [139.792, 35.718]]]    # Asakusa
    ]
})

# Polygon layer
polygon_layer = pdk.Layer(
    "PolygonLayer",
    data=districts,
    get_polygon="polygon",
    get_fill_color='[200, 30, 0, 90]',
    get_line_color=[80, 80, 80],
    line_width_min_pixels=1,
    pickable=True
)

# Scatterplot for center markers (for annotations on hover)
label_layer = pdk.Layer(
    "ScatterplotLayer",
    data=districts,
    get_position='[center_lon, center_lat]',
    get_fill_color='[0, 100, 200, 200]',
    get_radius=50,
    pickable=True
)

# Tooltip for annotations
tooltip = {
    "html": "<b>{name}</b><br/><i>{vibe}</i><br/>{info}",
    "style": {
        "backgroundColor": "black",
        "color": "white",
        "padding": "10px",
        "borderRadius": "5px"
    }
}

# Initial view
view_state = pdk.ViewState(
    latitude=35.68,
    longitude=139.75,
    zoom=11,
    pitch=0
)

# Display
st.title("Tokyo Districts with Vibes")
st.pydeck_chart(pdk.Deck(
    layers=[polygon_layer, label_layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style='mapbox://styles/mapbox/light-v9'
))
