import streamlit as st
import pandas as pd
from requests.exceptions import HTTPError
from code_editor import code_editor
from components.init import init
from components.menu import menu
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.confirmation import dialog_confirmation
from dialogs.query_name import dialog_query_name
from dialogs.confirmation import dialog_confirmation

try:

    # Initialize
    init(layout='wide')
    menu()

    # Title
    st.markdown('# SPARQL Editor')
    st.markdown('[More about the edior in the Documentation FAQ](/documentation#what-type-of-queries-can-i-write-in-the-sparql-editor)')
    
    st.markdown('')

    # From state
    sparql_queries = state.get_sparql_queries()
    sparql_query_name = state.get_sparql_query()
    data_bundle = state.get_data_bundle()

    # Find the selected one
    sparql_queries_names = [sq[0] for sq in sparql_queries]
    index = sparql_queries_names.index(sparql_query_name) if sparql_query_name else 0

    # Allow user to change the selected queries
    with st.container(horizontal=True, vertical_alignment='bottom'):
        sparql_query_name = st.selectbox('SPARQL query', options=sparql_queries_names, index=index,width=300, on_change=state.set_sparql_query, args=(sparql_query_name,), help="[Can I save a specific query?](/documentation#can-i-save-a-specific-query)")

        # And have a delete button for this query
        if st.button('', icon=':material/delete:', type='tertiary'):
            def callback_delete_query(sq_name: str) -> None:
                state.delete_sparql_query(sq_name)
                state.set_toast('Query removed', icon=':material/delete:')
            dialog_confirmation(f"You are about to delete the query *{sparql_query_name}*.", callback=callback_delete_query, sq_name=sparql_query_name)

    # Get the query content
    sparql_query_content = sparql_queries[sparql_queries_names.index(sparql_query_name)][1] if sparql_query_name else ''

    # Display prefixes for user to know
    prefixes_str = '`, `'.join([p.short for p in data_bundle.prefixes])
    st.markdown('Available prefixes are: `' + prefixes_str + '`')

    # Code editor
    editor = code_editor(
        lang="sparql",
        code=sparql_query_content,
        height="400px",
        buttons=[{"name": "Run", "hasText": True, "alwaysOn": True,"style": {"top": "350px", "right": "0.4rem"}, "commands": ["submit"]}]
    )

    st.write('')

    # When submit button is clicked
    if editor['type'] == 'submit' and editor['id'] != state.get_last_executed_sparql_id():

        # Run the query
        result = data_bundle.endpoint.run(editor['text'], data_bundle.prefixes)
        state.set_last_executed_sparql_id(editor['id'])

        # If there is a result
        if result != None:
            df = pd.DataFrame(result)

            option_line = st.container(horizontal=True, horizontal_alignment='distribute', vertical_alignment='bottom')

            # Option line: title, shape, and buttons
            with option_line.container(horizontal=True, horizontal_alignment='left', vertical_alignment='bottom'):
                st.markdown("### Response", width='content')
                st.markdown(f"Shape: {df.shape[0]}x{df.shape[1]}", width='content')

            # Options buttons: download and save query
            with option_line.container(horizontal=True, horizontal_alignment='right', vertical_alignment='bottom'):
                st.download_button('Download CSV', data=df.to_csv(index=False), file_name="logre-download.csv", mime="text/csv", icon=':material/download:')
                if st.button('Save query', kwargs={'text': editor['text']}, icon=':material/reorder:'): 
                    dialog_query_name(editor['text'])

            # Display query result
            st.dataframe(df, hide_index=True)

        # When there is no result: a insert/delete query
        else:
            # Inform user that the request went through
            state.set_toast('Query executed', icon=':material/done:')
            st.rerun()

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))