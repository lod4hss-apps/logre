from typing import List
import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation
from components.find_entities import dialog_find_entity
from components.create_entity import create_entity
from components.create_triple import create_triple
from lib.sparql_queries import list_entity_triples, delete, get_outgoing_triples_raw, get_incoming_triples_raw, insert, list_entities
from lib.sparql_shacl import build_shacl_card, get_properties_infos_shacl
from lib.schema import Triple
import pandas as pd


##### Functions #####

def delete_from_graph(entity_uri: str, graph_uri: str):
    """Delete all triples of a given entity in a given graph."""

    triples_outgoing = Triple(entity_uri, '?predicate', '?object')
    triples_incoming = Triple('?subject', '?predicate', entity_uri)

    delete([triples_outgoing], graph=graph_uri)
    delete([triples_incoming], graph=graph_uri)
    del st.session_state['selected_entity']


##### The page #####

init(layout='wide')
menu()



if "endpoint" not in st.session_state:
    st.warning('You must first chose an endpoint in the menu before accessing explore page')

else:

    graph = st.session_state['all_graphs'][st.session_state['activated_graph_index']]

    # General user commands
    col1, col2, col3 = st.columns([1, 1, 1])
    if col1.button('Find an entity'):
        dialog_find_entity()
    if col2.button('Create an entity'):
        create_entity()
    if st.session_state['endpoint']['model_lang'] not in ['SHACL']:
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
        if col3.button('🗑️', help='Delete all triples (incoming and outgoing) of this entity in selected graph'):
            dialog_confirmation(
                f"You are about to delete all triples from entity {st.session_state['selected_entity']['display_label']} from graph {graph['label']}",
                callback=delete_from_graph,
                entity_uri=st.session_state['selected_entity']['uri'],
                graph_uri=graph['uri']
            )

        tab1, tab2, tab3 = st.tabs(['Card', 'Triples', 'Visualization'])

        ### CARD ###

        tab1.text('')

        if st.session_state['endpoint']['model_lang'] != 'SHACL':
            st.markdown('This view is available if your SPARQL endpoint is correctly configured with a SHACL graph.')
            st.markdown('If you do not have a SHACL endpoint, please use the other tabs')
        else:

            # List all properties from the ontology
            entity_uri = st.session_state['selected_entity']['uri']
            class_uri = st.session_state['selected_entity']['class_uri']
            card = build_shacl_card(entity_uri, class_uri, graph['uri'])

            # card

            for i, row in card.iterrows():
                cardinality = f"{row['propertyMinCount']} to {row['propertyMaxCount'] if row['propertyMaxCount'] != 'inf' else 'n'}"
                
                col_left, col, col_right = tab1.columns([3, 5, 3], vertical_alignment='center')
                if row['rangeDatatype'] == "xsd:string":
                    value = row['objectLabel'] if pd.notna(row['objectLabel']) else ''
                    new_value = col.text_input(f"{row['propertyName']} ({cardinality} -- {row['rangeDatatype']})", value=value)
                    if new_value != row['objectLabel']:
                        old_triple = Triple(st.session_state['selected_entity']['uri'], row['propertyURI'], f"'{row['objectLabel']}'")
                        new_triple = Triple(st.session_state['selected_entity']['uri'], row['propertyURI'], f"'{new_value}'")
                        delete([old_triple], graph['uri'])
                        insert([new_triple], graph['uri'])
                        if row['propertyURI'] == 'rdfs:label':
                            st.session_state['selected_entity']['display_label'] = f"{new_value} ({st.session_state['selected_entity']['class_label']})"
                            st.rerun()
                        else:
                            st.toast('Entity updated', icon="✅")
                elif row['rangeDatatype'] == "rdf:HTML":
                    value = row['objectLabel'] if pd.notna(row['objectLabel']) else ''
                    new_value = col.text_area(f"{row['propertyName']} ({cardinality} -- {row['rangeDatatype']})", value=value)
                    if new_value != row['objectLabel']:
                        old_triple = Triple(st.session_state['selected_entity']['uri'], row['propertyURI'], f"'{row['objectLabel']}'")
                        new_triple = Triple(st.session_state['selected_entity']['uri'], row['propertyURI'], f"'{new_value}'")
                        delete([old_triple], graph['uri'])
                        insert([new_triple], graph['uri'])
                        st.toast('Entity updated', icon="✅")
                else:
                    uri = row['object'] if row['object'] else row['subject']
                    label = row['objectLabel'] if row['objectLabel'] else row['subjectLabel']
                    cls = row['rangeClassName'] if row['rangeClassName'] != "" else row['domainClassName']
                    cls_uri = row['rangeClassURI'] if row['rangeClassURI'] != "" else row['domainClassURI']
                    col.markdown(f"{row['propertyName']} ({cardinality})")

                    # If the triple has a value
                    if uri: 
                        col1, col2 = col.columns([1, 8])
                        if col2.button(f"{label} ({cls})", help="Jump to this entity card"):
                            st.session_state['selected_entity'] = {
                                'uri': uri,
                                'display_label': f"{label} ({cls})",
                                'class_uri': cls_uri,
                                'class_label': cls,
                            }
                            st.rerun()
                    

                        outgoing_triples = pd.DataFrame(get_outgoing_triples_raw(uri, graph['uri']))
                        all_properties = pd.DataFrame(get_properties_infos_shacl())
                        
                        all_properties = all_properties[all_properties['domainClassURI'] == cls_uri]
                        outgoing_triples = outgoing_triples.merge(all_properties, left_on='predicate', right_on='propertyURI', how='left')

                        for _, triple in outgoing_triples.iterrows():
                            if triple['predicate'] == 'rdfs:label':
                                continue
                            if triple['predicate'] == 'rdf:type':
                                continue
                            if triple['predicate'] == row['propertyURI']:
                                continue
                            col2.markdown(f"- {triple['propertyLabel']} -- {triple['object_label']}")

                    # If it has no value yet
                    else:   
                        cls_uri = row['rangeClassURI'] if row['rangeClassURI'] else row['domainClassURI']

                        entities_of_class = list_entities(cls=cls_uri)
                        entities_of_class_labels = [f"{entity['label']}" for entity in entities_of_class]
                        entity_label = col.selectbox('Select an entity', entities_of_class_labels, key=f'card-multiselect-{i}', index=None)
                        if entity_label:
                            entity = entities_of_class[entities_of_class_labels.index(entity_label)]
                            subject = st.session_state['selected_entity']['uri'] if not row['domainClassURI'] else entity['uri']
                            object = st.session_state['selected_entity']['uri'] if row['domainClassURI'] else entity['uri']
                            triple = Triple(subject, row['propertyURI'], object)
                            insert([triple], graph=graph['uri'])
                            st.toast('Triple created', icon='✅')
                            st.rerun()


                if col_right.button('Delete', key=f'card-delete-btn-{i}', disabled=int(row['propertyMinCount']) == 1 or not row['object'] and not row['subject']):
                    subject = row['subject'] if row['subject'] != '' else st.session_state['selected_entity']['uri']
                    predicate = row['propertyURI']
                    object = row['object'] if row['object'] != '' else st.session_state['selected_entity']['uri']
                    if row['rangeDatatype'] != '':
                        object = f"'{object}'"
                    st.write(f"{subject} {predicate} {object}")
                    dialog_confirmation(f"You are about to delete:<br/>{subject} -- {predicate} -- {object}.", delete, triples=[Triple(subject, predicate, object)], graph=graph['uri'])

                col.text('')



            ### ALL TRIPLES ### 

            tab2.text('')
            tab2.markdown('## Outgoing triples')
            tab2.text('')

            outgoing_triples = get_outgoing_triples_raw(st.session_state['selected_entity']['uri'], graph['uri'])

            col1, col2, col3 = tab2.columns([1, 1, 1], vertical_alignment='center')
            col1.markdown(st.session_state['selected_entity']['display_label'])
            for triple in outgoing_triples:
                col2.markdown(triple['predicate_label'])
                col3.markdown(f"{triple['object_label']} ({triple['object_class_label']})")

            tab2.text('')
            tab2.text('')

            col1, col2 = tab2.columns([1, 3], vertical_alignment='bottom')
            col1.markdown('## Incoming triples')
            tab2.text('')
            
            if col2.button('Fetch incoming triples', help='Be ware! Depending on your entity this request can be heavy!'):
                incoming_triples = get_incoming_triples_raw(st.session_state['selected_entity']['uri'], graph['uri'])

                if len(incoming_triples):
                    col1, col2, col3 = tab2.columns([1, 1, 1], vertical_alignment='center')
                    for triple in incoming_triples:
                        col1.markdown(f"{triple['subject_label']} ({triple['subject_class_label']})")
                        col2.markdown(triple['predicate_label'])
                    if len(incoming_triples):
                        col3.markdown(st.session_state['selected_entity']['display_label'])

                else:
                    tab2.text('')
                    tab2.markdown('*This entity has no incoming triples*')


        ### VISUALIZATION ###

        tab3.write('Coming soon')


