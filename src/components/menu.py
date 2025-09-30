import streamlit as st
from requests.exceptions import HTTPError, ConnectionError
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.find_entity import dialog_find_entity
from dialogs.entity_creation import dialog_entity_creation


def menu() -> None:
    """
    Builds and renders the Streamlit sidebar menu for the application.

    Features:
        - Displays the application title and version.
        - Provides navigation links to different pages (Configuration, SPARQL Editor, Import/Export, Entity, Data Table).
        - Allows selection of a data bundle from the available options.
        - Updates the selected data bundle in the application state.
        - Displays data bundle-related commands (e.g., Find entity, Create entity) when a bundle is selected.

    Returns:
        None
    """
    try:
        # From state
        version = state.get_version()
        data_bundles = state.get_data_bundles()
        data_bundle = state.get_data_bundle()

        # Sidebar title
        with st.sidebar.container(horizontal=True, vertical_alignment='bottom'):
            st.markdown(f"# Logre", width='content')
            st.markdown(f"<small>v{version}</small>", unsafe_allow_html=True, width='content')

        # Page links
        st.sidebar.page_link("pages/documentation.py", label="Documentation (FAQ)")
        st.sidebar.page_link("pages/configuration.py", label="Configuration")
        st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL Editor")
        st.sidebar.page_link("pages/import-export.py", label="Import, Export")
        st.sidebar.page_link("pages/entity.py", label="Entity")
        st.sidebar.page_link("pages/data-table.py", label="Data Table")

        st.sidebar.divider()
        
        # Data bundle selection
        db_names = [db.name for db in data_bundles]
        db_index = db_names.index(data_bundle.name) if data_bundle else None
        db_selected_name = st.sidebar.selectbox(label="Data Bundle", options=db_names, index=db_index, placeholder="None selected", help="[What are data bundles?](/documentation#what-are-data-bundles)")

        # Put Data Bundle in state only if not yet the case
        if db_selected_name and ((data_bundle and db_selected_name != data_bundle.name) or not data_bundle):
            db_selected_index = db_names.index(db_selected_name)
            db_selected = data_bundles[db_selected_index]
            state.set_data_bundle(db_selected)
            data_bundle = db_selected

        st.sidebar.divider()

        # Data bundle commands
        if data_bundle:
            with st.sidebar.container(horizontal=False, horizontal_alignment= 'center', vertical_alignment='bottom', height='stretch'):
                if st.button('Find entity', icon=':material/search:', type='primary', width='stretch', help="[How to see my data?](/documentation#how-to-see-my-data)"):
                    dialog_find_entity()
                if st.button('Create entity', icon=':material/line_start_circle:', type='primary', width='stretch', help="[How to create my data?](/documentation#how-to-create-new-data)"):
                    dialog_entity_creation()

    except HTTPError as err:
        message = get_HTTP_ERROR_message(err)
        st.error(message)
        print(message.replace('\n\n', '\n'))
    
    except ConnectionError as err:
        st.error('Failed to connect to server: check your internet connection and/or server status.')
        print('[CONNECTION ERROR]')