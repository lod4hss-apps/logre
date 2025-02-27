import os, shutil
from typing import List
import hashlib
import numpy as np
import streamlit as st
from pyvis.network import Network
from schema import Entity, Triple, Graph, DisplayTriple
from lib.sparql_queries import get_entity_card, get_entity_outgoing_triples, get_entity_incoming_triples, get_ontology, get_graph_of_entities
from lib.sparql_base import delete
import lib.state as state
from components.init import init
from components.menu import menu
from components.dialog_entity_info import dialog_entity_info
from components.dialog_triple_info import dialog_triple_info
from components.dialog_edit_entity import dialog_edit_entity
from components.dialog_confirmation import dialog_confirmation

def __delete_triple(display_triple: DisplayTriple, graph: Graph=None):
    """Delete a single triple from the endpoint."""

    triple = Triple(display_triple.subject.uri, display_triple.predicate.uri, display_triple.object.uri)

    delete([triple], graph=graph.uri)
    state.set_toast('Triple deleted', icon=':material/done:')
    

def __delete_entity(entity: Entity, graph: Graph=None):
    """Delete all triples of a given entity in the given graph."""

    delete([Triple(entity.uri, '?p', '?o')], graph=graph.uri)
    delete([Triple('?s', '?p', entity.uri)], graph=graph.uri)

    state.clear_entity()
    state.set_toast('Entity deleted', icon=':material/done:')


def __get_hex_color(label: str):
    """From a given label, determine an associated color."""
    if label is None or label == '': 
        return "#000"
    hash_val = hashlib.md5(label.encode()).hexdigest()  # Hash the subject name
    return f"#{hash_val[:6]}"  # Take the first 6 characters for a hex color



##### The page #####

init(layout='wide')
menu()

# By default, for performance, he disable the graph tab
state.set_element('entity-viz', False)

# From state
endpoint = state.get_endpoint()
graph = state.get_graph()
entity = state.get_entity()

# If no endpoint is selected, no entities can be displayed
if not endpoint:
    st.warning('You need to select an endpoint first (menu on the left).') 
    
# If no entity is selected, can't display its triples
elif not entity:
    
    st.warning('If an entity is selected (menu on the left), details about it will be on this page.')

