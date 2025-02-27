import os
import streamlit as st
from schema import Prefix
import lib.state as state
from lib.configuration import save_config


@st.dialog('Add a prefix')
def dialog_config_prefix():
    """Dialog function to provide a formular to add a prefix."""

    # Formular
    prefix_short = st.text_input('Prefix ❗️', value="", help="This is the prefix that will be used (eg 'rdf', 'owl', ...).")
    prefix_long = st.text_input('URL ❗️', value="", help="The URL the prefix should replace.")

    st.text("")

    # User commands: name and comment are mandatory
    if st.button('Save'):
        
        if prefix_short and prefix_long:
            
            all_prefixes = state.get_prefixes()
            all_prefixes.append(Prefix(short=prefix_short, url=prefix_long))
            state.set_prefixes(all_prefixes)
            
            # If Logre is running locally, save the config on disk
            # Otherwise tell the GUI that a configuration is present
            if os.getenv('ENV') != 'streamlit':
                save_config()
                # Validation message
                state.set_toast('Prefix saved', icon=':material/done:')

            # Reload
            st.rerun()
        
        else:
            st.warning('You need to fill all mandatory fields')
