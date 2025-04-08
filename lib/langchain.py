import streamlit as st
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict
import json
import re


def extract_recommendations_from_text(
    input_text: str, model: str = "mistral"
) -> List[Dict[str, str]]:
    """
    Call the Replicate API to extract a list of countries, cities, and preference scores from free-form text.

    Returns a list of dicts
    """
    user_input = f"""
You are a travel assistant. The user will provide a free-form description of travel preferences, context, or plans.
Your task is to extract a list of recommended or non-recommended things as JSON. Each entry should contain:

- "recommendation": a brief explanation of why this location is a good or bad match for the user's preferences
- "score": a number from -10 to 10 indicating how well this location matches the user's preferences, -10 being AVOID and 10 being MUST SEE
- "location": 
    - "country": the name of the country
    - "country_code": the ISO 3166-1 alpha-2 country code (e.g. "JP" for Japan, "US" for United States, "FR" for France)
    - "place": name of the place within the country, if relevant. If no cities are mentioned (e.g. an island, just use the largest city in that region)

Duplicate countries are allowed and cities are allowed, but the recommendation and score should have unique entries.

Respond with a JSON array like this:

[
    {{
        "recommendation": "Tokyo is known for its unique blend of tradition and modernity, and is a popular base for visiting the Japanese culture.",
        "score": 9,
        "location": {{
            "country": "Japan",
            "country_code": "JP",
            "place": "Tokyo"
        }}
    }},
    {{
        "recommendation": "Florence is famous for its art, architecture, and cuisine, and is a popular base for visiting the Italian culture.",
        "score": 7,
        "location": {{
            "country": "Italy",
            "country_code": "IT",
            "place": "Florence"
        }}
    }}
]

Here is the user input:
---
{input_text}
---
"""

    # Load model
    llm = Ollama(model="mistral")

    # Build a simple prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. ONLY return valid JSON. DO NOT add any commentary, notes, or explanation before or after. Output ONLY the JSON array as a raw value.",
            ),
            ("human", "{input}"),
        ]
    )

    # Combine prompt + model into a chain
    chain = prompt | llm
    output = chain.invoke({"input": user_input})

    # Try to parse JSON from the model output
    try:
        import json

        parsed = json.loads(output)
        indexed_records = (
            [dict(record, index=i) for i, record in enumerate(parsed)]
            if isinstance(parsed, list)
            else []
        )
        # add empty location fields if any of the fields are not given
        for record in indexed_records:
            if "location" in record:
                for field in ["country", "country_code", "place"]:
                    if field not in record["location"]:
                        record["location"][field] = ""

        return indexed_records

    except Exception as e:
        st.error(f"Failed to parse LLM output: {e}")
        st.error(f"Raw LLM response: {output}")

    return []


def fix_or_complete_location_data(raw_output: Dict) -> List[Dict]:
    """
    First asks LLM to analyze if data is complete — without changing it.
    Then (if needed) asks to correct it.
    Verdict is parsed from 'Verdict: YES' or 'Verdict: NO'.
    """
    llm = Ollama(model="mistral")

    def run_review_prompt():
        review_prompt = f"""
    You are a validator checking if the following dataset is valid.

    There are rules:
    1. 'country' must be a non-empty valid country name.
    2. 'place' must be a non-empty name of an actual place (city, island, region, etc).

    DO NOT suggest improvements.
    DO NOT fill in missing data.

    Just answer the following questions one by one:
    - Is 'country' valid? YES/NO
    - Is 'place' valid? YES/NO

    Then write: Verdict: YES if ALL fields are valid, otherwise Verdict: NO

    Here is the dataset:
    ---
    {json.dumps(raw_output, indent=2)}
    ---

    Please reason step by step and follow the format exactly.
    """
        review_chain = (
            ChatPromptTemplate.from_messages(
                [("system", "You are a helpful assistant."), ("human", "{input}")]
            )
            | llm
        )
        return review_chain.invoke({"input": review_prompt})

    def run_fix_prompt():
        fix_prompt = f"""
You are a travel data corrector.

Your task is to fix or complete missing or invalid fields in the following record:
- Fill in missing or incorrect 'country', or 'place' values.
- NEVER leave a field blank.
- NEVER add notes or explanations — just return corrected JSON.
- Do NOT modify existing valid fields.

Input:
---
{json.dumps(raw_output, indent=2)}
---

Return only the corrected JSON object.
"""
        fix_chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", "You are a helpful assistant."),
                    ("human", "{input}"),
                ]
            )
            | llm
        )
        return fix_chain.invoke({"input": fix_prompt})

    # Step 1: Strict review
    review_response = run_review_prompt()
    verdict_match = re.search(r"Verdict:\s*(YES|NO)", review_response, re.IGNORECASE)
    verdict = verdict_match.group(1).strip().upper() if verdict_match else "NO"

    if verdict == "NO":
        corrected = run_fix_prompt()
        try:
            return json.loads(corrected)
        except Exception as e:
            st.error(f"Failed to parse corrected LLM output: {e}")
            st.error(f"Raw correction: {corrected}")
    else:
        return raw_output
