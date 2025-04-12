import streamlit as st
import json
from lib.db import update_app_data


def show_filter_controls(data, default_filters):
    with st.expander("🗂 Filter by status and country"):
        selected_statuses = st.multiselect(
            "Select which statuses to display:",
            options=["included", "maybe", "skip"],
            default=default_filters.get("statuses", ["included", "maybe"]),
        )
        all_countries = sorted(set(item.get("country", "Unknown") for item in data))
        selected_countries = st.multiselect(
            "Select which countries to display:",
            options=all_countries,
            default=default_filters.get("countries", all_countries),
        )
        update_app_data(
            "brainstorm_filters",
            {
                "statuses": selected_statuses,
                "countries": selected_countries,
            },
        )
    return selected_statuses, selected_countries


def show_editable_item(item):
    st.markdown(f"### ✏️ Editing: {item['name']}")
    raw = st.text_area(
        "Raw JSON",
        json.dumps(item, indent=2),
        height=300,
        key=f"editor_{item['id']}",
    )
    if st.button("Save Changes", key=f"save_{item['id']}"):
        try:
            updated = json.loads(raw)
            return updated
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
    return None
