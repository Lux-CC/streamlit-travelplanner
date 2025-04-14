import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import Draw
import json

st.set_page_config(layout="wide")

from lib.batch_edit_flow import maybe_show_batch_enrich_fragment
from lib.cache import time_function
from lib.image_fetcher import enrich_items_with_images
from lib.render_edit_panel import render_edit_panel
from lib.brainstorm_data import (
    load_brainstorm_data,
    save_brainstorm_data,
)
from menu import menu_with_redirect
from lib.db import init_app_data
from lib.add_data_flow import maybe_show_add_places_fragment
from lib.filter_controls import show_filter_controls
from lib.display_map_locations import render_brainstorm_locations

# === Page Setup ===
st.title("🗺️ Brainstorm Map Viewer (Folium Edition)")
menu_with_redirect()

# === Session State Initialization ===
if "AppUserData" not in st.session_state:
    init_app_data()
if "brainstorm_data" not in st.session_state:
    st.session_state.brainstorm_data = load_brainstorm_data()
if "add_data_step" not in st.session_state:
    st.session_state.add_data_step = 0
if "add_data_raw" not in st.session_state:
    st.session_state.add_data_raw = "[]"
if "enrich_step" not in st.session_state:
    st.session_state.enrich_step = 0

# === Sidebar Controls ===
if st.sidebar.button("➕ Batch Edit"):
    st.session_state.enrich_step = 1
    st.rerun()

if st.sidebar.button("➕ Add New Places"):
    st.session_state.add_data_step = 1
    st.rerun()

st.sidebar.download_button(
    label="📤 Export Data",
    data=json.dumps(load_brainstorm_data(), indent=2),
    file_name="travel_data.json",
    mime="application/json",
)

# === Add Data Flow ===
maybe_show_add_places_fragment()
maybe_show_batch_enrich_fragment()

# === Filter Controls ===
brainstorm_data = st.session_state.brainstorm_data
selected_statuses, selected_countries = show_filter_controls(
    brainstorm_data,
    st.session_state["AppUserData"].get("brainstorm_filters", {}),
)

# === Render Map ===
map_view = render_brainstorm_locations(
    brainstorm_data=brainstorm_data,
    selected_statuses=selected_statuses,
    selected_countries=selected_countries,
)


# Draw(
#     export=True,
#     filename="drawn_data.geojson",
#     position="topleft",
#     draw_options={
#         "polyline": True,
#         "polygon": True,
#         "circle": False,
#         "rectangle": True,
#         "marker": True,
#         "circlemarker": False,
#     },
#     edit_options={"edit": True, "remove": True},
# ).add_to(map_view)
# === Layout ===

col1, col2 = st.columns([2, 1])


@time_function
def render_map(map_view_obj):
    map_output = st_folium(
        map_view_obj,
        use_container_width=True,
        height=600,
        returned_objects=["last_object_clicked_tooltip"],
    )

    clicked_id = map_output.get("last_object_clicked_tooltip")
    if clicked_id and clicked_id != st.session_state.get("selected_item"):
        st.session_state.selected_item = clicked_id


# === Left Column: Map Rendering ===
with col1:
    render_map(map_view_obj=map_view)


# === Right Column: Editing and Filters ===
with col2:
    render_edit_panel(brainstorm_data, st.session_state.get("selected_item"))


# === Debug Logs ===
with st.expander("🔍 Debug Output"):
    for log in st.session_state.get("debug_logs", []):
        st.write(log)


if st.button("🔄 Fetch 5 new images!"):
    enrich_items_with_images(brainstorm_data)
