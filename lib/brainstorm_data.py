import os
import json

BRAINSTORM_FILE = "static/brainstorm.json"


def load_brainstorm_data():
    if os.path.exists(BRAINSTORM_FILE):
        with open(BRAINSTORM_FILE) as f:
            return json.load(f)
    return []


def save_brainstorm_data(data):
    # remove duplicate 'id'
    ids = set()
    for item in data:
        if item["id"] in ids:
            data.remove(item)
        else:
            ids.add(item["id"])

    with open(BRAINSTORM_FILE, "w") as f:
        json.dump(data, f, indent=2)


brainstorm_item_schema = {
    "type": "object",
    "required": [
        "id",
        "name",
        "geo_query",
        "country",
        "location_type",
        "category",
        "metadata",
        "annotations",
    ],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "geo_query": {"type": "string"},
        "country": {"type": "string"},
        "location_type": {"type": "string", "enum": ["region", "city", "place"]},
        "category": {
            "type": "string",
            "enum": ["nature", "hiking", "culture", "city", "beach", "temple", "food"],
        },
        "metadata": {
            "type": "object",
            "required": ["score", "status"],
            "properties": {
                "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "status": {"type": "string", "enum": ["included", "maybe", "skip"]},
            },
        },
        "annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "text"],
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
        },
    },
}
