from typing import List
import streamlit as st
import lib.state as state
from graphly.schema import Resource


@st.dialog('Edit entity', width='medium')
def dialog_entity_edition(entity: Resource = None) -> None:
    """
    Displays a dialog form for editing an existing entity within the selected Data Bundle.

    Args:
        entity (Resource, optional): The entity to edit. If None, the dialog does not display content.

    Behavior:
        - Fetches all properties required for the entity's class.
        - Displays input fields pre-filled with the entity's current values.
            - Supports literals (string, integer, float) and references to other class instances.
            - Handles mandatory properties and tracks changes to ensure validation.
            - Allows adding or removing multiple values for properties when allowed by the model.
        - Maintains lists of triples to add and remove based on user edits.
        - Displays property metadata via popovers.
        - Validates that all mandatory fields have at least one value before submission.
        - Updates the entity in the data bundle's graph by deleting old triples and inserting new ones.
        - Sets a toast notification and navigates to the entity page upon successful edit.

    Returns:
        None
    """
    # From state
    data_bundle = state.get_data_bundle()

    # Triples that need to be added and removed
    triples_to_add = []
    triples_to_remove = []

    # Fetch all properties that need to be present in the form
    properties = data_bundle.get_card_properties_of(entity.class_uri)
    mandatories = {}

    # Loop through all of them
    for p in properties:
        with st.container():

                # Prepare
            if p.domain and p.domain.uri == entity.class_uri: # Outgoing
                label_prefix = ""
                target = p.range
                way = 'outgoing'
            else: # Incoming
                label_prefix = f'<small style="font-size: 10px; color: gray; text-decoration: none;">(incoming) </small>'
                target = p.domain
                way = 'incoming'

            # Property display label
            property_label = f"#### **{label_prefix}{p.get_text()}**"
        
            # Fetch existing triples
            existings = data_bundle.get_objects_of(entity, p)

            # If the property is mandatory
            if p.is_mandatory():
                property_label += " ❗️" # Change the display for the user
                mandatories[p.get_key()] = len(existings) # Keep track of how much triples of this property has the entity

            # Make 3 columns: One for the property label, one for objects/subjects, and one for informations
            col_prop, col_input = st.columns([5, 8], vertical_alignment='center')
            col_prop.markdown(property_label, unsafe_allow_html=True)

            # State stores how much of this field are open
            input_number = len(existings) + state.entity_edition_get_input_number(p)
            if input_number == 0: 
                input_number = 1 # Because by default the getter say 0. This is required elsewhere

            # And for each one of them, display it correctly
            for i in range(input_number):
                with col_input.container(horizontal=True, vertical_alignment='bottom'):

                    # User input
                    if not target.uri:
                        st.markdown("*Model does not specify class.*")

                    # If the target is a STRING
                    elif target.uri == 'xsd:string':
                        # If it has one, display current value
                        if i < len(existings): value = existings[i].subject.literal if way == 'incoming' else existings[i].object.literal
                        else: value = ''
                        input = st.text_input(target.get_text(), value, key=f"entity-creation-input-{p.get_key()}-{i}")
                        # If it is an update: mandatory is not touched
                        if value != '' and input != '' and input != value:
                            triples_to_remove.append((entity.uri, p.uri, value))
                            triples_to_add.append((entity.uri, p.uri, input))
                        # If it is a creation
                        elif value == '' and input != '':
                            triples_to_add.append((entity.uri, p.uri, input))
                            if p.is_mandatory(): mandatories[p.get_key()] += 1
                        # If it is a deletion
                        elif value != '' and input == '':
                            triples_to_remove.append((entity.uri, p.uri, value))
                            if p.is_mandatory(): mandatories[p.get_key()] -= 1

                    # If the target is an INTEGER
                    elif target.uri == 'xsd:integer':
                        # If it has one, display current value
                        if i < len(existings): value = existings[i].subject.literal if way == 'incoming' else existings[i].object.literal
                        else: value = ''
                        input = st.number_input(target.get_text(), value=value, step=1, key=f"entity-creation-input-{p.get_key()}-{i}")
                        # If it is an update: mandatory is not touched
                        if value != '' and input != '' and input != value:
                            triples_to_remove.append((entity.uri, p.uri, value))
                            triples_to_add.append((entity.uri, p.uri, input))
                        # If it is a creation
                        elif value == '' and input != '':
                            triples_to_add.append((entity.uri, p.uri, input))
                            if p.is_mandatory(): mandatories[p.get_key()] += 1
                        # If it is a deletion
                        elif value != '' and input == "":
                            triples_to_remove.append((entity.uri, p.uri, value))
                            if p.is_mandatory(): mandatories[p.get_key()] -= 1

                    # If the target is an FLOAT
                    elif target.uri == 'xsd:float':
                        # If it has one, display current value
                        if i < len(existings): value = float(existings[i].subject.literal) if way == 'incoming' else float(existings[i].object.literal)
                        else: value = ''
                        input = st.number_input(target.get_text(), value=value, key=f"entity-creation-input-{p.get_key()}-{i}")
                        # If it is an update: mandatory is not touched
                        if value != '' and input != '' and input != value:
                            triples_to_remove.append((entity.uri, p.uri, value))
                            triples_to_add.append((entity.uri, p.uri, input))
                        # If it is a creation
                        elif value == '' and input != '':
                            triples_to_add.append((entity.uri, p.uri, input))
                            if p.is_mandatory(): mandatories[p.get_key()] += 1
                        # If it is a deletion
                        elif value != '' and input == "":
                            triples_to_remove.append((entity.uri, p.uri, value))
                            if p.is_mandatory(): mandatories[p.get_key()] -= 1
                            
                    # Otherwise, target is a CLASS INSTANCE
                    else:
                        # Fetch all possible targets (can be heavy)
                        possibles: List[Resource] = data_bundle.find_entities(class_uri=target.uri, limit=None, offset=None)
                        possibles_labels = [resource.get_text() for resource in possibles]
                        # If it has one, display current value
                        if i < len(existings): 
                            value_uri = existings[i].subject.uri if way == 'incoming' else existings[i].object.uri
                            value = next(e.get_text() for e in possibles if e.uri == value_uri)
                            index = possibles_labels.index(value)
                        else: 
                            value = ''
                            index = None
                        # Class instance
                        input = st.selectbox(target.get_text(), options=possibles_labels, index=index, key=f"entity-creation-input-{p.get_key()}-{i}")
                        if input:
                            input_index = possibles_labels.index(input)
                            input_uri = possibles[input_index].uri
                        # If it is an update: mandatory is not touched
                        if value != '' and input != '' and input != value:
                            triples_to_remove.append((entity.uri, p.uri, value_uri) if way == 'outgoing' else (value_uri, p.uri, entity.uri))
                            triples_to_add.append((entity.uri, p.uri, input_uri) if way == 'outgoing' else (input_uri, p.uri, entity.uri))
                        # If it is a creation
                        elif value == '' and input != None:
                            triples_to_add.append((entity.uri, p.uri, input_uri))
                            if p.is_mandatory(): mandatories[p.get_key()] += 1
                        # If it is a deletion
                        elif value != '' and input == None:
                            triples_to_remove.append((entity.uri, p.uri, value_uri) if way == 'outgoing' else (value_uri, p.uri, entity.uri))
                            if p.is_mandatory(): mandatories[p.get_key()] -= 1

                    # Display the property information only on first row, others would be redundancy 
                    if i == 0:
                        with st.popover('', icon=':material/info:'):
                            st.markdown('### Property information')

                            # Its label
                            c1, c2 = st.columns([1, 1])
                            c1.markdown("label: ")
                            c2.markdown(p.label)

                            # Its URI
                            c1, c2 = st.columns([1, 1])
                            c1.markdown("URI: ")
                            c2.markdown(p.uri)

                            # Its order in the formular
                            c1, c2 = st.columns([1, 1])
                            c1.markdown("Order: ")
                            c2.markdown(p.order if p.order != 10**18 else 'n')

                            # The minimum count for this property any instance of this class should have
                            c1, c2 = st.columns([1, 1])
                            c1.markdown("Minimal count: ")
                            c2.markdown(p.min_count)

                            # The maximum count for this property any instance of this class should have
                            c1, c2 = st.columns([1, 1])
                            c1.markdown("Maximal count: ")
                            c2.markdown(p.max_count if p.max_count != 10**18 else 'n')

            # If the model allows to have mutliple, append the + and - so that user can use it
            with col_input.container(horizontal=True, horizontal_alignment='center'):
                # Check disabling of buttons
                disabled_minus = input_number <= 1
                disabled_plus = input_number >= (p.max_count or 10**18)
                # If at least one of the two can be pressed, display both
                if not disabled_minus or not disabled_plus:
                    # Minus button
                    if st.button('', type='tertiary', icon=':material/remove:', key=f"entity-creation-remove-{p.get_key()}", disabled=disabled_minus):
                        state.entity_edition_set_input_number(p, input_number - 1)
                        st.rerun(scope='fragment')
                    # Plus button
                    if st.button('', type='tertiary', icon=':material/add:', key=f"entity-creation-add-{p.get_key()}", disabled=disabled_plus):
                        state.entity_edition_set_input_number(p, input_number + 1)
                        st.rerun(scope='fragment')
        st.divider()

    # Validation button
    centered = st.container(horizontal=True, horizontal_alignment='center')
    if centered.button('Edit entity', type='primary'):
            
        # Verify that all mandatories are present (eg >= 0)
        validated = all(mandatories.values())

        if validated:
            # Remove triples that needs to
            data_bundle.graph_data.delete(triples_to_remove, prefixes=data_bundle.prefixes)
            # Add new triples
            data_bundle.graph_data.insert(triples_to_add, prefixes=data_bundle.prefixes)
            state.set_toast('Entity edited', ':material/save:')
            # And then, open it
            state.set_entity_uri(entity.uri)
            st.switch_page("pages/entity.py")
        else:
            # Error message for the user that some mandatory fields are missing
            st.error('All mandatories fields need to have at least one value')