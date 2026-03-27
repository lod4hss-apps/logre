import streamlit as st
import os
from urllib.parse import urlparse
from requests.exceptions import HTTPError, ConnectionError, Timeout
from components.doc_links import decorate_doc_links
from lib import state
from schema.data_bundle import DataBundle
from schema.model_framework import ModelFramework
from schema.sparql_technologies import (
    SPARQLTechnology,
    get_sparql_technology,
)
from components.help import help_text


ENDPOINT_TECHNOLOGIES_STR = [e.value for e in list(SPARQLTechnology)]
MODEL_FRAMEWORKS_STR = [e.value for e in list(ModelFramework)]


@st.dialog("Data Bundle", width="medium")
def dialog_data_bundle_form(db: DataBundle = None) -> None:
    """
    Displays a dialog form for creating or editing a Data Bundle.

    Args:
        db (DataBundle, optional): The existing Data Bundle to edit. If None, a new Data Bundle will be created.

    Returns:
        None

    Behavior:
        - Allows the user to input or modify:
            - Name, SPARQL endpoint technology and URL, credentials
            - Base URI
            - Graph URIs (data, model, metadata)
            - Model framework
            - Core properties (type, label, comment)
        - Validates required fields before enabling the save/create button.
        - Creates a new Data Bundle or updates the existing one in the application state.
        - Reruns the page after saving to reflect changes.
    """
    # Data Bundle name, alone on its line
    col_name, _ = st.columns([1, 1])
    new_name = col_name.text_input("Name ❗️", value=db.name if db else "")

    st.write("")
    st.write("")

    # SPARQL endpoint
    endpoints = state.get_endpoints()
    endpoints_names = list(map(lambda endpoint: endpoint.name, endpoints))
    if db and db.endpoint.name in endpoints_names:
        endpoint_index = endpoints_names.index(db.endpoint.name) if db else None
    else:
        endpoint_index = None
    new_endpoint_name = st.selectbox(
        "SPARQL endpoint ❗️", options=endpoints_names, index=endpoint_index
    )
    if new_endpoint_name:
        new_endpoint = endpoints[endpoints_names.index(new_endpoint_name)]
    else:
        new_endpoint = None

    st.write("")
    st.write("")

    # Data Bundle base URI
    new_base_uri = st.text_input(
        "Base URI ❗️",
        value=db.base_uri if db else "http://www.example.org/resource/",
        help=help_text("data_bundle_form.base_uri"),
    )

    st.write("")
    st.write("")

    # List current named graph
    if st.button(
        "List existing graphs on selected endpoint", disabled=not new_endpoint
    ):
        try:
            graphs = __get_graph_list(
                new_endpoint.technology_name,
                new_endpoint.url,
                new_endpoint.username,
                new_endpoint.password,
                new_base_uri.strip(),
            )
        except HTTPError as err:
            status_code = err.response.status_code
            reason = err.response.reason
            message = f"There was an error while loading the data bundle {new_name}'s graph list.\n\n"
            message += f"[HTTP Error {status_code}]: {reason}\n\n{err.args[0]}"
            if err.response.status_code == 400:
                message += f"\n\n{err.response.text}"
            raise Exception(message)
        except (ConnectionError, Timeout):
            state.deselect_bundle_after_endpoint_failure()
            st.rerun()

        st.markdown(f"> *Default graph*")
        for graph in graphs:
            st.markdown(f"> {graph}")

    st.write("")

    # Data Bundle graphs
    col_data, col_model, col_metadata = st.columns([1, 1, 1])
    new_graph_data_uri = col_data.text_input(
        "Data graph URI",
        value=db.data.uri if db else "base:data",
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation?section=in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)"
        ),
    )
    new_graph_model_uri = col_model.text_input(
        "Model graph URI",
        value=db.model.uri if db else "base:model",
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation?section=in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)"
        ),
    )
    new_graph_metadata_uri = col_metadata.text_input(
        "Metadata graph URI",
        value=db.metadata.uri if db else "base:metadata",
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation?section=in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)"
        ),
    )

    st.write("")
    st.write("")

    # Data Bundle framework used for model
    col_framework, _ = st.columns([1, 2])
    new_framework = col_framework.selectbox(
        "Model framework ❗️",
        options=MODEL_FRAMEWORKS_STR,
        index=MODEL_FRAMEWORKS_STR.index(db.model.framework_name) if db else None,
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[What are the supported model framework supported?](/documentation?section=what-are-the-supported-model-framework-supported)"
        ),
    )

    # Data Bundle basic properties (type, label, comment)
    col_type, col_label, col_comment = st.columns([1, 1, 1])
    new_type_prop_uri = col_type.text_input(
        "Type property ❗️",
        value=db.model.type_property if db else "rdf:type",
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[Why should I provide type, label and comment properties URIs?](/documentation?section=in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)"
        ),
    )
    new_label_prop_uri = col_label.text_input(
        "Label property ❗️",
        value=db.model.label_property if db else "rdfs:label",
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[Why should I provide type, label and comment properties URIs?](/documentation?section=in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)"
        ),
    )
    new_comment_prop_uri = col_comment.text_input(
        "Comment property ❗️",
        value=db.model.comment_property if db else "rdfs:comment",
        disabled=not new_endpoint,
        help=decorate_doc_links(
            "[Why should I provide type, label and comment properties URIs?](/documentation?section=in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)"
        ),
    )

    st.write("")
    st.write("")

    new_name_clean = new_name.strip()
    new_base_uri_clean = new_base_uri.strip()
    new_graph_data_uri_clean = new_graph_data_uri.strip()
    new_graph_model_uri_clean = new_graph_model_uri.strip()
    new_graph_metadata_uri_clean = new_graph_metadata_uri.strip()
    new_type_prop_uri_clean = new_type_prop_uri.strip()
    new_label_prop_uri_clean = new_label_prop_uri.strip()
    new_comment_prop_uri_clean = new_comment_prop_uri.strip()

    with st.container(horizontal=True, horizontal_alignment="center"):
        # Disabled if some required fields are missing
        disabled = not (
            new_name_clean
            and new_endpoint
            and new_base_uri_clean
            and new_framework
            and new_type_prop_uri_clean
            and new_label_prop_uri_clean
            and new_comment_prop_uri_clean
        )
        if st.button(
            "Save" if db else "Create", type="primary", width=200, disabled=disabled
        ):
            # Create the Data Bundle
            new_db = DataBundle.from_dict(
                {
                    "name": new_name_clean,
                    "base_uri": new_base_uri_clean,
                    "endpoint_name": new_endpoint.name,
                    "endpoint_url": new_endpoint.url,
                    "username": new_endpoint.username,
                    "password": new_endpoint.password,
                    "endpoint_technology": new_endpoint.technology_name,
                    "model_framework": new_framework,
                    "prop_type_uri": new_type_prop_uri_clean,
                    "prop_label_uri": new_label_prop_uri_clean,
                    "prop_comment_uri": new_comment_prop_uri_clean,
                    "graph_data_uri": new_graph_data_uri_clean,
                    "graph_model_uri": new_graph_model_uri_clean,
                    "graph_metadata_uri": new_graph_metadata_uri_clean,
                },
                prefixes=state.get_prefixes(),
                endpoints=endpoints,
            )

            current_bundle = state.get_data_bundle()
            was_selected_bundle = (
                db is not None
                and current_bundle is not None
                and current_bundle.key == db.key
                and state.get_endpoint_identifier(current_bundle.endpoint)
                == state.get_endpoint_identifier(db.endpoint)
            )

            # And add it to state
            state.update_data_bundle(db, new_db)

            # Keep current selection when editing the selected bundle so model/data
            # are reloaded with the updated bundle settings.
            if was_selected_bundle:
                state.set_data_bundle(new_db)
            st.rerun()


