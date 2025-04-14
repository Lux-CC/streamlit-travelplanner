import streamlit as st
import config_vars
import boto3

# add authentication from st.secrets
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
dynamo = boto3.resource(
    "dynamodb",
    region_name="eu-west-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
user_data_table = dynamo.Table("streamlit-worldtravel-user-data")


def update_app_data(key: str, object):
    if "AppUserData" not in st.session_state:
        init_app_data()

    st.session_state["AppUserData"][key] = object
    persist_app_data()
    st.rerun()


def persist_app_data():
    user_id = st.session_state.get("user_id", "Luuk")
    item_id = "AppUserData"
    data = st.session_state["AppUserData"]
    user_data_table.put_item(
        Item={"user_id": user_id, "item_id": item_id, "data": data}
    )
    st.toast("✅ Changes saved!")


def init_app_data():
    user_id = st.session_state.get("user_id", "Luuk")
    item_id = "AppUserData"
    response = user_data_table.get_item(Key={"user_id": user_id, "item_id": item_id})
    if "Item" in response:
        st.session_state["AppUserData"] = response["Item"]["data"]
    else:
        st.session_state["AppUserData"] = {}
