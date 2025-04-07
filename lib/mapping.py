import requests
from typing import Dict, List, Optional


def fetch_location_point(place_name: str) -> Optional[Dict]:
    """Fetch coordinates for a place using OSM Overpass API."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["name"="{place_name}"]["place"~"city|town|village"];
      way["name"="{place_name}"]["place"~"city|town|village"];
      relation["name"="{place_name}"]["place"~"city|town|village"];
    );
    out center 1;
    """

    try:
        response = requests.post(overpass_url, data={"data": query})
        response.raise_for_status()
        data = response.json()

        for element in data["elements"]:
            # Try node lat/lon directly
            if element["type"] == "node":
                return {
                    "name": place_name,
                    "lat": element.get("lat"),
                    "lon": element.get("lon"),
                }
            # For way/relation, get center
            elif "center" in element:
                return {
                    "name": place_name,
                    "lat": element["center"]["lat"],
                    "lon": element["center"]["lon"],
                }
    except Exception as e:
        print(f"Error fetching {place_name}: {e}")
        return None

    return None


def fetch_multiple_points(place_list: List[str]) -> List[Dict]:
    """Fetch coordinates for multiple places."""
    locations = []
    for place in place_list:
        location = fetch_location_point(place.strip())
        if location and location.get("lat") and location.get("lon"):
            locations.append(location)
    return locations


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
