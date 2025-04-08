import streamlit as st


def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link("streamlit_app.py", label="Home")
    if st.session_state.role in ["authenticated-user"]:
        st.sidebar.page_link("pages/world_view.py", label="World view")
        st.sidebar.page_link("pages/test_geopage.py", label="Test geopage")
        st.sidebar.page_link("pages/user_preferences.py", label="User preferences")
        st.sidebar.page_link("pages/world_brainstorm.py", label="World brainstorm")
        st.sidebar.page_link(
            "pages/city_planning.py",
            label="City Planning",
            # disabled=st.session_state.role != "authenticated-user", # optinally add disabled menu items for certain roles
        )


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("streamlit_app.py", label="Log in!")


def homepage_menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "role" not in st.session_state or st.session_state.role is None:
        unauthenticated_menu()
        return
    authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page("streamlit_app.py")
    homepage_menu()
