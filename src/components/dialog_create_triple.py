import streamlit as st
from schema import Triple
from lib.sparql_queries import find_entities, get_ontology
from lib.sparql_base import insert
import lib.state as state

@st.dialog("Create a new Triple", width='large')
def dialog_create_triple() -> None:
    """Dialog function allowing the user to create a new triple, following the ontology, or not."""


    # From state
    graph = state.get_graph()

    ontology = get_ontology()

    st.markdown('First choose an existing entity:')
    st.text('')

    col1, col2 = st.columns([1, 2])

    # Class filter
    classes_labels = list(map(lambda cls: cls.display_label , ontology.classes))
    class_label = col1.selectbox('Entity is instance of class:', options=classes_labels, index=None)
    # Label filter
    entity_label = col2.text_input('Entity label contains:', help='Write the entity label (or a part of it) and hit "Enter"')

    # Find the selected entity from the selected label
    if class_label:
        class_index = classes_labels.index(class_label)
        selected_class_uri = ontology.classes[class_index].uri
    else:
        selected_class_uri = None

    # Fetch the entities
    entities = find_entities(
        label_filter=entity_label if entity_label else None,
        class_filter=selected_class_uri,
        limit=5
    )


    # Set the state selected entity as being the one chosen
    st.text('')
    for i, entity in enumerate(entities):
        col1, col2, col3 = st.columns([2, 1, 1], vertical_alignment='center')
        col1.write(entity.display_label_comment)
        if col2.button('Choose as subject', key=f'dlg-create-triple-choose-subject-{i}'):
            state.set_create_triple_subject(entity)
        if col3.button('Choose as object', key=f'dlg-create-triple-choose-object-{i}'):
            state.set_create_triple_object(entity)



    st.divider()

    st.markdown('Then choose which property link those entity together:')

    # ontology = st.checkbox('Use the ontology', value=True)
    use_ontology = st.radio('Use the ontology', options=['Yes', 'No'], index=0, horizontal=True)

    st.text('')

    col1, col1b, col2, col2b, col3, col3b = st.columns([2, 1, 2, 1, 2, 1], vertical_alignment="center")

    col1.write("Subject:")
    col1b.button('', icon=':material/info:', type='tertiary', help='Choose a subject from the search entity fields below')
    col2.write("Predicate:")
    col2b.button('', icon=':material/info:', type='tertiary', help='Choose a subject and an object before choosing the property')
    col3.write("Object:")
    col3b.button('', icon=':material/info:', type='tertiary', help='Choose an object from the search entity fields below')

    col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="center")

    # Display selected subject
    subject = state.get_create_triple_subject()
    if subject: 
        col1.write(subject.display_label)

    # Display selected object
    object = state.get_create_triple_object()
    if object: 
        col3.write(object.display_label)

    # Display/Select the predicate
    property_label = state.get_create_triple_property()
    property_uri = None
    if use_ontology == 'Yes':
        if subject and object:
            properties = ontology.properties
            filtered_properties = [prop for prop in properties if prop.domain_class_uri == subject.class_uri and prop.range_class_uri == object.class_uri]
            if len(filtered_properties) == 0:
                col2.markdown('*There are no properties linking this domain class with this range class*')
            else:
                properties_label = [prop.label for prop in filtered_properties]
                property_label = col2.selectbox(label='', label_visibility='collapsed', options=properties_label, index=None)
                if property_label:
                    property_index = properties_label.index(property_label)
                    # Here we are interested in the property URI, because if the user choose 'No' at the ontology question,
                    # he can then only set property URI.
                    property_uri = filtered_properties[property_index].uri
    else:
        property_uri = col2.text_input('Property URI as string', placeholder='eg. "rdfs:label"')


    st.text('')

    if subject and property_uri and object and st.button('Create'):
        triple = Triple(subject.uri, property_uri, object.uri)
        insert([triple], graph.uri)
        state.clear_create_triple_subject()
        state.clear_create_triple_predicate()
        state.clear_create_triple_object()
        st.rerun()
