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
prefix shacl: <http://www.w3.org/ns/shacl#>
PREFIX ontome: <https://ontome.net/ontology/>
PREFIX infocean: <http://geovistory.org/information/>

SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object
}
LIMIT 10
""".strip()


def __read_saved_queries() -> dict[str:str]:
    """Put in session the content of the logre/data/saved_queries file."""

    # Read the file content
    file = open('../data/saved_queries', 'r')
    content = file.read().strip()
    file.close()

    # Parse the content into a list of objects
    queries_list = content.split('---')
    queries = []
    for raw_queries in queries_list:
        # If an error occurs here, it is because the file has the wrong format
        try:
            if raw_queries.strip() != "":
                colon_index = raw_queries.index(':')
                name = raw_queries[0:colon_index].strip()
                text = raw_queries[colon_index+1:].strip()
                queries.append({'name': name, 'text': text})
        except Exception:
            st.error('File "data/saved_queries" is wrongly formatted. Correct it then reload the page.')

    # Put the endpoints information in session
    st.session_state['all_queries'] = queries

    print(queries_list)

def __write_queries_list() -> None:
    """Write all queries that are in session memory on disk."""

    # Transform the list of objects into a string
    content = ""
    for i, query in enumerate(st.session_state['all_queries']):
        prefix = "\n---\n" if i != 0 else ""
        content += f"{prefix}{query['name']}:\n\n{query['text']}\n"

    # Write the generated string on disk
    file = open('../data/saved_queries', 'w')
    file.write(content)
    file.close()


##### Modals #####

@st.dialog('Load saved queries')
def dialog_load_saved_queries():
    """Dialog function to make user chose a saved query to load or delete."""

    # First read saved queries from disk
    __read_saved_queries()

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
            # And write new list on disk
            __write_queries_list()
            st.rerun()


@st.dialog('Save query')
def dialog_save_query(text: str):
    """Dialog function that finishes with the saving of the given SPARQL query (after giving it a name)."""

    # User inputs
    new_name = st.text_input('Query name', help="Give it a name so you will recognize this query among all your saved queries")
    btn = st.button('Save')

    # When the user has set a name and validates
    if new_name and btn:
        # Load last version of saved queries (might not have been loaded: only if he loaded a saved query)
        __read_saved_queries()
        # Add the new query to the session
        st.session_state['all_queries'].append({'name': new_name, 'text': text})
        # And write on disk
        __write_queries_list()
        st.rerun()


##### Initialize session variables #####

# The content of the editor
if 'sparql_editor_text' not in st.session_state:
    st.session_state['sparql_editor_text'] = default_query
# A flag variable to allow deletion confirmation (dialog_load_saved_queries)
if 'sparql_editor_query_confirm_deletion' not in st.session_state:
    st.session_state['sparql_editor_query_confirm_deletion'] = False


##### The page #####

init()
menu()

# Title and load query option
col1, col2 = st.columns([5, 3], vertical_alignment='bottom')
col1.markdown("# SPARQL Editor")
if col2.button('Load saved queries'):
    dialog_load_saved_queries()

# Code editor
sparql_query = code_editor(
    lang="sparql",
    code=st.session_state['sparql_editor_text'],
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
