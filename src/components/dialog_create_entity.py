from typing import List
import streamlit as st
import lib.state as state
from lib.sparql_queries import find_entities, get_ontology
from lib.sparql_base import insert
from schema import Entity
from lib.utils import generate_id
from schema import Triple
from components.dialog_triple_info import dialog_triple_info

def __create_entity(entity: Entity, triples: List[Triple]) -> None:

    # From state
    graph = state.get_graph()

    # Create all the triples
    insert(triples, graph=graph.uri)

    # From formular, set the session entity
    state.set_entity(entity)

    # Finalization: validation message and load the created entity
    state.set_toast('Entity Created', ':material/done:')
    st.switch_page("pages/my-entities.py")



@st.dialog('Create an entity', width='large')
def dialog_create_entity() -> None:
    """
    Dialog function allowing the user to create a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    Class (rdf:type), label (rdfs:label), comment (rdfs:comment) are mandatory, whatever the ontology.
    """

    # Fetch the ontology in order to have all needed information 
    # about the selected class (and build the formular)
    # But also to know the class list to chose from
    ontology = get_ontology()

    # Save triples that are going to be created on create click
    triples: List[Triple] = []

    # Also, keep a list of mandatories properties to check if all of them are present
    mandatories: List[str] = []

    # In order to create those triples, we also need to have an id
    id = generate_id()
    entity_uri = f"base:{id}"


    ### First part: mandatory fields ###

    # In all case, we make 3 statements mandatory, independant of the entology.
    # They are: the class (rdf:type), the label (rdfs:label) and the comment (rdfs:comment).
    col1, col2 = st.columns([2, 3])

    # Class selection
    classes_labels = list(map(lambda cls: cls.display_label , ontology.classes))
    class_label = col1.selectbox('Class ❗️', options=classes_labels, index=None)
    mandatories.append('rdf:type')
    if class_label:
        # Find the selected class from the selected label
        class_index = classes_labels.index(class_label)
        selected_class = ontology.classes[class_index]
        triples.append(Triple(entity_uri, 'rdf:type', selected_class.uri))

        # Input field to set the entity label: it is mandatory
        entity_label = col2.text_input('Label ❗️')
        mandatories.append('rdfs:label')
        if entity_label:
            triples.append(Triple(entity_uri, 'rdfs:label', f"'{entity_label.strip()}'"))

        # Input field to set the comment label
        entity_comment = st.text_input('Comment')
        if entity_comment and entity_comment.strip() != '':
            triples.append(Triple(entity_uri, 'rdfs:comment', f"'{entity_comment.strip()}'"))

        st.divider()


        ### Second part: formular for all triples from ontology

        # Get the right relevant prop from the ontology
        # Only outgoing ones!
        props_to_create = [prop for prop in ontology.properties if prop.domain_class_uri == selected_class.uri]
        # Also, remove those that are mandatory, in order to not set them multiple times
        props_to_create = [prop for prop in props_to_create if prop.uri not in ['rdfs:label', 'rdfs:comment', 'rdf:type']]
        # And we order it so that it appears in the correct order
        props_to_create.sort(key=lambda p: p.order)

        # Loop through all relevant properties and display the right input Field
        for i, prop in enumerate(props_to_create):
            col11, col1, col2 = st.columns([2, 4, 6], vertical_alignment='center') 

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
                suffix = "❗️"
                mandatories.append(prop.uri)
            else:
                suffix = ""

            # On the left: Property label
            col1.markdown(f"### {prop.label} {suffix}")
            
            # For code simplification
            field_key = f"dlg-create-entity-field-{i}"

            # If the range is a xsd:string, display a text field
            if prop.range_class_uri == 'xsd:string':
                string_value = col2.text_input(ontology.get_class_name(prop.range_class_uri), key=field_key)
                if string_value and string_value.strip() != '':
                    triples.append(Triple(entity_uri, prop.uri, f"'{string_value.strip()}'"))

            # If the range is a xsd:html, display a text area
            elif prop.range_class_uri == 'xsd:html':
                html_value = col2.text_area(ontology.get_class_name(prop.range_class_uri), key=field_key)
                if html_value and html_value.strip() != '':
                    triples.append(Triple(entity_uri, prop.uri, f"'{html_value.strip()}'"))
            
            # If the range is not a Literal, it should then be instances of classes 
            else: 
                # List all possible existing entities (right class) from the endpoint
                possible_objects = find_entities(class_filter=prop.range_class_uri)
                # Get their label
                possible_objects_label = [obj.display_label_comment for obj in possible_objects]
                # User form input field
                object_label = col2.selectbox(ontology.get_class_name(prop.range_class_uri), options=possible_objects_label, key=field_key, index=None)
                if object_label:
                    object_index = possible_objects_label.index(object_label)
                    object = possible_objects[object_index]
                    triples.append(Triple(entity_uri, prop.uri, object.uri))

            st.text('')

        st.divider()

        # Check if all the mandatory properties are actually in the triple list
        all_mandatories_present = True
        triples_properties = set([triple.predicate_uri for triple in triples])
        for mandatory in mandatories:
            if not mandatory in triples_properties:
                all_mandatories_present = False
                break
        
        # Validation, creation, and display
        if st.button('Create', disabled=not all_mandatories_present, icon=':material/add:'):
            entity = Entity(
                uri=entity_uri, 
                label=entity_label, 
                comment=entity_comment, 
                class_uri=selected_class.uri,
                class_label=selected_class.label
            )
            __create_entity(entity, triples)