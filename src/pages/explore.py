from typing import List
import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from components.find_entities import dialog_find_entity
from components.create_entity import create_entity
from components.create_triple import create_triple
from lib.sparql_queries import list_entity_triples, delete
from lib.schema import Triple


##### Functions #####

def delete_entity(entity_uri: str):
    """Loop through all graphs (even those not activated) in order to delete all triples related to the given entity."""

    triples_outgoing = Triple(entity_uri, '?predicate', '?object')
    triples_incoming = Triple('?subject', '?predicate', entity_uri)

    for graph in st.session_state['all_graphs']:
        delete([triples_outgoing], graph=graph['uri'])
        delete([triples_incoming], graph=graph['uri'])
        st.session_state['selected_entity'] = None


def delete_from_graph(entity_uri: str, graph_uri: str):
    """Delete all triples of a given entity in a given graph."""

    triples_outgoing = Triple(entity_uri, '?predicate', '?object')
    triples_incoming = Triple('?subject', '?predicate', entity_uri)

    delete([triples_outgoing], graph=graph_uri)
    delete([triples_incoming], graph=graph_uri)


##### The page #####

init(layout='wide')
menu()

if "endpoint" not in st.session_state:
    st.warning('You must first chose an endpoint in the menu before accessing explore page')

else:

    # General user commands
    col1, col2, col3 = st.columns([1, 1, 1])
    if col1.button('Find an entity'):
        dialog_find_entity()
    if col2.button('Create an entity'):
        create_entity()
    if col3.button('Create a triple'):
        create_triple()

    st.divider()

    # If an entity is selected (ie in session)
    if 'selected_entity' in st.session_state:

        # Entity title with label, class and id
        col1, col2, col3 = st.columns([22, 11, 2], vertical_alignment='bottom')
        col1.markdown('# ' + st.session_state['selected_entity']['display_label'])
        col2.markdown(f"###### {st.session_state['selected_entity']['uri']}")

        # And the delete button to cleanse graphs from this entity
        if col3.button('🗑️', help='Click on this button to delete all triples of this entity'):
            dialog_confirmation(
                f"You are about to delete all triples from entity {st.session_state['selected_entity']['display_label']} from **all graphs.**",
                callback=delete_entity,
                entity_uri=st.session_state['selected_entity']['uri']
            )


        # For each selected graph, displays all triples the selected entity has
        selected_graphs = [graph for graph in st.session_state['all_graphs'] if graph['activated']]
        for graph in selected_graphs:

            # Fetch all triples
            with st.spinner('Fetching entity triples...'):
                triples = list_entity_triples(st.session_state['selected_entity']['uri'], graph=graph['uri'])
                # st.dataframe(pd.DataFrame(data=triples))

            col1, _ = st.columns([5, 5])
            col1.divider()

            # Display all triples
            col_graph_name, col_delete_btn = st.columns([35, 2], vertical_alignment='center')
            col_graph_name.markdown(f'##### From graph "{graph["label"]}"')

            # Delete button to cleanse this entity from this graph
            if col_delete_btn.button('🗑️', key=f'explore-delete-{graph["label"]}', help="Click here to delete all triples of this entity only in this graph"):
                dialog_confirmation(
                    f"You are about to delete all triples from entity {st.session_state['selected_entity']['display_label']} from graph {graph['label']}",
                    callback=delete_from_graph,
                    entity_uri=st.session_state['selected_entity']['uri'],
                    graph_uri=graph['uri']
                )

            # Display all triples
            for i, triple in enumerate(triples):
                col1, col2, col3, col4 = st.columns([8, 4, 8, 1], vertical_alignment='center')
                
                # If the subject is not the selected entity
                if 'subject' in triple:
                    subject_display_label = f"{triple['subject_label']} ({triple['subject_class_label']})"

                    # Button to jump on the entity (change the "selected_entity" in session)
                    if col1.button(subject_display_label, type='tertiary', key=f'explore-subject-{graph["label"]}-{i}', help="Click to jump to this entity"):
                        st.session_state['selected_entity'] = {
                            'uri': triple['subject'],
                            'display_label': subject_display_label
                        }
                        st.rerun()
                else:
                    # Otherwise, just displays a "fake button"
                    subject_display_label = st.session_state['selected_entity']['display_label']
                    col1.button(subject_display_label, type='tertiary', key=f'explore-subject-{graph["label"]}-{i}', help="The current entity")


                # Display the property
                if 'predicate' in triple:
                    predicate_label = triple['predicate_label'] if 'predicate_label' else 'No label'
                    col2.write(predicate_label)

                # If the object is not the selected entity
                if 'object' in triple:

                    # Object can also be a literal. In such case, juste display a text (instead of a button)
                    if triple['object_literal'] == 'true':
                        object_display_label = triple['object']
                        col3.write(object_display_label)
                    else:
                        # Otherwise, do as subjects
                        object_display_label = f"{triple['object_label']} ({triple['object_class_label']})"
                        if col3.button(object_display_label, type='tertiary', key=f'explore-{graph["label"]}-{i}', help="Click to jump to this entity"):
                            st.session_state['selected_entity'] = {
                                'uri': triple['object'],
                                'display_label': object_display_label
                            }
                            st.rerun()
                else:
                    # Otherwise, just displays a "fake button"
                    object_display_label = st.session_state['selected_entity']['display_label']
                    col3.button(object_display_label, type='tertiary', key=f'explore-{graph["label"]}-{i}', help="The current entity")

                # Delete the triple in the graph
                if col4.button('🗑️', key=f'explore-delete-btn-{graph["label"]}-{i}', help='Click on this button to delete the triple', type='tertiary'):
                    
                    # Build the triple
                    subject = triple['subject'] if 'subject' in triple else st.session_state['selected_entity']['uri']
                    property = triple['predicate']
                    object = triple['object'] if 'object' in triple else st.session_state['selected_entity']['uri']

                    # Provide a nice message to user
                    dialog_confirmation(
                        f'You are about to delete the triple from graph "{graph["label"]}": <br><br>{subject_display_label}<br>{predicate_label}<br>{object_display_label}<br><br>', 
                        callback=delete, 
                        triples=[(subject, property, object)], 
                        graph=graph['uri']
                    )
