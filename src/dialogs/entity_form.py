from typing import List, Tuple
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# Local imports
import lib.state as state
from model import OntoEntity, OntoProperty
from lib import generate_uri


def __add_property_label(container: DeltaGenerator, prop: OntoProperty) -> None:
    "Private function that display the label of a property in the formular."

    # Build the label
    label = f"## {prop.label}" + ("" if not prop.is_mandatory() else " ❗️")

    # Add it to the formular
    container.markdown(label)
    container.text('')


def __add_property_info(container: DeltaGenerator, prop: OntoProperty) -> None:
    """Private function that add a info button to have additional information about the given property."""
    
    # Information about the property
    with container.popover('', icon=':material/info:'):
        st.markdown('### Property information')

        # Its label
        c1, c2 = st.columns([1, 1])
        c1.markdown("label: ")
        c2.markdown(prop.label)

        # Its URI
        c1, c2 = st.columns([1, 1])
        c1.markdown("URI: ")
        c2.markdown(prop.uri)

        # Its order in the formular
        c1, c2 = st.columns([1, 1])
        c1.markdown("Order: ")
        c2.markdown(prop.order if prop.order != 1000000000000000000 else 'n')

        # The minimum count for this property any instance of this class should have
        c1, c2 = st.columns([1, 1])
        c1.markdown("Minimal count: ")
        c2.markdown(prop.min_count)

        # The maximum count for this property any instance of this class should have
        c1, c2 = st.columns([1, 1])
        c1.markdown("Maximal count: ")
        c2.markdown(prop.max_count if prop.max_count != 1000000000000000000 else 'n')


# TODO: Rework this function: does not work as expected
# GUI does not update accordingly: when a value is set and limit not reach, a new empty one does not appear interactively.

def __add_string_field(container: DeltaGenerator, range_class_label: str, values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """
    Display all current string values inside text inputs and add another empty one if limit is not reached.
    
    Returns:
        tuple: A tuple with 2 elements:
            - list: triples to create
            - list: triples to remove
    """

    # This variable keeps track of all the values to add to the graph
    add_values = []

    # This variable keeps track of all the values to remove from the graph
    rem_values = []

    # For each existing values, display it in a text input
    for i, value in enumerate(values):
        new_value = container.text_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{i}", value=value)
        if new_value != value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")
            rem_values.append(f"'{value}'")

    # If max value is not reached, add a additional empty field
    if len(values) < max_count:
        new_value = container.text_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}")
        if new_value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")

    # Returns triples to add and triples to remove
    return add_values, rem_values


# TODO: Rework this function: does not work as expected
# GUI does not update accordingly: when a value is set and limit not reach, a new empty one does not appear interactively.

def __add_html_field(container: DeltaGenerator, range_class_label: str, values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """
    Display all current HTML values inside text areas and add another empty one if limit is not reached.
    
    Returns:
        tuple: A tuple with 2 elements:
            - list: triples to create
            - list: triples to remove
    """

    # This variable keeps track of all the values to add to the graph
    add_values = []

    # This variable keeps track of all the values to remove from the graph
    rem_values = []

    # For each existing values, display it in a text input
    for i, value in enumerate(values):
        new_value = container.text_area(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}", value=value)
        if new_value != value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")
            rem_values.append(f"'{value}'")

    # If max value is not reached, add a additional empty field
    if len(values) < max_count:
        new_value = container.text_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}")
        if new_value and new_value.strip() != "":
            add_values.append(f"'{new_value}'")

    # Returns triples to add and triples to remove
    return add_values, rem_values

def __add_integer_field(container: DeltaGenerator, range_class_label: str, values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """
    Display all current integer values inside number inputs and add another empty one if limit is not reached.
    
    Returns:
        tuple: A tuple with 2 elements:
            - list: triples to create
            - list: triples to remove
    """

    # This variable keeps track of all the values to add to the graph
    add_values = []

    # This variable keeps track of all the values to remove from the graph
    rem_values = []

    # For each existing values, display it in a text input
    for i, value in enumerate(values):
        new_value = container.number_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}", value=value, min_value=0, step=1)
        if new_value != value and new_value != 0:
            add_values.append(new_value)
            rem_values.append(value)

    # If max value is not reached, add a additional empty field
    if len(values) < max_count:
        new_value = container.number_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}", min_value=0, step=1)
        if new_value and new_value != 0:
            add_values.append(new_value)

    # Returns triples to add and triples to remove
    return add_values, rem_values

