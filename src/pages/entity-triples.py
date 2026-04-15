import streamlit as st
from graphly.schema import Statement, Resource, Property
from html import escape
import re
from urllib.parse import quote_plus
from components.doc_links import decorate_doc_links
from components.init import init
from components.menu import menu
from lib import state
from lib.utils import get_max_length_text, get_short_uri_with_tail
from dialogs.triple_info import dialog_triple_info

# Page parameters
INCOMING_TRIPLES_FETCHED = 5

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
    # If there is none, Inform the user
    if not entity_uri:
        st.info("Logre needs an URI to show triples.")
    else:
        endpoint_key = state.get_endpoint_key()

        def get_internal_entity_url(uri: str) -> str:
            endpoint_qs = (
                f"&endpoint={quote_plus(endpoint_key)}" if endpoint_key else ""
            )
            return f"/entity?db={quote_plus(data_bundle.key)}{endpoint_qs}&uri={quote_plus(uri)}"

        def get_uri_anchor_html(
            uri: str,
            url: str,
            max_length: int = 55,
            open_external: bool = False,
        ) -> str:
            short_uri = escape(get_short_uri_with_tail(uri, max_length))
            uri_text = escape(uri)
            url_text = escape(url, quote=True)
            if open_external:
                return (
                    f'<a href="{url_text}" target="_blank" rel="noopener noreferrer" '
                    f'title="{uri_text}">{short_uri}</a>'
                )
            return (
                f'<a href="{url_text}" target="_blank" rel="noopener noreferrer" '
                f'title="{uri_text}">{short_uri}</a>'
            )

        def get_resource_display_label(
            resource: Resource | Property,
            max_length: int,
            prefer_class_label_on_missing: bool = False,
        ) -> str:
            label = resource.get_text()
            if isinstance(label, str):
                stripped = label.strip()
                raw_label = (getattr(resource, "label", None) or "").strip()
                if prefer_class_label_on_missing and not raw_label:
                    class_uri = getattr(resource, "class_uri", None)
                    if class_uri:
                        resource_class = data_bundle.model.find_class(class_uri)
                        if resource_class:
                            class_label = (resource_class.get_text() or "").strip()
                            if class_label:
                                label = class_label
                                stripped = class_label
                looks_like_url = bool(
                    re.match(
                        r"^(https?://|www\.|[A-Za-z0-9.-]+\.[A-Za-z]{2,}/)", stripped
                    )
                )
                if looks_like_url:
                    if getattr(resource, "uri", None):
                        shortened = data_bundle.prefixes.shorten(resource.uri)
                        if shortened != resource.uri:
                            label = shortened
                        else:
                            uri_no_slash = resource.uri.rstrip("/")
                            label = (
                                uri_no_slash.rsplit("/", 1)[-1]
                                if "/" in uri_no_slash
                                else resource.uri
                            )
                    else:
                        label = stripped
            return get_max_length_text(str(label), max_length)

        def get_external_uri_url(uri: str) -> str:
            return data_bundle.prefixes.lengthen(uri)

        def render_entity_resource(
            col, resource: Resource, max_length: int = 40
        ) -> None:
            label = get_resource_display_label(
                resource,
                max_length,
                prefer_class_label_on_missing=True,
            )
            uri_html = get_uri_anchor_html(
                resource.uri,
                get_internal_entity_url(resource.uri),
                open_external=False,
            )
            with col:
                st.html(f"<strong>{escape(label)}</strong> ({uri_html})")

        def render_ontology_resource(
            col, resource: Resource | Property, max_length: int = 40
        ) -> None:
            label = get_resource_display_label(resource, max_length)
            uri_html = get_uri_anchor_html(
                resource.uri,
                get_external_uri_url(resource.uri),
                open_external=True,
            )
            with col:
                st.html(f"<span>{escape(label)}</span> ({uri_html})")

        # Function that is used for each category (Basic, Incomings, Outgoings)
        def display_triple(
            statement: Statement,
            object_kind: str = "entity_or_literal",
        ) -> None:
            col_sub, col_pred, col_obj, col_info = st.columns(
                [6, 6, 6, 1], gap="medium", vertical_alignment="bottom"
            )

            # Subject
            render_entity_resource(col_sub, statement.subject)

            # Predicate
            render_ontology_resource(col_pred, statement.predicate)

            # Object (Class instance)
            if statement.object.resource_type == "iri":
                if object_kind == "ontology":
                    render_ontology_resource(col_obj, statement.object)
                else:
                    render_entity_resource(col_obj, statement.object)
            # Object (Literal)
            else:
                object_text = get_max_length_text(statement.object.get_text(), 40)
                col_obj.markdown(f"> {object_text}")

            with col_info.container(horizontal=True, horizontal_alignment="right"):
                key = f"btn-{statement.subject.uri}-{statement.predicate.uri}-{statement.object.uri if hasattr(statement.object, 'uri') else statement.object.literal}-info"
                kwargs = {
                    "statement": statement,
                    "prefixes": data_bundle.prefixes,
                    "model": data_bundle.model,
                }
                st.button(
                    "",
                    icon=":material/info:",
                    type="tertiary",
                    on_click=dialog_triple_info,
                    kwargs=kwargs,
                    key=key,
                )

        # Header: entity name, additional info and description
        col_title, col_actions = st.columns([20, 10], vertical_alignment="bottom")
        entity = data_bundle.get_entity_basics(entity_uri)
        entity_label = get_resource_display_label(entity, max_length=120)
        entity_uri_html = get_uri_anchor_html(
            entity.uri,
            get_internal_entity_url(entity.uri),
            open_external=False,
        )
        with col_title:
            st.html(
                f"<h1 style='margin: 0;'><span>{escape(entity_label)}</span></h1>"
                "<div style='font-size: 0.85rem; color: var(--secondary-text-color, #6b7280); margin-top: 0.15rem;'>"
                f"{entity_uri_html}"
                "</div>"
            )

        # Header options
        with col_actions.container(horizontal=True, horizontal_alignment="right"):
            if st.button(
                "Entity Card",
                help=decorate_doc_links(
                    "[What is an entity card?](/documentation?section=what-is-an-entity-card)"
                ),
            ):
                st.switch_page("pages/entity-card.py")
            # Button to switch to visualization
            if st.button(
                "Visualize",
                help=decorate_doc_links(
                    "[What is the visualization?](/documentation?section=what-is-shown-on-page-visualization)"
                ),
            ):
                st.switch_page("pages/entity-chart.py")
        st.write("")

        st.divider()

        # First category: Basics
        st.markdown("### Basic information")

        # Type
        if entity.class_uri:
            prop_type = next(
                iter(data_bundle.model.find_properties(data_bundle.model.type_property))
            )
            entity_class = data_bundle.model.find_class(entity.class_uri)
            display_triple(
                Statement(entity, prop_type, entity_class), object_kind="ontology"
            )

        # Label
        if entity.label:
            prop_label = next(
                iter(
                    data_bundle.model.find_properties(data_bundle.model.label_property)
                )
            )
            entity_label = Resource(entity.label, resource_type="literal")
            display_triple(Statement(entity, prop_label, entity_label))

        # Comment
        if entity.comment:
            comment = next(
                iter(
                    data_bundle.model.find_properties(
                        data_bundle.model.comment_property
                    )
                )
            )
            entity_comment = Resource(entity.comment, resource_type="literal")
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
        title_container.markdown("### Outgoing statements", width="content")
        statements = data_bundle.get_outgoing_statements_of(
            entity, skip_props=skip_props
        )
        title_container.markdown(f"*{len(statements)} total outgoing triples*")

        # Display triples
        for s in statements:
            display_triple(s)
        if len(statements) == 0:
            st.markdown("*None*")

        st.divider()

        # Second category: Incoming statements
        title_container = st.container(horizontal=True, vertical_alignment="bottom")
        title_container.markdown("### Incoming statements", width="content")
        total_inc_number = data_bundle.get_incoming_statements_of_count(entity)
        title_container.markdown(f"*{total_inc_number} total incoming triples*")

        # Limit the quantity fetched, to not overload the page
        number_to_fetch = 5

        # This is the flag to not fetch twice in case user fetches more via the selectbox
        fetched = False

        # But if there is more, allow user to fetch more, but need interaction
        if total_inc_number >= 5:
            number_to_fetch = title_container.number_input(
                "Number to fetch", 5, step=5, width=150
            )
            if title_container.button("Fetch"):
                statements = data_bundle.get_incoming_statements_of(
                    entity, limit=number_to_fetch, skip_props=skip_props
                )
                fetched = True

        # Avoid re-fetching
        if not fetched:
            statements = data_bundle.get_incoming_statements_of(
                entity, skip_props=skip_props
            )

        # Display triples
        for s in statements:
            display_triple(s)
        if len(statements) == 0:
            st.markdown("*None*")
