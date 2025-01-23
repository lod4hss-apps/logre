import streamlit as st
import uuid
import time
from lib.utils import ensure_uri
from lib.sparql_queries import insert


@st.dialog("Create a new Entity", width='large')
def create_entity() -> None:
    """
    Dialog function allowing the user to create a new entity.
    User can fill the label, the class and the definition.
    Also, the only thing required to create the entity is the label.
    Class and Definition are optional.
    """

    # Graph selection (where to insert the informations)
    graphs_labels = [graph['label'] for graph in st.session_state['all_graphs']]
    graph_label = st.selectbox('Select the graph in which insert the new entity', graphs_labels)  

    st.divider()
    
    # If there is a selected graph, fetch all the information about this graph from the session
    if graph_label:
        graph_index = graphs_labels.index(graph_label)
        graph = st.session_state['all_graphs'][graph_index]
        
    # Formular
    col1, col2 = st.columns([1, 1])
    label = col1.text_input("Entity label ❗️", placeholder="Give a label", help="Will be object of a triple (new_entity, rdfs:label, 'your_label')")
    cls = col2.text_input("Entity class URI", placeholder="Set the class", help="eg. \"ontome:c21\" or \"https://ontome.net/ontology/c21\", or...")
    definition = st.text_area('Entity definition', placeholder="Write a definition", help="Will be object of a triple (new_entity, rdfs:comment, 'your_definition')")

    st.divider()

    # On click, if there is a label, create the entity
    if st.button('Create') and label:

        # Generate the entity key (UUID5)
        input_string = label + (cls if cls else "Unknown") + (definition if definition else "Unknown") 
        id = str(uuid.uuid5(uuid.NAMESPACE_DNS, input_string))

        # Create the correct triples
        triples = []
        if label:
            triples.append((f"infocean:{id}", "rdfs:label", f"'{label}'"))
        if cls:
            triples.append((f"infocean:{id}", "rdf:type", ensure_uri(cls)))
        if definition:
            triples.append((f"infocean:{id}", "rdfs:comment", f"'{definition}'"))

        # Insert triples
        insert(triples, graph['uri'])

        # And select
        st.session_state['selected_entity'] = {
            'uri': f"infocean:{id}",
            'display_label': f"{label} ({cls if cls else 'Unknown'})"
        }
    
        # Finalization: validation message and reload
        st.success('Entity created.')
        time.sleep(1)
        st.rerun()