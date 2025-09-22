import streamlit as st
from lib import state
from schema.data_bundle import DataBundle
from schema.model_framework import ModelFramework
from schema.sparql_technologies import SPARQLTechnology

ENDPOINT_TECHNOLOGIES_STR = [e.value for e in list(SPARQLTechnology)]
MODEL_FRAMEWORKS_STR = [e.value for e in list(ModelFramework)]

@st.dialog("Data Bundle", width='medium')
def dialog_data_bundle_form(db: DataBundle = None) -> None:
    """
    Displays a dialog form for creating or editing a Data Bundle.

    Args:
        db (DataBundle, optional): The existing Data Bundle to edit. If None, a new Data Bundle will be created.

    Returns:
        None

    Behavior:
        - Allows the user to input or modify:
            - Name, SPARQL endpoint technology and URL, credentials
            - Base URI
            - Graph URIs (data, model, metadata)
            - Model framework
            - Core properties (type, label, comment)
        - Validates required fields before enabling the save/create button.
        - Creates a new Data Bundle or updates the existing one in the application state.
        - Reruns the page after saving to reflect changes.
    """
    # Data Bundle name, alone on its line
    col_name, _ = st.columns([1, 1])
    new_name = col_name.text_input('Name ❗️', value=db.name if db else '')

    st.write('')
    st.write('')

    # SPARQL endpoint technology and URL
    col_techno, col_url = st.columns([1, 1])
    new_technology = col_techno.selectbox('Endpoint technology ❗️', options=ENDPOINT_TECHNOLOGIES_STR, index=ENDPOINT_TECHNOLOGIES_STR.index(db.endpoint.technology_name) if db else None)
    new_url = col_url.text_input('Endpoint URL ❗️', value=db.endpoint.url if db else '')

    # SPARQL endpoint credentials
    col_username, col_password = st.columns([1, 1])
    new_username = col_username.text_input('Endpoint username', value=db.endpoint.username if db else '')
    new_password = col_password.text_input('Endpoint password', value=db.endpoint.password if db else '', type='password')

    st.write('')
    st.write('')

    # Data Bundle base URI
    new_base_uri = st.text_input('Base URI ❗️', value=db.base_uri if db else 'http://www.example.org/resource/')

    # Data Bundle graphs
    col_data, col_model, col_metadata = st.columns([1, 1, 1])
    new_graph_data_uri = col_data.text_input('Data graph URI', value=db.graph_data.uri if db else 'base:data')
    new_graph_model_uri = col_model.text_input('Model graph URI', value=db.graph_model.uri if db else 'base:model')
    new_graph_metadata_uri = col_metadata.text_input('Metadata graph URI', value=db.graph_metadata.uri if db else 'base:metadata')
    
    st.write('')
    st.write('')

    # Data Bundle framework used for model
    col_framework, _ = st.columns([1, 2])
    new_framework = col_framework.selectbox('Model framework ❗️', options=MODEL_FRAMEWORKS_STR, index=MODEL_FRAMEWORKS_STR.index(db.model.framework_name) if db else None)

    # Data Bundle basic properties (type, label, comment)
    col_type, col_label, col_comment = st.columns([1, 1, 1])
    new_type_prop_uri = col_type.text_input('Type property ❗️', value=db.model.type_property if db else 'rdf:type')
    new_label_prop_uri = col_label.text_input('Label property ❗️', value=db.model.label_property if db else 'rdfs:label')
    new_comment_prop_uri = col_comment.text_input('Comment property ❗️', value=db.model.comment_property if db else 'rdfs:comment')

    st.write('')
    st.write('')

    with st.container(horizontal=True, horizontal_alignment='center'):
        # Disabled if some required fields are missing
        disabled = not(new_name and new_technology and new_url and new_base_uri and new_framework and new_type_prop_uri and new_label_prop_uri and new_comment_prop_uri)
        if st.button('Save' if db else 'Create', type='primary', width=200, disabled=disabled):

            # Create the Data Bundle
            new_db = DataBundle.from_dict({
                'name': new_name,
                'base_uri': new_base_uri,
                'endpoint_url': new_url,
                'username': new_username,
                'password': new_password,
                'endpoint_technology': new_technology,
                'model_framework': new_framework,
                'prop_type_uri': new_type_prop_uri,
                'prop_label_uri': new_label_prop_uri,
                'prop_comment_uri': new_comment_prop_uri,
                'graph_data_uri': new_graph_data_uri,
                'graph_model_uri': new_graph_model_uri,
                'graph_metadata_uri': new_graph_metadata_uri,
            }, prefixes=state.get_prefixes())

            # And add it to state
            state.update_data_bundle(db, new_db)

            st.rerun()