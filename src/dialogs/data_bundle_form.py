import streamlit as st
from requests.exceptions import HTTPError
from graphly.schema import Prefixes, Prefix
from lib import state
from lib.errors import get_HTTP_ERROR_message
from schema.data_bundle import DataBundle
from schema.model_framework import ModelFramework
from schema.sparql_technologies import SPARQLTechnology, get_sparql_technology


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
    new_technology = col_techno.selectbox('Endpoint technology ❗️', options=ENDPOINT_TECHNOLOGIES_STR, index=ENDPOINT_TECHNOLOGIES_STR.index(db.endpoint.technology_name) if db else None, help="[What are the supported SPARQL endpoint technologies?](/documentation#what-are-the-supported-sparql-endpoint-technologies)")
    new_url = col_url.text_input('Endpoint URL ❗️', value=db.endpoint.url if db else '', help="[What is a SPARQL endpoint?](/documentation#what-is-a-sparql-endpoint)")

    # SPARQL endpoint credentials
    col_username, col_password = st.columns([1, 1])
    new_username = col_username.text_input('Endpoint username', value=db.endpoint.username if db else '', help="[Where do I find my SPARQL endpoint username and password?](/documentation#in-the-data-bundle-creation-where-do-i-find-my-sparql-endpoint-username-and-password)")
    new_password = col_password.text_input('Endpoint password', value=db.endpoint.password if db else '', type='password', help="[Where do I find my SPARQL endpoint username and password?](/documentation#in-the-data-bundle-creation-where-do-i-find-my-sparql-endpoint-username-and-password)")

    st.write('')
    st.write('')

    # Data Bundle base URI
    new_base_uri = st.text_input('Base URI ❗️', value=db.base_uri if db else 'http://www.example.org/resource/', help="[what does 'Base URI' refers to?](/documentation#in-the-data-bundle-creation-what-does-base-uri-refers-to)")

    st.write('')
    st.write('')

    # List current named graph
    popover = st.popover('List of existing named graph', help="[Why am I given the list of existing graphs?](/documentation#in-the-data-bundle-creation-why-am-i-given-the-list-of-existing-graphs)")
    try: 
        graphs = __get_graph_list(new_technology, new_url, new_username, new_password, new_base_uri)
        popover.markdown('*(Default graph)*')
        for graph in graphs:
            popover.markdown(f"{graph}")
    except HTTPError as err:
        message = get_HTTP_ERROR_message(err)
        popover.error(message)
        print(message.replace('\n\n', '\n'))

    # Data Bundle graphs
    col_data, col_model, col_metadata = st.columns([1, 1, 1])
    new_graph_data_uri = col_data.text_input('Data graph URI', value=db.graph_data.uri if db else 'base:data', help="[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)")
    new_graph_model_uri = col_model.text_input('Model graph URI', value=db.graph_model.uri if db else 'base:model', help="[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)")
    new_graph_metadata_uri = col_metadata.text_input('Metadata graph URI', value=db.graph_metadata.uri if db else 'base:metadata', help="[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)")

    st.write('')
    st.write('')

    # Data Bundle framework used for model
    col_framework, _ = st.columns([1, 2])
    new_framework = col_framework.selectbox('Model framework ❗️', options=MODEL_FRAMEWORKS_STR, index=MODEL_FRAMEWORKS_STR.index(db.model.framework_name) if db else None, help="[What are the supported model framework supported?](/documentation#what-are-the-supported-model-framework-supported)")

    # Data Bundle basic properties (type, label, comment)
    col_type, col_label, col_comment = st.columns([1, 1, 1])
    new_type_prop_uri = col_type.text_input('Type property ❗️', value=db.model.type_property if db else 'rdf:type', help="[Why should I provide type, label and comment properties URIs?](documentation#in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)")
    new_label_prop_uri = col_label.text_input('Label property ❗️', value=db.model.label_property if db else 'rdfs:label', help="[Why should I provide type, label and comment properties URIs?](documentation#in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)")
    new_comment_prop_uri = col_comment.text_input('Comment property ❗️', value=db.model.comment_property if db else 'rdfs:comment', help="[Why should I provide type, label and comment properties URIs?](documentation#in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)")

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


@st.cache_data(ttl=120, show_spinner=False)
def __get_graph_list(technology: str | None, url: str | None, username: str | None, password: str | None, base_uri: str | None) -> None:

    if technology and url and username and password and base_uri:

        # First there is the need to set the endpoint, prefixes etc locally, based on things above
        endpoint = get_sparql_technology(technology)(url, username, password)

        # Retrieve prefixes but skip the configured 'base' one
        prefixes = Prefixes([prefix for prefix in state.get_prefixes().prefix_list if prefix.short != 'base'])
        prefixes.add(Prefix('base', base_uri))

        # Make the query
        with st.spinner('Fetching existing named graph'):
            graphs = endpoint.run("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o . } }", prefixes=prefixes)
        
        return [g['g'] for g in graphs]