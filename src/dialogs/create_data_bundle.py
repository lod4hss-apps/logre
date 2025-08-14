import streamlit as st

# Local imports
from model import DataBundle, Endpoint
from lib.configuration import save_config


@st.dialog('Create a Data Bundle')
def dialog_create_data_bundle(endpoint: Endpoint, ontology_frameworks: list[str]):
    """
    Dialog function to add a new Data Bundle to an existing Endpoint instance.

    Args:
        endpoint (Endpoint): The existing endpoint instance to add a Data Bundle to.
        ontologies_frameworks (list of strings): List of available ontologies frameworks.
    """
    
    # Formular
    name = st.text_input('Name ❗️')
    ontology_framework = st.selectbox('Ontology framework ❗️', options=ontology_frameworks, index=None)
    type_property = st.text_input('Type property ❗️', value='rdf:type')
    label_property = st.text_input('Label property ❗️', value='rdfs:label')
    comment_property = st.text_input('Comment property ❗️', value='rdfs:comment')
    data_graph_uri = st.text_input('Data Named Graph URI')
    ontology_graph_uri = st.text_input('Ontology Named Graph URI')
    metadata_graph_uri = st.text_input('Metadata Named Graph URI')

    st.text('')
    st.text('')

    # Verify if mandatories are set
    can_create = name and ontology_framework and type_property and label_property and comment_property

    # Create button and actions
    if st.button('Create', disabled=not can_create):
        
        # Create the new Data Bundle instance
        new_data_bundle = DataBundle(endpoint.sparql, name, data_graph_uri, ontology_graph_uri, metadata_graph_uri, ontology_framework, type_property, label_property, comment_property)

        # Add it to existing Endpoint instance and save new configuration
        endpoint.data_bundles.append(new_data_bundle)
        save_config()

        st.rerun()