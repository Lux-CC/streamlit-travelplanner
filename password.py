import hmac
import streamlit as st
from streamlit_cookies_controller import CookieController
import itertools as it

controller = CookieController()

def check_password():
    """Returns `True` if the user had the correct password."""
    def check_cookie():
        controller.getAll()
        if controller.get("PasswordHash") is None:
            pass
        else:
            # check if the cookie is valid
            encryption_key = st.secrets["encryption_key"]
            password = st.secrets["password"]
            correct_value = hmac.new(encryption_key.encode(), password.encode(), digestmod="sha256").hexdigest()
            if controller.get("PasswordHash") == correct_value:
                st.session_state["password_correct"] = True
            else:
                controller.delete("PasswordHash")
        
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            encryption_key = st.secrets["encryption_key"]
            encrypted_password = hmac.new(encryption_key.encode(), st.session_state["password"].encode(), digestmod="sha256").hexdigest()
            controller.set("PasswordHash", encrypted_password, path='/', domain="world-travelplanner.streamlit.app")
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    check_cookie()
    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        st.session_state.role = "authenticated-user"
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


