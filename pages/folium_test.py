# pages/01_brainstorm_map.py

import streamlit as st
import json
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

from lib.db import init_app_data
from lib.geo_resolver import resolve_geo_query
from lib.brainstorm_data import (
    load_brainstorm_data,
    save_brainstorm_data,
    brainstorm_item_schema,
)
from menu import menu_with_redirect
from lib.add_data_flow import maybe_show_add_places_fragment

# === Setup ===
st.set_page_config(layout="wide")
st.title("🗺️ Brainstorm Map Viewer (Folium Edition)")
menu_with_redirect()

import json


def show_editable_item(item):
    st.markdown(f"### ✏️ Editing: {item['name']}")
    advanced = st.session_state.get("advanced_edit", False)

    if not advanced:
        default_text = "\n".join(a["text"] for a in item.get("annotations", []))
        updated_text = st.text_area(
            "Annotations (one per line)", default_text, height=200
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save"):
                lines = [
                    line.strip() for line in updated_text.split("\n") if line.strip()
                ]
                item["annotations"] = [
                    {"id": f"a{i+1}", "text": line} for i, line in enumerate(lines)
                ]
                return item

        with col2:
            if st.button("⚙️ Advanced Modify"):
                st.session_state.advanced_edit = True
                st.rerun()

    else:
        st.markdown("### ⚙️ Advanced JSON Editor")
        raw_json = st.text_area(
            "Edit full JSON:", json.dumps(item, indent=2), height=300
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Advanced"):
                try:
                    updated = json.loads(raw_json)
                    st.session_state.advanced_edit = False
                    return updated
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")

        with col2:
            if st.button("⬅️ Back to Simple Edit"):
                st.session_state.advanced_edit = False
                st.rerun()

    return None


from lib.db import update_app_data


def show_filter_controls(data, default_filters):
    def persist_state():
        update_app_data(
            "brainstorm_filters",
            {
                "statuses": st.session_state.selected_status_debug,
                "countries": st.session_state.selected_countries_debug,
            },
        )

    with st.expander("🗂 Filter by status and country", expanded=True):
        selected_statuses = st.multiselect(
            "Select which statuses to display:",
            options=["included", "maybe", "skip"],
            default=default_filters.get("statuses", ["included", "maybe"]),
            key="selected_status_debug",
            on_change=persist_state,
        )
        all_countries = sorted(set(item.get("country", "Unknown") for item in data))
        selected_countries = st.multiselect(
            "Select which countries to display:",
            options=all_countries,
            default=default_filters.get("countries", all_countries),
            key="selected_countries_debug",
            on_change=persist_state,
        )

    return (
        st.session_state.selected_status_debug,
        st.session_state.selected_countries_debug,
    )


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
maybe_show_add_places_fragment()

# === Map Logic ===
brainstorm_data = st.session_state.brainstorm_data
selected_statuses, selected_countries = show_filter_controls(
    brainstorm_data,
    st.session_state["AppUserData"].get("brainstorm_filters", {}),
)

map_view = folium.Map(location=[10, 110], zoom_start=4)
Draw(
    export=True,
    filename="drawn_data.geojson",
    position="topleft",
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

            popup_html = f"""
<b>{item['name']}</b><br><br>
{"<br>".join(a['text'] for a in item.get('annotations', []))}
"""

            popup = folium.Popup(
                popup_html,
                max_width=250,
                show=(
                    True
                    if item["id"] == st.session_state.get("selected_item")
                    else False
                ),
            )

            folium.Marker(
                [result["lat"], result["lon"]],
                popup=popup,
                tooltip=item["id"],
            ).add_to(place_group)

country_group.add_to(map_view)
place_group.add_to(map_view)
folium.LayerControl(collapsed=False).add_to(map_view)


# === Layout ===
col1, col2 = st.columns([2, 1])

# === Left Column: Map Rendering ===
with col1:
    map_output = st_folium(
        map_view,
        use_container_width=True,
        height=600,
        returned_objects=["last_object_clicked_tooltip"],
    )

# === Right Column: Editing and Filters ===
with col2:
    clicked_id = map_output.get("last_object_clicked_tooltip")

    clicked_item = next((x for x in brainstorm_data if x["id"] == clicked_id), None)

    if edit_mode == "Clickable":
        selected_id = clicked_id
        if selected_id:
            item = clicked_item
            if item:
                updated = show_editable_item(item)
                if updated:
                    # Overwrite and save updated item
                    for i, it in enumerate(st.session_state.brainstorm_data):
                        if it["id"] == selected_id:
                            st.session_state.brainstorm_data[i] = updated
                            save_brainstorm_data(st.session_state.brainstorm_data)
                            st.success("✅ Changes saved!")
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


# === Debug Logs
with st.expander("🔍 Debug Output"):
    for log in debug_logs:
        st.write(log)
