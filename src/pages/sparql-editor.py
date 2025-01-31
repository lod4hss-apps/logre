import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from code_editor import code_editor
import lib.sparql_base as sparql
import pandas as pd

# The default query that is shown on first load of the page
default_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX shacl: <http://www.w3.org/ns/shacl#>
PREFIX ontome: <https://ontome.net/ontology/>
PREFIX base: <//base_uri//>

SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object
}
LIMIT 10
""".strip()


##### Modals #####

@st.dialog('Load saved queries')
def dialog_load_saved_queries():
    """Dialog function to make user chose a saved query to load or delete."""

    # Extract needed information
    queries_names = list(map(lambda query: query['name'], st.session_state['all_queries']))
    queries_text = list(map(lambda query: query['text'], st.session_state['all_queries']))

    # User inputs
    query_name = st.selectbox('Saved query name', queries_names, index=None, placeholder='Chose a query name')
    col1, col2 = st.columns(2)
    delete_btn = col1.button('Delete')
    load_btn = col2.button('Load')

    # When a query is selected and users clicks on "Load"
    if query_name and load_btn:
        # Find the selected query among the list
        query_index = queries_names.index(query_name)
        query_text = queries_text[query_index]
        # And add the text to the session
        st.session_state['sparql_editor_text'] = query_text
        st.rerun()
    
    # When a query is selected and users wants to delete it: need a confirmation
    if query_name and delete_btn:
        st.session_state['sparql_editor_query_confirm_deletion'] = True
    if st.session_state['sparql_editor_query_confirm_deletion'] and st.button(f'Confim deletion of query "{query_name}"'):
            # Delete query from session
            st.session_state['sparql_editor_query_confirm_deletion'] = False
            st.session_state['all_queries'] = list(filter(lambda query: query['name'] != query_name, st.session_state['all_queries']))
            st.rerun()


@st.dialog('Save query')
def dialog_save_query(text: str):
    """Dialog function that finishes with the saving of the given SPARQL query (after giving it a name)."""

    # User inputs
    new_name = st.text_input('Query name', help="Give it a name so you will recognize this query among all your saved queries")
    btn = st.button('Save')

    # When the user has set a name and validates
    if new_name and btn:
        # Add the new query to the session, and rerun
        st.session_state['all_queries'].append({'name': new_name, 'text': text})
        st.rerun()



##### The page #####

init()
menu()

if 'endpoint' not in st.session_state:
    st.markdown("# SPARQL Editor")
    st.warning('No endpoint is selected')

else:
    # A flag variable to allow deletion confirmation (dialog_load_saved_queries)
    if 'sparql_editor_query_confirm_deletion' not in st.session_state:
        st.session_state['sparql_editor_query_confirm_deletion'] = False

    # Title and load query option
    col1, col2 = st.columns([5, 3], vertical_alignment='bottom')
    col1.markdown("# SPARQL Editor")
    if col2.button('Load saved queries'):
        dialog_load_saved_queries()

    # Code editor
    sparql_query = code_editor(
        lang="sparql",
        code=default_query.replace('//base_uri//', st.session_state['endpoint']['base_uri']),
        height="450px",
        buttons=[{"name": "Run SPARQL Query", "hasText": True, "alwaysOn": True,"style": {"top": "400px", "right": "0.4rem"}, "commands": ["submit"]}]
    )

    # Results, save option, download option
    st.text("")

    # When the user executes via the inbox button
    if sparql_query['type'] == 'submit':

        # Run the query itself
        if 'endpoint' not in st.session_state:
            st.warning('No endpoint is selected')
        else:
            result = sparql.run(sparql_query['text'])
        
            # If there is a result, display result and options:
            #       Option1: Save the query that gave this result
            #       Option2: Download the dataframe as a CSV
            if isinstance(result, list):
                result_df = pd.DataFrame(data=result)
                
                # Option line
                col1, col2, col3 = st.columns([2, 1, 1], vertical_alignment='bottom')
                col1.markdown("### Response" + ' *(shape: ' + str(result_df.shape[0]) + 'x' + str(result_df.shape[1]) + "*)")
                col2.download_button('Download as CSV', data=result_df.to_csv(index=False), file_name="logre-download.csv", mime="text/csv")
                if col3.button('Save query'):
                    dialog_save_query(sparql_query['text'])
                
                # The result itself
                st.dataframe(result_df, use_container_width=True, hide_index=True)

            elif result:
                # In case the query was an insert or a delete, display a message to inform user
                st.success('Query executed')
