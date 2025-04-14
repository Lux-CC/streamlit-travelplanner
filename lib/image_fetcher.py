import time
import requests
import threading
import streamlit as st

from lib.brainstorm_data import save_brainstorm_data

# Load your Unsplash API key from Streamlit secrets
UNSPLASH_ACCESS_KEY = st.secrets["UNSPLASH_ACCESS_KEY"]
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


def fetch_unsplash_images(query, count=3):
    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": count,
        "orientation": "landscape",
    }
    response = requests.get(UNSPLASH_API_URL, params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
    st.toast(f"📷 Fetched {len(results)} images for {query}")
    return [img["urls"]["regular"] for img in results]


def enrich_items_with_images(data):
    max_enrichments = 5
    for item in data:
        meta = item.get("metadata", {})
        if "images" in meta and meta["images"]:
            continue  # Already enriched

        if max_enrichments <= 0:
            break

        query = item.get("name") or item.get("geo_query")
        print(f"🔍 Searching images for: {query}")
        try:
            urls = fetch_unsplash_images(query)
            meta["images"] = urls if urls else []
            max_enrichments -= 1
        except Exception as e:
            print(f"⚠️ Failed to fetch images for {query}: {e}")
            meta["images"] = []

        time.sleep(1)  # Respect Unsplash rate limit (50 req/hr on free tier)

    st.toast("✅ Image enrichment completed.")
    save_brainstorm_data(data)


def enrich_items_with_images_threaded(data):
    thread = threading.Thread(target=enrich_items_with_images, args=(data,))
    thread.start()
