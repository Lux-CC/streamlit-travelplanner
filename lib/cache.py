import boto3
import time
import json
import base64
import streamlit as st
from typing import Any

# add authentication from st.secrets
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
dynamo = boto3.resource(
    "dynamodb",
    region_name="eu-west-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
cache_table = dynamo.Table("streamlit-worldtravel-cache")


def serialize_data(data: Any) -> str:
    """
    Serialize data to JSON and encode to base64 to ensure DynamoDB compatibility.
    """
    json_str = json.dumps(data, default=str)  # default=str handles datetime objects
    return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")


def deserialize_data(encoded_data: str) -> Any:
    """
    Decode base64 and deserialize JSON data back to Python object.
    """
    try:
        json_str = base64.b64decode(encoded_data.encode("utf-8")).decode("utf-8")
        return json.loads(json_str)
    except (json.JSONDecodeError, base64.binascii.Error) as e:
        print(f"Error deserializing data: {e}")
        return None


def cache_response(ttl_hours=24):
    """
    Decorator that caches function responses in DynamoDB with TTL.

    Args:
        ttl_hours (int): Number of hours before the cache entry expires
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Create a more robust cache key
                cache_key = serialize_data(
                    {"func": func.__name__, "args": args, "kwargs": kwargs}
                )[
                    :1024
                ]  # DynamoDB has a 2048 byte limit for primary keys

                # Get current time and calculate expiration
                current_time = int(time.time())
                expiration_time = current_time + (ttl_hours * 3600)

                # Try to get from cache
                try:
                    response = cache_table.get_item(Key={"cache_key": cache_key})
                except Exception as e:
                    print(f"Error accessing cache: {e}")
                    # On cache error, just execute the function
                    return func(*args, **kwargs)

                # Check if item exists and hasn't expired
                if "Item" in response:
                    item = response["Item"]
                    if "TTL" not in item or item["TTL"] > current_time:
                        cached_data = deserialize_data(item["data"])
                        if cached_data is not None:
                            return cached_data

                # If we get here, either item doesn't exist, has expired, or couldn't be deserialized
                data = func(*args, **kwargs)

                # Serialize and store in cache
                serialized_data = serialize_data(data)
                cache_table.put_item(
                    Item={
                        "cache_key": cache_key,
                        "data": serialized_data,
                        "TTL": expiration_time,
                        "cached_at": current_time,
                    }
                )
                return data

            except Exception as e:
                print(f"Cache operation failed: {e}")
                # If anything goes wrong with caching, just return the function result
                return func(*args, **kwargs)

        return wrapper

    return decorator
