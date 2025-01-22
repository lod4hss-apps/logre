import streamlit as st
import time
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from tools.sparql_queries import count_graph_triples, insert, delete
from tools.utils import readable_number, to_snake_case


def __write_endpoint_list() -> None:
    """Write all endpoint URLs that are in session on disk."""

    # Transform the list of objects into a string
    content = ""
    for endpoint in st.session_state['all_endpoints']:
        content += f"{endpoint['name']}: {endpoint['url']}\n"

    # Write the generated string on disk
    file = open('../data/saved_endpoints', 'w')
    file.write(content)
    file.close()


def __delete_endpoint(index) -> None:
    """Delete the specified endpoint (will be deleted from session thanks to the given index)."""

    del st.session_state['all_endpoints'][index]
    __write_endpoint_list()
    st.rerun()


def __change_endpoint(index) -> None:
    """Change the name/URL of a given endpoint."""

    name_key = f"endpoint-config-endpoint-name-{index}"
    url_key = f"endpoint-config-endpoint-url-{index}"

    st.session_state['all_endpoints'][index]['name'] = st.session_state[name_key]
    st.session_state['all_endpoints'][index]['url'] = st.session_state[url_key]
    __write_endpoint_list()


def __delete_graph(graph_uri) -> None:
    """Delete all statements of a given graph"""

    # The delete "where clause" triple
    triple = (graph_uri, '?predicate', '?object')

    delete([triple], graph=graph_uri)
    del st.session_state['all_graphs']
    st.rerun()


##### Modals #####

@st.dialog("Add an endpoint")
def __dialog_add_endpoint():
    """Dialog function to provide a form for the endpoint creation."""

    # Formular
    endpoint_name = st.text_input('Endpoint name ❗️', value="", placeholder="Write an endpoint name")
    endpoint_url = st.text_input('Endpoint URL ❗️', value="", placeholder="Write an endpoint URL")

    st.text("")

    # User commands: name and url are mandatory
    if st.button('Save') and endpoint_name and endpoint_url:

        # Add to the session, write on disk, and rerun the page
        st.session_state['all_endpoints'].append({'name': endpoint_name, 'url': endpoint_url})
        __write_endpoint_list()

        # Finalization: validation message and reload
        st.success('New endpoint added')
        time.sleep(1)
        st.rerun()


@st.dialog('Create a graph')
def __dialog_create_graph():
    """Dialog function to provide a form for the graph creation."""
    
    # Formular
    graph_name = st.text_input('Graph name ❗️', value="", placeholder="Write a graph name")
    graph_comment = st.text_area('Graph comment ❗️', value="", placeholder="Write a graph comment (description)")

    st.text("")

    # User commands: name and comment are mandatory
    if st.button('Save') and graph_name and graph_comment:

        # Generate the graph name and uri
        name = to_snake_case(graph_name)
        graph_uri = 'infocean:' + name

        # Create triples
        triple_name = (graph_uri, 'rdfs:label', f"'{graph_name}'")
        graph_comment = graph_comment.replace('\n', ' ')
        triple_comment = (graph_uri, 'rdfs:comment', f"'{graph_comment}'")       

        # Insert triples
        insert([triple_name, triple_comment], graph=graph_uri)
        # And reset the graphs that are in session, to that, on rerun, they a newly fetched
        del st.session_state['all_graphs']
        
        # Finalization: validation message and reload
        st.success('New graph created.')
        time.sleep(1)
        st.rerun()


##### Session initialization #####

if 'endpoint-config-endpoints-list' not in st.session_state:
    st.session_state['endpoint-config-endpoints-list'] = False
if 'endpoint-config-graph-list' not in st.session_state:
    st.session_state['endpoint-config-graph-list'] = False
if 'endpoint-config-credentials' not in st.session_state:
    st.session_state['endpoint-config-credentials'] = False
if 'endpoint-username' not in st.session_state:
    st.session_state['endpoint-username'] = None
