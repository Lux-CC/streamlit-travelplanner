import streamlit as st
from datetime import datetime
from lib.db import update_app_data


@st.dialog("➕ Add to Itinerary", width="large")
def show_add_to_itinerary_dialog(item):
    st.markdown(f"### 📍 {item['name']}")

    # Define keys for this item's session state
    id_prefix = item["id"]
    must_key = f"{id_prefix}_must_see"
    date_toggle_key = f"{id_prefix}_use_target_date"
    date_value_key = f"{id_prefix}_target_date"

    # Initialize default values on first render
    if must_key not in st.session_state:
        st.session_state[must_key] = False
    if date_toggle_key not in st.session_state:
        st.session_state[date_toggle_key] = False
    if date_value_key not in st.session_state:
        st.session_state[date_value_key] = datetime.today()

    # Render interactive fields
    st.session_state[must_key] = st.checkbox(
        "⭐ Must See", value=st.session_state[must_key]
    )
    checkbox_value = st.checkbox(
        "📅 Specify Target Date", value=st.session_state[date_toggle_key]
    )
    st.toast(st.session_state[date_toggle_key], icon="📅")

    if st.session_state[date_toggle_key] != checkbox_value:
        st.session_state[date_toggle_key] = checkbox_value
        st.rerun(scope="fragment")

    if st.session_state[date_toggle_key]:
        st.session_state[date_value_key] = st.date_input(
            "📅 Target Date",
            value=st.session_state[date_value_key],
            min_value=datetime.today(),
        )

    duration = st.number_input("🔢 Duration (days)", min_value=1, max_value=60, value=5)
    notes = st.text_area("📝 Notes")

    # Save to itinerary
    if st.button("💾 Save", key="random"):
        new_entry = {
            "id": item["id"],
            "name": item["name"],
            "must_see": st.session_state[must_key],
            "target_date": (
                st.session_state[date_value_key].isoformat()
                if st.session_state[date_toggle_key]
                else None
            ),
            "duration_hint": duration,
            "notes": notes,
            "added_timestamp": datetime.now().isoformat(),
        }

        itinerary = st.session_state.get("itinerary_data", [])
        itinerary = [entry for entry in itinerary if entry["id"] != item["id"]]
        itinerary.append(new_entry)

        update_app_data("itinerary_data", itinerary)
        st.success("✅ Saved to itinerary")
        st.rerun()