def __add_float_field(container: DeltaGenerator, range_class_label: str, values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """
    Display all current integer values inside number inputs and add another empty one if limit is not reached.
    
    Returns:
        tuple: A tuple with 2 elements:
            - list: triples to create
            - list: triples to remove
    """

    # This variable keeps track of all the values to add to the graph
    add_values = []

    # This variable keeps track of all the values to remove from the graph
    rem_values = []

    # For each existing values, display it in a text input
    for i, value in enumerate(values):
        new_value = container.number_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}", value=float(value), min_value=0., step=0.1)
        if new_value != value and new_value != 0:
            add_values.append(new_value)
            rem_values.append(value)

    # If max value is not reached, add a additional empty field
    if len(values) < max_count:
        new_value = container.number_input(range_class_label, key=f"dialog-entity-form-prop-{prop_index}-{len(values) + 1}", min_value=0., step=0.1)
        if new_value and new_value != 0:
            add_values.append(new_value)

    # Returns triples to add and triples to remove
    return add_values, rem_values


# TODO: Rework this function: does not work as expected
# GUI does not update accordingly: when a value is set and limit not reach, a new empty one does not appear interactively.

def __add_class_field(container: DeltaGenerator, range_class_label: str, range_class_uri: str, uri_values: List[str], max_count: int, prop_index: int) -> Tuple[List[str], List[str]]:
    """
    Display all current classes instances inside select boxes (or multi select) and add another empty one if limit is not reached.
    
    Returns:
        tuple: A tuple with 2 elements:
            - list: triples to create
            - list: triples to remove
    """

    # This variable keeps track of all the values to add to the graph
    add_values = []

    # This variable keeps track of all the values to remove from the graph
    rem_values = []

    # Get variables from state
    data_bundle = state.get_data_bundle()

    # Find all possible object of the property (all instance of the given class) and their labels
    possible_objects: List[OntoEntity] = data_bundle.find_entities(class_uri=range_class_uri)
    possible_objects_label = [obj.display_label_comment for obj in possible_objects]

    # If the max count is one (ie only one possible triples for this property)
    if max_count == 1:

        # This for only exists to cover errors: since max_count = 1, if the data are correct, 
        # there could be only 1 uri_values, so the for should be irrelevant. But if the data are wrong
        # (eg coming from import, generations, ...) display and removal of "wrong" data is still allowed
        for uri in uri_values:
            entity = data_bundle.get_entity_infos(uri)
            
            # Because for some classes, a property can have multiple range classes (eg <is membership of> <group> OR/AND <person>)
            # When the entity has one, the formular tries to fit the class in the other (find the person among the groups)
            # Which raises an error (of course)
            # Also true for the "index is not None" in the 2nd next "if"
            if entity.display_label_comment in possible_objects_label: index = possible_objects_label.index(entity.display_label_comment)
            else: index = None
            new_value = container.selectbox(range_class_label, options=possible_objects_label, key=f"dialog-entity-form-prop-{prop_index}-{len(uri_values) + 1}", index=index)
            if index is not None and new_value != entity.display_label_comment:
                add_values.append(possible_objects[possible_objects_label.index(new_value)].uri)
                rem_values.append(entity.uri)
        
    else:

        # Information about instances that are objects of existing triples
        defaults = [data_bundle.get_entity_infos(uri) for uri in uri_values]

        # Because get_entity_infos returns None if given URI is a string 
        # (might happen when there is a property that has 2 class ranges: one String and one Class)
        # In case the property already has a value (so for edit form), the form tries to find an entity with the string as a URI, 
        # which leads to an errors and the function returns None
        defaults = list(filter(lambda d: d is not None, defaults))
        defaults_label = [ent.display_label_comment for ent in defaults]

        # Field to add / remove / edit objects of this property
        new_values = container.multiselect(range_class_label, options=possible_objects_label, default=defaults_label, max_selections=max_count)

        # For each instance selected
        for new_value in new_values:
            # Get the URI of the selected label
            new_uri = possible_objects[possible_objects_label.index(new_value)].uri

            # If the selected was not already object of a triple, and not yet added to "value to add", add it
            if new_value not in defaults_label and new_uri not in add_values:
                add_values.append(new_uri)
        
        # Also, check for all value that was present before, that they still are. 
        # Add them to remove list if not
        for old_value in defaults_label:
            # Get the URI of the selected label
            new_uri = possible_objects[possible_objects_label.index(new_value)].uri

            # If an old value is not anymore selected, add it to remove list
            if old_value not in new_values:
                rem_values.append(possible_objects[possible_objects_label.index(old_value)].uri)

    # Returns triples to add and triples to remove
    return add_values, rem_values


