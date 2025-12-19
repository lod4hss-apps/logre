import streamlit as st
from requests.exceptions import HTTPError, ConnectionError
from lib import state
from lib.errors import get_HTTP_ERROR_message
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

        def trigger_entity_action(action: str) -> None:
            state.set_pending_entity_action(action)  # type: ignore[arg-type]
            st.switch_page("pages/entity-card.py")

        # Sidebar title
        with st.sidebar.container(horizontal=True, vertical_alignment='bottom'):
            st.markdown(f"# Logre", width='content')
            st.markdown(f"<small>v{version}</small>", unsafe_allow_html=True, width='content')

        st.sidebar.write('')

        # Overview landing page
        st.sidebar.page_link("pages/dashboard.py", label="Overview")
        st.sidebar.divider()

        st.sidebar.markdown("#### Entity")
        st.sidebar.page_link("pages/entity-card.py", label="Entity card")
        entity_actions = st.sidebar.container()
        model_ready = bool(data_bundle and data_bundle.has_model_definitions())
        disabled_help = "Import a SHACL model to enable this action." if data_bundle and not model_ready else None
        with entity_actions:
            find_clicked = st.button(
                'Find entity',
                icon=':material/search:',
                type='secondary',
                use_container_width=True,
                disabled=not model_ready,
                help=disabled_help or help_text("dashboard.find_entity"),
                key='sidebar-find-entity'
            )
            if find_clicked:
                trigger_entity_action('find')

            create_clicked = st.button(
                'Create entity',
                icon=':material/line_start_circle:',
                type='secondary',
                use_container_width=True,
                disabled=not model_ready,
                help=disabled_help or help_text("dashboard.create_entity"),
                key='sidebar-create-entity'
            )
            if create_clicked:
                trigger_entity_action('create')
            if data_bundle and not model_ready:
                st.caption("Import a SHACL model to enable entity actions.")

        st.sidebar.divider()

        # Page links
        st.sidebar.markdown("#### Data exploration")
        st.sidebar.page_link("pages/data-table.py", label="Data Table")
        st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL Editor")

        st.sidebar.divider()

        st.sidebar.markdown("#### Configuration & support")
        st.sidebar.page_link("pages/configuration.py", label="Configuration")
        st.sidebar.page_link("pages/documentation.py", label="Documentation (FAQ)")

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
                state.set_query_params(['endpoint', 'db', 'uri'])
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
                    state.set_query_params(['endpoint', 'db', 'uri'])
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
