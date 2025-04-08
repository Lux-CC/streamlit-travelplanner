import requests
from typing import Dict, List, Optional
import streamlit as st
from lib.fixtures import COUNTRY_AREA_IDS
from lib.cache import cache_response


def get_area_id(country_code: str) -> int:
    """Get OSM area ID from ISO country code, or fallback to global."""
    return COUNTRY_AREA_IDS.get(country_code.upper(), 3606295631)


@cache_response()
def search_place_candidates(
    place_name: str, country_code: Optional[str] = None
) -> List[Dict]:
    """Search for place candidates within a country area, if given."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    area_clause = ""
    if country_code:
        area_id = get_area_id(country_code)
        area_clause = f"(area:{area_id})"

        query = f"""
        [out:json][timeout:25];
        (
        // place-tagged entities
        node["name"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};
        node["name:en"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};
        node["name:ascii"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};

        way["name"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};
        way["name:en"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};
        way["name:ascii"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};

        relation["name"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};
        relation["name:en"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};
        relation["name:ascii"="{place_name}"]["place"~"city|town|village|hamlet|suburb|neighbourhood|island|archipelago|locality"]{area_clause};

        // fallback for provinces/regions (e.g. Bali)
        relation["name"="{place_name}"]["boundary"="administrative"]["admin_level"~"4|5|6"]{area_clause};
        relation["name:en"="{place_name}"]["boundary"="administrative"]["admin_level"~"4|5|6"]{area_clause};
        relation["name:ascii"="{place_name}"]["boundary"="administrative"]["admin_level"~"4|5|6"]{area_clause};
        );
        out center tags;
        """

    response = requests.post(overpass_url, data={"data": query})
    response.raise_for_status()
    data = response.json()

    matches = []
    for el in data["elements"]:
        tags = el.get("tags", {})
        population = int(tags.get("population", 0)) if "population" in tags else None
        coords = None
        if el["type"] == "node":
            coords = {"lat": el["lat"], "lon": el["lon"]}
        elif "center" in el:
            coords = {"lat": el["center"]["lat"], "lon": el["center"]["lon"]}

        if coords:
            matches.append(
                {
                    "name": tags.get("name"),
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "population": population,
                    "country": country_code or "Unknown",
                    "raw_tags": tags,
                }
            )
    # sort matches on population or on the amount of data available in the raw_tags column (which is a dict probably but might also be text)
    return sorted(
        matches, key=lambda x: (x["population"] or 0, len(x["raw_tags"])), reverse=True
    )


def fetch_multiple_points(place_list) -> List[Dict]:
    """Fetch coordinates for multiple places with disambiguation via Streamlit."""
    locations = []
    found_places = []
    not_found_places = []

    for place in place_list:
        st.divider()
        index = place["index"]
        place_detailed = place["place"]
        country_code = place["country_code"]

        candidates = search_place_candidates(place_detailed, country_code)

        if not candidates:
            st.error(f"No matches found for {place}")
            not_found_places.append(place)
            continue
        elif len(candidates) == 1:
            st.success(f"Found {place_detailed} in {country_code}")
            locations.append(candidates[0])
            found_places.append(place)
            continue

        col1, col2 = st.columns([1, 2])  # Adjust width ratio as needed

        with col1:
            st.warning(f"⚠️ Found multiple matches for '{place}'")

        with col2:
            options = [
                f"{c['name']} ({c['country']}, pop: {c['population'] or 'unknown'})"
                for c in candidates
            ]
            default_index = 0  # You can customize this if needed
            selected = st.selectbox(
                f"Select the correct '{place}'",
                options,
                index=default_index,
                key=f"select_{place}_{index}",
            )
            with st.expander("🔍 More info on candidates..."):
                st.dataframe(candidates, hide_index=True)

        selected_index = options.index(selected)
        selected_place = candidates[selected_index]

        if selected_place.get("lat") and selected_place.get("lon"):
            locations.append(selected_place)

    return locations, found_places, not_found_places


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
        if (
            rel["type"] == "relation"
            and rel.get("tags", {}).get("boundary") == "administrative"
        ):
            coords = []

            for member in rel.get("members", []):
                if member["type"] == "way" and member.get("role") == "outer":
                    way_geometry = ways_by_id.get(member["ref"])
                    if way_geometry:
                        coords.append([[pt["lon"], pt["lat"]] for pt in way_geometry])

            if coords:
                return {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": coords,  # multiple outer rings if available
                            },
                            "properties": {
                                "name": rel.get("tags", {}).get("name", "Unknown")
                            },
                        }
                    ],
                }

    return None
