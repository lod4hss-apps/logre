import streamlit as st

# Local imports
from model import Endpoint
from lib import state
from lib.configuration import save_config

@st.dialog('Add Endpoint')
def dialog_add_endpoint(server_technologies: list[str]) -> None:
    """
    Dialog function to add an endpoint to configuration (and save it).

    Args:
        server_technologies (list of strings): List of available server technologies.
    """
    
    # Formular
    name = st.text_input('Name ❗️')
    technology = st.selectbox('Server technology ❗️', options=server_technologies, index=None)
    url = st.text_input('URL ❗️')
    base_uri = st.text_input('Base URI ❗️', value='http://example.org/')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    st.text('')
    st.text('')

    # Verify if mandatories are set
    can_create = name and technology and url and base_uri

    # Create button and actions
    if st.button('Create', disabled=not can_create):

        # Get currents endpoints
        all_endpoints = state.get_endpoints()

        # Create the new enpoint instance
        new_endpoint = Endpoint(technology, name, url, username, password, base_uri)

        # Add all default prefixes to state and new endpoint instance
        have_prefixes = set(list(map(lambda p: p.short, new_endpoint.sparql.prefixes)))
        for prefix in state.get_default_prefixes():
            if prefix.short not in have_prefixes:
                new_endpoint.sparql.prefixes.append(prefix)

        # Add the new endpoint to current ones, and save new configuration
        all_endpoints.append(new_endpoint)
        save_config()

        st.rerun()