import streamlit as st
import json
from lib.brainstorm_data import load_brainstorm_data, save_brainstorm_data


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
                    st.session_state.brainstorm_data = json.loads(raw)
                    save_brainstorm_data(st.session_state.brainstorm_data)
                    st.success("✅ Dataset saved.")
                    st.session_state.enrich_step = 0
                    st.rerun(scope="app")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")
        with col2:
            if st.button("Cancel", key="enrich_cancel"):
                st.session_state.enrich_step = 0
                st.rerun(scope="app")


def maybe_show_batch_enrich_fragment():
    if st.session_state.get("enrich_step", 0) > 0:
        batch_enrich_fragment()
        st.divider()
