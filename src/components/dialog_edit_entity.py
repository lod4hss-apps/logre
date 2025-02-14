from typing import List
import streamlit as st
import lib.state as state
from lib.sparql_queries import find_entities, get_ontology
from lib.sparql_base import insert, delete
from schema import Entity
from schema import Triple, DisplayTriple

def __edit_entity(entity: Entity, triples_to_create: List[Triple], triples_to_delete: List[Triple]) -> None:

    # From state
    graph = state.get_graph()

    # Delete the wanted triples
    delete(triples_to_delete, graph=graph.uri)

    # Create the wanted triples
    insert(triples_to_create, graph=graph.uri)

    # From formular, set the session entity (in case label or comment have changed)
    state.set_entity(entity)

    # Finalization: validation message and load the created entity
    state.set_toast('Entity Updated', ':material/done:')
    st.switch_page("pages/my-entities.py")



@st.dialog('Edit an entity', width='large')
def dialog_edit_entity(entity: Entity, triples: List[DisplayTriple]) -> None:
    """
    Dialog function allowing the user to edit a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    Class (rdf:type), label (rdfs:label), comment (rdfs:comment) are mandatory, whatever the ontology.
    """

    # Save triples that are going to be created/deleted on save click
    triples_to_create: List[Triple] = []
    triples_to_delete: List[Triple] = []

    # Get the ontology, to have labels
    ontology = get_ontology()

    col1, col2 = st.columns([5, 1], vertical_alignment='bottom')
    col1.title(entity.display_label_comment)
    col2.button('', icon=':material/info:', type='tertiary', help='You can only edit outgoing triples, to edit an incoming one, go to the subject entity.')

    st.divider()

    ### First part: default mandatory fields ###

    # In all case, we make 3 statements mandatory, independant of the ontology.
    # They are: the class (rdf:type), the label (rdfs:label) and the comment (rdfs:comment).
    col1, col2 = st.columns([2, 3])

    # 1/ Class is fixed, we can not update it for an entity
    col1.selectbox('Class ❗️', options=[entity.class_label], index=0, disabled=True)

    # 2/ Input field to set the entity label
    new_entity_label = col2.text_input('Label ❗️', value=entity.label)
    # If the label is nothing, we forbid it: label is mandatory
    if new_entity_label.strip() == '':
        st.warning('This will have no effect: the label is mandatory')
    # Otherwise, delete the existing one, and create the new one
    elif new_entity_label != entity.label:
        triples_to_delete.append(Triple(entity.uri, 'rdfs:label', f"'{entity.label}'"))
        triples_to_create.append(Triple(entity.uri, 'rdfs:label', f"'{new_entity_label.strip()}'"))

    # 3/ Input field to set the comment label
    new_entity_comment = st.text_input('Comment', value=entity.comment)
    if new_entity_comment != entity.comment:
        triples_to_delete.append(Triple(entity.uri, 'rdfs:comment', f"'{entity.comment}'"))
        # Only append the new if it not an empty string
        if new_entity_comment.strip() != '': triples_to_create.append(Triple(entity.uri, 'rdfs:comment', f"'{new_entity_comment.strip()}'"))

    st.divider()


    ### Second part: formular for all triples from ontology

    # Get the right relevant prop from the ontology
    # Only outgoing ones!
    props_to_create = [prop for prop in ontology.properties if prop.domain_class_uri == entity.class_uri]
    # Also, remove those that are mandatory, in order to not set them multiple times
    props_to_create = [prop for prop in props_to_create if prop.uri not in ['rdfs:label', 'rdfs:comment', 'rdf:type']]
    # And we order it so that it appears in the correct order
    props_to_create.sort(key=lambda p: p.order)

    # Loop through all relevant properties and display the right input Field
    for i, prop in enumerate(props_to_create):
        col11, col1, col2 = st.columns([2, 4, 6], vertical_alignment='center') 

        # Fetch the existing triple
        existing_triples = [triple for triple in triples if triple.predicate.uri == prop.uri]
        if len(existing_triples): existing_triple = existing_triples[0]
        else: existing_triple = None

        # Information about the property
        with col11.popover('', icon=':material/info:'):
            st.markdown('### Property information')

            c1, c2 = st.columns([1, 1])
            c1.markdown("URI: ")
            c2.markdown(prop.uri)

            c1, c2 = st.columns([1, 1])
            c1.markdown("Order: ")
            c2.markdown(prop.order if prop.order != 1000000000000000000 else 'n')

            c1, c2 = st.columns([1, 1])
            c1.markdown("Minimal count: ")
            c2.markdown(prop.min_count)

            c1, c2 = st.columns([1, 1])
            c1.markdown("Maximal count: ")
            c2.markdown(prop.max_count if prop.max_count != 1000000000000000000 else 'n')

        # Append a special char if the field is mandatory
        # ie if the min cardinality is strictly bigger than 0
        # And add the property to the mandatories accordingly
        if prop.min_count != 0: 
            mandatory = True
            suffix = " ❗️"
        else: 
            suffix = ""
            mandatory = False


        # On the left: Property label
        col1.markdown(f"### {prop.label}{suffix}")
        
        # For code simplification
        field_key = f"dlg-edit-entity-field-{i}"

        # If the range is a xsd:string, display a text field
        if prop.range_class_uri == 'xsd:string':
            # Fetch the existing value (literal) if there is any
            existing_value = existing_triple.object.label if existing_triple else None
            # User form input field
            new_string_value = col2.text_input(ontology.get_class_name(prop.range_class_uri), key=field_key, value=existing_value)
            # If this property is mandatory, we forbid to set this property value to empty string
            if mandatory and new_string_value.strip() == '':
                st.warning('This will have no effect: this property is mandatory')
            elif new_string_value != existing_value:
                # Delete the old one, if there is any
                if existing_triple: triples_to_delete.append(Triple(entity.uri, prop.uri, f"'{existing_value}'"))
                # Only append the new if it not an empty string (not mandatory here)
                if new_string_value.strip() != '': triples_to_create.append(Triple(entity.uri, prop.uri, f"'{new_string_value.strip()}'"))

        # If the range is a xsd:html, display a text area
        elif prop.range_class_uri == 'xsd:html':
            # Fetch the existing value (literal) if there is any
            existing_value = existing_triple.object.label if existing_triple else None
            # User form input field
            new_html_value = col2.text_area(ontology.get_class_name(prop.range_class_uri), key=field_key, value=existing_value)
            # If this property is mandatory, we forbid to set this property value to empty string
            if mandatory and new_html_value.strip() == '':
                st.warning('This will have no effect: this property is mandatory')
            elif new_html_value != existing_value:
                # Delete the old one, if there is any
                if existing_triple: triples_to_delete.append(Triple(entity.uri, prop.uri, f"'{existing_value}'"))
                # Only append the new if it not an empty string (not mandatory here)
                if new_html_value.strip() != '': triples_to_create.append(Triple(entity.uri, prop.uri, f"'{new_html_value.strip()}'"))
        
        # If the range is not a Literal, it should then be instances of classes 
        else: 
            # List all possible existing entities (right class) from the endpoint
            possible_objects = find_entities(class_filter=prop.range_class_uri)
            # Get their label
            possible_objects_label = [obj.display_label_comment for obj in possible_objects]
            # If the property is mandatory, add the possibility to set to nothing
            if not mandatory: possible_objects_label = ['None'] + possible_objects_label
            # Target the existing entity with its uri, if any
            existing_object = [ent for ent in possible_objects if ent.uri == existing_triple.object.uri][0] if existing_triple else None
            # Get the index of this entity, if any
            existing_index = possible_objects_label.index(existing_object.display_label_comment) if existing_triple else None
            # Get its URI (for code conveniance), if any
            existing_uri = existing_object.uri if existing_triple else None
            # User form input field
            new_object_label = col2.selectbox(ontology.get_class_name(prop.range_class_uri), options=possible_objects_label, key=field_key, index=existing_index)
            if new_object_label:
                # If the user selected an entity
                if new_object_label != 'None':
                    object_index = possible_objects_label.index(new_object_label) - 1
                    new_object = possible_objects[object_index]
                    if new_object.uri != existing_uri:
                        if existing_triple: triples_to_delete.append(Triple(entity.uri, prop.uri, existing_uri))
                        triples_to_create.append(Triple(entity.uri, prop.uri, new_object.uri))
                # If the user selected 'None' and there was an entity, just delete the old one
                elif existing_triple:
                    triples_to_delete.append(Triple(entity.uri, prop.uri, existing_uri))


        st.text('')

    st.divider()

    # st.write('DELETE')
    # for triple in triples_to_delete:
    #     st.write(f"{triple.subject_uri} --- {triple.predicate_uri} --- {triple.object_uri}")
    # st.write('CREATE')
    # for triple in triples_to_create:
    #     st.write(f"{triple.subject_uri} --- {triple.predicate_uri} --- {triple.object_uri}")


    # Validation, edition, and display
    if st.button('Save', icon=":material/save:"):
        entity = Entity(
            uri=entity.uri, 
            label=new_entity_label.strip() if new_entity_label.strip() != '' else entity.label, # This might have changed
            comment=new_entity_comment.strip() if new_entity_comment.strip() != '' else entity.comment, # This might have changed
            class_uri=entity.class_uri,
            class_label=entity.class_label
        )
        __edit_entity(entity, triples_to_create, triples_to_delete)