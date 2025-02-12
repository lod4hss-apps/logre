import streamlit as st
import time, toml, os
from components.init import init
from components.menu import menu
from components.dialog_confirmation import dialog_confirmation
from lib.sparql_base import insert, delete
from lib.sparql_queries import count_graph_triples
from lib.utils import readable_number, to_snake_case, ensure_uri
from schema import Triple
import lib.state as state
from schema import EndpointTechnology, OntologyFramework, Endpoint
from lib.configuration import save_config
from components.dialog_config_endpoint import dialog_config_endpoint
from components.dialog_config_graph import dialog_config_graph
from lib.configuration import get_config_toml, CONFIG_PATH

# Contants
technologies = [e.value for e in EndpointTechnology]
frameworks = [e.value for e in OntologyFramework]


def __delete_endpoint(endpoint: Endpoint) -> None:
    """Delete the specified endpoint"""

    # Delete endpoint from state
    state.delete_endpoint(endpoint)

    # Save config if local
    if state.get_configuration() == 'local':
        save_config()

    # Close confirmation window and reload the page with new state
    state.set_toast('Endpoint removed', icon=':material/delete:')
    st.rerun()


def __prune_graph(graph: str) -> None:
    """Delete all statements of a given graph"""

    graph_uri = ensure_uri(graph)

    # The delete "where clause" triple: delete all triples from the graph
    triple = Triple('?s', '?p', '?o')
    delete(triple, graph=graph_uri)

    # Also, from the default graph, delete all predicates related to the graph (label, comment, ...)
    triple = Triple(graph_uri, '?p', '?o')
    delete(triple)

    state.clear_graphs()
    state.set_toast('Graph deleted', icon=':material/delete:')
    st.rerun()


def __show_endpoint_list() -> None:
    # Here, because it is only for here and for display information
    # We took the liberty of handling the session_state directly
    st.session_state['display_endpoint_list'] = True


def __hide_endpoint_list() -> None:
    # Here, because it is only for here and for display information
    # We took the liberty of handling the session_state directly
    st.session_state['display_endpoint_list'] = False


def __endpoint_list() -> None:

    # If endpoint list is deactivated, display nothing
    # Here, because it is only for here and for display information
    # We took the liberty of handling the session_state directly
    if 'display_endpoint_list'not in st.session_state or not st.session_state['display_endpoint_list']:
        return

    # Fetch from state
    all_endpoints = state.get_endpoints()

    # Display all saved endpoints
    for i, endpoint in enumerate(all_endpoints):

        # Display all information from the endpoint as disabled inputs
        col1, col2 = st.columns([6, 13], vertical_alignment='center')
        col1.text_input('Name', value=endpoint.name, key=f"config-endpoint-name-{i}", disabled=True)
        col2.text_input('URL', value=endpoint.url, key=f"config-endpoint-url-{i}", disabled=True)
        col1, col2, col3 = st.columns([6, 6, 7], vertical_alignment='center')
        col1.text_input('Username', value=endpoint.username, key=f"config-endpoint-username-{i}", disabled=True)
        col2.text_input('Password', value=endpoint.password, key=f"config-endpoint-password-{i}", type='password', disabled=True)
        col3.selectbox('Endpoint technology', technologies, index=technologies.index(endpoint.technology), key=f"config-endpoint-technology-{i}", disabled=True)
        col1, col2, col3 = st.columns([8, 5, 5], vertical_alignment='center')
        col1.text_input('Base URI', value=endpoint.base_uri, key=f"config-endpoint-base-uri-{i}", disabled=True)
        col2.text_input('Ontology graph URI', value=endpoint.ontology_uri, key=f"config-endpoint-ontology-graph-uri-{i}", disabled=True)
        col3.text_input('Ontology Framework', value=endpoint.ontology_framework, key=f"config-endpoint-ontology-framework-{i}", disabled=True)

        st.text('')
        
        col1, col2, col3 = st.columns([3, 3, 2])

        # Button to delete an endpoint
        if col1.button(f'Remove this endpoint', key=f"config-endpoint-delete-{i}", icon=':material/delete:'):
            dialog_confirmation(f"You are about to delete \"{endpoint.name}\" endpoint.", __delete_endpoint, endpoint=endpoint)

        # Button to edit an endpoint
        if col2.button(f'Edit this endpoint', key=f"config-endpoint-edit-{i}", icon=":material/edit:"):
            dialog_config_endpoint(endpoint, i)

        # Divider between endpoints
        col1, col2, col3 = st.columns([3, 7, 3], vertical_alignment='center')
        col2.divider()


def __show_graph_list() -> None:
    # Here, because it is only for here and for display information
    # We took the liberty of handling the session_state directly
    st.session_state['display_graph_list'] = True


def __hide_graph_list() -> None:
    # Here, because it is only for here and for display information
    # We took the liberty of handling the session_state directly
    st.session_state['display_graph_list'] = False


def __graph_list() -> None:

    # If graph list is deactivated, display nothing
    # Here, because it is only for here and for display information
    # We took the liberty of handling the session_state directly
    if 'display_graph_list'not in st.session_state or not st.session_state['display_graph_list']:
        return

    # Fetch from state
    all_graphs = state.get_graphs()

    # Display all graphs in sessions
    for i, graph in enumerate(all_graphs):
        st.text('')
        col1, col2, col3, col4 = st.columns([3, 2, 5, 4], vertical_alignment='center')
        col1.markdown(graph.label)
        col2.markdown(f"{readable_number(count_graph_triples(graph.uri))} triples")
        col3.markdown(graph.comment)

        # Button to cleanse a graph
        if col4.button('Prune graph', key=f"config-graph-{i}", icon=":material/delete_sweep:", help='From the endpoint, this will remove all triples of this graph, but also information about the graph in others. Resulting in making the graph fully disapear.'):
            dialog_confirmation(f'You are about to delete the graph "{graph.label}" and all its triples.', __prune_graph, graph=graph.uri)


##### The page #####

init()
menu()

# From state
endpoint = state.get_endpoint()


### CONFIGURATION ###

col1, col2 = st.columns([6, 2], vertical_alignment='bottom')
col1.title("Endpoint configuration")
col2.download_button(
    label='Download', 
    data=get_config_toml(), 
    disabled=state.get_configuration() != 'uploaded',
    file_name=CONFIG_PATH,
    help='Download this configuration as a toml file. If Logre is running locally and have a configuration, it will be updated automatically.',
    icon=':material/download:'
)

st.divider()


### ENDPOINTS ###

col1, col2, col3, col4 = st.columns([2, 2, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoints')

st.text("")

col2.button('Show list', on_click=__show_endpoint_list, icon=':material/visibility:', key='config-btn-show-endpoints')
col3.button('Hide list', on_click=__hide_endpoint_list, icon=':material/visibility_off:', key='config-btn-hide-endpoints')
col4.button('Add new', on_click=dialog_config_endpoint, icon=':material/add:', key='config-btn-add-endpoint')

__endpoint_list()

st.divider()


### GRAPHS ###

# Only display graph section if an endpoint is selected:
# can't fetch information from nowhere
if endpoint:

    # Title and boxes for graph actions (show/hide graph list)
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2], vertical_alignment='bottom')
    col1.markdown('### Graphs')

    col2.button('Show list', on_click=__show_graph_list, icon=':material/visibility:', key='config-btn-show-graphs')
    col3.button('Hide list', on_click=__hide_graph_list, icon=':material/visibility_off:', key='config-btn-hide-graphs')
    col4.button('Add new', on_click=dialog_config_graph, icon=':material/add:', key='config-btn-add-graph')

    __graph_list()

    st.divider()