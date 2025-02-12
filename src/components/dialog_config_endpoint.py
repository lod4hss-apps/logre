import streamlit as st
from schema import EndpointTechnology, OntologyFramework, Endpoint
import lib.state as state
from lib.configuration import save_config

# Contants
technologies = [e.value for e in EndpointTechnology]
frameworks = [e.value for e in OntologyFramework]


@st.dialog("Add an endpoint")
def dialog_config_endpoint(endpoint: Endpoint = None, index: int = None) -> None:
    """Dialog function to provide a formular for the endpoint creation/edition."""

    # Values, and default
    name = endpoint.name if endpoint else ""
    url = endpoint.url if endpoint else ""
    technology = technologies.index(endpoint.technology) if endpoint else 0
    base_uri = endpoint.base_uri if endpoint else "http://www.example.org/"
    ontology_uri = endpoint.ontology_uri if endpoint else "base:shacl"
    framework_index = frameworks.index(endpoint.ontology_framework) if endpoint else 0
    username = endpoint.username if endpoint else ""
    password = endpoint.password if endpoint else ""

    # Formular
    endpoint_name = st.text_input('Endpoint name ❗️', value=name)
    endpoint_url = st.text_input('Endpoint URL ❗️', value=url)
    endpoint_base_uri = st.text_input('Endpoint base URI ❗️', value=base_uri, help="This is the base URI that will be given to new nodes in the endpoint (plus an ID).")
    endpoint_technology = st.selectbox('Technology', options=technologies, index=technology)
    endpoint_ontological_framework = st.selectbox('Select the ontological framework', options=frameworks, index=framework_index)
    endpoint_ontology_uri = st.text_input('Select the graph in which the ontologycal model lies', value=ontology_uri, help="This should be the URI (or shortcut) of the graph containing the ontologycal model; e.g. base:shacl>")
    endpoint_username = st.text_input('Username', value=username)
    endpoint_password = st.text_input('Password', value=password, type='password')

    st.text("")

    # User commands
    if st.button('Save'):

        # Those are the mandatories fields
        if endpoint_name and endpoint_url and endpoint_base_uri:
        
            new_endpoint = Endpoint(
                name=endpoint_name,
                url=endpoint_url,
                technology=endpoint_technology,
                base_uri=endpoint_base_uri,
                ontology_uri=endpoint_ontology_uri,
                ontology_framework=endpoint_ontological_framework,
                username=endpoint_username,
                password=endpoint_password
            )

            # Update the endpoint, or add it to the list
            all_endpoints = state.get_endpoints()
            if endpoint: all_endpoints[index] = new_endpoint
            else: all_endpoints.append(new_endpoint)
            state.set_endpoints(all_endpoints)

            # Also, to avoid error, here selected endpoint is just reset
            state.clear_endpoint()

            # If Logre is running locally and has a configuration: save the config on disk
            if state.get_configuration() == 'local': 
                save_config()

            # Finalization: validation message and reload
            state.set_toast('Endpoint saved', icon=':material/done:')
            st.rerun()
        
        else:
            st.warning('You need to fill all mandatory fields')
