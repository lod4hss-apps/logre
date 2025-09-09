import streamlit as st, numpy as np, hashlib, os, shutil
from typing import List
from pyvis.network import Network
import lib.state as state
from components.init import init
from components.menu import menu
from dialogs import dialog_confirmation, dialog_entity_info, dialog_entity_form
from model import OntoEntity, DataBundle, Statement
from dialogs import dialog_triple_info


def __delete_entity(entity: OntoEntity) -> None:
    """Delete all triples of a given entity in the given graph."""

    # From state
    data_bundle = state.get_data_bundle()

    # Delete data
    data_bundle.graph_data.delete((entity.uri, '?p', '?o')) # Outgoing
    data_bundle.graph_data.delete(('?s', '?p', entity.uri)) # Incoming

    state.clear_entity()
    state.set_toast('Entity deleted', icon=':material/done:')


def __delete_triple(display_triple: Statement) -> None:
    """Delete a single triple from the endpoint."""

    # From state
    data_bundle = state.get_data_bundle()
    entity = state.get_entity()

    subject = display_triple.subject.uri
    predicate = display_triple.predicate.uri
    object = f"'{display_triple.object.uri}'" if display_triple.object.is_literal else display_triple.object.uri
    triple = (subject, predicate, object)

    data_bundle.graph_data.delete([triple])

    state.set_toast('Triple deleted', icon=':material/done:')
    st.cache_data.clear()
    st.cache_resource.clear()

    entity = data_bundle.get_entity_infos(entity.uri)
    state.set_entity(entity)
    

def __get_hex_color(label: str):
    """From a given label, determine an associated color."""
    if label is None or label == '': 
        return "#000"
    hash_val = hashlib.md5(label.encode()).hexdigest()  # Hash the subject name
    return f"#{hash_val[:6]}"  # Take the first 6 characters for a hex color


##### The page #####

init(layout='wide')

#### QUERY PARAM HANDLING - BEGIN ####
# If there are query parameters: endpoint name
query_param_endpoint_name = st.query_params.get('endpoint', None)
if query_param_endpoint_name:
    all_endpoints = state.get_endpoints()
    targets = list(filter(lambda e: e.name == query_param_endpoint_name, all_endpoints))
    if len(targets): 
        endpoint = targets[0]
        state.set_endpoint(targets[0])

        # If there are query parameters: data bundle name
        query_param_data_bundle_name = st.query_params.get('databundle', None)
        if query_param_data_bundle_name:
            targets = list(filter(lambda e: e.name == query_param_data_bundle_name, endpoint.data_bundles))
            if len(targets): 
                data_bundle = targets[0]
                state.set_data_bundle(data_bundle)

                # If there are query parameters: entity URI
                query_param_entity_uri = st.query_params.get('entity', None)
                if query_param_entity_uri:
                    entity = data_bundle.get_entity_infos(query_param_entity_uri)
                    state.set_entity(entity)
    
                else: state.clear_entity()        
            else: state.clear_data_bundle()
    else: state.clear_endpoint()
#### QUERY PARAM HANDLING - END ####    

menu()

# From state
endpoint = state.get_endpoint()
data_bundle = state.get_data_bundle()
entity = state.get_entity()


# If no endpoint is selected, no entities can be displayed
if not endpoint:
    st.warning('You need to select an endpoint first (menu on the left).') 

# If no entity is selected, can't display its triples
elif not entity:
    st.warning('If an entity is selected (menu on the left), details about it will be on this page.')

