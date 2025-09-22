import streamlit as st
from lib import state

@st.dialog("Choose a query name")
def dialog_query_name(query_text: str) -> None:

    # User input
    name = st.text_input('Query name', value='')

    # Validation button
    with st.container(horizontal=True, horizontal_alignment='center'):
        # Verify that all mandatories are present
        disabled = name is None or name == ''
        # And create or edit the entity
        if st.button('Save', disabled=disabled, width=200, type='primary'):
            state.update_sparql_query([name, query_text])
            st.rerun()