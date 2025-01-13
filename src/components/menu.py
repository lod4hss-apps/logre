import streamlit as st

def menu() -> None:
    """Component function: the sidebar"""

    col1, col2 = st.sidebar.columns([2, 1], vertical_alignment='bottom')
    col1.markdown(f"# Logre")
    col2.markdown(f"<small>v{st.session_state['VERSION']}</small>", unsafe_allow_html=True)

    st.sidebar.page_link("pages/home.py", label="Presentation")
    st.sidebar.page_link("pages/endpoint-config.py", label="Endpoint configuration")
    st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL editor")
    st.sidebar.page_link("pages/explore.py", label="Explore Graph")

    if 'endpoint' in st.session_state:
        st.sidebar.divider()
        st.sidebar.markdown(f"### Endpoint:")
        st.sidebar.markdown(f"***{st.session_state['endpoint']['name']}***")