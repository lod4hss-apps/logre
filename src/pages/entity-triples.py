import streamlit as st
from requests.exceptions import HTTPError
from graphly.schema import Statement, Resource, Property
from components.init import init
from components.menu import menu
from lib import state
from lib.utils import get_max_length_text
from lib.errors import get_HTTP_ERROR_message
from dialogs.triple_info import dialog_triple_info

# Page parameters
INCOMING_TRIPLES_FETCHED = 5

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
    if not entity_uri:
        st.warning('No Entity URI provided')
    else:

        # If there is none, Inform the user
        if not entity_uri:
            st.info("Logre needs an URI to show triples.")
        else: 
            
            # Function that is used for each category (Basic, Incomings, Outgoings)
            def display_triple(statement: Statement) -> None:
                col_sub, col_pred, col_obj, col_info = st.columns([6, 6, 6, 1], gap="medium", vertical_alignment='bottom')

                # Subject
                subject_text = f"{statement.subject.uri} ({get_max_length_text(statement.subject.get_text(), 40)})"
                subject_link = data_bundle.prefixes.lengthen(statement.subject.uri)
                col_sub.markdown(f"[{subject_text}]({subject_link})")

                # Predicate
                predicate_text = f"{statement.predicate.uri} ({get_max_length_text(statement.predicate.get_text(), 40)})"
                predicate_link = data_bundle.prefixes.lengthen(statement.predicate.uri)
                col_pred.markdown(f"[{predicate_text}]({predicate_link})")

                # Object (Class instance)
                if statement.object.resource_type == 'iri':
                    object_text = f"{statement.object.uri} ({get_max_length_text(statement.object.get_text(), 40)})"
                    object_link = data_bundle.prefixes.lengthen(statement.object.uri)
                    col_obj.markdown(f"[{object_text}]({object_link})")
                # Object (Literal)
                else:
                    object_text = get_max_length_text(statement.object.get_text(), 40)
                    col_obj.markdown(f"> {object_text}")

                with col_info.container(horizontal=True, horizontal_alignment='right'):
                    key = f"btn-{statement.subject.uri}-{statement.predicate.uri}-{statement.object.uri if hasattr(statement.object, 'uri') else statement.object.literal}-info"
                    kwargs = {'statement': statement, 'prefixes': data_bundle.prefixes, 'model': data_bundle.model}
                    st.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs=kwargs, key=key)


            # Header: entity name, additional info and description
            col_title, col_actions = st.columns([20, 10], vertical_alignment='bottom')
            col_title.markdown(f'# {entity_uri}')

            # Header options
            with col_actions.container(horizontal=True, horizontal_alignment="right"):
                if st.button('Entity Card'):
                    st.switch_page('pages/entity-card.py')
                if st.button('Visualize'):
                    st.switch_page('pages/entity-chart.py')
            st.write('')

            st.divider()

            # First category: Basics
            st.markdown('### Basic information')
            entity = data_bundle.get_entity_basics(entity_uri)

            # Type
            if entity.class_uri:
                prop_type = next(iter(data_bundle.model.find_properties(data_bundle.model.type_property)))
                entity_class = data_bundle.model.find_class(entity.class_uri)
                display_triple(Statement(entity, prop_type, entity_class))

            # Label
            if entity.label:
                prop_label = next(iter(data_bundle.model.find_properties(data_bundle.model.label_property)))
                entity_label = Resource(entity.label, resource_type='literal')
                display_triple(Statement(entity, prop_label, entity_label))

            # Comment
            if entity.comment:
                comment = next(iter(data_bundle.model.find_properties(data_bundle.model.comment_property)))
                entity_comment = Resource(entity.comment, resource_type='literal')
                display_triple(Statement(entity, comment, entity_label))

            st.divider()

            # List of property already displayed: no need to redisplay them
            skip_props = [
                Property(data_bundle.model.type_property),
                Property(data_bundle.model.label_property),
                Property(data_bundle.model.comment_property),
            ]

            # Second category: Outgoing statements
            title_container = st.container(horizontal=True, vertical_alignment="bottom")
            title_container.markdown('### Outgoing statements', width='content')
            statements = data_bundle.get_outgoing_statements_of(entity, skip_props=skip_props)
            title_container.markdown(f"*{len(statements)} total outgoing triples*")

            # Display triples
            for s in statements: 
                display_triple(s)
            if len(statements) == 0:
                st.markdown('*None*')

            st.divider()

            # Second category: Incoming statements
            title_container = st.container(horizontal=True, vertical_alignment="bottom")
            title_container.markdown('### Incoming statements', width='content')
            total_inc_number = data_bundle.get_incoming_statements_of_count(entity)
            title_container.markdown(f"*{total_inc_number} total incoming triples*")

            # Limit the quantity fetched, to not overload the page
            number_to_fetch = 5

            # This is the flag to not fetch twice in case user fetches more via the selectbox
            fetched = False

            # But if there is more, allow user to fetch more, but need interaction
            if total_inc_number >= 5:
                number_to_fetch = title_container.number_input("Number to fetch", 5, step=5, width=150)
                if title_container.button('Fetch'):
                    statements = data_bundle.get_incoming_statements_of(entity, limit=number_to_fetch, skip_props=skip_props)
                    fetched = True
            
            # Avoid re-fetching
            if not fetched:
                statements = data_bundle.get_incoming_statements_of(entity, skip_props=skip_props)

            # Display triples
            for s in statements: 
                display_triple(s)
            if len(statements) == 0:
                st.markdown('*None*')

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))