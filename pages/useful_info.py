import streamlit as st
import pandas as pd
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
    ]
})

# Add a title and description
st.header("Key Locations in Tokyo")
st.write("Explore some of Tokyo's most famous landmarks")

# Display the locations in a table
st.subheader("Famous Landmarks")
st.dataframe(tokyo_locations[['name', 'lat', 'lon']], hide_index=True)

# Create the map with the locations
st.subheader("Map View")
my_map = st.map(
    data=tokyo_locations,
    latitude='lat',
    longitude='lon',
    size=20,
    zoom=11,
    use_container_width=True
)

# Add some additional information about the locations
st.subheader("About These Locations")
for name in tokyo_locations['name']:
    with st.expander(name):
        if name == "Shibuya Crossing":
            st.write("The world's busiest pedestrian crossing, with up to 3,000 people crossing at once.")
        elif name == "Tokyo Tower":
            st.write("A 333-meter-tall communications and observation tower, inspired by the Eiffel Tower.")
        elif name == "Senso-ji Temple":
            st.write("Tokyo's oldest Buddhist temple, founded in 645 AD.")
        elif name == "Shinjuku Station":
            st.write("The world's busiest railway station, serving millions of passengers daily.")
        elif name == "Meiji Shrine":
            st.write("A Shinto shrine dedicated to Emperor Meiji and Empress Shoken.")
