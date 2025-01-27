from typing import Any
import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation


def __get_import_url(graph_uri: str = ""):

    technology = st.session_state['endpoint']['technology']
    endpoint_url = st.session_state['endpoint']['url']

    if technology == 'Allegrograph':
        # If it is an Allegrograph endpoint
        if graph_uri: 
            graph_uri = graph_uri.replace('infocean:', 'http://geovistory.org/information/')
            graph_uri = '%3C' + graph_uri.replace(':', '%3A').replace('/', '%2F') + '%3E'
            allegrograph_base_url = endpoint_url.replace('/sparql', '')
            return f"{allegrograph_base_url}/statements?context={graph_uri}"
        else: 
            return allegrograph_base_url
    
    elif technology == 'Fuseki':
        # If it is a Fuseki endpoint
        if graph_uri:
            graph_uri = graph_uri.replace('infocean:', 'http://geovistory.org/information/')
            return f"{endpoint_url}?graph={graph_uri}"
        else: 
            return endpoint_url


def upload_turtle_file(file: Any, graph_uri: str):

    # The turtle data
    ttl_data = file.read().decode("utf-8")

    # Upload
    url = __get_import_url(graph_uri)
    headers = {"Content-Type": "text/turtle"}
    response = requests.post(url, data=ttl_data, headers=headers, auth=(st.session_state['endpoint']['username'], st.session_state['endpoint']['password']))

    # Check response
    if response.status_code >= 400:
        st.error(f"Failed to upload file. Status code: {response.status_code}. Reason: {response.reason}. Message: {response.text}.")
        return 'error'
    else:
        st.cache_data.clear()
        del st.session_state['all_graphs']



##### The page #####

init()
menu()

if "endpoint" not in st.session_state:
    st.warning('You must first chose an endpoint in the menu before accessing explore page')

else:

    col1, col2 = st.columns([1, 1])

    # Graph selection
    graphs_labels = [graph['label'] for graph in st.session_state['all_graphs']]
    graph_label = col1.selectbox('Select the graph in which to import data', graphs_labels)  

    # Fetch the graph URI
    if graph_label:
        selected_graph = [graph for graph in st.session_state['all_graphs'] if graph['label'] == graph_label][0]

    # File format selection
    all_formats = ['Turtle (e.g. name.ttl)']
    format = col2.selectbox('Select the file format', options=all_formats, disabled=(graph_label is None))
    if format == all_formats[0]:
        file_type = 'ttl'

    # File uploader
    file = st.file_uploader(f"Load your {format} file:", type=[file_type], disabled=(format is None))
    st.text('')

    if file and file_type == 'ttl' and st.button('Upload'):
        dialog_confirmation(
            f'You are about to upload **{file.name.upper()}** into **{graph_label.upper()}**.', 
            callback=upload_turtle_file, 
            file=file,
            graph_uri=selected_graph['uri']
        )

