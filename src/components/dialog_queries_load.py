import streamlit as st
import lib.state as state
from lib.configuration import save_config
import pyperclip


@st.dialog('Saved queries', width='large')
def dialog_queries_load() -> None:
    """Dialog function to make user chose a saved query to copy to clipboard or delete."""

    # Get all queries from state (initially from config file)
    all_queries = state.get_queries()

    # Loop through all queries to display the query name and allow user to do things with it
    for i, query in enumerate(all_queries):
        
        col1, col2, col3 = st.columns([3, 2, 3])
        col1.write(query.name)

        # To delete the query from the state
        if col2.button('Delete', icon=':material/delete:', key=f'query-load-delete-{i}'):
            state.set_confirmation(i, query.name)

        # To load the query into the SPARQL editor
        if col3.button('Copy to clipboard', icon=':material/content_copy:', key=f'query-load-load-l{i}'):
            pyperclip.copy(query.text)
            state.set_toast('Query copied to clipboard', icon=':material/content_copy:')
            st.rerun()          

        st.text('')
    

    # Here we handle the query deletion confirmation
    confirm_index, confirm_name = state.get_confirmation()
    if confirm_index is not None and confirm_name is not None:

        st.divider()

        if st.button(f'Confirm deletion of {confirm_name}', type='primary'):
            del all_queries[confirm_index]
            state.set_queries(all_queries)

            # Save on disk if we are local
            if state.get_configuration() == 'local':
                save_config()   

            # Finalization: validation message and reload
            state.set_toast('Query deleted', ':material/delete:')
            st.rerun()