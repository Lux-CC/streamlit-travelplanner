import streamlit as st

st.title("Travel Planner")

st.text_area(
    "What do you (dis)-like to do while travelling?",
    key="likes",
    help="Enter your general travel preferences, likes and dislikes",
    placeholder="Example: I enjoy hiking and local cuisine, but dislike crowded tourist attractions",
    height=150,
)

st.text_area(
    "What would you like to do on your next trip?",
    key="now",
    help="Consider your current mood, energy level, weather preferences, etc.",
    placeholder="Example: Looking for a warm beach destination as it's cold here, feeling adventurous",
    height=150,
)
