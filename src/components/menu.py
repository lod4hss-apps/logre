import streamlit as st


def menu() -> None:
    """Component function: the sidebar."""

    st.sidebar.page_link("pages/home.py", label="Presentation")
    st.sidebar.page_link("pages/endpoint-config.py", label="Endpoint configuration")
    st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL editor")


    if 'endpoint' in st.session_state:
        st.sidebar.divider()
        st.sidebar.markdown(f"### Endpoint:")
        st.sidebar.markdown(f"***{st.session_state['endpoint']['name']}***")