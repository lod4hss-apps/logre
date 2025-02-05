import streamlit as st
from lib.sparql_queries import list_graphs
from lib.utils import load_config


def menu() -> None:
    """Component function: the sidebar"""

    col1, col2 = st.sidebar.columns([2, 1], vertical_alignment='bottom')
    col1.markdown(f"# Logre")
    col2.markdown(f"<small>v{st.session_state['VERSION']}</small>", unsafe_allow_html=True)

    st.sidebar.page_link("pages/home.py", label="Home")
    st.sidebar.page_link("pages/getting-started.py", label="Getting started")
    st.sidebar.page_link("pages/configuration.py", label="Configuration")
    st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL editor", disabled=not st.session_state['configuration'])
    st.sidebar.page_link("pages/explore.py", label="Explore", disabled=not st.session_state['configuration'])
    st.sidebar.page_link("pages/import-data.py", label="Import data", disabled=not st.session_state['configuration'])

    st.sidebar.divider()

    # Allow to set a configuration
    if not st.session_state['configuration']:
        config_file = st.sidebar.file_uploader('Set a configuration:', 'toml', accept_multiple_files=False)

        if config_file:
            load_config(config_file.getvalue().decode("utf-8"))
            st.rerun()

    else:

        ### Endpoint Selection part ###

        # Display endpoints, and allow user to choose which one he wants
        endpoint_labels = list(map(lambda endpoint: endpoint['name'], st.session_state['all_endpoints']))

        # If an endpoint is already selected, find it, otherwise just init to Nothing
        if 'endpoint' in st.session_state:
            selected_index = endpoint_labels.index(st.session_state['endpoint']['name'])
        else:
            selected_index = None

        # In session endpoint selection
        selected_label = st.sidebar.selectbox('Selected endpoint', endpoint_labels, index=selected_index, placeholder="None selected")

        # If there is a selected endpoint, 
        if selected_label:

            # That is different that the one in session
            if 'endpoint' not in st.session_state or selected_label != st.session_state['endpoint']['name']:
                selected_endpoint = [endpoint for endpoint in st.session_state['all_endpoints'] if endpoint['name'] == selected_label][0]

                # Update the one in session (or set)
                st.session_state['endpoint'] = selected_endpoint

                # When a new endpoint is selected, all graphs needs to be cleansed.
                if 'all_graphs' in st.session_state:
                    del st.session_state['all_graphs']

                # Clear the cache
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()

            # Fetch all graphs from the endpoint, and add the default one (at first position)
            if "all_graphs" not in st.session_state:

                # Manually add Default graph
                st.session_state["all_graphs"] = [{
                    'uri': None,
                    'label': 'Default',
                    'comment': "No comment",
                    'activated': True
                }]

                # Fetch and add other graphs
                graphs = list_graphs(st.sidebar)
                for i, graph in enumerate(graphs):
                    st.session_state["all_graphs"].append({
                        'uri': graph['uri'],
                        'label': graph['label'],
                        'comment': graph['comment'],
                        'activated': False
                    })

            # Allow user to activate/deactivate a graph
            st.sidebar.markdown('#### Endpoint graph List:')
            for i, graph in enumerate(st.session_state["all_graphs"]):
                # Make the session match the GUI
                if st.sidebar.checkbox(graph['label'], value=graph['activated'], key=f'graph-checkbox-{i}'):
                    if st.session_state['all_graphs'][i]['activated'] != True:
                        st.session_state['all_graphs'][i]['activated'] = True
                        st.rerun()
                else:
                    if st.session_state['all_graphs'][i]['activated'] != False:
                        st.session_state['all_graphs'][i]['activated'] = False
                        st.rerun()