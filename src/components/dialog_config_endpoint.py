import os
from enum import Enum
import streamlit as st
from schema import EndpointTechnology, OntologyFramework, Endpoint
import lib.state as state
from lib.configuration import save_config

# Contants
technologies = [e for e in EndpointTechnology]
technologies_str = [e.value for e in EndpointTechnology]
frameworks =  [e for e in OntologyFramework]
frameworks_str = [e.value for e in OntologyFramework]


@st.dialog("Add an endpoint", width='large')
def dialog_config_endpoint(endpoint: Endpoint = None, index: int = None) -> None:
    """Dialog function to provide a formular for the endpoint creation/edition."""

    # For some reason, sometimes, especially on hot reload, Enums are lost.
    # Maybe its my fault, by I can't find the reason why after some clicking around, the enums are lost
    # This is the way I found to make it work every time
    if endpoint:
        technology = endpoint.technology.value if isinstance(endpoint.technology, Enum) else endpoint.technology
        ontology_framework = endpoint.ontology_framework.value if isinstance(endpoint.ontology_framework, Enum) else endpoint.ontology_framework
    else:
        technology = 'None'
        ontology_framework = 'None'

    # Values, and default
    name = endpoint.name if endpoint else ""
    url = endpoint.url if endpoint else ""
    technology_index = technologies_str.index(technology) if endpoint else 0
    base_uri = endpoint.base_uri if endpoint else "http://www.example.org/"
    ontology_uri = endpoint.ontology_uri if endpoint else "base:ontology"
    framework_index = frameworks_str.index(ontology_framework) if endpoint else 0
    username = endpoint.username if endpoint else ""
    password = endpoint.password if endpoint else ""
    metadata_uri = endpoint.metadata_uri if endpoint else "base:metadata"

    # Formular
    endpoint_name = st.text_input('Name ❗️', value=name, help="Give a name to your endpoint, so that you recognize it in the list.")
    endpoint_url = st.text_input('URL ❗️', value=url, help="If the endpoint is local, it is propably something like 'http://localhost:9999/', otherwise, see with your endpoint provider.")
    endpoint_technology = st.selectbox('Technology ❗️', options=technologies_str, index=technology_index, help="Is your endpoint a Fuseki server? Allegrograph server? Set to \"None\" if it is another one")
    endpoint_base_uri = st.text_input('Base URI ❗️', value=base_uri, help="Root URI that will be used for new nodes (plus an suffix: an ID), do not forget the trailing \"/\" or \"#\"")
    endpoint_ontology_uri = st.text_input('Ontology graph ❗️', value=ontology_uri, help="URI (or shortcut) of the graph containing the ontologycal model.")
    endpoint_ontological_framework = st.selectbox('Ontological framework ❗️', options=frameworks_str, index=framework_index, help="As of now, only those in the list are supported.")
    endpoint_metadata_uri = st.text_input('Metadata graph ❗️', value=metadata_uri, help="URI (or shortcut) of the graph containing the endpoint metadata.")
    endpoint_username = st.text_input('Username', value=username, help="In case their is authentication on the endpoint. Leave it empty if not.")
    endpoint_password = st.text_input('Password', value=password, type='password', help="In case their is authentication on the endpoint. Leave it empty if not.")

    st.text("")

    # User commands
    if st.button('Save'):

        # Those are the mandatories fields
        if endpoint_name and endpoint_url and endpoint_technology and endpoint_base_uri and endpoint_ontology_uri and endpoint_ontological_framework and endpoint_metadata_uri:
        
            new_endpoint = Endpoint(
                name=endpoint_name,
                url=endpoint_url,
                technology=EndpointTechnology(endpoint_technology),
                base_uri=endpoint_base_uri,
                ontology_uri=endpoint_ontology_uri,
                ontology_framework=OntologyFramework(endpoint_ontological_framework),
                username=endpoint_username,
                password=endpoint_password,
                metadata_uri=endpoint_metadata_uri
            )
            
            # Update the endpoint, or add it to the list
            all_endpoints = state.get_endpoints()
            if endpoint: all_endpoints[index] = new_endpoint
            else: all_endpoints.append(new_endpoint)
            state.set_endpoints(all_endpoints)

            # Also, to avoid error, here selected endpoint is just reset
            state.clear_endpoint()

            # If Logre is running locally, save the config on disk
            # Otherwise tell the GUI that a configuration is present
            if os.getenv('ENV') != 'streamlit':
                save_config()
                # Validation message
                state.set_toast('Endpoint saved', icon=':material/done:')

            # Reload
            st.rerun()
        
        else:
            st.warning('You need to fill all mandatory fields')
