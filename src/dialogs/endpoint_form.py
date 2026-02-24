import streamlit as st
from graphly.schema import Sparql
from lib import state
from schema.sparql_technologies import SPARQLTechnology, get_sparql_technology


ENDPOINT_TECHNOLOGIES_STR = [e.value for e in list(SPARQLTechnology)]

@st.dialog("Endpoint", width='small')
def dialog_endpoint_form(endpoint: Sparql = None) -> None:
    """
    Displays a dialog form for creating or editing a Sparql endpoint.

    Args:
        endpoint (Sparql, optional): The existing endpoint to edit. If None, a new endpoint will be created.

    Returns:
        None

    Behavior:
        - Allows the user to input or modify:
            - Name,
            - URL, 
            - Username and password
        - Validates required fields before enabling the save/create button.
        - Creates a new Endpoint or updates the existing one in the application state.
        - Reruns the page after saving to reflect changes.
    """
    # Data Bundle name, alone on its line
    new_name = st.text_input('Name ❗️', value=endpoint.name if endpoint else '')

    st.write('')
    st.write('')

    # SPARQL endpoint technology
    new_technology = st.selectbox('Endpoint technology ❗️', options=ENDPOINT_TECHNOLOGIES_STR, index=ENDPOINT_TECHNOLOGIES_STR.index(endpoint.technology_name) if endpoint else None, help="[What are the supported SPARQL endpoint technologies?](/documentation#what-are-the-supported-sparql-endpoint-technologies)")

    # SPARQL endpoint URL
    new_url = st.text_input('Endpoint URL ❗️', value=endpoint.url if endpoint else '', help="[What is a SPARQL endpoint?](/documentation#what-is-a-sparql-endpoint)")

    st.write('')

    # SPARQL endpoint credentials
    new_username = st.text_input('Endpoint username', value=endpoint.username if endpoint else '', help="[Where do I find my SPARQL endpoint username and password?](/documentation#in-the-data-bundle-creation-where-do-i-find-my-sparql-endpoint-username-and-password)")

    # SPRAQL endpoint password
    new_password = st.text_input('Endpoint password', value=endpoint.password if endpoint else '', type='password', help="[Where do I find my SPARQL endpoint username and password?](/documentation#in-the-data-bundle-creation-where-do-i-find-my-sparql-endpoint-username-and-password)")

    st.write('')
    st.write('')

    with st.container(horizontal=True, horizontal_alignment='center'):
        # Disabled if some required fields are missing
        disabled = not(new_name and new_technology and new_url)
        if st.button('Save' if endpoint else 'Create', type='primary', width=200, disabled=disabled):

            # Create the Endpoint
            SparqlClass = get_sparql_technology(new_technology)
            new_endpoint = SparqlClass(new_url, new_username, new_password, new_name)

            # Loop through all Data Bundles, and also update their endpoint
            for db in state.get_data_bundles():
                if db.endpoint == endpoint:
                    db.endpoint = new_endpoint
            
            # And add it to state (has to be done after updating data_bundles, because of configuration saving)
            state.update_endpoint(endpoint, new_endpoint)

            state.set_endpoint(None)  # To make sure new things are loaded
            st.rerun()