if 'endpoint-password' not in st.session_state:
    st.session_state['endpoint-password'] = None


##### The page #####

init()
menu()

st.title("Endpoint configuration")

st.divider()

## Endpoint Section

col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoints List')

# Button to show/hide endpoint list
if col2.button('Show endpoints'):
    st.session_state['endpoint-config-endpoints-list'] = True

# If endpoint list should be shown
if st.session_state['endpoint-config-endpoints-list']:
    
    # Command to hide again endpoint list
    if col3.button('Hide endpoints'):
        st.session_state['endpoint-config-endpoints-list'] = False
        st.rerun()

    # Display all saved endpoints
    for i, endpoint in enumerate(st.session_state['all_endpoints']):
        col1, col2, col3 = st.columns([6, 12, 1], vertical_alignment='bottom')
        col1.text_input('Name', value=endpoint['name'], key=f"endpoint-config-endpoint-name-{i}", on_change=__change_endpoint, kwargs={'index': i})
        col2.text_input('URL', value=endpoint['url'], key=f"endpoint-config-endpoint-url-{i}", on_change=__change_endpoint, kwargs={'index': i})

        # Button to delete a saved endpoint
        if col3.button(f'🗑️', key=f"endpoint-config-{i}"):
            dialog_confirmation(f"You are about to delete \"{endpoint['name']}\" endpoint.", __delete_endpoint, index=i)

    st.text("")

    # Dialog opener to add a new endpoint
    if st.button('Add another endpoint'):
        __dialog_add_endpoint()


st.divider()

## Graphs Section

col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoint graphs')

# Button to show/hide graph list
if col2.button('Show graphs'):
    st.session_state['endpoint-config-graph-list'] = True

# If endpoint list should be shown
if st.session_state['endpoint-config-graph-list']:

    # In case the user did not yet choose an endpoint
    if 'endpoint' not in st.session_state:
        st.warning('Please select an endpoint first')
    else:
    
        # Command to hide again graph list
        if col3.button('Hide graphs'):
            st.session_state['endpoint-config-graph-list'] = False
            st.rerun()

        st.text("")

        # Display all saved endpoints
        for i, graph in enumerate(st.session_state['all_graphs']):
            col1, col2, col3, col4 = st.columns([3, 2, 5, 2], vertical_alignment='bottom')
            col1.markdown(graph['label'])
            col2.markdown(f"{readable_number(count_graph_triples(graph['uri']))} triples")
            col3.markdown(graph['comment'])

            # Button to cleanse a graph
            if col4.button('🗑️', key=f"endpoint-config-graph-{i}"):
                dialog_confirmation(f'You are about to delete the graph "{graph["label"]}".', __delete_graph, graph_uri=graph['uri'])

        st.text("")

        # Dialog opener to create a new graph
        if st.button('Create a graph'):
            __dialog_create_graph()


st.divider()

## Credential sections

col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoint Credentials')

# Button to show/hide graph list
if col2.button('Show credentials'):
    st.session_state['endpoint-config-credentials'] = True

# If endpoint list should be shown
if st.session_state['endpoint-config-credentials']:

    # In case the user did not yet choose an endpoint
    if 'endpoint' not in st.session_state:
        st.warning('Please select an endpoint first')
    else:
    
        # Command to hide again credentials
        if col3.button('Hide credentials'):
            st.session_state['endpoint-config-credentials'] = False
            st.rerun()
        
        # User inputs
        col1, col2, col3 = st.columns([6, 12, 1], vertical_alignment='bottom')
        username = col1.text_input('Username', placeholder='Endpoint username', value=st.session_state['endpoint-username'])
        password = col2.text_input('Password', placeholder='Endpoint password', value=st.session_state['endpoint-password'], type='password')

        # Session attribution
        if username:
            st.session_state['endpoint-username'] = username
        if password:
            st.session_state['endpoint-password'] = password
