import streamlit as st
from schema import Entity, Triple, Graph, DisplayTriple
from lib.sparql_queries import get_entity_card, get_entity_outgoing_triples, get_entity_incoming_triples
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


##### The page #####

init(layout='wide')
menu()

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
    col1, col2, col_delete, col_edit = st.columns([10, 1, 1, 1], vertical_alignment='bottom')
    col1.title(entity.display_label)
    col2.button('', icon=':material/info:', type='tertiary', on_click=dialog_entity_info, kwargs={'entity': entity})
    if col_delete.button('', icon=':material/delete:', type='primary'):
        dialog_confirmation("You are about to delete this entity (including all triples) in this graph.", __delete_entity, entity=entity, graph=graph)
    st.markdown(entity.comment or '')

    st.text('')

    # Multi tab window
    tab1, tab2, tab3 = st.tabs(['Card', 'Triples', 'Visualization'])

    ### TAB CARD ###

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
            col2.button(triple.object.display_label_comment, type='tertiary', key=f"my-entities-card-jump-{i}", on_click=state.set_entity, kwargs={'entity': triple.object})

        # (incoming triple) Add an additional information on the predicate label that it is incoming
        # and display the subject (as a clickable button: no subject can be a literal)
        elif triple.object.uri == entity.uri:
            col1.markdown(f"##### [incoming] {triple.predicate.display_label}")
            col2.button(triple.subject.display_label_comment, type='tertiary', key=f"my-entities-card-jump-{i}", on_click=state.set_entity, kwargs={'entity': triple.subject})

        # Also, for each triple allow user to have all detailed information about the triple
        col3.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"my-entities-card-info-{i}")

        tab1.text('')
        tab1.text('')


    ### TAB TRIPLES ###

    # First part: the outgoing triples
    tab2.markdown('## Outgoing triples')
    col1, col2 = tab2.columns([1, 2], vertical_alignment='center')

    # Fetch all outgoing triples
    outgoing_triples = get_entity_outgoing_triples(entity, graph)

    # Col 1: here the first column (subject) is always the selected entity because we are listing the outgoing entities
    if len(outgoing_triples):
        col1.markdown(entity.display_label)

    # For each triple, we display as a list all triples
    for i, triple in enumerate(outgoing_triples):
        col1_, col2_, col3_, col4_ = col2.columns([3, 3, 1, 1], vertical_alignment='center')

        # Col 2: the predicate
        col1_.markdown(triple.predicate.display_label)

        # Col3: Object information, can be a literal or an entity
        if triple.object.is_literal:
            col2_.markdown(f"> {triple.object.display_label}")
        else:
            # Allow user to jump from the card of another entity by clicking on it
            col2_.button(triple.object.display_label_comment, type='tertiary', key=f"my-entities-triple-jump-out-{i}", on_click=state.set_entity, kwargs={'entity': triple.object})

        # Also, for each triple allow user to have all detailed information about the triple
        col3_.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"my-entities-triple-info-out-{i}")

        # Allow user to delete this triple
        if col4_.button('', icon=':material/delete:', type='tertiary', key=f"my-entities-triple-delete-out-{i}"):
            dialog_confirmation('You are about to delete the triple.', __delete_triple, display_triple=triple, graph=graph)


        if i != len(outgoing_triples) - 1:
            col2.divider()
        # col2.text('')
        # col2.text('')

    tab2.divider()

    # Second part: the incoming triples
    col1, col2 = tab2.columns([1, 3], vertical_alignment='bottom')
    col1.markdown('## Incoming triples')
    fetch_incoming = col2.checkbox('Fetch incoming triples', value=False)

    col1, col2 = tab2.columns([2, 1], vertical_alignment='center')

    if fetch_incoming: 
        with st.spinner('Fetching incoming statements'):
            incoming_triples = get_entity_incoming_triples(entity, graph)
    

        # Col 1: here the first column (subject) is always the selected entity because we are listing the outgoing entities
        if len(incoming_triples):
            col2.markdown(entity.display_label)

        # For each triple, we display as a list all triples
        for i, triple in enumerate(incoming_triples):
            col1_, col2_, col3_, col4_ = col1.columns([1, 1, 3, 3], vertical_alignment='center')

            # Col 2: the predicate
            col4_.markdown(triple.predicate.display_label)

            # Col3: Subject information
            # Allow user to jump from the card of another entity by clicking on it
            col3_.button(triple.subject.display_label_comment, type='tertiary', key=f"my-entities-triple-jump-inc-{i}", on_click=state.set_entity, kwargs={'entity': triple.subject})

            # Also, for each triple allow user to have all detailed information about the triple
            col2_.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs={'triple': triple}, key=f"my-entities-triple-info-inc-{i}")
            
            # Allow user to delete this triple
            if col1_.button('', icon=':material/delete:', type='tertiary', key=f"my-entities-triple-delete-inc-{i}"):
                dialog_confirmation('You are about to delete the triple.', __delete_triple, display_triple=triple, graph=graph)


            col1.text('')


    ### TAB TRIPLES ###

    tab3.write('Coming soon')