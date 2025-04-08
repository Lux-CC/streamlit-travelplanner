import streamlit as st

st.title("Travel Planner")

# placeholder to brainstorm ideas together, which contains data, text, images etc.
st.text_area(
    "Enter your travel plans",
    value="I want to visit Paris, Berlin and Rome. I like to visit museums and eat good food.",
    height=150,
    help="Make sure it mentions cities and countries you want to visit",
)
