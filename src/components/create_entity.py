import streamlit as st
import uuid
import time
from lib.utils import ensure_uri, generate_id
from lib.sparql_queries import insert, list_entities, get_objects_of, get_subjects_of
from lib.sparql_shacl import list_shacl_classes, list_shacl_class_properties
from lib.schema import Triple


@st.dialog("Create a new Entity", width='large')
def create_entity() -> None:
     
    graph_label = st.session_state['all_graphs'][st.session_state['activated_graph_index']]['label']
    st.markdown(f"**Graph: *{graph_label}***")

    if st.session_state['endpoint']['model_lang'] == 'SHACL':
        create_shacl_entity()
    else:
        create_entity_without_formular()



def create_entity_without_formular() -> None:
    """
    Dialog function allowing the user to create a new entity.
    User can fill the label, the class and the definition.
    Also, the only thing required to create the entity is the label.
    Class and Definition are optional.
    """

    # Formular
    col1, col2 = st.columns([1, 1])
    label = col1.text_input("Entity label ❗️", placeholder="Give a label", help="Will be object of a triple (new_entity, rdfs:label, 'your_label')")
    cls = col2.text_input("Entity class URI", placeholder="Set the class", help="eg. \"ontome:c21\" or \"https://ontome.net/ontology/c21\", or...")
    definition = st.text_area('Entity definition', placeholder="Write a definition", help="Will be object of a triple (new_entity, rdfs:comment, 'your_definition')")

    st.divider()

    # On click, if there is a label, create the entity
    if st.button('Create') and label:

        # Generate the entity key
        id = generate_id()

        # Create the correct triples
        triples = []
        if label:
            triples.append(Triple(f"base:{id}", "rdfs:label", f"'{label}'"))
        if cls:
            triples.append(Triple(f"base:{id}", "rdf:type", ensure_uri(cls)))
        if definition:
            triples.append(Triple(f"base:{id}", "rdfs:comment", f"'{definition}'"))

        # Insert triples
        graph = st.session_state['all_graphs'][st.session_state['activated_graph_index']]
        insert(triples, graph['uri'])

        # And select
        st.session_state['selected_entity'] = {
            'uri': f"base:{id}",
            'display_label': f"{label} ({cls if cls else 'Unknown'})"
        }
    
        # Finalization: validation message and reload
        st.success('Entity created.')
        time.sleep(1)
        st.rerun()