else:

    # Header: entity name, additional info and description
    col1, col2, col_delete, col_edit = st.columns([20, 1, 1, 4], vertical_alignment='bottom')
    col1.markdown(f'# {entity.display_label_class} <small style="font-size: 16px; color: gray; text-decoration: none;">{entity.uri}</small>', unsafe_allow_html=True)
    col2.button('', icon=':material/info:', type='tertiary', on_click=dialog_entity_info, kwargs={'entity': entity})
    if col_delete.button('', icon=':material/delete:', type='primary'):
        dialog_confirmation("You are about to delete this entity, and all its triples.", __delete_entity, entity=entity)
    st.markdown(entity.comment or '')

    st.text('')

    # Multi tab window
    tab1, tab2, tab3 = st.tabs(['Card', 'Triples', 'Visualization'])


    ### 1ST TAB: CARD ###

    # Get the card statements
    all_card = data_bundle.get_card(entity)

    # Filter out rdf:type, rdfs:label, rdfs:comment they are already in the header
    card = [triple for triple in all_card if triple.predicate.uri not in [data_bundle.type_property, data_bundle.label_property, data_bundle.comment_property]]

    # Make sure triples are unique (can happen if multiple ontology has been imported for a class)
    have_triple = set()
    unique_card_triples: List[Statement] = []
    for triple in card:
        key = f"{triple.subject.uri}-{triple.predicate.uri}-{triple.object.uri}"
        if key not in have_triple:
            have_triple.add(key)
            unique_card_triples.append(triple)
    card = unique_card_triples

    # Since we have a card (ie an ontology), we give the edit button triples from the card
    triples = [(statement.subject.uri, statement.predicate.uri, statement.object.uri) for statement in all_card]
    col_edit.button('Edit', icon=':material/edit:', type='primary', on_click=dialog_entity_form, kwargs={'entity': entity, 'triples': triples})

    # Loop through all card triples to display them correctly
    for i, triple in enumerate(card):
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
            col1.markdown(f'##### <small style="font-size: 12px; color: gray;">(incoming)</small> {triple.predicate.display_label}', unsafe_allow_html=True)
            col2.button(triple.subject.display_label_comment, type='tertiary', key=f"entity-card-jump-{i}", on_click=state.set_entity, kwargs={'entity': triple.subject})

        # Also, for each triple allow user to have all detailed information about the triple
        col3.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"entity-card-info-{i}")

        tab1.text('')
        tab1.text('')

        
    ### 2ND TAB: ALL TRIPLES ###

    # PART 1: outgoing triples

    tab2.markdown('#### Outgoing triples')
    tab2.text('')

    # Fetch all outgoing triples
    outgoing_triples = data_bundle.get_outgoing_statements(entity)

    # For each triple, we display as a list all triples
    for i, triple in enumerate(outgoing_triples):
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
            dialog_confirmation('You are about to delete the triple.', __delete_triple, display_triple=triple)

        tab2.text('')

    tab2.divider()


    # PART 2: incoming triples

    col1, col2 = tab2.columns([1, 3], vertical_alignment='bottom')
    col1.markdown('#### Incoming triples')
    tab2.text('')

    # Fetch all incoming triples
    incoming_triples = data_bundle.get_incoming_statements(entity, limit=5)

    # Give the possibility to fetch more
    if len(incoming_triples) == 5:
        if col2.button('Fetch more incoming triples', help="For performance reasons, only first 5 have been fetched. Keep in mind that fetching all other incoming can lead to overload the page if they are too many."):
            incoming_triples = data_bundle.get_incoming_statements(entity)

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
            dialog_confirmation('You are about to delete the triple.', __delete_triple, display_triple=triple)

        tab2.text('')



    ### 3RD TAB: VISUALIZATION ###
    
    col1, col2, col3, col4 = tab3.columns([2, 1, 4, 4], vertical_alignment='bottom')

    classes = data_bundle.ontology.get_classes()

    # To avoid to do heavy request on each entity card, we ask the user to confirm the loading
    if col1.button('Load visualization', help='Depending on information on your entities, this can take a while'):
        state.set_element('graph-viz', True)

    if state.get_element('graph-viz'):
        classes_labels = list(map(lambda cls: cls.display_label , classes))
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
                excluded_classes_uris.add(classes[idx].uri)

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
                    included_classes_uris.add(classes[idx].uri)

        # Get the asked graph
        graph_triples: List[Statement] = []
        uris_done = set()
        for depth in range(0, graph_depth):

            # List all entities
            subjects = [triple.subject for triple in graph_triples if (not triple.subject.is_blank)]
            objects = [triple.object for triple in graph_triples if (not triple.object.is_literal) and (not triple.object.is_blank)]
            to_fetch = [entity] + subjects + objects

            # Filter out those already done
            to_fetch = [ent for ent in to_fetch if ent.uri not in uris_done]

            # Fetch triples (if there at least one entity to fetch)
            if len(to_fetch) == 0: break
            triples: List[Statement] = []
            for ent in to_fetch:
                triples += data_bundle.get_outgoing_statements(ent)
                triples += data_bundle.get_incoming_statements(ent)
                uris_done.add(ent.uri)

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
