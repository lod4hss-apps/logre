import streamlit as st
from components.menu import menu
from code_editor import code_editor
import tools.sparql_base as sparql

default_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX ontome: <https://ontome.net/ontology/>
PREFIX infocean: <http://geovistory.org/information/>

SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object
}
LIMIT 10
""".strip()



menu()


##### The page #####

st.title("SPARQL Editor")

# Code editor with syntax highlighting
sparql_query = code_editor(
    lang="sparql",
    code=default_query,
    height="350px",
    buttons=[{"name": "Run SPARQL Query", "hasText": True, "alwaysOn": True,"style": {"top": "300px", "right": "0.4rem"}, "commands": ["submit"],}]
)

if sparql_query['type'] == "submit":
    result = sparql.run(sparql_query['text'])
    if result is not None:
        st.markdown("### Response" + ' *(shape: ' + str(result.shape[0]) + 'x' + str(result.shape[1]) + "*)")
        st.dataframe(result, use_container_width=True, hide_index=True)
    else:
        st.success('Query executed')