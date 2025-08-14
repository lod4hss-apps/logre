import streamlit as st

# Local imports
from model import Endpoint, Prefix
from lib.configuration import save_config


@st.dialog('Create prefix')
def dialog_create_prefix(endpoint: Endpoint) -> None:
    """
    Dialog function to add a new Prefix to an existing Endpoint instance.

    Args:
        endpoint (Endpoint): The existing endpoint instance to add a new Prefix to.
    """

    # Formular
    short = st.text_input('Short ❗️')
    long = st.text_input('Long ❗️')

    st.text('')
    st.text('')
    
    # Verify if mandatories are set
    can_create = short and long

    # Create button and actions
    if st.button('Create', disabled=not can_create):

        # Create the new Prefix instance
        prefix = Prefix(short, long)

        # Add it to existing Endpoint instance and save new configuration
        endpoint.sparql.prefixes.append(prefix)
        save_config()
        
        st.rerun()