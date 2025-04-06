import streamlit as st
import pandas as pd
import pydeck as pdk
from menu import menu_with_redirect

# Redirect to streamlit_app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

# Create a DataFrame with key locations in Tokyo
tokyo_locations = pd.DataFrame({
    'name': [
        'Shibuya Crossing',
        'Tokyo Tower',
        'Senso-ji Temple',
        'Shinjuku Station',
        'Meiji Shrine'
    ],
    'lat': [
        35.6595,  # Shibuya Crossing
        35.6586,  # Tokyo Tower
        35.7147,  # Senso-ji Temple
        35.6896,  # Shinjuku Station
        35.6764   # Meiji Shrine
    ],
    'lon': [
        139.7004,  # Shibuya Crossing
        139.7454,  # Tokyo Tower
        139.7967,  # Senso-ji Temple
        139.7006,  # Shinjuku Station
        139.6993   # Meiji Shrine
    ],
    'description': [
        "The world's busiest pedestrian crossing, with up to 3,000 people crossing at once.",
        "A 333-meter-tall communications and observation tower, inspired by the Eiffel Tower.",
        "Tokyo's oldest Buddhist temple, founded in 645 AD.",
        "The world's busiest railway station, serving millions of passengers daily.",
        "A Shinto shrine dedicated to Emperor Meiji and Empress Shoken."
    ]
})

# Add a title and description
st.header("Key Locations in Tokyo")
st.write("Explore some of Tokyo's most famous landmarks")

# Display the locations in a table
st.subheader("Famous Landmarks")
st.dataframe(tokyo_locations[['name', 'lat', 'lon']], hide_index=True)

# Create the interactive map using Pydeck
st.subheader("Map View")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=tokyo_locations,
    pickable=True,
    get_position='[lon, lat]',
    get_radius=100,
    get_fill_color='[255, 100, 100, 160]',
)

tooltip = {
    "html": "<b>{name}</b><br/>{description}",
    "style": {
        "backgroundColor": "black",
        "color": "white",
        "padding": "10px"
    }
}

view_state = pdk.ViewState(
    latitude=tokyo_locations['lat'].mean(),
    longitude=tokyo_locations['lon'].mean(),
    zoom=11,
    pitch=0
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style='mapbox://styles/mapbox/light-v9'
))

# Add additional information about the locations
st.subheader("About These Locations")
for i, row in tokyo_locations.iterrows():
    with st.expander(row['name']):
        st.write(row['description'])
