import streamlit as st
import pydeck as pdk
import requests
from menu import menu_with_redirect

menu_with_redirect()

# Function to query OSM via Overpass API and return GeoJSON
def fetch_osm_boundary(place_name: str):
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    relation["name:en"="{place_name}"]["boundary"="administrative"];
    out body;
    >;
    out geom;
    """

    response = requests.post(overpass_url, data={"data": query})
    response.raise_for_status()
    data = response.json()

    # Separate all ways with geometry
    ways_by_id = {}
    for element in data["elements"]:
        if element["type"] == "way" and "geometry" in element:
            ways_by_id[element["id"]] = element["geometry"]

    # Look for the boundary relation
    for rel in data["elements"]:
        if rel["type"] == "relation" and rel.get("tags", {}).get("boundary") == "administrative":
            coords = []

            for member in rel.get("members", []):
                if member["type"] == "way" and member.get("role") == "outer":
                    way_geometry = ways_by_id.get(member["ref"])
                    if way_geometry:
                        coords.append([[pt["lon"], pt["lat"]] for pt in way_geometry])

            if coords:
                return {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": coords  # multiple outer rings if available
                        },
                        "properties": {
                            "name": rel.get("tags", {}).get("name", "Unknown")
                        }
                    }]
                }

    return None


# UI: search input
st.title("🗾 Draw Tokyo District Boundaries")
place = st.text_input("Enter an area name (e.g., Asakusa, Shibuya, Akihabara)", "Asakusa")

# If place entered, try to fetch and draw
if place:
    geojson_data = fetch_osm_boundary(place)

    if geojson_data and geojson_data["features"]:
        # Estimate center of the first polygon
        coords = geojson_data["features"][0]["geometry"]["coordinates"][0]
        center_lon = sum([pt[0] for pt in coords]) / len(coords)
        center_lat = sum([pt[1] for pt in coords]) / len(coords)

        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=14,
            pitch=0
        )

        layer = pdk.Layer(
            "GeoJsonLayer",
            data=geojson_data,
            pickable=True,
            stroked=True,
            filled=True,
            get_fill_color='[200, 100, 150, 60]',
            get_line_color='[100, 100, 100]',
            line_width_min_pixels=1
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>{name}</b>", "style": {"color": "white"}}
        ))

    else:
        st.error("❌ Could not find boundaries for that place.")
