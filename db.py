import streamlit as st
from streamlit_cookies_controller import CookieController, 
import config_vars


controller = CookieController('db')


def update_app_data(key: str, object):
    if "AppUserData" not in st.session_state:
        init_app_data()

    st.session_state["AppUserData"][key] = object
    persist_app_data()


def persist_app_data():
    controller.set(
        "AppUserData",
        st.session_state["AppUserData"],
        path="/",
        domain=config_vars.DOMAIN,
    )


def init_app_data():
    st.session_state["AppUserData"] = controller.get("AppUserData", {})
