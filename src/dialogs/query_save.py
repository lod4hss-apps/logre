import os
import streamlit as st
from model import Query
from lib.configuration import save_config
import lib.state as state

@st.dialog('Save query')
def dialog_queries_save(text: str) -> None:
    """Dialog function to provide a formular to save the SPARQL endpoint (with a name)."""

    # User inputs
    new_name = st.text_input('Query name ❗️', help="Give it a name so you will recognize this query among all your saved queries")
    btn = st.button('Save')

    # When the user has set a name and validates
    if new_name and btn:

        # Add the new query to the session
        all_queries = state.get_queries()
        all_queries.append(Query(name=new_name, text=text))
        state.set_queries(all_queries)

        # If Logre is running locally, save the config on disk
        if os.getenv('ENV') != 'streamlit':
            save_config()

        # Finalization: validation message and reload
        state.set_toast('Query saved', icon=':material/done:')
        st.rerun()
