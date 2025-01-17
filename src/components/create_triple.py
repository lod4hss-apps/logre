import streamlit as st
from tools.sparql_queries import list_entities, insert
import time


@st.dialog("Create a new Triple", width='large')
def create_triple() -> None:
    """
    Dialog function allowing the user to create a new triple.
    User can fill the subject, predicate and the object of the triple.
    """


    # Graph selection (where to insert the informations)
    graphs_labels = [graph['label'] for graph in st.session_state['all_graphs']]
    graph_label = st.selectbox('Select the graph in which insert the new triple', graphs_labels)  

    # To know from where query the entities (only from selected graphs!)
    activated_graphs = [graph for graph in st.session_state['all_graphs'] if graph['activated']]
    
    st.divider()

    # If there is a selected graph, fetch all the information about this graph from the session
    if graph_label:
        graph_index = graphs_labels.index(graph_label)
        graph_to_write = st.session_state['all_graphs'][graph_index]

    # Fetch all entities from all selected graphs
    entities = []
    for graph in activated_graphs:
        entities += list_entities(graph=graph['uri'], limit=None)

    # Generate all the entities display labels
    for i, entity in enumerate(entities):
        entities[i]['display_label'] = f"{entity['label']} ({entity['class_label']})"

    # To avoid run through the loop twice:
    entities_display_label = [entity['display_label'] for entity in entities]

    # Formular
    subject_label = st.selectbox("Subject ❗️", entities_display_label, placeholder="Select an entity", index=None, help="has to exist on the endpoint and selected graphs")
    property = st.text_input("Property ❗️", placeholder="Write a property URI", help="e.g. \"ontome:p1111\" or \"rdfs:label\" or \"https://ontome.net/ontology/c21 \"")
    object_label = st.selectbox("Object ❗️", entities_display_label, placeholder="Select an entity", index=None, help="has to exist on the endpoint and selected graphs")

    st.divider()

    # On click, if everything is properly filled
    if st.button('Create') and subject_label and property and object_label :

        # Retrive object and subject dictionaries
        subject = [entity['uri'] for entity in entities if entity['display_label'] == subject_label][0]
        object = [entity['uri'] for entity in entities if entity['display_label'] == object_label][0]
        
        # Generate the triple and insert it in the graph
        triple = (subject, property, object)
        insert([triple], graph_to_write['uri'])

        # Finalization: validation message and reload
        st.success('Triple inserted.')
        time.sleep(1)
        st.rerun()