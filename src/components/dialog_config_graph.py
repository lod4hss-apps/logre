import streamlit as st
from schema import Triple
from lib.utils import to_snake_case
from lib.sparql_base import insert
import lib.state as state

@st.dialog('Create a graph')
def dialog_config_graph():
    """Dialog function to provide a formular for the graph creation."""

    # From state
    endpoint = state.get_endpoint()

    # Formular
    graph_name = st.text_input('Name ❗️', value="", help="Will be used as the rdfs:label.")
    graph_uri = st.text_input('Graph URI ❗️', value="base:", help="Value of the graph URI. You can use shortcuts.")
    graph_comment = st.text_area('Comment ❗️', value="", help="Brief description of what is in the graph.")

    st.text("")

    # User commands: name and comment are mandatory
    if st.button('Save'):
        
        if graph_name and graph_uri and graph_comment:

            # Create triples in default graph
            triple_class = Triple(graph_uri, 'rdf:type', 'http://www.example.org/Graph')
            triple_name = Triple(graph_uri, 'rdfs:label', f"'{graph_name}'")
            triple_comment = Triple(graph_uri, 'rdfs:comment', f'"""{graph_comment}"""')       

            # Insert triples
            insert([triple_class, triple_name, triple_comment], graph=endpoint.metadata_uri) # graph label and comment can't be added to the graph itself by convention

            # And reset the graphs that are in session, so that, they are fetched on rerun
            state.clear_graphs()
            
            # Finalization: validation message and reload
            state.set_toast("New graph created", icon=':material/done:')
            st.rerun()
        
        else:
            st.warning('You need to fill all mandatory fields')
