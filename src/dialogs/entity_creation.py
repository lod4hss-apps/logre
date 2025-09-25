from typing import List
import streamlit as st
import lib.state as state
from lib.utils import generate_uri
from graphly.schema import Resource


@st.dialog('Create entity', width='medium')
def dialog_entity_creation() -> None:
    """
    Displays a dialog form for creating a new entity within the selected Data Bundle.

    Behavior:
        - Allows the user to select a class for the entity.
        - Dynamically generates input fields for all properties required by the selected class.
            - Supports literals (string, integer, float) and references to other class instances.
            - Handles mandatory properties and validates that they are filled before creation.
            - Supports adding or removing multiple values for properties when allowed by the model.
        - Displays detailed property information via popovers.
        - Generates a unique URI for the new entity.
        - Inserts the created entity triples into the data bundle's graph.
        - Updates the application state with a toast notification and navigates to the entity page upon successful creation.

    Returns:
        None
    """
    # From state
    data_bundle = state.get_data_bundle()

    # Class filter
    classes_labels = [c.get_text() for c in data_bundle.model.classes]
    class_label = st.selectbox('Class ❗️', options=classes_labels, index=None, width=220)

    # Initialize the triples list to create and the entity URI
    triples = []
    entity_uri = generate_uri()

    # Formular can only be displayed when the class is chosen, because it depends on it
    if class_label:
        st.divider()

        # Find the selected class from the selected label
        class_index = classes_labels.index(class_label)
        selected_class = data_bundle.model.classes[class_index]

        # Add the type triple
        triples.append((entity_uri, data_bundle.model.type_property, selected_class.uri))

        # Fetch all properties that need to be present in the form
        properties = data_bundle.get_card_properties_of(selected_class.uri)
        mandatories = {}

        # Loop through all of them
        for p in properties:
            with st.container():

                # Prepare
                if p.domain and p.domain.uri == selected_class.uri: # Outgoing
                    label_prefix = ""
                    target = p.range
                    way = 'outgoing'
                else: # Incoming
                    label_prefix = f'<small style="font-size: 10px; color: gray; text-decoration: none;">(incoming) </small>'
                    target = p.domain
                    way = 'incoming'

                # Property display label
                property_label = f"#### **{label_prefix}{p.get_text()}**"

                # If the property is mandatory
                if p.is_mandatory():
                    property_label += " ❗️" # Change the display for the user
                    mandatories[p.get_key()] = False # List it as not yet added, so that it can be checked later if it has been set

                # Make 3 columns: One for the property label, one for objects/subjects, and one for informations
                col_prop, col_input = st.columns([5, 8], vertical_alignment='center')
                col_prop.markdown(property_label, unsafe_allow_html=True)

                # State stores how much of this field are open
                input_number = state.entity_creation_get_input_number(p)

                # And for each one of them, display it correctly
                for i in range(input_number):
                    with col_input.container(horizontal=True, vertical_alignment='bottom'):

                        # User input
                        if not target.uri:
                            st.markdown("*Model does not specify class.*")
                        
                        # If the target is a STRING
                        elif target.uri == 'xsd:string':
                            input = st.text_input(target.get_text(), "", key=f"entity-creation-input-{p.get_key()}-{i}")
                            if input:
                                if way == 'outgoing': triples.append((entity_uri, p.uri, input))
                                else: raise Exception('Can not have an incoming property with a Literal as domain')
                                if p.is_mandatory(): mandatories[p.get_key()] = True

                        # If the target is an INTEGER
                        elif target.uri == 'xsd:integer':
                            input = st.number_input(target.get_text(), step=1, key=f"entity-creation-input-{p.get_key()}-{i}")
                            if input:
                                if way == 'outgoing': triples.append((entity_uri, p.uri, input))
                                else: raise Exception('Can not have an incoming property with a Literal as domain')
                                if p.is_mandatory(): mandatories[p.get_key()] = True

                        # If the target is a FLOAT
                        elif target.uri == 'xsd:float':
                            input = st.number_input(target.get_text(), key=f"entity-creation-input-{p.get_key()}-{i}")
                            if input:
                                if way == 'outgoing': triples.append((entity_uri, p.uri, input))
                                else: raise Exception('Can not have an incoming property with a Literal as domain')
                                if p.is_mandatory(): mandatories[p.get_key()] = True

                        # Otherwise, target is a CLASS INSTANCE
                        else:
                            # Fetch all possible targets (can be heavy)
                            possibles: List[Resource] = data_bundle.find_entities(class_uri=target.uri, limit=None, offset=None)
                            possibles_labels = [resource.get_text() for resource in possibles]
                            # Class instance
                            input_label = st.selectbox(target.get_text(), options=possibles_labels, index=None, key=f"entity-creation-input-{p.get_key()}-{i}")
                            if input_label:
                                input_index = possibles_labels.index(input_label)
                                input = possibles[input_index]
                                if way == 'outgoing': triples.append((entity_uri, p.uri, input.uri))
                                else: triples.append((input.uri, p.uri, entity_uri))
                                if p.is_mandatory(): mandatories[p.get_key()] = True

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
                            state.entity_creation_set_input_number(p, input_number - 1)
                            st.rerun(scope='fragment')
                        # Plus button
                        if st.button('', type='tertiary', icon=':material/add:', key=f"entity-creation-add-{p.get_key()}", disabled=disabled_plus):
                            state.entity_creation_set_input_number(p, input_number + 1)
                            st.rerun(scope='fragment')

            st.divider()

        # Validation button
        centered = st.container(horizontal=True, horizontal_alignment='center')
        if centered.button('Create entity', type='primary'):
                
            # Verify that all mandatories are present
            validated = all(mandatories.values())
            if validated:
                # And create the entity
                data_bundle.graph_data.insert(triples, prefixes=data_bundle.prefixes)
                state.set_toast('Entity created', ':material/save:')
                # And then, open it
                state.set_entity_uri(entity_uri)
                st.switch_page("pages/entity.py")
            else:
                # Error message for the user that some mandatory fields are missing
                st.error('All mandatories fields need to have at least one value')