def create_shacl_entity() -> None:
    """
    Dialog function allowing the user to create a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    """

    graph = st.session_state['all_graphs'][st.session_state['activated_graph_index']]

    # List available classes
    all_classes = list_shacl_classes()
    all_classes_labels = [cls['label'] for cls in all_classes]

    # Select the class
    selected_class_label = st.selectbox('Select the class', placeholder='Choose a class', options=all_classes_labels, index=None)
    if selected_class_label:
        selected_class = [cls for cls in all_classes if cls['label'] == selected_class_label][0]

        # Fetch the properties: no need to sort, already done by the query
        property_nodes = list_shacl_class_properties(selected_class['uri'])
        property_nodes = list(filter(lambda property: property['domainClassURI'] == '', property_nodes))
        
        # Generate a uuid for the instance to create
        new_uri = f"base:{generate_id()}"

        triples = [Triple(new_uri, 'a', selected_class['uri'])]
        mandatories = []
        form_errors = []

        st.divider()

        # Construct the formular
        for i, property in enumerate(property_nodes):
            col1, col2 = st.columns([4, 7], vertical_alignment='center')
            
            # Here we avoid the display of a incoming identity defining proper  ty
            # Those properties can only by created from the correct class form
            # if property['domainClassURI'] and property['propertyMaxCount'] == "1":
            #     continue

            # Display property name
            # col1.write(property['propertyName'])
            col1.markdown(f"{property['propertyName']} *({property['propertyURI']})*")

            # Get mandatory suffix
            if int(property['propertyMinCount']) == 1:
                suffix = " ❗️"
                mandatories.append(f"{property['propertyName']} ({property['propertyURI']})")
            else: 
                suffix = ""

            # Field: If object should be a string
            if property['rangeDatatype'] == 'xsd:string':
                input_str = col2.text_input('Fill object (Literal)' + suffix, key=f'create-entity-field-{i}')
                if input_str:
                    triples.append(Triple(new_uri, property['propertyURI'], f"'{input_str}'"))

            # Field: If object should be a HTML
            elif property['rangeDatatype'] == 'rdf:HTML':
                input_html = col2.text_area('Fill object (HTML)' + suffix, key=f'create-entity-field-{i}')
                if input_html:
                    triples.append(Triple(new_uri, property['propertyURI'], f"'{input_html}'"))
            
            # Field: If object is an instance of a class
            elif property['rangeClassURI']:
                # Fetch all instance of the right class
                possible_objects = list_entities(cls=property['rangeClassURI'])
                display_labels = [f"{obj['label']} ({obj['class_label']})" for obj in possible_objects]

                # Allow user to choose from one of the existing instance
                selected_object_label = col2.selectbox(f"Choose a {property['rangeClassName']}" + suffix, options=display_labels, key=f'create-entity-field-{i}', index=None)

                if selected_object_label:
                    selected_subject = [obj for obj in possible_objects if f"{obj['label']} ({obj['class_label']})" == selected_object_label][0]

                    # Get existing triples for this entity with this property
                    existing_triples = get_objects_of(selected_subject['uri'], property['propertyURI'])

                    # If the selected entity already has reached maxCount, display message and forbid to create the entity
                    if len(existing_triples) >= float(property['propertyMaxCount']):
                        st.error('This triple can not be selected: Entity has already more (or equal) than the maximum number.')
                    else:
                        triples.append(Triple(new_uri, property['propertyURI'], selected_subject['uri']))

            # Field: If property is incoming (object should be an instance of a class)
            elif property['domainClassURI']:
                # Fetch all instance of the right class
                possible_subjects = list_entities(cls=property['domainClassURI'])
                display_labels = [f"{obj['label']} ({obj['class_label']})" for obj in possible_subjects]

                # Allow user to choose from one of the existing instance
                selected_subject_label = col2.selectbox(f"Choose a {property['domainClassName']}" + suffix, options=display_labels, key=f'create-entity-field-{i}', index=None)

                if selected_subject_label:
                    selected_subject = [obj for obj in possible_subjects if f"{obj['label']} ({obj['class_label']})" == selected_subject_label][0]

                    # Get existing triples for this entity with this property
                    existing_triples = get_subjects_of(selected_subject['uri'], property['propertyURI'])

                    # If the selected entity already has reached maxCount, display message and forbid to create the entity
                    if len(existing_triples) >= float(property['propertyMaxCount']):
                        st.error('This triple can not be selected: Entity has already more (or equal) than the maximum number.')
                        form_errors.append(f"{property['propertyURI']} - {property['propertyName']}")
                    else:
                        form_errors = [error for error in form_errors if property['propertyURI'] not in error]
                        triples.append(Triple(selected_subject['uri'], property['propertyURI'], new_uri))
        
        st.divider()
        
        for error in form_errors:
            st.error(f"Can not create entity: {error}")

        if st.button('Create', disabled=len(form_errors)):
            
            # Check if every mandatory properties are present
            valid = True
            all_properties_to_create = [triple.predicate for triple in triples]
            for mandatory in mandatories:
                # Extract property from mandatory display label
                mandatory_property = mandatory[mandatory.index('(')+1:mandatory.index(')')].strip()
                if mandatory_property not in all_properties_to_create:
                    valid = False
                    st.error(f'Please fill property: {mandatory}')
            
            if valid:
                graph = st.session_state['all_graphs'][st.session_state['activated_graph_index']]
                insert(triples, graph['uri'])

                # Finalization: validation message and reload
                st.success('Entity created.')
                time.sleep(1)
                st.rerun()

