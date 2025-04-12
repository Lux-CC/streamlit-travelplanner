import requests
from typing import Optional, Dict
import streamlit as st
import time
from lib.cache import cache_response


@st.cache_data(show_spinner=False)
@cache_response(ttl_hours=48)
def resolve_geo_query(query: str) -> Optional[Dict]:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "polygon_geojson": 1,
    }
    headers = {"User-Agent": "MyTravelApp/1.2 (luuk@luxcloudconsulting.nl)"}

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers)
        time.sleep(1.5)
        response.raise_for_status()
        results = response.json()
        if not results:
            return None

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
