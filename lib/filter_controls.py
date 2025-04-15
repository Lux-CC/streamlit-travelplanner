# features/filter_controls.py

import streamlit as st
from lib.db import update_app_data


def show_filter_controls(data, default_filters):
    """
    Display multiselect filters for statuses and countries and persist selection.
    Returns:
        tuple: (selected_statuses, selected_countries)
    """

    def persist_filters():
        update_app_data(
            "brainstorm_filters",
            {
                "statuses": st.session_state.selected_status_debug,
                "countries": st.session_state.selected_countries_debug,
            },
        )

    all_countries = sorted(set(item.get("country", "Unknown") for item in data))

    # st.multiselect(
    #     "Select which statuses to display:",
    #     options=["included", "maybe", "skip"],
    #     default=default_filters.get("statuses", ["included", "maybe"]),
    #     key="selected_status_debug",
    #     on_change=persist_filters,
    # )
    st.session_state.selected_status_debug = ["included", "maybe", "skip"]

    # if default_filters have countries not in the all_countries, remove them
    if default_filters.get("countries"):
        default_filters["countries"] = [
            c for c in default_filters["countries"] if c in all_countries
        ]
    st.multiselect(
        "Select which countries to display:",
        options=all_countries,
        default=default_filters.get("countries", all_countries),
        key="selected_countries_debug",
        on_change=persist_filters,
    )

    return (
        st.session_state.selected_status_debug,
        st.session_state.selected_countries_debug,
    )
