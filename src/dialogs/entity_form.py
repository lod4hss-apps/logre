from typing import List, Tuple
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import lib.state as state
from model import OntoEntity, OntoProperty
from lib import generate_id


def __add_property_label(container: DeltaGenerator, prop: OntoProperty) -> None:

    label = f"## {prop.label}" + ("" if not prop.is_mandatory() else " ❗️")
    container.markdown(label)
    container.text('')


def __add_property_info(container: DeltaGenerator, prop: OntoProperty) -> None:
    
    # Information about the property
    with container.popover('', icon=':material/info:'):
        st.markdown('### Property information')

        c1, c2 = st.columns([1, 1])
        c1.markdown("label: ")
        c2.markdown(prop.label)

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


def __add_string_field(container: DeltaGenerator, range_class_label: str, values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """Display all current string values inside text inputs and add another empty one if limit is not reached"""

    add_values = []
    rem_values = []
    for i, value in enumerate(values):
        new_value = container.text_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{i}", value=value)
        if new_value != value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")
            rem_values.append(f"'{value}'")


    # Partie à revoir
    if len(values) < max_count:
        new_value = container.text_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}")
        if new_value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")

    return add_values, rem_values


def __add_html_field(container: DeltaGenerator, range_class_label: str, values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """Display all current HTML values inside text areas and add another empty one if limit is not reached"""

    add_values = []
    rem_values = []
    for i, value in enumerate(values):
        new_value = container.text_area(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}", value=value)
        if new_value != value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")
            rem_values.append(f"'{value}'")
    

    # Partie à revoir
    if len(values) < max_count:
        new_value = container.text_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}")
        if new_value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")

    return add_values, rem_values


def __add_class_field(container: DeltaGenerator, range_class_label: str, range_class_uri: str, uri_values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """Display all current HTML values inside select boxes (or multi select) and add another empty one if limit is not reached"""

    add_values = []
    rem_values = []

    data_bundle = state.get_data_bundle()
    possible_objects: List[OntoEntity] = data_bundle.find_entities(class_uri=range_class_uri)
    possible_objects_label = [obj.display_label_comment for obj in possible_objects]

    if max_count == 1:

        for uri in uri_values:
            entity = data_bundle.get_entity_infos(uri)
            
            # We do this because for some classes, a property can have multiple range classes (eg is membership of group OR/AND person)
            # So when the entity has one, the formular tries to fit the class in the other (find the person among the groups)
            # Which raises an error (of course)
            # Also true for the "index is not None" in the Following "if"
            if entity.display_label_comment in possible_objects_label: index = possible_objects_label.index(entity.display_label_comment)
            else: index = None
            new_value = container.selectbox(range_class_label, options=possible_objects_label, key=f"dialog-entity-form-prop-{prop_index}-{len(uri_values) + 1}", index=index)
            if index is not None and new_value != entity.display_label_comment:
                add_values.append(possible_objects[possible_objects_label.index(new_value)].uri)
                rem_values.append(entity.uri)


    # Partie à revoir
        if len(uri_values) < max_count:
            new_value = container.selectbox(range_class_label, options=possible_objects_label, key=f"dialog-entity-form-prop-{prop_index}-{len(uri_values) + 1}", index=None)
            if new_value and new_value.strip() != "":
                add_values.append(possible_objects[possible_objects_label.index(new_value)].uri)

        
    else:

        defaults = [data_bundle.get_entity_infos(uri) for uri in uri_values]
        defaults_label = [ent.display_label_comment for ent in defaults]
        new_values = container.multiselect(range_class_label, options=possible_objects_label, default=defaults_label, max_selections=max_count)

        for new_value in new_values:
            if new_value not in defaults_label:
                add_values.append(possible_objects[possible_objects_label.index(new_value)].uri)
        for old_value in defaults_label:
            if old_value not in new_values:
                rem_values.append(possible_objects[possible_objects_label.index(old_value)].uri)

    return add_values, rem_values




@st.dialog('Entity formular', width='large')
def dialog_entity_form(entity: OntoEntity = None, triples: List[tuple[str, str, str]] = []) -> None:
    """
    Dialog function allowing the user to create or edit a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    """

    # From state
    data_bundle = state.get_data_bundle()
    classes = data_bundle.ontology.get_classes()
    properties = data_bundle.ontology.get_properties()

    # Save triples that are going to be created on create click
    triples_to_add: List[tuple[str, str, str]] = []
    triples_to_rem: List[tuple[str, str, str]] = []

    # Also, keep a list of mandatories properties to check if all of them are present
    mandatories: List[str] = []

    # In order to create those triples, we also need to have an id and a URI for the entity to be created, 
    # They are generated on dialog open
    if entity: entity_uri = entity.uri
    else:
        id = generate_id()
        entity_uri = f"base:{id}"

    # Class selection (if entity creation, otherwise block the class change)
    classes_labels = list(map(lambda cls: cls.display_label, classes))
    index = None if not entity else classes_labels.index(entity.class_label)
    disabled = False if not entity else True
    col1, _ = st.columns([1, 2])
    st.divider()
    class_label = col1.selectbox('Class ❗️', options=classes_labels, index=index, disabled=disabled)
    mandatories.append(data_bundle.type_property)
    if class_label:

        # Find the selected class from the selected label
        class_index = classes_labels.index(class_label)
        selected_class = classes[class_index]
        triples_to_add.append((entity_uri, data_bundle.type_property, selected_class.uri))

        # Select properties of interest
        properties = [prop for prop in properties if prop.domain_class_uri == selected_class.uri]

        # Order them so that they appears in the correct order
        properties.sort(key=lambda p: p.order)

        for i, prop in enumerate(properties):

            if prop.is_mandatory(): mandatories.append(prop.uri)

            col_label, col_range, col_info = st.columns([4, 6, 2], vertical_alignment='bottom') 

            range_class_name = data_bundle.ontology.get_class_name(prop.range_class_uri)
            existing_values = list(map(lambda t: t[2], filter(lambda t: t[1] == prop.uri, triples)))

            __add_property_label(col_label, prop)
            __add_property_info(col_info, prop)

            if prop.range_class_uri == "xsd:string": 
                add, rem = __add_string_field(col_range, range_class_name, existing_values, prop.max_count, i)
            elif prop.range_class_uri == "xsd:html":
                add, rem = __add_html_field(col_range, range_class_name, existing_values, prop.max_count, i)
            else:
                add, rem = __add_class_field(col_range, range_class_name, prop.range_class_uri, existing_values, prop.max_count, i)

            for value in add: 
                triples_to_add.append((entity_uri, prop.uri, value))
            for value in rem: 
                triples_to_rem.append((entity_uri, prop.uri, value))
            
            st.text('')
            # st.divider()


        # Check if all mandatory fields are present
        have_props = list(map(lambda t: t[1], triples)) + list(map(lambda t: t[1], triples_to_add))
        ready = all([p in have_props for p in mandatories])

        st.divider()

        # Validation, creation, and load
        if st.button('Save', disabled=not ready, icon=':material/save:'):

            data_bundle.graph_data.delete(triples_to_rem)
            data_bundle.graph_data.insert(triples_to_add)

            entity = data_bundle.get_entity_infos(entity_uri)
            state.set_entity(entity)

            # Clear the cache
            data_bundle.get_outgoing_statements.clear()

            # Finalization: validation message and load the created entity
            state.set_toast('Entity saved', ':material/done:')
            st.switch_page("pages/entity.py")
        

