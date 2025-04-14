import boto3
import time
import json
import base64
import streamlit as st
from typing import Any, List

# Load AWS credentials from Streamlit secrets
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

dynamo = boto3.resource(
    "dynamodb",
    region_name="eu-west-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

cache_table = dynamo.Table("streamlit-worldtravel-cache")


# === Helpers ===


def serialize_data(data: Any) -> str:
    """Serialize Python object to base64-encoded JSON string."""
    json_str = json.dumps(data, default=str)
    return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")


def deserialize_data(encoded_data: str) -> Any:
    """Deserialize base64-encoded JSON string back to Python object."""
    try:
        json_str = base64.b64decode(encoded_data.encode("utf-8")).decode("utf-8")
        return json.loads(json_str)
    except (json.JSONDecodeError, base64.binascii.Error) as e:
        print(f"Error deserializing data: {e}")
        return None


def chunk_string(s: str, max_size: int = 300_000) -> List[str]:
    """Split a string into chunks of max_size."""
    return [s[i : i + max_size] for i in range(0, len(s), max_size)]


def query_all_chunks(cache_key: str) -> List[dict]:
    """Query DynamoDB for all chunks of a given cache_key, paginated."""
    all_items = []
    last_key = None

    while True:
        params = {
            "KeyConditionExpression": "cache_key = :ck",
            "ExpressionAttributeValues": {":ck": cache_key},
            "ScanIndexForward": True,
        }
        if last_key:
            params["ExclusiveStartKey"] = last_key

        response = cache_table.query(**params)
        all_items.extend(response.get("Items", []))

        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break

    return all_items


# === Caching Decorator ===


def cache_response(ttl_hours=24):
    """
    Decorator to cache responses in DynamoDB, chunked if necessary.

    Args:
        ttl_hours (int): Time-to-live in hours
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                cache_key_raw = {"func": func.__name__, "args": args, "kwargs": kwargs}
                cache_key = serialize_data(cache_key_raw)[:1024]

                current_time = int(time.time())
                expiration_time = current_time + (ttl_hours * 3600)

                # Try to get all chunks
                try:
                    items = query_all_chunks(cache_key)
                except Exception as e:
                    print(f"Error accessing cache: {e}")
                    return func(*args, **kwargs)

                if items and all("data" in item for item in items):
                    full_data = "".join(item["data"] for item in items)
                    cached_data = deserialize_data(full_data)
                    if cached_data is not None:
                        print("Got cached data from dynamodb")
                        return cached_data, True

                # Cache miss → compute
                data = func(*args, **kwargs)
                serialized_data = serialize_data(data)
                chunks = chunk_string(serialized_data)

                for idx, chunk in enumerate(chunks):
                    cache_table.put_item(
                        Item={
                            "cache_key": cache_key,
                            "chunk_index": idx,
                            "data": chunk,
                            "TTL": expiration_time,
                            "cached_at": current_time,
                        }
                    )
                print("Cache miss, but computed data")
                return data, False

            except Exception as e:
                print(f"Cache wrapper failed: {e}")
                return func(*args, **kwargs)

        return wrapper

    return decorator


def time_function(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️ {func.__name__} took {end_time - start_time:.2f} seconds")
        return result

    return wrapper
