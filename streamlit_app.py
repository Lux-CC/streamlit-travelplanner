from password import check_password
import streamlit as st
from menu import homepage_menu
from streamlit_cookies_controller import CookieController

controller = CookieController('homepage')

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Initialize st.session_state.role to None
if "role" not in st.session_state:
    st.session_state.role = None

# Retrieve the role from Session State to initialize the widget
st.session_state._role = st.session_state.role

homepage_menu() # Render the dynamic homepage menu!

# add a logout button
if st.button("Logout"):
    controller.delete("PasswordHash")
    st.session_state.role = None
    st.rerun()