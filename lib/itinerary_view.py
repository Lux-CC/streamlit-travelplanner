import streamlit as st
from datetime import datetime
from lib.db import update_app_data


@st.fragment
def render_itinerary_overview():
    itinerary = st.session_state.get("AppUserData", {}).get("itinerary_data")

    st.markdown("## 🧭 Your Itinerary")
    if not itinerary:
        st.info("No items in your itinerary yet.")
        return

    # Sort by target_date if available, otherwise fallback to name
    itinerary_sorted = sorted(
        itinerary,
        key=lambda x: x.get("target_date") or "",
    )

    for idx, item in enumerate(itinerary_sorted):
        with st.container():
            st.markdown(f"### 📍 {item['name']}")

            cols = st.columns([2, 1])
            with cols[0]:
                if item.get("must_see"):
                    st.markdown("⭐ **Must See**")
                if item.get("notes"):
                    st.markdown(f"📝 _{item['notes'].strip()}_")

            with cols[1]:
                if item.get("target_date"):
                    target_date = datetime.fromisoformat(item["target_date"]).strftime(
                        "%b %d, %Y"
                    )
                    st.markdown(f"📅 **{target_date}**")
                if item.get("duration_hint"):
                    st.markdown(f"⏱️ {item['duration_hint']} days")

            if st.button("Delete entry"):
                itinerary_sorted.pop(idx)
                update_app_data("itinerary_data", itinerary_sorted)
                st.rerun(scope="fragment")

            st.divider()
