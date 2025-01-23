from typing import Any
import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from lib.utils import ensure_uri
import requests
from urllib.parse import quote, urlencode



def upload_turtle_file(file: Any, graph_uri: str):

    # The turtle data
    ttl_data = file.read().decode("utf-8")

    # Upload to Fuseki
    if graph_uri:
        # We need to put back the full URL of the graph
        graph_uri = graph_uri.replace('infocean:', 'http://geovistory.org/information/')
        target_url = f"{st.session_state['endpoint']['url']}?graph={graph_uri}"
    else:
        target_url = f"{st.session_state['endpoint']['url']}"
    headers = {"Content-Type": "text/turtle"}
    response = requests.post(target_url, data=ttl_data, headers=headers)

    # Check response
    if response.status_code != 200:
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

