import streamlit as st
import json
from jsonschema import validate, ValidationError
from datetime import datetime

from lib.brainstorm_data import (
    brainstorm_item_schema,
    load_brainstorm_data,
    save_brainstorm_data,
)
from lib.cache import time_function


def get_prompt(existing_data, user_suggestions=None):
    existing_places = ", ".join([place["name"] for place in existing_data])
    suggestion_note = (
        f"The user is particularly interested in: {user_suggestions}"
        if user_suggestions
        else ""
    )
    return f"""
You are helping plan a structured, flexible travel itinerary. Based on brainstormed ideas or suggestions, generate a list of compelling travel destinations in JSON format.

You can skip {existing_places} as they are already included.

Follow this strict schema per destination:

- **id**: short unique identifier (`kebun-raya`)
- **name**: readable name (`Kebun Raya Botanical Garden`)
- **geo_query**: a string that can be resolved on a map (`Banaue, Philippines`)
- **image_query**: a specific location-based term to find representative images (e.g. `"hanoi old quarter"` instead of `"hanoi"`; avoid ambiguous terms like `"dakar"` which may return unrelated results)
- **country**: the country of the destination
- **location_type**: one of `region`, `city`, or `place`
- **category**: one of `nature`, `hiking`, `culture`, `city`, `beach`, `temple`, or `food`
- **metadata**:
  - `status`: "included", "maybe", or "skip"
  - `score`: float from 0.0 to 1.0 indicating overall attractiveness
  - `flexibility_rank`: optional float from 0.0 to 1.0 (how easy it is to shift dates)
  - `cluster_id`: optional string for regional grouping (`north-bali`, `central-vietnam`)
  - `typical_duration_days`: integer estimate of how long to stay
  - `budget_level`: "low", "medium", or "high"
  - `access_notes`: optional string with helpful tips on how to reach it
  - `activities`: optional list of key things to do, each with:
    - `description`: short activity name
    - `season`: when the activity is best done (e.g. `Nov–Mar`)
  - `seasonal_notes`: optional block:
    - `best_months`: e.g. ["Nov", "Dec", "Jan"]
    - `avoid_months`: e.g. ["Apr", "May"]
    - `weather_type`: e.g. "tropical dry/wet"
    - `notes`: freeform context (e.g. "Monsoon season starts in April")
  - `images`: empty array if no URLs provided; copy any that exist
  - `dependencies`: optional list of IDs for places that should be visited before this one
- **annotations**: a list of extra info or tips. The first entry must summarize the metadata in natural language. Contains
  - id: annotation id
  - text: text for the annotation

The exact schema is {json.dumps(brainstorm_item_schema)}
✅ The `image_query` should be as specific and unambiguous as possible to return location-relevant results from Unsplash.  
⛔ Do not include vague or generic search terms like "beach" or "Thailand".  
🎯 If the destination has a well-known landmark or district, include that in the query.

{suggestion_note}

Output must be a valid JSON array. Avoid nested explanation or markdown — just the JSON result.
"""


@st.fragment
def _add_places_fragment():
    step = st.session_state.get("add_data_step", 0)
    st.markdown("## ➕ Add Brainstorm Data")

    if step == 1:
        st.markdown("### Step 1/4: Add inspiration (optional)")
        user_input = st.text_input(
            "Suggest places or a vibe (or leave empty)",
            placeholder="E.g. manila, bohol, jakarta — or 'quiet surf towns with local food'",
            help="You can name one or more specific places (comma-separated), describe a vibe like 'remote mountains for hiking', or leave it empty if your chat history already has context.",
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Next →", key="step0_next"):
                st.session_state.user_suggestions = user_input
                st.session_state.add_data_step = 2
                st.rerun(scope="fragment")
        with col3:
            if st.button("Cancel", key="step0_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")

    elif step == 2:
        st.markdown("### Step 2/4: Copy this prompt")
        prompt = get_prompt(
            load_brainstorm_data(), st.session_state.get("user_suggestions")
        )
        st.code(prompt, language="text", height=240)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Next →", key="step1_next"):
                st.session_state.add_data_step = 3
                st.rerun(scope="fragment")
        with col1:
            if st.button("← Back", key="step1_back"):
                st.session_state.add_data_step = 1
                st.rerun(scope="fragment")
        with col3:
            if st.button("Cancel", key="step1_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")

    elif step == 3:
        st.markdown("### Step 3/4: Use ChatGPT with the prompt above")
        st.info("Paste the prompt into ChatGPT and copy the resulting JSON array.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back", key="step2_back"):
                st.session_state.add_data_step = 2
                st.rerun(scope="fragment")
        with col2:
            if st.button("Next →", key="step2_next"):
                st.session_state.add_data_step = 4
                st.rerun(scope="fragment")
        with col3:
            if st.button("Cancel", key="step2_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")

    elif step == 4:
        st.markdown("### Step 4/4: Paste your new entries")
        raw = st.text_area(
            "Paste entries (JSON array)",
            placeholder=st.session_state.get("add_data_raw", "[]"),
            height=300,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("← Back", key="step3_back"):
                st.session_state.add_data_raw = raw
                st.session_state.add_data_step = 3
                st.rerun(scope="fragment")
        with col2:
            if st.button("✅ Append", key="step3_submit"):
                try:
                    entries = json.loads(raw)
                    if not isinstance(entries, list):
                        raise ValueError("Must be a JSON array")

                    for i, entry in enumerate(entries):
                        validate(instance=entry, schema=brainstorm_item_schema)
                        entry["last_edited_timestamp"] = datetime.utcnow().isoformat()

                    st.session_state.brainstorm_data.extend(entries)
                    save_brainstorm_data(st.session_state.brainstorm_data)

                    st.success("✅ Entries added successfully!")
                    st.session_state.add_data_step = 0
                    st.session_state.add_data_raw = "[]"
                    st.session_state.user_suggestions = ""
                    st.rerun()

                except (json.JSONDecodeError, ValidationError, ValueError) as e:
                    st.error(f"❌ Validation failed: {e}")

        with col3:
            if st.button("Cancel", key="step3_cancel"):
                st.session_state.add_data_step = 0
                st.rerun(scope="app")


@time_function
def maybe_show_add_places_fragment():
    if st.session_state.get("add_data_step", 0) > 0:
        left, center, right = st.columns([1, 2, 1])  # 2/4 = 50% width
        with center:
            _add_places_fragment()
        st.divider()
