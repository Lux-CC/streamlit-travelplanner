import streamlit as st
import json
from lib.brainstorm_data import save_brainstorm_data


def show_editable_item(item):
    st.markdown(f"### ✏️ Editing: {item['name']}")
    advanced = st.session_state.get("advanced_edit", False)

    if not advanced:
        default_text = "\n".join(a["text"] for a in item.get("annotations", []))
        updated_text = st.text_area(
            "Annotations (one per line)", default_text, height=200
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save"):
                lines = [
                    line.strip() for line in updated_text.split("\n") if line.strip()
                ]
                item["annotations"] = [
                    {"id": f"a{i+1}", "text": line} for i, line in enumerate(lines)
                ]
                return item

        with col2:
            if st.button("⚙️ Advanced Modify"):
                st.session_state.advanced_edit = True
                st.rerun()

    else:
        st.markdown("### ⚙️ Advanced JSON Editor")
        raw_json = st.text_area(
            "Edit full JSON:", json.dumps(item, indent=2), height=300
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Advanced"):
                try:
                    updated = json.loads(raw_json)
                    st.session_state.advanced_edit = False
                    return updated
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")

        with col2:
            if st.button("⬅️ Back to Simple Edit"):
                st.session_state.advanced_edit = False
                st.rerun()

    return None


def render_edit_panel(brainstorm_data, clicked_id):
    selected_id = clicked_id
    if selected_id:
        item = next((x for x in brainstorm_data if x["id"] == selected_id), None)
        if item:
            updated = show_editable_item(item)
            if updated:
                for i, it in enumerate(st.session_state.brainstorm_data):
                    if it["id"] == selected_id:
                        st.session_state.brainstorm_data[i] = updated
                        save_brainstorm_data(st.session_state.brainstorm_data)
                        break


def maybe_show_raw_edit():
    raw = st.text_area(
        "Edit entire dataset as JSON array:",
        json.dumps(st.session_state.brainstorm_data, indent=2),
        height=600,
    )
    if st.button("💾 Save Batch Edit"):
        try:
            st.session_state.brainstorm_data = json.loads(raw)
            save_brainstorm_data(st.session_state.brainstorm_data)
            st.success("✅ Entire dataset saved.")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
