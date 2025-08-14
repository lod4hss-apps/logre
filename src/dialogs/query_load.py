import os
import streamlit as st
import pyperclip

# Local imports
from lib.configuration import save_config
import lib.state as state


@st.dialog('Saved queries', width='large')
def dialog_queries_load() -> None:
    """Dialog function to make user chose a saved query to copy to clipboard or delete."""

    # Get all queries from state (initially from config file)
    all_queries = state.get_queries()

    # In case there are no queries
    if len(all_queries) == 0:
        st.markdown('*No saved queries*')

    # Loop through all queries to display the query name and allow user to do things with it
    for i, query in enumerate(all_queries):
        
        # Formating
        col1, col2, col3 = st.columns([3, 2, 3])

        # Display query name
        col1.write(query.name)

        # To delete the query from the state
        if col2.button('Delete', icon=':material/delete:', key=f'query-load-delete-{i}'):
            # Use of dialog_confirmation is not possible here:
            # A dialog is already open, and Streamlit does not allow opening of a second one
            state.set_confirmation(i, query.name)

        # To load the query into the SPARQL editor
        if col3.button('Copy to clipboard', icon=':material/content_copy:', key=f'query-load-load-l{i}'):
            pyperclip.copy(query.text)
            state.set_toast('Query copied to clipboard', icon=':material/content_copy:')
            st.rerun()          

        st.text('')

    # Query deletion confirmation
    confirm_index, confirm_name = state.get_confirmation()
    if confirm_index is not None and confirm_name is not None:

        st.divider()

        if st.button(f'Confirm deletion of saved query named *{confirm_name}*', type='primary'):
            del all_queries[confirm_index]
            state.set_queries(all_queries)

            # Save on disk if we are local
            if os.getenv('ENV') != 'streamlit':
                save_config()   

            # Finalization: validation message and reload
            state.set_toast('Query deleted', ':material/delete:')
            st.rerun()