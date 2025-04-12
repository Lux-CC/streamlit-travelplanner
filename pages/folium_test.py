# pages/01_brainstorm_map.py

import streamlit as st
import json
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from jsonschema import validate, ValidationError

from lib.db import init_app_data
from lib.geo_resolver import resolve_geo_query
from lib.brainstorm_data import (
    load_brainstorm_data,
    save_brainstorm_data,
    brainstorm_item_schema,
)
from lib.brainstorm_ui import show_filter_controls, show_editable_item
from menu import menu_with_redirect

PROMPT_TEXT = """
OK.

You are helping create a structured travel plan. Convert the brainstormed locations and ideas into the following JSON structure.

For each destination, include:
- id: a short, unique identifier
- name: readable name
- geo_query: a string that can be resolved on a map (e.g. city, island, or landmark)
- country: the country
- location_type: one of [region, city, place]
- category: one of [nature, hiking, culture, city, beach, temple, food]
- metadata: a dictionary with at least:
    - score: a float between 0 and 1 for how attractive it is
    - status: one of [included, maybe, skip]
- annotations: a list of tips or comments, each with:
    - id: unique inside the entry
    - text: the annotation text

Output the result as a JSON array with 5–10 destinations. If the data is too long, ask the user if you'd like to continue with the next batch.

Example:

[
  {
    "id": "north-bali",
    "name": "North Bali",
    "geo_query": "Lovina, Bali, Indonesia",
    "country": "Indonesia",
    "location_type": "region",
    "category": "nature",
    "metadata": {
      "score": 0.85,
      "status": "maybe"
    },
    "annotations": [
      {"id": "a1", "text": "Check if waterfalls are open in May"},
      {"id": "a2", "text": "Could be a chill nature alternative to Ubud"}
    ]
  }
]"""

# === Setup ===
st.set_page_config(layout="wide")
st.title("🗺️ Brainstorm Map Viewer (Folium Edition)")
menu_with_redirect()

# === Init session state ===
if "brainstorm_data" not in st.session_state:
    st.session_state.brainstorm_data = load_brainstorm_data()
if "AppUserData" not in st.session_state:
    init_app_data()
if "add_data_step" not in st.session_state:
    st.session_state.add_data_step = 0
if "add_data_raw" not in st.session_state:
    st.session_state.add_data_raw = "[]"

# === Sidebar ===
edit_mode = st.sidebar.radio("Edit Mode", ["Clickable", "Batch Edit"])
if st.sidebar.button("➕ Add New Places"):
    st.session_state.add_data_step = 1
    st.rerun()