@st.dialog('Entity formular', width='large')
def dialog_entity_form(entity: OntoEntity = None, triples: List[tuple[str, str, str]] = []) -> None:
    """
    Dialog function allowing the user to create or edit a new entity.
    The formular is deducted from the SHACL taken from the Model graph.
    And display input field according to each property range class.

    Args:
        entity (OntoEntity): The entity to edit (or None if it is a creation).
        triples (triple list): Outgoing triples of the given entity.
    """ 

    # From state
    data_bundle = state.get_data_bundle()
    classes = data_bundle.ontology.get_classes()
    properties = data_bundle.ontology.get_properties()

    # Save triples that are going to be created on "Create" click
    triples_to_add: List[tuple[str, str, str]] = []
    triples_to_rem: List[tuple[str, str, str]] = []

    # Also, keep a list of mandatories properties to check if all of them are present
    mandatories: List[str] = []

    # Entity class is mandatory
    mandatories.append(data_bundle.type_property)

    # In order to create those triples, we also need to have an id and a URI for the entity (only if it is a creation), 
    # So URIs are generated on dialog open: it means that there can only be URI overlapping if 2 users open the dialog at the same millisecond
    if entity: entity_uri = entity.uri
    else: entity_uri = generate_uri()

    # Class selection (Only for entity creation, otherwise block the class change)
    disabled = False if not entity else True
    classes_labels = list(map(lambda cls: cls.display_label, classes))
    index = None if not entity else classes_labels.index(entity.class_label)

    # Class formular
    col1, _ = st.columns([1, 2])
    class_label = col1.selectbox('Class ❗️', options=classes_labels, index=index, disabled=disabled)
    st.divider()

    # Formular can only be displayed when the class is chosen, because it depends on it
    if class_label:

        # Find the selected class from the selected label
        class_index = classes_labels.index(class_label)
        selected_class = classes[class_index]

        # Set the entity class
        triples_to_add.append((entity_uri, data_bundle.type_property, selected_class.uri))

        # Select properties of interest (only outgoing properties)
        properties = [prop for prop in properties if prop.domain_class_uri == selected_class.uri]

        # Order them so that they appears in the correct order (according to ontology)
        properties.sort(key=lambda p: p.order)

        # Loop through filtered and sorted properties
        for i, prop in enumerate(properties):
            
            # Add to mandatories list the property only if it is the case (for display and for the formular)
            if prop.is_mandatory(): mandatories.append(prop.uri)

            # Formular 
            col_label, col_range, col_info = st.columns([4, 6, 2], vertical_alignment='bottom') 

            # Get the name of the range class
            range_class_name = data_bundle.ontology.get_class_name(prop.range_class_uri)

            # And get only triples of the same property
            existing_values = list(map(lambda t: t[2], filter(lambda t: t[1] == prop.uri, triples)))

            # Call private function to display label and info
            __add_property_label(col_label, prop)
            __add_property_info(col_info, prop)
            
            # Dispatch the right input field according to the range class
            if prop.range_class_uri == "xsd:string": 
                add, rem = __add_string_field(col_range, range_class_name, existing_values, prop.max_count, i)
            elif prop.range_class_uri == "xsd:html":
                add, rem = __add_html_field(col_range, range_class_name, existing_values, prop.max_count, i)
            elif prop.range_class_uri == "xsd:integer":
                add, rem = __add_integer_field(col_range, range_class_name, existing_values, prop.max_count, i)
            elif prop.range_class_uri == "xsd:float":
                add, rem = __add_float_field(col_range, range_class_name, existing_values, prop.max_count, i)
            else:
                add, rem = __add_class_field(col_range, range_class_name, prop.range_class_uri, existing_values, prop.max_count, i)
            
            # Add triples forwarded by fields and save them in memory (before real creation)
            for value in add: 
                triples_to_add.append((entity_uri, prop.uri, value))
            for value in rem: 
                triples_to_rem.append((entity_uri, prop.uri, value))
            
            st.text('')

        # Check if all mandatory fields are present
        have_props = list(map(lambda t: t[1], triples)) + list(map(lambda t: t[1], triples_to_add))
        ready = all([p in have_props for p in mandatories])

        st.divider()

        # Validation, creation, and load
        if st.button('Save', disabled=(not ready), icon=':material/save:'):
            
            # Delete and create triples that need to
            data_bundle.graph_data.delete(triples_to_rem)
            data_bundle.graph_data.insert(triples_to_add)

            # Then fetch basic informations about created entity (for correct display)
            # And put it in state so that entity card can be fetched
            entity = data_bundle.get_entity_infos(entity_uri)
            state.set_entity(entity)

            # Clear the cache
            # Because when entity is created/edited, we do not want to fetch an old version of it
            data_bundle.get_outgoing_statements.clear()

            # Finalization: validation message and load the created entity
            state.set_toast('Entity saved', ':material/done:')
            st.switch_page("pages/entity.py")
        

