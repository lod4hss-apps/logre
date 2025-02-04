import streamlit as st
import time, toml
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from lib.sparql_queries import count_graph_triples, insert, delete
from lib.utils import readable_number, to_snake_case


# Contants
technologies = ['Fuseki', 'Allegrograph']
model_langs = ['SHACL']


def __prepare_configuration():
    """Build the configuration object and transform it into a toml string, ready to be downloaded."""

    config = {
        'all_queries': st.session_state['all_queries'],
        'all_endpoints': st.session_state['all_endpoints']
    }

    return toml.dumps(config)


def __delete_endpoint(index) -> None:
    """Delete the specified endpoint (will be deleted from session thanks to the given index)."""
    
    del st.session_state['all_endpoints'][index]
    st.rerun()


def __delete_graph(graph_uri) -> None:
    """Delete all statements of a given graph"""

    # The delete "where clause" triple
    triple = ('?subject', '?predicate', '?object')

    delete([triple], graph=graph_uri)
    del st.session_state['all_graphs']
    st.rerun()


##### Modals #####

@st.dialog("Add an endpoint")
def __dialog_endpoint(endpoint=None, index=None):
    """Dialog function to provide a form for the endpoint creation."""

    # Values
    name = endpoint['name'] if endpoint else ""
    url = endpoint['url'] if endpoint else ""
    technology = technologies.index(endpoint['technology']) if endpoint else 0
    base_uri = endpoint['base_uri'] if endpoint else "http://www.example.org/"
    model_uri = endpoint['model_uri'] if endpoint else "base:default"
    model_lang = model_langs.index(endpoint['model_lang']) if endpoint else 0
    username = endpoint['username'] if endpoint else ""
    password = endpoint['password'] if endpoint else ""

    # Formular
    endpoint_name = st.text_input('Endpoint name ❗️', value=name, placeholder="Write an endpoint name")
    endpoint_url = st.text_input('Endpoint URL ❗️', value=url, placeholder="Write an endpoint URL")
    endpoint_technology = st.selectbox('Technology ❗️', options=technologies, index=technology, placeholder="Select a technology")
    endpoint_base_uri = st.text_input('Endpoint base URI ❗️', value=base_uri, help="This is the base URI that will be given to new nodes in the endpoint (plus a UUID).")
    endpoint_model_uri = st.text_input('Select the graph in which the ontologycal model lies ❗️', value=model_uri, help="This should be the URI (or shortcut) of the graph containing the ontologycal model.")
    endpoint_model_lang = st.selectbox('Select the model language ❗️', options=model_langs, index=model_lang)
    endpoint_username = st.text_input('Username', value=username, placeholder="Write a username for this endpoint")
    endpoint_password = st.text_input('Password', value=password, placeholder="Write a password for this endpoint", type='password')

    st.text("")

    # User commands: name and url are mandatory
    if st.button('Save') and endpoint_name and endpoint_url and endpoint_technology and endpoint_base_uri and endpoint_model_uri and endpoint_model_lang:
        
        new_endpoint = {
            'name': endpoint_name,
            'url': endpoint_url,
            'technology': endpoint_technology,
            'base_uri': endpoint_base_uri,
            'model_uri': endpoint_model_uri,
            'model_lang': endpoint_model_lang,
            'username': endpoint_username,
            'password': endpoint_password,
        }

        if endpoint:
            st.session_state['all_endpoints'][index] = new_endpoint
        else:
            st.session_state['all_endpoints'].append(new_endpoint)

        st.session_state['configuration'] = True
        if 'endpoint' in st.session_state:
            del st.session_state['endpoint']
        
        # Finalization: validation message and reload
        st.success('Endpoint saved')
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
        graph_uri = 'base:' + name

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

if 'config-endpoints-list' not in st.session_state:
    st.session_state['config-endpoints-list'] = False
if 'config-graph-list' not in st.session_state:
    st.session_state['config-graph-list'] = False
if 'config-credentials' not in st.session_state:
    st.session_state['config-credentials'] = False
if 'endpoint-username' not in st.session_state:
    st.session_state['endpoint-username'] = None
if 'endpoint-password' not in st.session_state:
    st.session_state['endpoint-password'] = None


##### The page #####

