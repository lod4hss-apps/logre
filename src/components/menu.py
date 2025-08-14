import streamlit as st

# Local imports
import lib.state as state
from lib.configuration import load_config
from dialogs import dialog_find_entity, dialog_entity_form


def menu() -> None:
    """Logre sidebar."""

    # Fetch variables from State
    version = state.get_version()
    all_endpoints = state.get_endpoints()
    endpoint = state.get_endpoint()

    # Sidebar title
    col1, col2 = st.sidebar.columns([2, 1], vertical_alignment='bottom')
    col1.markdown(f"# Logre")
    col2.markdown(f"<small>v{version}</small>", unsafe_allow_html=True)

    # Page links
    st.sidebar.page_link("pages/documentation.py", label="Documentation")
    st.sidebar.page_link("pages/configuration.py", label="Configuration")
    st.sidebar.page_link("pages/import-export.py", label="Import and Export", disabled=not endpoint)
    st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL editor", disabled=not endpoint)
    st.sidebar.page_link("pages/data-tables.py", label="Data tables", disabled=not endpoint)

    st.sidebar.divider()


    ##### SET CONFIGURATION #####

    # If there is not configuration, allow user to upload a yaml file
    if not state.get_has_config():
        
        # TOML file uploader
        config_file = st.sidebar.file_uploader('Set a configuration:', 'yaml', accept_multiple_files=False)

        # On file upload, load its content to state
        if config_file:
            file_content = config_file.getvalue().decode("utf-8")
            load_config(file_content)
            st.rerun()


    ##### ENDPOINT SELECTION #####
    
    # Or display the endpoint select box
    else:

        # List of all endpoint labels
        endpoint_labels = list(map(lambda endpoint: endpoint.name, all_endpoints))

        # Find the index of the current selected endpoint (if any)
        if endpoint: selected_index = endpoint_labels.index(endpoint.name)
        else: selected_index = None

        # Endpoint selection
        endpoint_label = st.sidebar.selectbox(label='Endpoint', options=endpoint_labels, index=selected_index, placeholder="No Endpoint selected")

        # If an endpoint is selected...
        if endpoint_label:

            # ...that is different that the one in session
            if not endpoint or endpoint_label != endpoint.name:
                
                # Get the right endpoint instance from session, and update selected one
                endpoint = next((e for e in all_endpoints if e.name == endpoint_label), None)
                state.set_endpoint(endpoint)

                # When a new endpoint is selected, the cache need to be cleansed
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
                

            ##### DATA BUNDLE SELECTION #####

            # Fetch the one in session (if any)
            data_bundle = state.get_data_bundle()

            # If none is selected, by default, select the first
            if not data_bundle and len(endpoint.data_bundles): 
                data_bundle = endpoint.data_bundles[0]
                state.set_data_bundle(data_bundle)

            st.sidebar.text('')

            # Get all data bundles names
            data_bundles_labels = [s.name for s in endpoint.data_bundles]

            # Manage the data bundle selection
            if len(endpoint.data_bundles):
                data_bundles_label = st.sidebar.radio(
                    label='Working Data Bundle', 
                    options=data_bundles_labels, 
                    index=endpoint.data_bundles.index(data_bundle), 
                    key='radio-btn-data_bundle-selection', 
                )
                state.set_data_bundle([d for d in endpoint.data_bundles if d.name == data_bundles_label][0])
            else:
                st.sidebar.markdown("*⚠️ No Data Bundle. Add one in your endpoint configuration.*")

            st.sidebar.divider()


            ##### DATA BUNDLE COMMANDS #####
            if data_bundle:
                st.sidebar.button('Find entity', icon=':material/search:', on_click=dialog_find_entity)
                st.sidebar.button('Create an entity', icon=':material/line_start_circle:', on_click=dialog_entity_form)