import requests
from typing import Optional, Dict

def resolve_geo_query(query: str) -> Optional[Dict]:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'limit': 1,
        'polygon_geojson': 1,
    }
    headers = {'User-Agent': 'YourTravelApp/1.0 (your.email@example.com)'}

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()
        if not results:
            return None

        result = results[0]
        return {
            'name': result.get('display_name'),
            'lat': float(result['lat']),
            'lon': float(result['lon']),
            'boundingbox': result.get('boundingbox'),
            'geojson': result.get('geojson')
        }
    except Exception as e:
        return {"error": str(e)}
