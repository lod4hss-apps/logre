"""Contextual help snippets reused across pages."""

from __future__ import annotations

from typing import Optional
import streamlit as st

HELP_TEXTS = {
    "configuration.prefixes": (
        "Prefixes are shortcuts for long URIs. Configure them once so every page displays readable identifiers."
        " [See the FAQ](/documentation#what-are-prefixes)."
    ),
    "configuration.data_bundles": (
        "A data bundle groups your Data/Model/Metadata graphs plus the authentication info for the endpoint."
        " Manage several bundles and pick the one you want to use by default."
        " [Learn more](/documentation#what-are-data-bundles)."
    ),
    "configuration.import_data": (
        "Import N-Quads or Turtle files directly into the selected graph."
        " [How to import data?](/documentation#how-to-import-data-into-the-sparql-endpoint)."
    ),
    "configuration.update_model": (
        "Download, clear or upload your SHACL model from this block."
        " [What are SHACL models?](/documentation#what-are-shacl)."
    ),
    "dashboard.data_bundle_select": (
        "Switch the active bundle to load another endpoint/configuration."
        " [What are data bundles?](/documentation#what-are-data-bundles)."
    ),
    "data_table.overview": (
        "Browse class instances without writing SPARQL: filter by class, sort results and export the view in a few clicks."
        " [How to see my data?](/documentation#how-to-see-my-data)."
    ),
    "data_table.class_filter": (
        "Select the class whose instances you want to inspect. Only business classes (non-xsd) are listed."
    ),
    "data_table.limit": (
        "Defines how many rows are retrieved per query. Increase it for exports, decrease it for faster iterations."
    ),
    "data_table.sort": (
        "Pick a column and direction to sort server-side before displaying the data."
    ),
    "data_table.filter": (
        "Filter a column using a partial value (case-insensitive). Useful to isolate a subset before exporting."
    ),
    "data_table.export": (
        "Download exactly the current view (filters, sorting and limits applied) as CSV to share or work offline."
    ),
    "dashboard.export": (
        "Jump to the filterable table to prepare a targeted export."
    ),
    "dashboard.find_entity": (
        "Open the global search dialog without leaving the dashboard."
    ),
    "dashboard.create_entity": (
        "Open the entity creation dialog using your SHACL model."
    ),
    "menu.find_entity": (
        "Open the cross-entity search without leaving the current page."
        " [How to see my data?](/documentation#how-to-see-my-data)."
    ),
    "menu.create_entity": (
        "Open the entity creation form that uses your SHACL/model."
        " [How to create new data?](/documentation#how-to-create-new-data)."
    ),
    "find_entity.label": (
        "Type part of the label and press Enter to filter the results."
    ),
    "sparql_editor.saved_query": (
        "Select a saved query to load and run it instantly."
        " [Can I save a specific query?](/documentation#can-i-save-a-specific-query)."
    ),
    "entity_card.raw_triples": (
        "Show the raw triples related to the entity to inspect the stored data."
        " [What is the page Raw triples for?](/documentation#what-is-the-page-raw-triples-for)."
    ),
    "entity_card.visualize": (
        "Open the graph view to navigate through related entities."
        " [What is shown on page Visualization?](/documentation#what-is-shown-on-page-visualization)."
    ),
    "entity_chart.entity_card": (
        "Return to the detailed entity card."
    ),
    "entity_chart.raw_triples": (
        "Display the raw triples for the current entity."
    ),
    "entity_triples.entity_card": (
        "Go back to the entity card to edit its properties."
    ),
    "entity_triples.visualize": (
        "Open the graph navigation starting from this entity."
    ),
    "data_bundle_form.endpoint_technology": (
        "Choose the SPARQL technology used by your server (Fuseki, RDF4J, GraphDB, Allegro…)."
        " [Supported technologies](/documentation#what-are-the-supported-sparql-endpoint-technologies)."
    ),
    "data_bundle_form.endpoint_url": (
        "Provide the full SPARQL endpoint URL."
        " [What is a SPARQL endpoint?](/documentation#what-is-a-sparql-endpoint)."
    ),
    "data_bundle_form.endpoint_username": (
        "Endpoint username, if any (leave blank when public)."
        " [Where do I find credentials?](/documentation#in-the-data-bundle-creation-where-do-i-find-my-sparql-endpoint-username-and-password)."
    ),
    "data_bundle_form.endpoint_password": (
        "Endpoint password, if required."
        " [Where do I find credentials?](/documentation#in-the-data-bundle-creation-where-do-i-find-my-sparql-endpoint-username-and-password)."
    ),
    "data_bundle_form.base_uri": (
        "Defines the root URI used when Logre generates resources (e.g. http://www.example.org/resource/)."
    ),
    "data_bundle_form.named_graphs": (
        "Lists the existing graphs in the endpoint to help you pick the right identifiers."
    ),
    "data_bundle_form.graph_data": (
        "URI of the graph containing your business data (triples)."
        " [Why three graphs?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)."
    ),
    "data_bundle_form.graph_model": (
        "URI of the graph that stores your SHACL/model."
    ),
    "data_bundle_form.graph_metadata": (
        "URI of the graph that stores metadata (imports, provenance, etc.)."
    ),
    "data_bundle_form.model_framework": (
        "Choose the framework used to interpret your model (SHACL, etc.)."
        " [Supported frameworks](/documentation#what-are-the-supported-model-framework-supported)."
    ),
    "data_bundle_form.type_property": (
        "Property used to type your entities (default: rdf:type)."
    ),
    "data_bundle_form.label_property": (
        "Property used for labels (default: rdfs:label)."
    ),
    "data_bundle_form.comment_property": (
        "Property used for descriptions/comments."
    ),
}


def help_text(key: str, fallback: Optional[str] = None) -> Optional[str]:
    """Return the textual hint associated with `key`, falling back when requested."""
    return HELP_TEXTS.get(key, fallback)


def info(key: str) -> None:
    """Render a contextual info caption for the provided key if it exists."""
    text = HELP_TEXTS.get(key)
    if text:
        st.caption(f":material/info: {text}")


def info_icon(key: str) -> None:
    """Render an inline info icon using Streamlit's native tooltip."""
    text = HELP_TEXTS.get(key)
    if not text:
        return
    st.caption("", help=text)
