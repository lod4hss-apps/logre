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

    def get_external_link_icon_html(url: str, title: str = "Open external resource") -> str:
        external_url = escape(url, quote=True)
        tooltip = escape(title, quote=True)
        return (
            f'<a href="{external_url}" target="_blank" rel="noopener noreferrer" title="{tooltip}" '
            "style='display: inline-flex; align-items: center; justify-content: center; margin-left: 0.45rem; color: #84e17f; text-decoration: none; font-size: 1.15rem; line-height: 1;'>"
            "&#8599;"
            "</a>"
        )

    def get_internal_entity_uri_html(uri: str, max_uri_length: int = 55) -> str:
        internal_url = escape(get_internal_entity_url(uri), quote=True)
        uri_text = escape(uri)
        short_uri = escape(get_short_uri_with_tail(uri, max_uri_length))
        return f'<a href="{internal_url}" target="_blank" rel="noopener noreferrer" title="{uri_text}">{short_uri}</a>'

    def get_entity_uri_html(uri: str, max_uri_length: int = 55) -> str:
        return (
            f"{get_internal_entity_uri_html(uri, max_uri_length)} "
            f"{get_external_link_icon_html(get_external_uri_url(uri), f'Open {uri} outside Logre')}"
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

    def get_property_meta_html(property, is_outgoing: bool) -> str:
        property_url = escape(get_external_uri_url(property.uri), quote=True)
        short_property_uri = escape(get_short_uri_with_tail(property.uri))
        related_class = property.range if is_outgoing else property.domain
        meta_parts = [
            f'<a href="{property_url}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">{short_property_uri}</a>'
        ]
        if related_class and related_class.uri and related_class.get_text():
            related_class_url = escape(get_external_uri_url(related_class.uri), quote=True)
            related_class_label = escape(related_class.get_text())
            meta_parts.append(
                f'<a href="{related_class_url}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">{related_class_label}</a>'
            )
        return (
            "<div style='font-size: 0.82rem; color: color-mix(in srgb, var(--secondary-text-color, #6b7280) 82%, transparent); margin-top: 0.5rem; line-height: 1.35;'>"
            + " &bull; ".join(meta_parts)
            + "</div>"
        )

    def get_property_heading_html(property, is_outgoing: bool) -> str:
        label = escape(property.get_text())
        if is_outgoing:
            return f"<div style='font-size: 0.98rem; color: color-mix(in srgb, var(--text-color, #f3f4f6) 90%, transparent); margin-bottom: 0.1rem;'>{label}</div>"
        return (
            "<div style='display: flex; align-items: center; gap: 0.45rem;'>"
            f"<span style='font-size: 0.98rem; color: color-mix(in srgb, var(--text-color, #f3f4f6) 90%, transparent);'>{label}</span>"
            "<span style='font-size: 0.72rem; color: color-mix(in srgb, var(--secondary-text-color, #6b7280) 82%, transparent); text-transform: uppercase; letter-spacing: 0.04em;'>Incoming</span>"
            "</div>"
        )

    def get_literal_value_html(value: str) -> str:
        return (
            "<div style='font-size: 1.3rem; font-weight: 600; line-height: 1.3; margin-top: 0.2rem;'>"
            f"{escape(value)}"
            "</div>"
        )

    def get_entity_value_html(resource, max_length: int | None = None) -> str:
        label = resource.get_text()
        if max_length:
            label = get_max_length_text(label, max_length)
        internal_url = escape(get_internal_entity_url(resource.uri), quote=True)
        label_title = escape(resource.get_text(), quote=True)
        external_icon_html = get_external_link_icon_html(
            get_external_uri_url(resource.uri),
            f"Open {resource.uri} outside Logre",
        )
        return (
            "<div style='display: flex; align-items: center; gap: 0.15rem; font-size: 1.3rem; font-weight: 600; line-height: 1.3; margin-top: 0.2rem;'>"
            f'<a href="{internal_url}" target="_blank" rel="noopener noreferrer" title="{label_title}" style="color: inherit; text-decoration: none;">{escape(label)}</a>{external_icon_html}'
            "</div>"
        )

    def get_entity_header_html(resource, uri_max_length: int = 55) -> str:
        label = escape(resource.get_text())
        label_title = escape(resource.get_text(), quote=True)
        return (
            f"<h1 style='margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{label_title}'>{label}</h1>"
        )

    def get_entity_class_html(resource) -> str:
        if not resource or not resource.uri:
            return ""
        class_url = escape(get_external_uri_url(resource.uri), quote=True)
        class_label = escape(resource.get_text())
        short_uri = escape(get_short_uri_with_tail(resource.uri))
        return (
            "<div style='font-size: 1rem; color: var(--secondary-text-color, #9ca3af); margin-top: 0.35rem;'>"
            f"{class_label} - <a href=\"{class_url}\" target=\"_blank\" rel=\"noopener noreferrer\" style=\"color: inherit; text-decoration: none;\">{short_uri}</a>"
            "</div>"
        )

    def get_header_external_action_html(url: str, title: str) -> str:
        return get_external_link_icon_html(url, title)

    def get_last_page_offset(total_count: int) -> int:
        if total_count <= PAGINATION_LENGTH:
            return 0
        return ((total_count - 1) // PAGINATION_LENGTH) * PAGINATION_LENGTH

    def get_model_property(uri: str):
        properties = data_bundle.model.find_properties(uri)
        return properties[0] if properties else None

    def get_system_skip_props() -> list:
        system_props = []
        for uri in (
            data_bundle.model.type_property,
            data_bundle.model.label_property,
            data_bundle.model.comment_property,
        ):
            property = get_model_property(uri)
            if property:
                system_props.append(property)
        return system_props

    def group_statements_by_property(statements: list) -> list:
        grouped = {}
        for statement in statements:
            property_uri = statement.predicate.uri
            if property_uri not in grouped:
                grouped[property_uri] = {
                    "property": statement.predicate,
                    "statements": [],
                }
            grouped[property_uri]["statements"].append(statement)
        return list(grouped.values())

    def render_statement_value(statement, key_prefix: str, index: int) -> None:
        col_value, col_info = st.columns([12, 1], vertical_alignment="top")

        if statement.object.resource_type == "iri":
            with col_value:
                st.html(get_entity_value_html(statement.object, MAX_STRING_LENGTH))
            object_key = statement.object.uri
        else:
            object_text = get_max_length_text(statement.object.get_text(), MAX_STRING_LENGTH)
            with col_value:
                st.html(get_literal_value_html(object_text))
            object_key = statement.object.literal

        with col_info.container(horizontal=False, horizontal_alignment="right"):
            kwargs = {
                "statement": statement,
                "prefixes": data_bundle.prefixes,
                "model": data_bundle.model,
            }
            st.button(
                "",
                icon=":material/expand_more:",
                type="tertiary",
                help="Show RDF details",
                on_click=dialog_triple_info,
                kwargs=kwargs,
                key=f"btn-{key_prefix}-{object_key}-{index}-info",
            )

    def render_property_group(property, statements: list, key_prefix: str) -> None:
        st.html(get_property_heading_html(property, is_outgoing=True))
        for i, statement in enumerate(statements):
            render_statement_value(statement, key_prefix, i)
            if i < len(statements) - 1:
                st.divider()
        st.html(get_property_meta_html(property, is_outgoing=True))

    def get_section_heading_html(label: str) -> str:
        return (
            "<div style='font-size: 1.02rem; color: color-mix(in srgb, var(--text-color, #f3f4f6) 92%, transparent); margin-bottom: 0.1rem;'>"
            f"{escape(label)}"
            "</div>"
        )

    def get_section_meta_html(resource=None, property=None) -> str:
        meta_parts = []
        if property and property.uri:
            property_url = escape(get_external_uri_url(property.uri), quote=True)
            property_uri = escape(get_short_uri_with_tail(property.uri))
            meta_parts.append(
                f'<a href="{property_url}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">{property_uri}</a>'
            )

        if resource and getattr(resource, "class_uri", None):
            resource_class = data_bundle.model.find_class(resource.class_uri)
            if resource_class and resource_class.uri:
                class_url = escape(get_external_uri_url(resource_class.uri), quote=True)
                class_label = escape(resource_class.get_text())
                meta_parts.append(
                    f'<a href="{class_url}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">{class_label}</a>'
                )

        if not meta_parts:
            return ""

        return (
            "<div style='font-size: 0.82rem; color: color-mix(in srgb, var(--secondary-text-color, #6b7280) 82%, transparent); margin-top: 0.5rem; line-height: 1.35;'>"
            + " &bull; ".join(meta_parts)
            + "</div>"
        )

    def get_section_label(resource, fallback_property=None) -> str:
        if resource and resource.get_text():
            resource_text = resource.get_text().strip()
            resource_uri = getattr(resource, "uri", "") or ""
            if (
                resource_text
                and resource_text != resource_uri
                and not resource_text.startswith("http://")
                and not resource_text.startswith("https://")
            ):
                return resource_text

        if resource and getattr(resource, "class_uri", None):
            resource_class = data_bundle.model.find_class(resource.class_uri)
            if resource_class and resource_class.get_text():
                return resource_class.get_text()

        if fallback_property and fallback_property.get_text():
            return fallback_property.get_text()
        if resource and getattr(resource, "uri", None):
            return get_short_uri_with_tail(resource.uri)
        if fallback_property and getattr(fallback_property, "uri", None):
            return get_short_uri_with_tail(fallback_property.uri)
        return "Additional information"

    # Header: entity name, additional info and description
    st.html(get_entity_header_html(entity))

    if entity_class and entity_class.uri:
        st.html(get_entity_class_html(entity_class))
    if entity.comment:
        st.markdown(entity.comment)

    # Header options
    col_nav, col_actions = st.columns([10, 3], vertical_alignment="center")
    with col_nav.container(horizontal=True, horizontal_alignment="left"):
        if st.button(
            "Raw triples",
            type="secondary",
            help=decorate_doc_links(
                "[What are raw triples?](/documentation?section=what-is-the-page-raw-triples-for)"
            ),
        ):
            st.switch_page("pages/entity-triples.py")
        if st.button(
            "Visualize",
            type="secondary",
            help=decorate_doc_links(
                "[What is the visualization?](/documentation?section=what-is-shown-on-page-visualization)"
            ),
        ):
            st.switch_page("pages/entity-chart.py")
        st.html(
            get_header_external_action_html(
                get_external_uri_url(entity.uri),
                f"Open {entity.uri} outside Logre",
            )
        )

    with col_actions.container(horizontal=True, horizontal_alignment="right"):
        if st.button("", icon=":material/edit:", type="tertiary"):
            dialog_entity_edition(entity)
        # Button to delete the entity (open confirmation dialog)
        if st.button("", icon=":material/delete:", type="tertiary"):

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

    st.divider()

    # According to the model (thanks to the entity class), get all the properties that the entity can have in its card
    all_properties = data_bundle.get_card_properties_of(entity.class_uri)
    system_skip_props = get_system_skip_props()

    # Loop through all of them
    for prop_index, p in enumerate(all_properties):
        # In case it is not the first "st.run", get the right entities
        offset = state.get_offset(entity.uri, p.get_key())
        is_outgoing = p.domain and p.domain.uri == entity_class.uri

        if is_outgoing:
            statements = data_bundle.get_objects_of(entity, p, PAGINATION_LENGTH, offset)
            if not statements and offset != 0:
                total_count = data_bundle.get_objects_of_count(entity, p)
                if total_count > 0:
                    state.set_offset(entity.uri, p.get_key(), get_last_page_offset(total_count))
                    st.rerun()
            elif not statements:
                continue
        else:
            statements = data_bundle.get_subjects_of(
                entity, p, limit=PAGINATION_LENGTH, offset=offset
            )
            if not statements and offset != 0:
                total_count = data_bundle.get_subjects_of_count(entity, p)
                if total_count > 0:
                    state.set_offset(entity.uri, p.get_key(), get_last_page_offset(total_count))
                    st.rerun()
            elif not statements:
                continue

        with st.container():
            st.html(get_property_heading_html(p, is_outgoing=is_outgoing))

            for i, s in enumerate(statements):
                if is_outgoing:
                    render_statement_value(s, f"{entity_uri}-{p.get_key()}-out", i)
                else:
                    col_value, col_info = st.columns([12, 1], vertical_alignment="top")
                    with col_value:
                        st.html(get_entity_value_html(s.subject, MAX_STRING_LENGTH))
                    with col_info.container(horizontal=False, horizontal_alignment="right"):
                        kwargs = {
                            "statement": s,
                            "prefixes": data_bundle.prefixes,
                            "model": data_bundle.model,
                        }
                        st.button(
                            "",
                            icon=":material/expand_more:",
                            type="tertiary",
                            help="Show RDF details",
                            on_click=dialog_triple_info,
                            kwargs=kwargs,
                            key=f"btn-{entity_uri}-{p.get_key()}-{s.subject.uri}-{i}-info",
                        )

                if i < len(statements) - 1:
                    st.divider()

            st.html(get_property_meta_html(p, is_outgoing=is_outgoing))

            if len(statements) >= PAGINATION_LENGTH or offset != 0:
                st.write("")
                with st.container(horizontal=True, vertical_alignment="center"):
                    total_count = (
                        data_bundle.get_objects_of_count(entity, p)
                        if is_outgoing
                        else data_bundle.get_subjects_of_count(entity, p)
                    )

                    btn_key = f"btn-{entity_uri}-{p.get_key()}-previous"
                    disabled = offset <= 0
                    if st.button("<-", type="tertiary", disabled=disabled, key=btn_key):
                        if offset > PAGINATION_LENGTH:
                            state.set_offset(
                                entity.uri, p.get_key(), offset - PAGINATION_LENGTH
                            )
                        else:
                            state.set_offset(entity.uri, p.get_key(), 0)
                        st.rerun()

                    st.markdown(
                        f"{offset} - {min(offset + PAGINATION_LENGTH, total_count)}",
                        width="content",
                    )

                    btn_key = f"btn-{entity_uri}-{p.get_key()}-next"
                    disabled = offset + PAGINATION_LENGTH >= total_count
                    if st.button("->", type="tertiary", disabled=disabled, key=btn_key):
                        if offset < total_count:
                            state.set_offset(
                                entity.uri, p.get_key(), offset + PAGINATION_LENGTH
                            )
                        else:
                            state.set_offset(entity.uri, p.get_key(), total_count)
                        st.rerun()

                    st.markdown(f"*Total count: {total_count}*", width="content")

        if prop_index < len(all_properties) - 1:
            st.divider()

    extended_skip_props = list(all_properties) + system_skip_props
    extended_candidates = data_bundle.get_outgoing_statements_of(
        entity, skip_props=extended_skip_props
    )
    extended_candidates = [
        statement
        for statement in extended_candidates
        if statement.object.resource_type == "iri"
    ]

    extended_sections = []
    for property_group in group_statements_by_property(extended_candidates):
        enriched_objects = []
        for statement in property_group["statements"]:
            child_statements = data_bundle.get_outgoing_statements_of(
                statement.object, skip_props=system_skip_props
            )
            enriched_objects.append(
                {
                    "statement": statement,
                    "child_groups": group_statements_by_property(child_statements),
                }
            )

        if enriched_objects:
            extended_sections.append(
                {
                    "kind": "outgoing",
                    "property": property_group["property"],
                    "objects": enriched_objects,
                    "label": property_group["property"].get_text(),
                }
            )

    incoming_total = data_bundle.get_incoming_statements_of_count(entity)
    incoming_candidates = []
    if incoming_total > 0:
        incoming_candidates = data_bundle.get_incoming_statements_of(
            entity, limit=incoming_total, skip_props=system_skip_props
        )
        incoming_candidates = [
            statement
            for statement in incoming_candidates
            if statement.subject.resource_type == "iri"
        ]

    for statement in incoming_candidates:
        child_skip_props = list(system_skip_props) + [statement.predicate]
        child_statements = data_bundle.get_outgoing_statements_of(
            statement.subject, skip_props=child_skip_props
        )
        child_statements = [
            child_statement
            for child_statement in child_statements
            if not (
                child_statement.object.resource_type == "iri"
                and child_statement.object.uri == entity.uri
            )
        ]

        extended_sections.append(
            {
                "kind": "incoming",
                "resource": statement.subject,
                "property": statement.predicate,
                "child_groups": group_statements_by_property(child_statements),
                "label": get_section_label(statement.subject, statement.predicate),
            }
        )

    if extended_sections:
        st.divider()
        with st.expander(
            f"Additional information ({len(extended_sections)})", expanded=False
        ):
            st.markdown("Select additional sections")
            selected_sections = []
            for section_index, section in enumerate(extended_sections):
                if section["kind"] == "outgoing":
                    section_key = section["property"].get_key()
                else:
                    section_key = section["resource"].uri
                checkbox_key = f"extended-card-{entity.uri}-{section_key}-selected"
                if st.checkbox(
                    section["label"],
                    value=False,
                    key=checkbox_key,
                ):
                    selected_sections.append((section_index, section))

            if selected_sections:
                st.divider()

            for selected_index, (section_index, section) in enumerate(selected_sections):
                if section["kind"] == "outgoing":
                    st.html(get_property_heading_html(section["property"], is_outgoing=True))
                    st.html(get_property_meta_html(section["property"], is_outgoing=True))

                    for object_index, enriched_object in enumerate(section["objects"]):
                        st.html(get_entity_value_html(enriched_object["statement"].object))

                        for child_group_index, child_group in enumerate(
                            enriched_object["child_groups"]
                        ):
                            with st.container():
                                render_property_group(
                                    child_group["property"],
                                    child_group["statements"],
                                    (
                                        f"extended-{section_index}-{object_index}-"
                                        f"{child_group['property'].get_key()}"
                                    ),
                                )
                            if child_group_index < len(enriched_object["child_groups"]) - 1:
                                st.divider()

                        if object_index < len(section["objects"]) - 1:
                            st.divider()
                else:
                    st.html(get_section_heading_html(section["label"]))
                    meta_html = get_section_meta_html(
                        resource=section["resource"], property=section["property"]
                    )
                    if meta_html:
                        st.html(meta_html)

                    if section["child_groups"]:
                        for child_group_index, child_group in enumerate(
                            section["child_groups"]
                        ):
                            with st.container():
                                render_property_group(
                                    child_group["property"],
                                    child_group["statements"],
                                    (
                                        f"extended-in-{section_index}-"
                                        f"{child_group['property'].get_key()}"
                                    ),
                                )
                            if child_group_index < len(section["child_groups"]) - 1:
                                st.divider()
                    else:
                        st.html(get_entity_value_html(section["resource"]))

                if selected_index < len(selected_sections) - 1:
                    st.divider()
