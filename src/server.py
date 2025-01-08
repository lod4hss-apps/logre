import streamlit as st
from code_editor import code_editor
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd


##### Page preparation ##### 

default_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object
}
LIMIT 10
""".strip()


def connect_to_sparql_endpoint(url: str) -> SPARQLWrapper:
    """Prepare the execution of SPARQL against the endpoint."""

    sparql_endpoint = SPARQLWrapper(url)
    sparql_endpoint.setReturnFormat(JSON)
    return sparql_endpoint


def run_sparql(endpoint: SPARQLWrapper, query: str) -> pd.DataFrame | None:
    """Run the given query."""

    endpoint.setQuery(query)

    # Execute the query (only selects) and returns a Dataframe
    if 'select' in query.lower():
        response = endpoint.queryAndConvert()["results"]["bindings"]
        response_rows = list(map(handle_row, response))
        return pd.DataFrame(data=response_rows)
    
    # Execute the query (only insert or delete)
    elif 'delete' in query.lower() or 'insert' in query.lower():
        endpoint.method = "POST"
        endpoint.query()

    # If select or delete has not been recognized, raise an error
    else:
        raise Exception('Unrecognized query type: supported are only "select", "insert" and "delete"')


def handle_row(row: dict) -> dict:
    """Transform a returning object into a dictionnary for better use."""

    obj = {}
    for key in row.keys():
        obj[key] = row[key]["value"]
    return obj


##### The page #####

st.title('Logre: Local graph editor')

# Endpoint selection: allow to chose the endpoint on which to run the query against
endpoint_URL = st.text_input('SPARQL endpoint URL', help='e.g.: "https://query.wikidata.org/sparql"')

# The Code editor, with a "Run" button
editor: str = code_editor(
    lang="sparql",
    code=default_query,
    height="300px",
    buttons=[{"name": "Run SPARQL Query", "hasText": True, "alwaysOn": True,"style": {"top": "250px", "right": "0.4rem"}, "commands": ["submit"],}]
)

# On click of the "Run button"
if editor['type'] == "submit":
    endpoint = connect_to_sparql_endpoint(endpoint_URL)
    result = run_sparql(endpoint, editor['text'])

    if result is not None:
        st.markdown("### Response" + ' (shape: ' + str(result.shape[0]) + 'x' + str(result.shape[1]) + ")")
        st.dataframe(result, use_container_width=True, hide_index=True)
    else:
        st.success('Execution finished')