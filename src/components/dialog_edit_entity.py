from typing import List
import streamlit as st
from lib.sparql_queries import find_entities, get_ontology
from lib.sparql_base import insert, delete
import lib.state as state
from schema import Entity, Triple, DisplayTriple


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
    st.switch_page("pages/entity.py")


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

    col_label, col_range = st.columns([5, 1], vertical_alignment='bottom')
    col_label.title(entity.display_label_comment)
    col_range.button('', icon=':material/info:', type='tertiary', help='You can only edit outgoing triples, to edit an incoming one, go to the subject entity.')

    st.divider()

    ### First part: default mandatory fields ###

    # In all case, we make 3 statements mandatory, independant of the ontology.
    # They are: the class (rdf:type), the label (rdfs:label) and the comment (rdfs:comment).
    col_label, col_range = st.columns([2, 3])

    # 1/ Class is fixed, we can not update it for an entity
    col_label.selectbox('Class ❗️', options=[entity.class_label], index=0, disabled=True)

    # 2/ Input field to set the entity label
    new_entity_label = col_range.text_input('Label ❗️', value=entity.label)
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
        entity.comment = new_entity_comment

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
        col_label, col_range, col_info = st.columns([4, 6, 2], vertical_alignment='bottom') 

        # Fetch the existing triple
        existing_triples = [triple for triple in triples if triple.predicate.uri == prop.uri]
        if len(existing_triples): existing_triple = existing_triples[0]
        else: existing_triple = None

        # Information about the property
        with col_info.popover('', icon=':material/info:'):
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
        col_label.markdown(f"### {prop.label}{suffix}")
        
        # For code simplification
        field_key = f"dlg-edit-entity-field-{i}"

        # If the range is a xsd:string, display a text field
        if prop.range_class_uri == 'xsd:string':
            # Get all the existing labels from the existing triples
            existing_values = [triple.object.label for triple in existing_triples]

            # For each one of them, display it correctly, and give wanted behavior (create/delete on save click)
            for j, existing_value in enumerate(existing_values):
                new_string_value = col_range.text_input(ontology.get_class_name(prop.range_class_uri), key=field_key + f'-{j}', value=existing_value)
                # If this property is mandatory, we forbid to set this property value to empty string
                if mandatory and new_string_value.strip() == '':
                    st.warning('This will have no effect: this property is mandatory')
                elif new_string_value != existing_value:
                    # Delete the old one, if there is any
                    if existing_triple: triples_to_delete.append(Triple(entity.uri, prop.uri, f"'{existing_value}'"))
                    # Only append the new if it not an empty string (not mandatory here)
                    if new_string_value.strip() != '': triples_to_create.append(Triple(entity.uri, prop.uri, f"'{new_string_value.strip()}'"))
   
            # Dedicated behavior:
            # Here, if the property have a max count greater that 1,
            # We would like to give the user the possibility to add them accrodingly
            # So the strategy is the following:
            # Each time the user fill a value, we display another empty field so that he can add another value
            # Of course it is limited by the max count of the cardinality, once it is reached

            def recursive_call_xsdstring(index: int) -> None:
                """Recursive call that add another field each time the previous one has a value (and maxcount not reached)."""
                string_value = col_range.text_input(ontology.get_class_name(prop.range_class_uri), key=field_key + f"-{len(existing_values)+index}", placeholder="Start writing to add a new value")
                if string_value and string_value.strip() != '':
                    triples_to_create.append(Triple(entity.uri, prop.uri, f"'{string_value.strip()}'"))
                if string_value and index + 1 < prop.max_count:
                    recursive_call_xsdstring(index + 1)

            # If we do not yet have reached max value, add possibility to add some
            if len(existing_values) < prop.max_count: 
                recursive_call_xsdstring(len(existing_values)) 


        # If the range is a xsd:html, display a text area
        elif prop.range_class_uri == 'xsd:html':

            # Get all the existing labels from the existing triples
            existing_values = [triple.object.label for triple in existing_triples]

            # For each one of them, display it correctly, and give wanted behavior (create/delete on save click)
            for j, existing_value in enumerate(existing_values):
                new_html_value = col_range.text_area(ontology.get_class_name(prop.range_class_uri), key=field_key + f'-{j}', value=existing_value)
                # If this property is mandatory, we forbid to set this property value to empty string
                if mandatory and new_html_value.strip() == '':
                    st.warning('This will have no effect: this property is mandatory')
                elif new_html_value != existing_value:
                    # Delete the old one, if there is any
                    if existing_triple: triples_to_delete.append(Triple(entity.uri, prop.uri, f"'{existing_value}'"))
                    # Only append the new if it not an empty string (not mandatory here)
                    if new_html_value.strip() != '': triples_to_create.append(Triple(entity.uri, prop.uri, f"'{new_string_value.strip()}'"))
   
            # Dedicated behavior:
            # Here, if the property have a max count greater that 1,
            # We would like to give the user the possibility to add them accrodingly
            # So the strategy is the following:
            # Each time the user fill a value, we display another empty field so that he can add another value
            # Of course it is limited by the max count of the cardinality, once it is reached

            def recursive_call_xsdhtml(index: int) -> None:
                """Recursive call that add another field each time the previous one has a value (and maxcount not reached)."""
                html_value = col_range.text_area(ontology.get_class_name(prop.range_class_uri), key=field_key + f"-{len(existing_values)+index}", placeholder="Start writing to add a new value")
                if html_value and html_value.strip() != '':
                    triples_to_create.append(Triple(entity.uri, prop.uri, f"'{html_value.strip()}'"))
                if html_value and index + 1 < prop.max_count:
                    recursive_call_xsdhtml(index + 1)

            # If we do not yet have reached max value, add possibility to add some
            if len(existing_values) < prop.max_count: 
                recursive_call_xsdhtml(len(existing_values)) 


        # If the range is not a Literal, it should then be instances of classes 
        else: 
            # List all possible existing entities (right class) from the endpoint
            possible_objects = find_entities(class_filter=prop.range_class_uri)
            # Get their label
            possible_objects_label = [obj.display_label_comment for obj in possible_objects]

            # Only if this prop has max cardinality equal to 1
            if prop.max_count == 1:
                # If the property is mandatory, add the possibility to set to nothing
                if not mandatory: possible_objects_label = ['None'] + possible_objects_label
                # Target the existing entity with its uri, if any
                existing_object = [ent for ent in possible_objects if ent.uri == existing_triple.object.uri][0] if existing_triple else None
                # Get the index of this entity, if any
                existing_index = possible_objects_label.index(existing_object.display_label_comment) if existing_triple else None
                # Get its URI (for code conveniance), if any
                existing_uri = existing_object.uri if existing_triple else None
                # User form input field
                new_object_label = col_range.selectbox(ontology.get_class_name(prop.range_class_uri), options=possible_objects_label, key=field_key, index=existing_index)
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
            
            # If it can have multiple ranges:
            else:
                # Target all the existing entities so that they are correctly displayed
                existing_objects_uris = [triple.object.uri for triple in triples if triple.predicate.uri == prop.uri]
                existing_objects = [ent for ent in possible_objects if ent.uri in existing_objects_uris]
                existing_objects_labels = [ent.display_label for ent in existing_objects]

                # Allow user to modify current values
                new_object_labels = col_range.multiselect(ontology.get_class_name(prop.range_class_uri), options=possible_objects_label, key=field_key, default=existing_objects_labels)

                # Find the selected entities
                new_objects_uris = [ent.uri for ent in possible_objects if ent.display_label in new_object_labels]
                
                # Find the triples to delete
                uri_to_delete = [uri for uri in existing_objects_uris if uri not in new_objects_uris]
                for uri in uri_to_delete:
                    triples_to_delete.append(Triple(entity.uri, prop.uri, uri))
                
                # Find the triples to create
                uri_to_create = [uri for uri in new_objects_uris if uri not in existing_objects_uris]
                for uri in uri_to_create:
                    triples_to_create.append(Triple(entity.uri, prop.uri, uri))

        st.text('')

    st.divider()

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