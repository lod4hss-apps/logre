import streamlit as st
from schema import Triple
from lib.utils import to_snake_case
from lib.sparql_base import insert
import lib.state as state

@st.dialog('Create a graph')
def dialog_config_graph():
    """Dialog function to provide a formular  for the graph creation."""

    # Formular
    graph_name = st.text_input('Name ❗️', value="")
    graph_comment = st.text_area('Comment ❗️', value="")

    st.text("")

    # User commands: name and comment are mandatory
    if st.button('Save'):
        
        if graph_name and graph_comment:

            # Generate the graph name and uri
            name = to_snake_case(graph_name)
            graph_uri = 'base:' + name

            # Create triples in default graph
            triple_name = Triple(graph_uri, 'rdfs:label', f"'{graph_name}'")
            triple_comment = Triple(graph_uri, 'rdfs:comment', f'"""{graph_comment}"""')       

            # Also, in order to make the graph visible in queries, it needs to have at least one triple
            # So here it creates a dummy triple. This solution is in test, let see in the future if this triple is disturbing or not
            dummy_triple = Triple('_:dummy1', 'base:dummyPredicate', '_:dummy2')

            # Insert triples
            insert([triple_name, triple_comment]) # graph label and comment can't be added to the graph itself by convention
            insert([dummy_triple], graph=graph_uri)

            # And reset the graphs that are in session, so that, they are fetched on rerun
            state.clear_graphs()
            
            # Finalization: validation message and reload
            state.set_toast("New graph created", icon=':material/done:')
            st.rerun()
        
        else:
            st.warning('You need to fill all mandatory fields')
