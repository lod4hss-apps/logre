import streamlit as st
import uuid
import time
from lib.utils import ensure_uri, generate_uuid
from lib.sparql_queries import insert, list_entities, get_objects_of, get_subjects_of
from lib.sparql_shacl import list_available_classes, list_properties_of_node
from lib.schema import Triple


@st.dialog("Create a new Entity", width='large')
def create_entity() -> None:
    """
    Dialog function allowing the user to create a new entity.
    User can fill the label, the class and the definition.
    Also, the only thing required to create the entity is the label.
    Class and Definition are optional.
    """

    # Graph selection (where to insert the informations)
    graphs_labels = [graph['label'] for graph in st.session_state['all_graphs']]
    graph_label = st.selectbox('Select the graph in which insert the new entity', graphs_labels)  

    st.divider()
    
    # If there is a selected graph, fetch all the information about this graph from the session
    if graph_label:
        graph_index = graphs_labels.index(graph_label)
        graph = st.session_state['all_graphs'][graph_index]
        
    # Formular
    col1, col2 = st.columns([1, 1])
    label = col1.text_input("Entity label ❗️", placeholder="Give a label", help="Will be object of a triple (new_entity, rdfs:label, 'your_label')")
    cls = col2.text_input("Entity class URI", placeholder="Set the class", help="eg. \"ontome:c21\" or \"https://ontome.net/ontology/c21\", or...")
    definition = st.text_area('Entity definition', placeholder="Write a definition", help="Will be object of a triple (new_entity, rdfs:comment, 'your_definition')")

    st.divider()

    # On click, if there is a label, create the entity
    if st.button('Create') and label:

        # Generate the entity key (UUID5)
        input_string = label + (cls if cls else "Unknown") + (definition if definition else "Unknown") 
        id = str(uuid.uuid5(uuid.NAMESPACE_DNS, input_string))

        # Create the correct triples
        triples = []
        if label:
            triples.append(Triple(f"base:{id}", "rdfs:label", f"'{label}'"))
        if cls:
            triples.append(Triple(f"base:{id}", "rdf:type", ensure_uri(cls)))
        if definition:
            triples.append(Triple(f"base:{id}", "rdfs:comment", f"'{definition}'"))

        # Insert triples
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




@st.dialog("Create a new Entity", width='large')
def create_entity_() -> None:
    """
    Dialog function allowing the user to create a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    """

    # List available classes
    all_classes = list_available_classes()
    all_classes_labels = [cls['label'] for cls in all_classes]

    # Select the class
    selected_class_label = st.selectbox('Select the class', placeholder='Choose a class', options=all_classes_labels, index=None)
    if selected_class_label:
        selected_class = [cls for cls in all_classes if cls['label'] == selected_class_label][0]

        # Fetch the properties
        property_nodes = list_properties_of_node(selected_class['node'])
        property_nodes.sort(key=lambda obj: float(obj['order']))

        # Generate a uuid for the instance to create
        new_uri = f"base:{generate_uuid()}"

        triples = [Triple(new_uri, 'a', selected_class['uri'])]
        mandatories = []

        # Construct the formular
        for i, property in enumerate(property_nodes):
            col1, col2 = st.columns([3, 7], vertical_alignment='center')

            # Display property label
            col1.write(property['label'])

            # Get mandatory suffix
            if int(property['minCount']) == 1:
                suffix = " ❗️"
                mandatories.append(property['uri'])
            else: 
                suffix = ""

            # Field: If object should be a string
            if property['datatype'] == 'xsd:string':
                input_str = col2.text_input('Fill object (Literal)' + suffix, key=f'create-entity-field-{i}')
                if input_str:
                    triples.append(Triple(new_uri, property['uri'], f"'{input_str}'"))

            # Field: If object should be a HTML
            elif property['datatype'] == 'rdf:HTML':
                input_html = col2.text_area('Fill object (HTML)' + suffix, key=f'create-entity-field-{i}')
                if input_html:
                    triples.append(Triple(new_uri, property['uri'], f"'{input_html}'"))

            # Field: If object (or inverse Object) should be an instance of class
            elif property['datatype'] == '' and property['class'] != '':
                way = 'outgoing' if property['inverseUri'] != "" else 'incoming'

                possible_objects = list_entities(cls=property['class'])
                display_labels = [f"{obj['label']} ({obj['class_label']})" for obj in possible_objects]

                selected_object_label = col2.selectbox(f"Choose a {property['class']}" + suffix, options=display_labels, key=f'create-entity-field-{i}', index=None)
                if selected_object_label:
                    selected_object = [obj for obj in possible_objects if f"{obj['label']} ({obj['class_label']})" == selected_object_label][0]


                    # Verification
                    if way == 'incoming':
                        # Fetch all triples with the selected object and the property
                        existing_triples = get_subjects_of(selected_object['uri'], property['uri'])
                        if len(existing_triples) >= float(property['maxCount']):
                            st.error('This triple can not be selected: Entity has already more (or equal) than the maximum number.')
                    if way == 'outgoing':
                        # Fetch all triples with the selected object and the property
                        existing_triples = get_objects_of(selected_object['uri'], property['uri'])
                        if len(existing_triples) >= float(property['maxCount']):
                            st.error('This triple can not be selected: Entity has already more (or equal) than the maximum number.')



                    if way == "outgoing":
                        triples.append(Triple(selected_object['uri'], property['uri'], new_uri))
                    else:
                        triples.append(Triple(new_uri, property['uri'], selected_object['uri']))


        if st.button('Create'):
            
            # Check if every mandatory properties are present
            valid = True
            properties = [triple[1] for triple in triples]
            for mandatory in mandatories:
                if mandatory not in properties:
                    valid = False
                    st.error(f'Please fill property {mandatory}')
            
            if valid:
                insert(triples)

                # Finalization: validation message and reload
                st.success('Entity created.')
                time.sleep(1)
                st.rerun()

