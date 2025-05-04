import streamlit as st
from model import DataSet, Endpoint
from lib.configuration import save_config

@st.dialog('Create Data Set')
def dialog_create_data_set(endpoint: Endpoint, ontology_frameworks: list[str]):
    
    name = st.text_input('Name ❗️')
    ontology_framework = st.selectbox('Ontology framework ❗️', options=ontology_frameworks, index=None)
    label_property = st.text_input('Label property ❗️', value='rdfs:label')
    comment_property = st.text_input('Comment property ❗️', value='rdfs:comment')
    data_graph_uri = st.text_input('Data Named Graph URI')
    ontology_graph_uri = st.text_input('Ontology Named Graph URI')
    metadata_graph_uri = st.text_input('Metadata Named Graph URI')

    st.text('')
    st.text('')

    can_create = name and ontology_framework and label_property and comment_property
    if st.button('Create', disabled=not can_create):
        endpoint.data_sets.append(DataSet(endpoint.sparql, name, data_graph_uri, ontology_graph_uri, metadata_graph_uri, ontology_framework, label_property, comment_property))
        save_config()
        st.rerun()