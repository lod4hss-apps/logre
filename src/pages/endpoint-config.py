import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from tools.sparql_queries import count_graph_triples, insert, delete
from tools.utils import readable_number, to_snake_case


def write_endpoint_list() -> None:
    """Write all endpoint URLs that are in session memory on disk."""

    # Transform the list of objects into a string
    content = ""
    for endpoint in st.session_state['all_endpoints']:
        content += f"{endpoint['name']}: {endpoint['url']}\n"

    # Write the generated string on disk
    file = open('../data/saved_endpoints', 'w')
    file.write(content)
    file.close()


def delete_endpoint(index) -> None:
    """Delete the specified endpoint."""

    del st.session_state['all_endpoints'][index]
    write_endpoint_list()
    st.rerun()


def change_endpoint(index) -> None:
    """Change the name/URL of a given endpoint"""

    name_key = f"endpoint-config-endpoint-name-{index}"
    url_key = f"endpoint-config-endpoint-url-{index}"

    st.session_state['all_endpoints'][index]['name'] = st.session_state[name_key]
    st.session_state['all_endpoints'][index]['url'] = st.session_state[url_key]
    write_endpoint_list()


def delete_graph(graph_uri) -> None:
    """Delete all statement of a given graph"""

    triple = (graph_uri, '?predicate', '?object')
    delete([triple], graph=graph_uri)
    del st.session_state['all_graphs']
    st.rerun()




##### Modals #####

@st.dialog("Add an endpoint")
def dialog_add_endpoint():
    """Form to add an endpoint"""

    endpoint_name = st.text_input('Endpoint name', value="", placeholder="Write an endpoint name")
    endpoint_url = st.text_input('Endpoint URL', value="", placeholder="Write an endpoint URL")
    st.text("")
    if st.button('Save') and endpoint_name and endpoint_url:
        # Add to the session, write on disk, and rerun the page
        st.session_state['all_endpoints'].append({'name': endpoint_name, 'url': endpoint_url})
        write_endpoint_list()
        st.rerun()


@st.dialog('Create a graph')
def dialog_create_graph():
    """Form to create a graph on the selected endpoint"""

    graph_name = st.text_input('Graph name', value="", placeholder="Write a graph name")
    graph_comment = st.text_area('Graph comment', value="", placeholder="Write a graph comment (description)")
    st.text("")
    if st.button('Save') and graph_name and graph_comment:
        name = to_snake_case(graph_name)
        graph_uri = st.session_state['endpoint']['url'] + '/' + name

        # Create the triples
        triple_name = (graph_uri, 'rdfs:label', f"'{graph_name}'")
        triple_comment = (graph_uri, 'rdfs:comment', f"'{graph_comment}'")       

        # Insert triples
        insert([triple_name, triple_comment], graph=graph_uri)
        del st.session_state['all_graphs']

        st.rerun()



##### Session initialization #####

if 'endpoint-config-endpoints-list' not in st.session_state:
    st.session_state['endpoint-config-endpoints-list'] = False
if 'endpoint-config-graph-list' not in st.session_state:
    st.session_state['endpoint-config-graph-list'] = False

##### The page #####

init()
menu()

st.title("Endpoint configuration")

st.divider()

# Endpoint list titles and buttons
col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoints List')
if col2.button('Display endpoints'):
    st.session_state['endpoint-config-endpoints-list'] = True

if st.session_state['endpoint-config-endpoints-list']:
    
    # Endpoint list titles and buttons
    if col3.button('Hide endpoints'):
        st.session_state['endpoint-config-endpoints-list'] = False
        st.rerun()

    # Display all saved endpoints
    for i, endpoint in enumerate(st.session_state['all_endpoints']):
        col1, col2, col3 = st.columns([6, 12, 1], vertical_alignment='bottom')
        col1.text_input('Name', value=endpoint['name'], key=f"endpoint-config-endpoint-name-{i}", on_change=change_endpoint, kwargs={'index': i})
        col2.text_input('URL', value=endpoint['url'], key=f"endpoint-config-endpoint-url-{i}", on_change=change_endpoint, kwargs={'index': i})

        # Button to delete a saved endpoint
        if col3.button(f'🗑️', key=f"endpoint-config-{i}"):
            dialog_confirmation(f"You are about to delete \"{endpoint['name']}\" endpoint.", delete_endpoint, index=i)

    st.text("")
    
    if st.button('Add another endpoint'):
        dialog_add_endpoint()


st.divider()

col1, col2, col3 = st.columns([5, 2, 2], vertical_alignment='bottom')
col1.markdown('### Endpoint graphs')
if col2.button('Display graphs'):
    st.session_state['endpoint-config-graph-list'] = True

if st.session_state['endpoint-config-graph-list']:

    # In case the user did not yet choose an endpoint
    if 'endpoint' not in st.session_state:
        st.warning('Please select an endpoint first')
    else:
    
        # Endpoint list titles and buttons
        if col3.button('Hide graphs'):
            st.session_state['endpoint-config-graph-list'] = False
            st.rerun()


        st.text("")
        for i, graph in enumerate(st.session_state['all_graphs']):

            col1, col2, col3, col4 = st.columns([3, 2, 5, 2], vertical_alignment='bottom')
            col1.markdown(graph['label'])
            col2.markdown(f"{readable_number(count_graph_triples(graph['uri']))} triples")
            col3.markdown(graph['comment'])
            if col4.button('🗑️', key=f"endpoint-config-graph-{i}"):
                dialog_confirmation(f'You are about to delete the graph "{graph["label"]}".', delete_graph, graph_uri=graph['uri'])


        st.text("")

        if st.button('Create a graph'):
            dialog_create_graph()