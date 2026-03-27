import streamlit as st
from html import escape
from urllib.parse import quote_plus
from components.doc_links import decorate_doc_links
from components.init import init
from components.menu import menu
from lib import state
from lib.utils import get_max_length_text, get_short_uri_with_tail
from dialogs.triple_info import dialog_triple_info
from dialogs.entity_edition import dialog_entity_edition
from dialogs.confirmation import dialog_confirmation

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

# Initialize
init(layout="wide", required_query_params=["endpoint", "db", "uri"])
menu()

# From state
data_bundle = state.get_data_bundle()
entity_uri = state.get_entity_uri()

# Make verifications
if not entity_uri:
    st.warning("No Entity URI provided")
else:
    # Gather minimal information about the entity
    # i.e. Fill Resource instance
    entity = data_bundle.get_entity_basics(entity_uri)
    entity_class = data_bundle.model.find_class(entity.class_uri)
    endpoint_key = state.get_endpoint_key()

    def get_internal_entity_url(uri: str) -> str:
        endpoint_qs = f"&endpoint={quote_plus(endpoint_key)}" if endpoint_key else ""
        return f"/entity?db={quote_plus(data_bundle.key)}{endpoint_qs}&uri={quote_plus(uri)}"

    def get_external_uri_url(uri: str) -> str:
        return data_bundle.prefixes.lengthen(uri)

    def get_class_text_with_uri(resource) -> str:
        if not resource or not resource.uri:
            return ""
        class_uri_url = get_external_uri_url(resource.uri)
        short_uri = get_short_uri_with_tail(resource.uri)
        return f"{resource.get_text()} ([{short_uri}]({class_uri_url}))"

    def get_property_text_with_uri(resource) -> str:
        if not resource or not resource.uri:
            return ""
        property_uri_url = get_external_uri_url(resource.uri)
        short_uri = get_short_uri_with_tail(resource.uri)
        return f"{resource.get_text()} ([{short_uri}]({property_uri_url}))"

    def get_entity_uri_html(uri: str, max_uri_length: int = 55) -> str:
        internal_url = escape(get_internal_entity_url(uri), quote=True)
        external_url = escape(get_external_uri_url(uri), quote=True)
        uri_text = escape(uri)
        short_uri = escape(get_short_uri_with_tail(uri, max_uri_length))
        return (
            f'<a href="{internal_url}" target="_blank" rel="noopener noreferrer" title="{uri_text}">{short_uri}</a> '
            f'<a href="{external_url}" target="_blank" rel="noopener noreferrer" title="Open externally">↗</a>'
        )

    def get_entity_text_with_uri(
        resource, max_length: int | None = None, uri_max_length: int = 55
    ) -> str:
        label = resource.get_text()
        if max_length:
            label = get_max_length_text(label, max_length)
        return (
            f"<span>{escape(label)}</span> "
            f"({get_entity_uri_html(resource.uri, uri_max_length)})"
        )

    def get_entity_header_html(resource, uri_max_length: int = 55) -> str:
        label = escape(resource.get_text())
        uri_html = get_entity_uri_html(resource.uri, uri_max_length)
        return (
            f"<h1 style='margin: 0;'>{label}</h1>"
            "<div style='font-size: 0.85rem; color: var(--secondary-text-color, #6b7280); margin-top: 0.15rem;'>"
            f"{uri_html}"
            "</div>"
        )

    # Header: entity name, additional info and description
    col_title, col_actions = st.columns([20, 10], vertical_alignment="bottom")
    with col_title:
        st.html(get_entity_header_html(entity))

    if entity_class and entity_class.uri:
        col_title.markdown(f"**Class:** {get_class_text_with_uri(entity_class)}")
    st.markdown(entity.comment or "")

    # Header options
    with col_actions.container(horizontal=True, horizontal_alignment="right"):
        # Button to switch to raw triples
        if st.button(
            "Raw triples",
            help=decorate_doc_links(
                "[What are raw triples?](/documentation?section=what-is-the-page-raw-triples-for)"
            ),
        ):
            st.switch_page("pages/entity-triples.py")
        # Button to switch to visualization
        if st.button(
            "Visualize",
            help=decorate_doc_links(
                "[What is the visualization?](/documentation?section=what-is-shown-on-page-visualization)"
            ),
        ):
            st.switch_page("pages/entity-chart.py")
        # Button to edit the entity (open edit dialog)
        if st.button("", icon=":material/edit:", type="primary"):
            dialog_entity_edition(entity)
        # Button to delete the entity (open confirmation dialog)
        if st.button("", icon=":material/delete:", type="primary"):

            def delete_entity(entity_uri: str) -> None:
                data_bundle.data.delete((entity_uri, "?p", "?o"))  # Delete all outgoing
                data_bundle.data.delete(
                    ("?s", "?p", entity_uri)
                )  # Delete all incomings
                state.set_entity_uri(None)
                st.rerun()

            dialog_confirmation(
                "You are about to delete all statements of this entity.",
                callback=delete_entity,
                entity_uri=entity.uri,
            )

    st.write("")

    # According to the model (thanks to the entity class), get all the properties that the entity can have in its card
    all_properties = data_bundle.get_card_properties_of(entity.class_uri)

    # Loop through all of them
    for p in all_properties:
        # In case it is not the first "st.run", get the right entities
        offset = state.get_offset(entity.uri, p.get_key())

        # Property and object/subjects container
        with st.container(horizontal=True, horizontal_alignment="right", border=True):
            # Make 3 columns: One for the property label, one for objects/subjects, and one for informations
            col_prop, col_entity = st.columns([5, 8])

            # If the property is OUTGOING for the entity
            if p.domain and p.domain.uri == entity_class.uri:
                # Property Label
                col_prop.markdown(f"##### **{get_property_text_with_uri(p)}**")
                if p.range and p.range.uri:
                    col_prop.markdown(f"*Range:* {get_class_text_with_uri(p.range)}")

                # Fetch all the objects (with paginagion)
                statements = data_bundle.get_objects_of(
                    entity, p, PAGINATION_LENGTH, offset
                )

                # Loop through all retrieved objects
                for i, s in enumerate(statements):
                    col_value, col_info = col_entity.columns(
                        [7, 1], vertical_alignment="center"
                    )

                    # Different behavior depending on the object resource type
                    object_text = get_max_length_text(
                        s.object.get_text(), MAX_STRING_LENGTH
                    )
                    if s.object.resource_type == "iri":
                        with col_value:
                            st.html(
                                get_entity_text_with_uri(s.object, MAX_STRING_LENGTH)
                            )
                    else:
                        # Simply diplay the VALUE
                        col_value.markdown(f"> {object_text}")
                        col_value.write("")

                    # Add a button which opens a dialog with raw informations about the triple
                    with col_info.container(
                        horizontal=False, horizontal_alignment="right"
                    ):
                        btn_key = f"btn-{entity_uri}-{p.get_key()}-{s.object.uri if s.object.resource_type == 'iri' else s.object.literal}-{i}-info"
                        kwargs = {
                            "statement": s,
                            "prefixes": data_bundle.prefixes,
                            "model": data_bundle.model,
                        }
                        st.button(
                            "",
                            icon=":material/info:",
                            type="tertiary",
                            on_click=dialog_triple_info,
                            kwargs=kwargs,
                            key=btn_key,
                        )

                # If there is more object than a single page, or if it is not page 1, display the pagination options
                if len(statements) >= PAGINATION_LENGTH or offset != 0:
                    col_entity.write("")

                    # Container for the paginator
                    with col_entity.container(
                        horizontal=True, vertical_alignment="center"
                    ):
                        # Total entity number
                        total_count = data_bundle.get_objects_of_count(entity, p)

                        # Go one page back
                        btn_key = f"btn-{entity_uri}-{p.get_key()}-previous"
                        disabled = offset <= 0
                        if st.button(
                            "<-", type="tertiary", disabled=disabled, key=btn_key
                        ):
                            if offset > PAGINATION_LENGTH:
                                state.set_offset(
                                    entity.uri, p.get_key(), offset - PAGINATION_LENGTH
                                )
                            else:
                                state.set_offset(entity.uri, p.get_key(), 0)
                            st.rerun()

                        # Current page
                        st.markdown(
                            f"{offset} - {min(offset + PAGINATION_LENGTH, total_count)}",
                            width="content",
                        )

                        # Go one page ahead
                        btn_key = f"btn-{entity_uri}-{p.get_key()}-next"
                        disabled = offset + PAGINATION_LENGTH >= total_count
                        if st.button(
                            "->", type="tertiary", disabled=disabled, key=btn_key
                        ):
                            if offset < total_count:
                                state.set_offset(
                                    entity.uri, p.get_key(), offset + PAGINATION_LENGTH
                                )
                            else:
                                state.set_offset(entity.uri, p.get_key(), total_count)
                            st.rerun()

                        # Display total triples
                        st.markdown(f"*Total count: {total_count}*", width="content")

            # If the property is INCOMING for the entity
            else:
                # Property Label
                incoming_text = f'<small style="font-size: 10px; color: gray; text-decoration: none;">(incoming)</small>'
                col_prop.markdown(
                    f"##### **{incoming_text} {get_property_text_with_uri(p)}**",
                    unsafe_allow_html=True,
                )
                if p.domain and p.domain.uri:
                    col_prop.markdown(f"*Domain:* {get_class_text_with_uri(p.domain)}")

                # Fetch all the subjects (with paginagion)
                statements = data_bundle.get_subjects_of(
                    entity, p, limit=PAGINATION_LENGTH, offset=offset
                )

                # Loop through all retrieved subjects
                for i, s in enumerate(statements):
                    col_value, col_info = col_entity.columns(
                        [7, 1], vertical_alignment="center"
                    )

                    # Link to the SUBJECT entity
                    # Because subjects are always entities, no need to differenciate from values
                    with col_value:
                        st.html(get_entity_text_with_uri(s.subject, MAX_STRING_LENGTH))

                    # Add a button which opens a dialog with raw informations about the triple
                    with col_info.container(
                        horizontal=False, horizontal_alignment="right"
                    ):
                        btn_key = (
                            f"btn-{entity_uri}-{p.get_key()}-{s.subject.uri}-{i}-info"
                        )
                        kwargs = {
                            "statement": s,
                            "prefixes": data_bundle.prefixes,
                            "model": data_bundle.model,
                        }
                        st.button(
                            "",
                            icon=":material/info:",
                            type="tertiary",
                            on_click=dialog_triple_info,
                            kwargs=kwargs,
                            key=btn_key,
                        )

                # If there is more object than a single page, or if it is not page 1, display the pagination options
                if len(statements) >= PAGINATION_LENGTH or offset != 0:
                    col_entity.write("")

                    # Container for the paginator
                    with col_entity.container(
                        horizontal=True, vertical_alignment="center"
                    ):
                        # Total entity number
                        total_count = data_bundle.get_subjects_of_count(entity, p)

                        # Go one page back
                        btn_key = f"btn-{entity_uri}-{p.get_key()}-previous"
                        disabled = offset <= 0
                        if st.button(
                            "<-", type="tertiary", disabled=disabled, key=btn_key
                        ):
                            if offset > PAGINATION_LENGTH:
                                state.set_offset(
                                    entity.uri, p.get_key(), offset - PAGINATION_LENGTH
                                )
                            else:
                                state.set_offset(entity.uri, p.get_key(), 0)
                            st.rerun()

                        # Current page
                        st.markdown(
                            f"{offset} - {min(offset + PAGINATION_LENGTH, total_count)}",
                            width="content",
                        )

                        # Go one page ahead
                        btn_key = f"btn-{entity_uri}-{p.get_key()}-next"
                        disabled = offset + PAGINATION_LENGTH >= total_count
                        if st.button(
                            "->", type="tertiary", disabled=disabled, key=btn_key
                        ):
                            if offset < total_count:
                                state.set_offset(
                                    entity.uri, p.get_key(), offset + PAGINATION_LENGTH
                                )
                            else:
                                state.set_offset(entity.uri, p.get_key(), total_count)
                            st.rerun()

                        # Display total triples
                        st.markdown(f"*Total count: {total_count}*", width="content")