# Display all informations about an entity
else:

    # Header: entity name, additional info and description
    col1, col2, col_delete, col_edit = st.columns([20, 1, 1, 4], vertical_alignment='bottom')
    col1.markdown(f'# {entity.display_label} <small style="font-size: 16px; color: gray; text-decoration: none;">{entity.uri}</small>', unsafe_allow_html=True)
    col2.button('', icon=':material/info:', type='tertiary', on_click=dialog_entity_info, kwargs={'entity': entity})
    if col_delete.button('', icon=':material/delete:', type='primary'):
        dialog_confirmation("You are about to delete this entity (including all triples) in this graph.", __delete_entity, entity=entity, graph=graph)
    st.markdown(entity.comment or '')

    st.text('')

    # Multi tab window
    tab1, tab2, tab3 = st.tabs(['Card', 'Triples', 'Visualization'])



    ### 1ST TAB: CARD ###
    # Since this is the default we load everything anyways

    # Get all triples linked to the ontology (and only!)
    # We fetch them here so we have them for edition
    card_triples = get_entity_card(entity, graph)

    # Filter out rdf:type, rdfs:label, rdfs:comment they are already in the header
    card_triples = [triple for triple in card_triples if triple.predicate.uri not in ['rdf:type', 'rdfs:label', 'rdfs:comment']]

    # Since we have a card (ie an ontology), we give the edit button triples from the card
    col_edit.button('Edit', icon=':material/edit:', type='primary', on_click=dialog_edit_entity, kwargs={'entity': entity, 'triples': card_triples})

    # Loop through all card triples to display them correctly
    for i, triple in enumerate(card_triples):
        col1, col2, col3 = tab1.columns([3, 3, 1], vertical_alignment='center')

        # (outgoing triple) On the middle: display the object info: can be a literal or an entity
        if triple.subject.uri == entity.uri and triple.object.is_literal: # If literal
            col1.markdown(f"##### {triple.predicate.display_label}")
            col2.markdown(f"> {triple.object.display_label}")
        elif triple.subject.uri == entity.uri: # If entity
            col1.markdown(f"##### {triple.predicate.display_label}")
            # Allow user to jump from the card of another entity by clicking on it
            col2.button(triple.object.display_label_comment, type='tertiary', key=f"entity-card-jump-{i}", on_click=state.set_entity, kwargs={'entity': triple.object})

        # (incoming triple) Add an additional information on the predicate label that it is incoming
        # and display the subject (as a clickable button: no subject can be a literal)
        elif triple.object.uri == entity.uri:
            col1.markdown(f"##### [incoming] {triple.predicate.display_label}")
            col2.button(triple.subject.display_label_comment, type='tertiary', key=f"entity-card-jump-{i}", on_click=state.set_entity, kwargs={'entity': triple.subject})

        # Also, for each triple allow user to have all detailed information about the triple
        col3.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"entity-card-info-{i}")

        tab1.text('')
        tab1.text('')



    ### 2ND TAB: ALL TRIPLES ###

    # PART 1: outgoing triples

    tab2.markdown('## Outgoing triples')
    tab2.text('')
    # col1, col2 = tab2.columns([1, 2], vertical_alignment='center')

    # Fetch all outgoing triples
    all_triples = get_entity_outgoing_triples(entity, graph)

    # Col 1: here the first column (subject) is always the selected entity because we are listing the outgoing entities
    # if len(all_triples):
    #     col1.markdown(entity.display_label)

    # For each triple, we display as a list all triples
    for i, triple in enumerate(all_triples):
        col1_, col2_, col3_, col4_ = tab2.columns([3, 3, 1, 1], vertical_alignment='center')

        # Col 2: the predicate
        col1_.markdown(f"*{triple.predicate.display_label}*")

        # Col3: Object information, can be a literal or an entity
        if triple.object.is_literal:
            col2_.markdown(f"> {triple.object.display_label}")
        else:
            # Allow user to jump from the card of another entity by clicking on it
            col2_.button(triple.object.display_label_comment, type='tertiary', key=f"entity-triple-jump-out-{i}", on_click=state.set_entity, kwargs={'entity': triple.object})

        # Also, for each triple allow user to have all detailed information about the triple
        col3_.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"entity-triple-info-out-{i}")

        # Allow user to delete this triple
        if col4_.button('', icon=':material/delete:', type='tertiary', key=f"entity-triple-delete-out-{i}"):
            dialog_confirmation('You are about to delete the triple.', __delete_triple, display_triple=triple, graph=graph)

        tab2.text('')

    tab2.divider()


    # PART 2: incoming triples

    col1, col2 = tab2.columns([1, 3], vertical_alignment='bottom')
    col1.markdown('## Incoming triples')
    fetch_incoming = col2.checkbox('Fetch incoming triples', value=False)
    tab2.text('')

    if fetch_incoming: 
        with st.spinner('Fetching incoming statements'):
            incoming_triples = get_entity_incoming_triples(entity, graph)
    
        # Col 1: here the first column (subject) is always the selected entity because we are listing the outgoing entities
        # if len(incoming_triples):
        #     col2.markdown(entity.display_label)

        # For each triple, we display as a list all triples
        for i, triple in enumerate(incoming_triples):
            col1_, col2_, col3_, col4_ = tab2.columns([3, 3, 1, 1], vertical_alignment='center')

            # Col 2: the predicate
            col1_.markdown(f"*{triple.predicate.display_label}*")

            # Col3: Subject information
            # Allow user to jump from the card of another entity by clicking on it
            col2_.button(triple.subject.display_label_comment, type='tertiary', key=f"entity-triple-jump-inc-{i}", on_click=state.set_entity, kwargs={'entity': triple.subject})

            # Also, for each triple allow user to have all detailed information about the triple
            col3_.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"entity-triple-info-inc-{i}")
            
            # Allow user to delete this triple
            if col4_.button('', icon=':material/delete:', type='tertiary', key=f"entity-triple-delete-inc-{i}"):
                dialog_confirmation('You are about to delete the triple.', __delete_triple, display_triple=triple, graph=graph)

            tab2.text('')



    ### 3RD TAB: VISUALIZATION ###
    
    col1, col2, col3, col4 = tab3.columns([2, 1, 4, 4], vertical_alignment='bottom')

    # To avoid to do heavy request on each entity card, we ask the user to confirm the loading
    if col1.button('Load visualization', help='Depending on information on your entities, this can take a while'):
        state.set_element('graph-viz', True)

    if state.get_element('graph-viz'):
        ontology = get_ontology()
        classes_labels = list(map(lambda cls: cls.display_label , ontology.classes))
        excluded_predicate_uris = set(['rdf:type', 'rdfs:label']) # Because there is no point of displaying them on the graph

        # Also for performance reasons, we set the value of graph depth on each page back to 2.
        graph_depth = col2.number_input('Graph depth', min_value=1, step=1)

        # Option to not filter out particular classes (eg genders on a family tree might not be relevant)
        excluded_classes_labels = col3.multiselect('Filter out classes', options=classes_labels)

        # If classes have been selected to be excluded, get their URIs
        excluded_classes_uris = set()
        if excluded_classes_labels:
            for class_label in excluded_classes_labels:
                idx = classes_labels.index(class_label)
                excluded_classes_uris.add(ontology.classes[idx].uri)

        # Option to only display a certain list of classes
        included_classes_labels = col4.multiselect('Include classes', options=['All'] + classes_labels, default=['All'])

        # If classes have been selected to be excluded, get their URIs
        included_classes_uris = set()
        if included_classes_labels:
            for class_label in included_classes_labels:
                if class_label == "All": 
                    included_classes_uris.add('All')
                else:
                    idx = classes_labels.index(class_label)
                    included_classes_uris.add(ontology.classes[idx].uri)

        # Get the asked graph
        graph_triples: List[DisplayTriple] = []
        uris_done = set()
        for depth in range(0, graph_depth):

            # List all entities
            subjects_uris = [triple.subject.uri for triple in graph_triples if (not triple.subject.is_blank)]
            objects_uris = [triple.object.uri for triple in graph_triples if (not triple.object.is_literal) and (not triple.object.is_blank)]
            uris = [entity.uri] + subjects_uris + objects_uris

            # Filter out those already done
            uris = [uri for uri in uris if uri not in uris_done]

            # Fetch triples (if there at least one entity to fetch)
            if len(uris) == 0: 
                break
            triples = get_graph_of_entities(uris)

            # List the asked
            for uri in uris: uris_done.add(uri)

            # Filter out excluded classes: if the triples has subject or object of one excluded class, 
            # triple is itself excluded
            # Also, exclude the triples if it is in the list of excluded predicates
            triples = [
                triple for triple in triples 
                if  triple.predicate.uri not in excluded_predicate_uris and
                    triple.subject.class_uri not in excluded_classes_uris and
                    triple.object.class_uri not in excluded_classes_uris and
                    ('All' in included_classes_uris or triple.subject.class_uri in included_classes_uris) and 
                    ('All' in included_classes_uris or triple.object.class_uri in included_classes_uris) 
            ]

            # Add them to the fetched triples
            graph_triples += triples

        # To make the visualization prettier, we change the entity labels and make it on multiple lines
        formated_triples = [{
                "subject": triple.subject.display_label.replace(' (', '\n('),
                "predicate": triple.predicate.display_label.replace(' (', '\n('),
                "object": triple.object.display_label.replace(' (', '\n(')
            } for triple in graph_triples
        ]

        # Network object: the one that will be displayed
        network = Network(width="100%", neighborhood_highlight=True)

        # Build and add the needed information for the Network: Nodes
        nodes = [t['subject'] for t in formated_triples] + [t['object'] for t in formated_triples]
        nodes = list(np.unique(nodes))

        # Special behavior: Handle the bug in pyvis
        # In pyvis, later on, when adding edges, when one is a string that can be parsed into a integer (at least, maybe also a float, but not sure)
        # It crashes because it does not find it in the nodes, which is false: it actually is in the node
        # I assume this is a bug from pyvis, and that, somehow, internally it parsed it into an integer, so far that it does not find the string of it in the nodes
        # The strategy used here is to make the string not parsable as an integer (by adding a ".", which is not perfect, but work around the bug)
        for i, node in enumerate(nodes):
            try:
                int(node)
                nodes[i] = str(node) + '.'
            except ValueError: pass

        # Determine the color: each class has the same color
        # Values are black, blank nodes are grey
        nodes_colors = []
        for node in nodes:
            if '\n(' in node: nodes_colors.append(__get_hex_color(node[node.index('\n('):]))
            elif node.startswith('(blank)'): nodes_colors.append('#535353')
            else: nodes_colors.append('#000')
        network.add_nodes(nodes, color=nodes_colors)
    
        # Build and add the needed information for the Network: Edges
        for t in formated_triples:
            try:
                int(t['object'])
                object = t['object'] + '.'
            except ValueError:
                object = t['object']
            network.add_edge(t['subject'], object, label=t['predicate'])

        # Set the options
        network.set_options("""
            const options = {
                "nodes": {"font": {"face": "tahoma"}},
                "edges": {
                    "length": 150,
                    "arrows": {"to": {"enabled": true}},
                    "font": {"size": 10,"face": "tahoma","align": "top"}
                }
            }
        """)

        # Because pyvis work like that, there is no direct way of getting the html directly:
        # We need to save on disk and then read it and finally delete it in order to display it
        # It is not so clean, but the displayed graph is the better out there IMHO

        # Generate the graph
        network.save_graph('network.html')
        
        # Read from disk
        with open("network.html", 'r', encoding='utf-8') as file:
            source_code = file.read()

        # Delete the file from disk
        os.remove('network.html')
        shutil.rmtree('./lib/')

        # Display the read HTML
        # Here we have to use "with" because it appears that it is the only way with streamlit to display HTML
        with tab3:
            # 617 as height because it makes the network look centered
            st.components.v1.html(source_code, height=617)
