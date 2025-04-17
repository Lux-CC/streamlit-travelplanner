import streamlit as st
import json
from lib.brainstorm_data import load_brainstorm_data, save_brainstorm_data
from lib.cache import time_function
from datetime import datetime
import copy


# === Load data and generate prompt ===
def get_prompt(data):
    return f"""
OK.

I currently have the following travel dataset:

```json
{json.dumps(data, indent=2)}
```

Each item includes:
- `id`, `name`, and `geo_query`
- A `metadata` dictionary with fields like:
  - `status` ("included", "maybe", "skip")
  - `score`: float (0–1)
  - `flexibility_rank`: float (0–1)
  - `typical_duration_days`
  - `budget_level`: "low" | "medium" | "high"
  - `access_notes`: how to reach it
  - `seasonal_notes`: includes `best_months`, `avoid_months`, `weather_type`, and `notes`
  - `activities`: list of activity descriptions with seasons
  - `images`: list of URLs
  - `dependencies`: list of stop IDs to be visited before this one
- An `annotations` array with travel tips or insights

---

Please suggest metadata and annotation improvements using the following JSON format:

```json
[
  {{
    "id": "banaue",
    "metadata": {{
      "score": 0.85,
      "flexibility_rank": 0.3,
      "typical_duration_days": 3,
      "seasonal_notes": {{
        "notes": "Add warning for landslides in July"
      }}
    }},
    "annotations": [
      {{
        "id": "a3",
        "text": "Can get very muddy after heavy rains"
      }}
    ]
  }}
]
```

👍 Only include items that need enrichment or improvement.  
📝 Add missing metadata like `access_notes`, `activities`, `budget_level`, or more helpful `annotations`.  
🚫 Don't change fields unless you're correcting or enriching them.  
🧠 If there’s too much content, split your output and ask if I want the next batch.

Return **only the enriched JSON array**, nothing else.
"""


from datetime import datetime
import copy


def update_last_edited_if_changed(edited_entries, original_entries):
    original_by_id = {e["id"]: e for e in original_entries if "id" in e}
    updated = []

    for entry in edited_entries:
        entry_id = entry.get("id")
        old_entry = original_by_id.get(entry_id)

        # Deep copy & strip last_edited_timestamp for comparison
        old_clean = copy.deepcopy(old_entry) if old_entry else {}
        new_clean = copy.deepcopy(entry)

        for e in [old_clean, new_clean]:
            e.pop("last_edited_timestamp", None)

        if old_clean != new_clean:
            entry["last_edited_timestamp"] = datetime.now().isoformat()

        updated.append(entry)

    return updated


@st.fragment
def batch_enrich_fragment():
    data = load_brainstorm_data()
    step = st.session_state.get("enrich_step", 0)
    st.markdown("## 🧠 Batch Enrichment Flow")

    if step == 1:
        st.markdown("### Step 1/2: Copy this prompt")
        st.code(get_prompt(data), language="text", height=300)
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Next →", key="enrich_step1_next"):
                st.session_state.enrich_step = 2
                st.rerun(scope="fragment")
        with col2:
            if st.button("Cancel", key="enrich_step1_cancel"):
                st.session_state.enrich_step = 0
                st.rerun(scope="app")

    elif step == 2:
        st.markdown("### Step 2/2: Edit and save enriched dataset")
        st.info("Manually apply suggestions from ChatGPT below.")

        raw = st.text_area(
            "Edit full dataset as JSON array:",
            value=json.dumps(st.session_state.brainstorm_data, indent=2),
            height=500,
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Edits", key="enrich_submit"):
                try:
                    edited_entries = json.loads(raw)
                    if not isinstance(edited_entries, list):
                        raise ValueError("Dataset must be a JSON array")

                    updated_entries = update_last_edited_if_changed(
                        edited_entries, st.session_state.brainstorm_data
                    )

                    st.session_state.brainstorm_data = updated_entries
                    save_brainstorm_data(updated_entries)
                    st.success("✅ Dataset saved.")
                    st.session_state.enrich_step = 0
                    st.rerun(scope="app")

                except (json.JSONDecodeError, ValueError) as e:
                    st.error(f"❌ Invalid JSON: {e}")


@time_function
def maybe_show_batch_enrich_fragment():
    if st.session_state.get("enrich_step", 0) > 0:
        batch_enrich_fragment()
        st.divider()
