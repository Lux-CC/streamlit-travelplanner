# pages/01_Geo_Resolver_Test.py
import streamlit as st
from lib.geo_resolver import resolve_geo_query
from menu import menu_with_redirect


st.title("Geo Resolver Test")
query = st.text_input("Enter a place (e.g. 'Hue, Vietnam')")
menu_with_redirect()
if query:
    result = resolve_geo_query(query)
    if result:
        st.success("Location found:")
        st.json(result)
    else:
        st.error("Could not resolve location.")
