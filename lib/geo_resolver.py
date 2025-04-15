import requests
from typing import Optional, Dict, List
import streamlit as st
import time
from lib.cache import cache_response


def generate_query_variants(query: str) -> List[str]:
    """
    Given a geo_query like 'General Luna, Siargao, Philippines',
    return progressively simpler queries to fall back to:
    - 'General Luna, Siargao, Philippines'
    - 'General Luna, Siargao'
    - 'General Luna'
    """
    parts = [part.strip() for part in query.split(",")]
    variants = []

    # Generate simplified versions of the query by removing parts from the end
    for i in range(len(parts), 0, -1):
        variant = ", ".join(parts[:i])
        variants.append(variant)

    # Ensure the base part is added as a final fallback if not already
    if parts and parts[0] not in variants:
        variants.append(parts[0])

    return variants


@st.cache_data(show_spinner=False)
@cache_response(ttl_hours=48)
def resolve_geo_query(query: str) -> Optional[Dict]:
    """
    Resolves a geo_query string to lat/lon and geojson data using the Nominatim API.
    If no result is found, it retries with simplified versions of the query.

    Example:
      query = 'General Luna, Siargao, Philippines'
      Will try:
        - 'General Luna, Siargao, Philippines'
        - 'General Luna, Siargao'
        - 'General Luna'
    """
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "MyTravelApp/1.2 (luuk@luxcloudconsulting.nl)"}

    queries_to_try = generate_query_variants(query)

    for attempt_query in queries_to_try:
        params = {
            "q": attempt_query,
            "format": "json",
            "limit": 1,
            "polygon_geojson": 1,
        }

        try:
            response = requests.get(NOMINATIM_URL, params=params, headers=headers)
            time.sleep(1.0)
            response.raise_for_status()
            results = response.json()

            if results:
                result = results[0]
                return {
                    "name": result.get("display_name"),
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "boundingbox": result.get("boundingbox"),
                    "geojson": result.get("geojson"),
                }

        except Exception as e:
            return {"error": str(e)}

    return None
