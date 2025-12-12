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

        st.sidebar.divider()

        endpoint_groups = state.get_endpoint_groups()
        endpoint_key = state.get_endpoint_key()

        if not endpoint_groups:
            st.sidebar.info("Configure an endpoint and at least one Data Bundle to start.", icon=":material/info:")
        else:
            endpoint_labels = [group['label'] for group in endpoint_groups]
            endpoint_index = 0
            if endpoint_key:
                endpoint_index = next((i for i, group in enumerate(endpoint_groups) if group['key'] == endpoint_key), 0)

            selected_endpoint_label = st.sidebar.selectbox(
                label='Endpoint',
                options=endpoint_labels,
                index=endpoint_index,
                key='sidebar-endpoint-select'
            )
            selected_endpoint = endpoint_groups[endpoint_labels.index(selected_endpoint_label)]
            if endpoint_key != selected_endpoint['key']:
                state.set_endpoint_key(selected_endpoint['key'])
                st.rerun()

            bundles = selected_endpoint['data_bundles']
            if bundles:
                bundle_labels = [db.name for db in bundles]
                current_bundle = state.get_data_bundle()
                if current_bundle and current_bundle in bundles:
                    bundle_index = bundles.index(current_bundle)
                else:
                    bundle_index = 0

                selected_bundle_label = st.sidebar.radio(
                    label='Working Data Bundle',
                    options=bundle_labels,
                    index=bundle_index,
                    key='sidebar-data-bundle'
                )
                selected_bundle = bundles[bundle_labels.index(selected_bundle_label)]
                if current_bundle != selected_bundle:
                    state.set_data_bundle(selected_bundle)
                    st.rerun()
            else:
                st.sidebar.warning("No Data Bundle configured for this endpoint.", icon=":material/info:")

    except HTTPError as err:
        message = get_HTTP_ERROR_message(err)
        st.error(message)
        print(message.replace('\n\n', '\n'))
    
    except ConnectionError as err:
        st.error('Failed to connect to server: check your internet connection and/or server status.')
        print('[CONNECTION ERROR]')
