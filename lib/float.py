import streamlit as st


def inject_sidebar_style():
    st.markdown(
        """
        <style>
        .map-wrapper {
            position: relative;
        }
        .floating-sidebar {
            position: absolute;
            top: 0;
            right: 0;
            width: 400px;
            max-height: 100vh;
            overflow-y: auto;
            padding: 1rem;
            background-color: #ffffffee;
            box-shadow: -4px 0 10px rgba(0,0,0,0.1);
            z-index: 999;
            border-left: 1px solid #ddd;
        }
        .streamlit-container {
            padding-right: 420px; /* avoid overlap when scrolling */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
