import streamlit as st
from datetime import datetime
from lib.db import update_app_data


@st.dialog("➕ Add to Itinerary", width="large")
def show_add_to_itinerary_dialog(item):
    st.markdown(f"### 📍 {item['name']}")

    # Initialize default values (only one item at a time)
    if "must_see" not in st.session_state:
        st.session_state["must_see"] = False
    if "use_target_date" not in st.session_state:
        st.session_state["use_target_date"] = False
    if "target_date" not in st.session_state:
        st.session_state["target_date"] = datetime.today()

    # Render checkboxes
    st.session_state["must_see"] = st.checkbox(
        "⭐ Must See", value=st.session_state["must_see"]
    )
    checkbox_value = st.checkbox(
        "📅 Specify Target Date", value=st.session_state["use_target_date"]
    )

    # Handle toggle for date input
    if st.session_state["use_target_date"] != checkbox_value:
        st.session_state["use_target_date"] = checkbox_value
        st.rerun(scope="fragment")

    if st.session_state["use_target_date"]:
        st.session_state["target_date"] = st.date_input(
            "📅 Target Date",
            value=st.session_state["target_date"],
            min_value=datetime.today(),
        )

    # Additional fields
    duration = st.number_input("🔢 Duration (days)", min_value=1, max_value=60, value=5)
    notes = st.text_area("📝 Notes")

    # Save to itinerary
    if st.button("💾 Save"):
        new_entry = {
            "id": item["id"],
            "name": item["name"],
            "must_see": st.session_state["must_see"],
            "target_date": (
                st.session_state["target_date"].isoformat()
                if st.session_state["use_target_date"]
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
