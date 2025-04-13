# features/add_flow.py

import streamlit as st
import json
from jsonschema import validate, ValidationError

from lib.brainstorm_data import brainstorm_item_schema, save_brainstorm_data

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
"""


@st.fragment
def _add_places_fragment():
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


def maybe_show_add_places_fragment():
    if st.session_state.get("add_data_step", 0) > 0:
        _add_places_fragment()
        st.divider()
