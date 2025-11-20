import streamlit as st
from requests.exceptions import HTTPError, ConnectionError
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.find_entity import dialog_find_entity
from dialogs.entity_creation import dialog_entity_creation
from components.help import help_text


def menu() -> None:
    """
    Builds and renders the Streamlit sidebar menu for the application.

    Features:
        - Displays the application title and version.
        - Provides navigation links to the various application pages.
        - Displays data bundle-related commands (e.g., Find entity, Create entity) when a bundle is selected.

    Returns:
        None
    """
    try:
        # From state
        version = state.get_version()
        data_bundle = state.get_data_bundle()

        # Sidebar title
        with st.sidebar.container(horizontal=True, vertical_alignment='bottom'):
            st.markdown(f"# Logre", width='content')
            st.markdown(f"<small>v{version}</small>", unsafe_allow_html=True, width='content')

        # Page links
        nav_sections = [
            (None, [("pages/dashboard.py", "Dashboard")]),
            ("Data exploration", [
                ("pages/data-table.py", "Data Table"),
                ("pages/entity-card.py", "Entity"),
                ("pages/sparql-editor.py", "SPARQL Editor"),
            ]),
            ("Configuration & support", [
                ("pages/configuration.py", "Configuration"),
                ("pages/documentation.py", "Documentation (FAQ)"),
            ])
        ]

        for section_title, links in nav_sections:
            if section_title:
                st.sidebar.markdown(f"#### {section_title}")
            for target, label in links:
                st.sidebar.page_link(target, label=label)

    except HTTPError as err:
        message = get_HTTP_ERROR_message(err)
        st.error(message)
        print(message.replace('\n\n', '\n'))
    
    except ConnectionError as err:
        st.error('Failed to connect to server: check your internet connection and/or server status.')
        print('[CONNECTION ERROR]')
