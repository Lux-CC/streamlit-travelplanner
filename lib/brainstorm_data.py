import json
import streamlit as st
from lib.db import update_app_data


def load_brainstorm_data():
    data = json.loads(st.session_state.AppUserData.get("brainstorm_data", "[]"))
    st.toast(f"✅ Loaded {len(data)} places from brainstorm data")
    return data


def save_brainstorm_data(data):
    # remove duplicate 'id'
    ids = set()
    for item in data:
        if item["id"] in ids:
            data.remove(item)
        else:
            ids.add(item["id"])

    update_app_data("brainstorm_data", json.dumps(data))


brainstorm_item_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Travel Location Entry",
    "type": "object",
    "required": [
        "id",
        "name",
        "geo_query",
        "image_query",
        "country",
        "location_type",
        "category",
        "metadata",
        "annotations",
    ],
    "properties": {
        "id": {"type": "string", "description": "A short, unique identifier"},
        "name": {"type": "string"},
        "geo_query": {"type": "string"},
        "image_query": {"type": "string"},
        "country": {"type": "string"},
        "location_type": {"type": "string", "enum": ["region", "city", "place"]},
        "category": {
            "type": "string",
            "enum": ["nature", "hiking", "culture", "city", "beach", "temple", "food"],
        },
        "metadata": {
            "type": "object",
            "required": ["status", "score", "images"],
            "properties": {
                "status": {"type": "string", "enum": ["included", "maybe", "skip"]},
                "score": {"type": "number", "minimum": 0, "maximum": 1},
                "flexibility_rank": {"type": "number", "minimum": 0, "maximum": 1},
                "cluster_id": {"type": "string"},
                "typical_duration_days": {"type": "number", "minimum": 0},
                "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "access_notes": {"type": "string"},
                "activities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["description", "season"],
                        "properties": {
                            "description": {"type": "string"},
                            "season": {"type": "string"},
                        },
                    },
                },
                "seasonal_notes": {
                    "type": "object",
                    "properties": {
                        "best_months": {"type": "array", "items": {"type": "string"}},
                        "avoid_months": {"type": "array", "items": {"type": "string"}},
                        "weather_type": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string", "format": "uri"},
                },
                "dependencies": {"type": "array", "items": {"type": "string"}},
            },
        },
        "annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "text"],
                "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
            },
        },
    },
}
