import streamlit as st
from requests.exceptions import HTTPError
from components.init import init
from components.menu import menu
from lib import state
from lib.utils import get_max_length_text
from dialogs.triple_info import dialog_triple_info
from dialogs.entity_edition import dialog_entity_edition
from dialogs.confirmation import dialog_confirmation

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

try:
    # Initialize
    init(layout='wide', query_param_keys=['db', 'uri'])
    menu()

    # From state
    data_bundle = state.get_data_bundle()
    entity_uri = state.get_entity_uri()

    # Make verifications
    if not data_bundle:
        st.warning('No Data Bundle selected')
    elif not entity_uri:
        st.warning('No Entity URI provided')
    else:
        
        # Gather minimal information about the entity
        # i.e. Fill Resource instance
        entity = data_bundle.get_entity_basics(entity_uri)
        entity_class = data_bundle.model.find_class(entity.class_uri)

        # Header: entity name, additional info and description
        col_title, col_actions = st.columns([20, 10], vertical_alignment='bottom')
        uri_text = f'<small style="font-size: 16px; color: gray; text-decoration: none;">{entity.uri}</small>'
        col_title.markdown(f"# {entity.get_text()} ({entity_class.get_text()}) {uri_text}", unsafe_allow_html=True)
        st.markdown(entity.comment or '')

        # Header options
        with col_actions.container(horizontal=True, horizontal_alignment="right"):
            # Button to switch to raw triples
            if st.button('Raw triples'):
                st.switch_page('pages/entity-triples.py')
            # Button to switch to visualization
            if st.button('Visualize'):
                st.switch_page('pages/entity-chart.py')
            # Button to edit the entity (open edit dialog)
            if st.button('', icon=":material/edit:", type='primary'):
                dialog_entity_edition(entity)
            # Button to delete the entity (open confirmation dialog)
            if st.button('', icon=":material/delete:", type='primary'):
                def delete_entity(entity_uri: str) -> None:
                    data_bundle.delete('data', (entity_uri, '?p', '?o')) # Delete all outgoing
                    data_bundle.delete('data', ('?s', '?p', entity_uri)) # Delete all incomings
                    state.set_entity_uri(None)
                    st.rerun()
                dialog_confirmation('You are about to delete all statements of this entity.', callback=delete_entity, entity_uri=entity.uri)

        st.write('')

        # According to the model (thanks to the entity class), get all the properties that the entity can have in its card
        all_properties = data_bundle.get_card_properties_of(entity.class_uri)

        # Loop through all of them
        for p in all_properties:

            # In case it is not the first "st.run", get the right entities
            offset = state.get_offset(entity.uri, p.get_key())

            # Property and object/subjects container
            with st.container(horizontal=True, horizontal_alignment='right', border=True):

                # Make 3 columns: One for the property label, one for objects/subjects, and one for informations
                col_prop, col_entity= st.columns([5, 8])

                # If the property is OUTGOING for the entity
                if p.domain and p.domain.uri == entity_class.uri:
                    
                    # Property Label
                    col_prop.markdown(f"##### **{p.get_text()} {f'({p.range.get_text()})' if p.range and p.range.uri else ''}**")

                    # Fetch all the objects (with paginagion)
                    statements = data_bundle.get_objects_of(entity, p, PAGINATION_LENGTH, offset)
                    
                    # Loop through all retrieved objects
                    for s in statements:
                        col_value, col_info = col_entity.columns([7, 1], vertical_alignment='center')
                        object_class = data_bundle.model.find_class(s.object.class_uri)
                        
                        # Different behavior depending on the object resource type
                        object_text = get_max_length_text(s.object.get_text(comment=True), MAX_STRING_LENGTH)
                        if s.object.resource_type == 'iri':
                            # Link to the OBJECT entity
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-{s.object.uri}-link"
                            kwargs = {'uri': s.object.uri}
                            col_value.button(f"{object_text}", type='tertiary', on_click=state.set_entity_uri, kwargs=kwargs, key=btn_key)
                        else:
                            # Simply diplay the VALUE
                            col_value.markdown(f"> {object_text}")
                            col_value.write('')

                        # Add a button which opens a dialog with raw informations about the triple
                        with col_info.container(horizontal=False, horizontal_alignment='right'):
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-{s.object.uri if s.object.resource_type == 'iri' else s.object.literal}-info"
                            kwargs = {'statement': s, 'prefixes': data_bundle.prefixes, 'model': data_bundle.model}
                            st.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs=kwargs, key=btn_key)


                    # If there is more object than a single page, or if it is not page 1, display the pagination options
                    if len(statements) >= PAGINATION_LENGTH or offset != 0:
                        col_entity.write('')

                        # Container for the paginator
                        with col_entity.container(horizontal=True, vertical_alignment="center"):

                            # Total entity number
                            total_count = data_bundle.get_objects_of_count(entity, p)

                            # Go one page back
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-previous"
                            disabled = offset <= 0
                            if st.button('<-', type='tertiary', disabled=disabled, key=btn_key):
                                if offset > PAGINATION_LENGTH: state.set_offset(entity.uri, p.get_key(), offset - PAGINATION_LENGTH)
                                else: state.set_offset(entity.uri, p.get_key(), 0)
                                st.rerun()
                            
                            # Current page
                            st.markdown(f"{offset} - {min(offset + PAGINATION_LENGTH, total_count)}", width="content")

                            # Go one page ahead
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-next"
                            disabled = offset + PAGINATION_LENGTH >= total_count
                            if st.button('->', type='tertiary', disabled=disabled, key=btn_key):
                                if offset < total_count: state.set_offset(entity.uri, p.get_key(), offset + PAGINATION_LENGTH)
                                else: state.set_offset(entity.uri, p.get_key(), total_count)
                                st.rerun()

                            # Display total triples
                            st.markdown(f"*Total count: {total_count}*", width="content")

                # If the property is INCOMING for the entity
                else: 
                    
                    # Property Label
                    incoming_text = f'<small style="font-size: 10px; color: gray; text-decoration: none;">(incoming)</small>'
                    col_prop.markdown(f"##### **{incoming_text}{f'({p.domain.get_text()})' if p.domain and p.domain.uri else ''} {p.get_text()}**", unsafe_allow_html=True)

                    # Fetch all the subjects (with paginagion)
                    statements = data_bundle.get_subjects_of(entity, p, limit=PAGINATION_LENGTH, offset=offset)

                    # Loop through all retrieved subjects
                    for s in statements:
                        col_value, col_info = col_entity.columns([7, 1], vertical_alignment='center')
                        subject_class = data_bundle.model.find_class(s.subject.class_uri)

                        # Link to the SUBJECT entity
                        # Because subjects are always entities, no need to differenciate from values
                        subject_text = get_max_length_text(s.subject.get_text(comment=True), MAX_STRING_LENGTH)
                        btn_key = f"btn-{entity_uri}-{p.get_key()}-{s.subject.uri}-link"
                        kwargs = {'uri': s.subject.uri}
                        col_value.button(f"{subject_text}", type='tertiary', on_click=state.set_entity_uri, kwargs=kwargs, key=btn_key)

                        # Add a button which opens a dialog with raw informations about the triple
                        with col_info.container(horizontal=False, horizontal_alignment='right'):
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-{s.subject.uri}-info"
                            kwargs = {'statement': s, 'prefixes': data_bundle.prefixes, 'model': data_bundle.model}
                            st.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs=kwargs, key=btn_key)


                    # If there is more object than a single page, or if it is not page 1, display the pagination options
                    if len(statements) >= PAGINATION_LENGTH or offset != 0:
                        col_entity.write('')

                        # Container for the paginator
                        with col_entity.container(horizontal=True, vertical_alignment="center"):

                            # Total entity number
                            total_count = data_bundle.get_subjects_of_count(entity, p)

                            # Go one page back
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-previous"
                            disabled = offset <= 0
                            if st.button('<-', type='tertiary', disabled=disabled, key=btn_key):
                                if offset > PAGINATION_LENGTH: state.set_offset(entity.uri, p.get_key(), offset - PAGINATION_LENGTH)
                                else: state.set_offset(entity.uri, p.get_key(), 0)
                                st.rerun()

                            # Current page
                            st.markdown(f"{offset} - {min(offset + PAGINATION_LENGTH, total_count)}", width="content")

                            # Go one page ahead
                            btn_key = f"btn-{entity_uri}-{p.get_key()}-next"
                            disabled = offset + PAGINATION_LENGTH >= total_count
                            if st.button('->', type='tertiary', disabled=disabled, key=btn_key):
                                if offset < total_count: state.set_offset(entity.uri, p.get_key(), offset + PAGINATION_LENGTH)
                                else: state.set_offset(entity.uri, p.get_key(), total_count)
                                st.rerun()

                            # Display total triples
                            st.markdown(f"*Total count: {total_count}*", width="content")
   
except HTTPError as err:
    message = f"""[HTTP ERROR]\n\n{err.args[0]}"""
    st.error(message)
    print(message.replace('\n\n', ' - '))