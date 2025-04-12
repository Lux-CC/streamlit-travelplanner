import streamlit as st
import json
from lib.brainstorm_data import save_brainstorm_data, brainstorm_item_schema
from jsonschema import validate, ValidationError


@st.dialog("Add Brainstorm Data")
def show_add_brainstorm_dialog():
    step = st.session_state.get("add_data_step", 1)

    if step == 1:
        st.markdown("### Step 1/3: Copy this prompt (top right 'copy' button)")
        st.code(PROMPT_TEXT, language="text", height=200)
        _step_nav(2)

    elif step == 2:
        st.markdown(
            "### Step 2/3: Go to ChatGPT and paste the prompt in your chat with activities. Then copy the output."
        )
        _step_nav(3)

    elif step == 3:
        st.markdown("### Step 3/3: Paste new brainstorm entries (JSON array)")
        raw = st.text_area("Paste entries here:", placeholder="[]", height=300)
        if st.button("➕ Append Entries"):
            try:
                new_entries = json.loads(raw)
                if not isinstance(new_entries, list):
                    raise ValueError("Input must be a JSON array")

                # Validate each entry
                for i, entry in enumerate(new_entries):
                    try:
                        validate(instance=entry, schema=brainstorm_item_schema)
                    except ValidationError as ve:
                        raise ValueError(f"Entry {i + 1} is invalid: {ve.message}")

                # All valid → append and save
                st.session_state.brainstorm_data.extend(new_entries)
                save_brainstorm_data(st.session_state.brainstorm_data)
                st.success("✅ Entries added!")
                st.session_state.pop("add_data_step", None)
                st.session_state.pop("show_add_dialog", None)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Validation failed: {e}")


def _step_nav(next_step):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Continue"):
            st.session_state.add_data_step = next_step
            st.session_state.show_add_dialog = True
            st.rerun()
    with col2:
        if st.button("❌ Cancel"):
            _close_modal()


def _close_modal():
    st.session_state.pop("add_data_step", None)
    st.session_state.pop("show_add_dialog", None)

