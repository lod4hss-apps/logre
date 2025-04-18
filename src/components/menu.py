import streamlit as st
from schema import Graph, Entity
from lib.sparql_queries import list_graphs
from lib.configuration import load_config
from lib.prefixes import explicits_uri, shorten_uri
import lib.state as state
from components.dialog_find_entity import dialog_find_entity
from components.dialog_create_entity import dialog_create_entity
from components.dialog_create_triple import dialog_create_triple


def __on_graph_selection():
    """Callback function for the graph selection"""

    # Fetch variables from State
    all_graphs = state.get_graphs()
    
    # Compute all graph labels, and fetch radio button value
    graphs_labels = [g.label for g in all_graphs]
    graph_label = state.get_element('radio-btn-graph-selection')

    # Find the selected graph, and set the session variable
    index = graphs_labels.index(graph_label)
    state.set_graph_index(index)

    # Also, because entities can have different information in different graph, reload the entity
    state.set_reload_entity(True)


def menu() -> None:
    """Component function: the sidebar"""

    # Fetch variables from State
    version = state.get_version()
    all_endpoints = state.get_endpoints()
    endpoint = state.get_endpoint()
    all_graphs = state.get_graphs()

    # Sidebar title
    col1, col2 = st.sidebar.columns([2, 1], vertical_alignment='bottom')
    col1.markdown(f"# Logre")
    col2.markdown(f"<small>v{version}</small>", unsafe_allow_html=True)

    # Page links◊
    st.sidebar.page_link("pages/documentation.py", label="Documentation")
    st.sidebar.page_link("pages/configuration.py", label="Configuration")
    st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL editor", disabled=not endpoint)
    st.sidebar.page_link("pages/import.py", label="Import", disabled=not endpoint)
    st.sidebar.page_link("pages/data-tables.py", label="Data tables", disabled=not endpoint)
    # st.sidebar.page_link("pages/entity.py", label="Entity", disabled=not all_endpoints)

    st.sidebar.divider()


    ##### SET CONFIGURATION #####

    # If there is not configuration, allow user to upload a toml file
    if not all_endpoints:
        
        # TOML file uploader
        config_file = st.sidebar.file_uploader('Set a configuration:', 'toml', accept_multiple_files=False)

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
        endpoint_label = st.sidebar.selectbox(
            label='Selected endpoint', 
            options=endpoint_labels, 
            index=selected_index, 
            placeholder="No Endpoint selected"
        )

        # If there is a selected endpoint, 
        if endpoint_label:

            # That is different that the one in session
            if not endpoint or endpoint_label != endpoint.name:
                
                # Get the right endpoint instance from session, and update selected one
                endpoint = next((e for e in all_endpoints if e.name == endpoint_label), None)
                state.set_endpoint(endpoint)
                
                # When a new endpoint is selected, all graphs needs to be cleansed
                state.clear_graphs()

                # When a new endpoint is selected, the cache need to be cleansed
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
                

            ##### GRAPH SELECTION #####

            # If the graphs are not yet loaded, fetch them, add the default one and set current graphs to default
            if not all_graphs:
                default_graph = Graph(label="Default", comment="Endpoint default graph")
                other_graphs = list_graphs()
                all_graphs = [default_graph] + other_graphs
                state.set_graphs(all_graphs)
                state.set_graph_index(0) # Because default graph is at position 0

            # But, if there is a query param to select a graph, set it
            graph_uri = state.get_query_param('graph')
            if graph_uri != None:

                # Find and set the right graph
                index = next((i for i, graph in enumerate(all_graphs) if explicits_uri(graph.uri) == graph_uri), 0)
                state.set_graph_index(index)

                # Now entity can also be selected
                graph = state.get_graph()
                entity_uri = state.get_query_param('entity')
                state.set_entity(Entity(uri=shorten_uri(entity_uri)))
                state.set_reload_entity(True)

                # We clear the query param at this point, because we now have all needed information
                state.clear_query_param()

            st.sidebar.text('')

            # Allow user to choose the graph to activate
            graphs_labels = [g.label for g in all_graphs]

            # Manage the graph selection
            st.sidebar.radio(
                label='Selected graph', 
                options=graphs_labels, 
                index=state.get_graph_index(), 
                key='radio-btn-graph-selection', 
                on_change=__on_graph_selection
            )

            st.sidebar.divider()

            ##### GRAPH COMMANDS #####

            st.sidebar.button('Find entity', icon=':material/search:', on_click=dialog_find_entity)
            st.sidebar.button('Create an entity', icon=':material/line_start_circle:', on_click=dialog_create_entity)
            st.sidebar.button('Create a triple', icon=':material/share:', on_click=dialog_create_triple)