@st.cache_data(ttl=120, show_spinner=False)
def __get_graph_list(
    technology: str | None,
    url: str | None,
    username: str | None,
    password: str | None,
    base_uri: str | None,
) -> list[str]:
    technology_clean = (technology or "").strip()
    url_clean = (url or "").strip()
    username_clean = (username or "").strip()
    password_clean = password or ""
    base_uri_clean = (base_uri or "").strip()

    has_credentials = bool(username_clean and password_clean)
    allow_without_credentials = _is_local_rdf4j_endpoint(technology_clean, url_clean)

    if (
        technology_clean
        and url_clean
        and base_uri_clean
        and (has_credentials or allow_without_credentials)
    ):
        # First there is the need to set the endpoint, prefixes etc locally, based on things above
        endpoint = get_sparql_technology(technology_clean)(
            url_clean,
            username_clean,
            password_clean,
        )

        # Make the query
        with st.spinner("Fetching existing named graph"):
            graphs = endpoint.run("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }")

        return [g["g"] for g in graphs]
    else:
        return []


def _is_local_rdf4j_endpoint(technology: str, url: str) -> bool:
    if technology != SPARQLTechnology.RDF4J.value:
        return False

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    local_hosts = {"localhost", "127.0.0.1", "::1", "rdf4j", "host.docker.internal"}

    configured_rdf4j_server_url = os.getenv("RDF4J_SERVER_URL", "")
    configured_rdf4j_hostname = (
        urlparse(configured_rdf4j_server_url).hostname or ""
    ).lower()
    if configured_rdf4j_hostname:
        local_hosts.add(configured_rdf4j_hostname)

    return hostname in local_hosts