init()
menu()


col1, col2 = st.columns([6, 2], vertical_alignment='center')
col1.title("Endpoint configuration")
if st.session_state['configuration']:
    col2.download_button('Download', data=__prepare_configuration(), file_name='logre-config.toml')

st.divider()

## Endpoint Section

col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoints List')
st.text("")

# Button to show/hide endpoint list
if col2.button('Show endpoints'):
    st.session_state['config-endpoints-list'] = True

# If endpoint list should be shown
if st.session_state['config-endpoints-list']:
    
    # Command to hide again endpoint list
    if col3.button('Hide endpoints'):
        st.session_state['config-endpoints-list'] = False
        st.rerun()

    # Display all saved endpoints
    for i, endpoint in enumerate(st.session_state['all_endpoints']):
        col1, col2 = st.columns([6, 13], vertical_alignment='center')
        col1.text_input('Name', value=endpoint['name'], key=f"config-endpoint-name-{i}", disabled=True)
        col2.text_input('URL', value=endpoint['url'], key=f"config-endpoint-url-{i}", disabled=True)
        col1, col2, col3 = st.columns([6, 6, 7], vertical_alignment='center')
        col1.text_input('Username', value=endpoint['username'], key=f"config-endpoint-username-{i}", disabled=True)
        col2.text_input('Password', value=endpoint['password'], key=f"config-endpoint-password-{i}", type='password', disabled=True)
        col3.selectbox('Endpoint technology', technologies, index=technologies.index(endpoint['technology']), key=f"config-endpoint-technology-{i}", disabled=True)

        col1, col2, col3 = st.columns([8, 5, 5], vertical_alignment='center')
        col1.text_input('Base URI', value=endpoint['base_uri'], key=f"config-endpoint-base-uri-{i}", disabled=True)
        col2.text_input('Model URI', value=endpoint['model_uri'], key=f"config-endpoint-model-uri-{i}", disabled=True)
        col3.text_input('Model language', value=endpoint['model_lang'], key=f"config-endpoint-model-lang-{i}", disabled=True)

        st.text('')
        col1, col2, col3 = st.columns([3, 3, 2])

        # Button to delete an endpoint
        if col1.button(f'Forget this endpoint', key=f"config-endpoint-delete-{i}"):
            dialog_confirmation(f"You are about to delete \"{endpoint['name']}\" endpoint.", __delete_endpoint, index=i)

        # Button to edit an endpoint
        if col2.button(f'Edit this endpoint', key=f"config-endpoint-edit-{i}"):
            __dialog_endpoint(endpoint, i)

        # Divider between endpoints
        col1, col2, col3 = st.columns([3, 7, 3], vertical_alignment='center')
        col2.divider()

    st.text("")

    # Dialog opener to add a new endpoint
    if st.button('Add another endpoint'):
        __dialog_endpoint()


st.divider()

## Graphs Section

if 'endpoint' in st.session_state:


    col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
    col1.markdown('### Endpoint graphs')

    # Button to show/hide graph list
    if col2.button('Show graphs'):
        st.session_state['config-graph-list'] = True

    # If endpoint list should be shown
    if st.session_state['config-graph-list']:

        # In case the user did not yet choose an endpoint
        if 'endpoint' not in st.session_state:
            st.warning('Please select an endpoint first')
        else:
        
            # Command to hide again graph list
            if col3.button('Hide graphs'):
                st.session_state['config-graph-list'] = False
                st.rerun()

            st.text("")

            # Display all saved endpoints
            for i, graph in enumerate(st.session_state['all_graphs']):
                col1, col2, col3, col4 = st.columns([3, 2, 5, 2], vertical_alignment='bottom')
                col1.markdown(graph['label'])
                col2.markdown(f"{readable_number(count_graph_triples(graph['uri']))} triples")
                col3.markdown(graph['comment'])

                # Button to cleanse a graph
                if col4.button('🗑️', key=f"config-graph-{i}"):
                    dialog_confirmation(f'You are about to delete the graph "{graph["label"]}".', __delete_graph, graph_uri=graph['uri'])

            st.text("")

            # Dialog opener to create a new graph
            if st.button('Create a graph'):
                __dialog_create_graph()


    st.divider()