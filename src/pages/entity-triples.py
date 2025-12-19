import streamlit as st
from requests.exceptions import HTTPError
from graphly.schema import Statement, Resource, Property
from components.init import init
from components.menu import menu
from components.help import help_text
from lib import state
from lib.utils import get_max_length_text
from lib.errors import get_HTTP_ERROR_message
from dialogs.triple_info import dialog_triple_info

# Page parameters
INCOMING_TRIPLES_FETCHED = 5

# Initialize
init(layout='wide', query_param_keys=['endpoint', 'db', 'uri'])
menu()

try:

    # From state
    data_bundle = state.get_data_bundle()
    entity_uri = state.get_entity_uri()

    # Make verifications
    if not data_bundle:
        st.warning('No Data Bundle selected')
    if not entity_uri:
        st.warning('No Entity URI provided')
    else:

        entity = data_bundle.get_entity_basics(entity_uri)

        def render_resource(column, resource, prefixes, empty_placeholder='–'):
            """Pretty-print a resource or property within a column."""
            if getattr(resource, 'resource_type', None) == 'literal':
                text = get_max_length_text(resource.get_text(), 80) or empty_placeholder
                column.markdown(f"**{text}**")
                datatype = getattr(resource, 'datatype', None)
                if datatype:
                    column.caption(datatype)
                return

            uri = getattr(resource, 'uri', None)
            label = get_max_length_text(resource.get_text(), 80) if hasattr(resource, 'get_text') else None
            if uri:
                short = prefixes.shorten(uri)
                display = label or short or uri
                column.markdown(f"[**{display}**]({prefixes.lengthen(uri)})")
                column.caption(f"`{short or uri}`")
            else:
                column.markdown(f"**{label or empty_placeholder}**")

        def display_triple(statement: Statement) -> None:
            """Render a triple row with subject/predicate/object visually aligned."""
            with st.container(border=True):
                col_sub, col_pred, col_obj, col_info = st.columns([5, 4, 5, 1], gap="small", vertical_alignment='bottom')
                render_resource(col_sub, statement.subject, data_bundle.prefixes)
                render_resource(col_pred, statement.predicate, data_bundle.prefixes)
                if statement.object.resource_type == 'iri':
                    render_resource(col_obj, statement.object, data_bundle.prefixes)
                else:
                    render_resource(col_obj, statement.object, data_bundle.prefixes)

                with col_info.container(horizontal=True, horizontal_alignment='right'):
                    key = f"btn-{statement.subject.uri}-{statement.predicate.uri}-{statement.object.uri if hasattr(statement.object, 'uri') else statement.object.literal}-info"
                    kwargs = {'statement': statement, 'prefixes': data_bundle.prefixes, 'model': data_bundle.model}
                    st.button('', icon=':material/info:', type='tertiary', on_click=dialog_triple_info, kwargs=kwargs, key=key)


        # Header: entity name, additional info and description
        col_title, col_actions = st.columns([20, 10], vertical_alignment='bottom')
        entity_title = entity.get_text() or data_bundle.prefixes.shorten(entity.uri)
        col_title.markdown(f'# {entity_title}')
        col_title.caption(entity_uri)

        # Header options
        with col_actions.container(horizontal=True, horizontal_alignment="right"):
            if st.button('Entity Card', help=help_text("entity_triples.entity_card")):
                st.switch_page('pages/entity-card.py')
            # Button to switch to visualization
            if st.button('Visualize', help=help_text("entity_triples.visualize")):
                st.switch_page('pages/entity-chart.py')
        st.write('')

        st.divider()

        # First category: Basics
        st.markdown('### Basic information')
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
            display_triple(Statement(entity, comment, entity_comment))

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
