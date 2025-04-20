import streamlit as st
from streamlit_folium import st_folium
import json
from streamlit_float import float_init, float_css_helper

from lib.itinerary_view import render_itinerary_overview


st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://www.extremelycoolapp.com/help",
        "Report a bug": "https://www.extremelycoolapp.com/bug",
        "About": "# This is a header. This is an *extremely* cool app!",
    },
)
float_init()
# if not st.session_state.get("rerun_count"):
#     st.session_state.rerun_count = 0

# st.session_state.rerun_count += 1
# st.toast(f"{datetime.datetime.now()} rerender {st.session_state.rerun_count}!")

from lib.batch_edit_flow import maybe_show_batch_enrich_fragment
from lib.cache import time_function
from lib.image_fetcher import enrich_items_with_images
from lib.render_edit_panel import render_edit_panel
from lib.brainstorm_data import (
    load_brainstorm_data,
)
from menu import menu_with_redirect
from lib.db import init_app_data
from lib.add_data_flow import maybe_show_add_places_fragment
from lib.filter_controls import show_filter_controls
from lib.display_map_locations import render_brainstorm_locations

# === Page Setup ===
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
if "show_edit_panel" not in st.session_state:
    st.session_state.show_edit_panel = True

# === Map Toolkit Section ===
st.sidebar.markdown("## 📍 Map Toolkit")

# Search bar (currently inactive)
# st.sidebar.text_input(
#     "🔍 Search for a place", placeholder="(coming soon)", disabled=True
# )

# Primary action
if st.sidebar.button("➕ Add New Place"):
    st.session_state.add_data_step = 1
    st.rerun()

# === Filters Section ===
st.sidebar.markdown("## 🗂 Filters")
with st.sidebar:
    brainstorm_data = st.session_state.brainstorm_data
    selected_statuses, selected_countries = show_filter_controls(
        brainstorm_data,
        st.session_state["AppUserData"].get("brainstorm_filters", {}),
    )

# === Advanced Tools ===
st.sidebar.markdown("### ⚙️ Advanced")
with st.sidebar.expander("Show advanced tools", expanded=False):
    if st.button("📝 Batch Edit"):
        st.session_state.enrich_step = 1
        st.rerun()

    if st.button("🔄 Fetch 5 new images!"):
        enrich_items_with_images(brainstorm_data)

    st.download_button(
        label="📤 Export Data",
        data=json.dumps(load_brainstorm_data(), indent=2),
        file_name="travel_data.json",
        mime="application/json",
    )

st.sidebar.markdown("---")
# === Add/Edit Data Flow ===

maybe_show_add_places_fragment()
maybe_show_batch_enrich_fragment()


# === Fill Map With Locations ===
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
@time_function
def render_map(map_view_obj):
    map_output = st_folium(
        map_view_obj,
        use_container_width=True,
        height=600,
        zoom=st.session_state.get("map", {}).get("zoom", 4),
        center=st.session_state.get("map", {}).get("center"),
        returned_objects=["last_object_clicked_tooltip"],
        key="map",
    )

    # Track clicked item
    clicked_id = map_output.get("last_object_clicked_tooltip")
    if clicked_id and clicked_id != st.session_state.get("selected_item"):
        st.session_state.show_edit_panel = True
        st.session_state.selected_item = clicked_id


render_map(map_view_obj=map_view)


# === Floating right-hand sidebar ===
if st.session_state.get("selected_item"):

    if st.session_state.get("show_edit_panel", True):
        # === Expanded Panel ===
        full_dialog = st.container()
        with full_dialog:
            col1, col2 = st.columns([0.05, 0.95], vertical_alignment="center")
            with col1:
                if st.button(
                    "›", key="minimize_edit_panel", help="Minimize", type="tertiary"
                ):
                    st.session_state.show_edit_panel = False
                    st.rerun()
            with col2:
                render_edit_panel(brainstorm_data, st.session_state["selected_item"])

        float_css = float_css_helper(
            width="20rem",
            right="0rem",
            top="0rem",
            bottom="0rem",
            background="#ffffff",
            transition=4,
            shadow=5,
            css="""
                padding: 1rem;
                border-radius: 0.5rem;
            """,
        )
        full_dialog.float(float_css)

    else:
        # === Collapsed Sidebar Toggle ===
        mini_dialog = st.container()
        with mini_dialog:
            _, col, _ = st.columns([0.01, 0.95, 0.01], vertical_alignment="center")
            with col:
                if st.button(
                    "‹", key="expand_edit_panel", help="Open Sidebar", type="tertiary"
                ):
                    st.session_state.show_edit_panel = True
                    st.rerun()

        mini_css = float_css_helper(
            width="3.5rem",  # small button-sized width
            right="0rem",
            top="0rem",
            bottom="0rem",
            background="#ffffff",
            transition=4,
            shadow=5,
            css="""
                padding: 0.5rem;
                border-radius: 0.5rem;
                text-align: center;
            """,
        )
        mini_dialog.float(mini_css)


# col1, col2 = st.columns([2, 1])

# # === Left Column: Map Rendering ===
# with col1:
#     render_map(map_view_obj=map_view)


# # === Right Column: Editing and Filters ===
# with col2:
#     render_edit_panel(brainstorm_data, st.session_state.get("selected_item"))


with st.expander("Itinerary"):
    render_itinerary_overview()