# === Add Data Flow via Fragment ===
@st.fragment
def add_places_fragment():
    step = st.session_state.get("add_data_step", 0)
    st.markdown("## ➕ Add Brainstorm Data")

    if step == 1:
        st.markdown("### Step 1/3: Copy this prompt")
        st.code(PROMPT_TEXT, language="text", height=240)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Next →", key="step1_next"):
                st.session_state.add_data_step = 2
                st.rerun(scope="fragment")
        with col2:
            if st.button("Cancel", key="step1_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")

    elif step == 2:
        st.markdown("### Step 2/3: Use ChatGPT with the prompt above")
        st.info("Paste the prompt into ChatGPT and copy the resulting JSON array.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back", key="step2_back"):
                st.session_state.add_data_step = 1
                st.rerun(scope="fragment")
        with col2:
            if st.button("Next →", key="step2_next"):
                st.session_state.add_data_step = 3
                st.rerun(scope="fragment")
        with col3:
            if st.button("Cancel", key="step2_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")

    elif step == 3:
        st.markdown("### Step 3/3: Paste your new entries")
        raw = st.text_area(
            "Paste entries (JSON array)",
            placeholder=st.session_state.get("add_data_raw", "[]"),
            height=300,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back", key="step3_back"):
                st.session_state.add_data_raw = raw
                st.session_state.add_data_step = 2
                st.rerun(scope="fragment")
        with col2:
            if st.button("✅ Append", key="step3_submit"):
                try:
                    entries = json.loads(raw)
                    if not isinstance(entries, list):
                        raise ValueError("Must be a JSON array")

                    for i, entry in enumerate(entries):
                        validate(instance=entry, schema=brainstorm_item_schema)

                    st.session_state.brainstorm_data.extend(entries)
                    save_brainstorm_data(st.session_state.brainstorm_data)

                    st.success("✅ Entries added successfully!")
                    st.session_state.add_data_step = 0
                    st.session_state.add_data_raw = "[]"
                    st.rerun()
                except (json.JSONDecodeError, ValidationError, ValueError) as e:
                    st.error(f"❌ Validation failed: {e}")
        with col3:
            if st.button("Cancel", key="step3_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")


# === Mount fragment if active ===
if st.session_state.add_data_step > 0:
    add_places_fragment()
    st.divider()

# === Layout ===
col1, col2 = st.columns([2, 1])
selected_statuses, selected_countries = [], []

# === Right Column: Editing and Filters ===
with col2:
    if edit_mode == "Clickable":
        selected_statuses, selected_countries = show_filter_controls(
            st.session_state.brainstorm_data,
            st.session_state["AppUserData"].get("brainstorm_filters", {}),
        )
        selected_id = st.session_state.get("selected_item")
        if selected_id:
            item = next(
                (x for x in st.session_state.brainstorm_data if x["id"] == selected_id),
                None,
            )
            if item:
                updated = show_editable_item(item)
                if updated:
                    for i, it in enumerate(st.session_state.brainstorm_data):
                        if it["id"] == selected_id:
                            st.session_state.brainstorm_data[i] = updated
                            save_brainstorm_data(st.session_state.brainstorm_data)
                            st.success("✅ Saved!")
                            break

    elif edit_mode == "Batch Edit":
        raw = st.text_area(
            "Edit entire dataset as JSON array:",
            json.dumps(st.session_state.brainstorm_data, indent=2),
            height=600,
        )
        if st.button("💾 Save Batch Edit"):
            try:
                st.session_state.brainstorm_data = json.loads(raw)
                save_brainstorm_data(st.session_state.brainstorm_data)
                st.success("✅ Entire dataset saved.")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")

# === Left Column: Map Rendering ===
with col1:
    brainstorm_data = st.session_state.brainstorm_data
    if edit_mode != "Clickable":
        selected_statuses, selected_countries = [], []

    map_view = folium.Map(location=[10, 110], zoom_start=4)
    Draw(
        export=True,
        filename="drawn_data.geojson",
        position="topright",
        draw_options={
            "polyline": True,
            "polygon": True,
            "circle": False,
            "rectangle": True,
            "marker": True,
            "circlemarker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(map_view)
    resolved, debug_logs = [], []

    country_group = folium.FeatureGroup(name="Country Outlines", show=True)
    place_group = folium.FeatureGroup(name="Places", show=True)

    if edit_mode == "Clickable":
        unique_countries = {
            item["country"]
            for item in brainstorm_data
            if item.get("metadata", {}).get("status") in selected_statuses
            and item.get("country") in selected_countries
        }
        for country in sorted(unique_countries):
            result, _ = resolve_geo_query(country)
            if result and "geojson" in result:
                folium.GeoJson(
                    result["geojson"],
                    name=f"{country}-outline",
                    style_function=lambda feature: {
                        "fillColor": "#00000000",
                        "color": "#444444",
                        "weight": 1.5,
                        "dashArray": "5,5",
                        "fillOpacity": 0.0,
                    },
                ).add_to(country_group)

    for item in brainstorm_data:
        if edit_mode == "Clickable":
            if item.get("metadata", {}).get("status") not in selected_statuses:
                continue
            if item.get("country") not in selected_countries:
                continue

        result, cache_hit = resolve_geo_query(item["geo_query"])
        debug_logs.append(f"{'✅' if cache_hit else '🆕'} {item['geo_query']}")

        if result and "error" not in result:
            result["id"] = item["id"]
            result["popup_id"] = item["id"]
            result["tooltip_text"] = f"{item['name']}<br>" + "<br>".join(
                [a["text"] for a in item.get("annotations", [])]
            )
            resolved.append(result)

            if result.get("geojson"):
                folium.GeoJson(
                    result["geojson"],
                    tooltip=result["tooltip_text"],
                    name=item["name"],
                    style_function=lambda feature: {
                        "fillColor": "#3388ff",
                        "color": "black",
                        "weight": 1,
                        "fillOpacity": 0.3,
                    },
                ).add_to(place_group)

            folium.Marker(
                [result["lat"], result["lon"]],
                popup=folium.Popup(item["id"], parse_html=True, show=True),
                tooltip=item["name"] or item["id"],
            ).add_to(place_group)

    country_group.add_to(map_view)
    place_group.add_to(map_view)
    folium.LayerControl(collapsed=False).add_to(map_view)

    map_output = st_folium(map_view, use_container_width=True, height=600)

    if edit_mode == "Clickable" and map_output.get("last_object_clicked_popup"):
        clicked_id = map_output["last_object_clicked_popup"]
        clicked_item = next((x for x in brainstorm_data if x["id"] == clicked_id), None)
        if clicked_item and st.session_state.get("selected_item") != clicked_item["id"]:
            st.session_state["selected_item"] = clicked_item["id"]
            st.rerun()

# === Debug Logs
with st.expander("🔍 Debug Output"):
    for log in debug_logs:
        st.write(log)
