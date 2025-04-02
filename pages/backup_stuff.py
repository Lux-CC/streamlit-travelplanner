import streamlit as st
from menu import menu_with_redirect

# Redirect to streamlit_app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()


# display static/cat.jpg using streamlit
st.image("static/cat.jpg", caption="Cat", width=400)
