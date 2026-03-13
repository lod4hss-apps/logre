import streamlit as st

from components.doc_links import decorate_doc_links
from lib import state
from dialogs.find_entity import dialog_find_entity
from dialogs.entity_creation import dialog_entity_creation
from components.help import help_text


def menu() -> None:
    """
    Builds and renders the Streamlit sidebar menu for the application.

    Features:
        - Displays the application title and version.
        - Provides navigation links to different pages (Configuration, SPARQL Editor, Import/Export, Entity, Data Table).
        - Allows selection of a data bundle from the available options.
        - Updates the selected data bundle in the application state.
        - Displays data bundle-related commands (e.g., Find entity, Create entity) when a bundle is selected.

    Returns:
        None
    """
    try:
        # From state
        version = state.get_version()
        endpoints = state.get_endpoints()
        endpoint = state.get_endpoint()
        data_bundles = state.get_data_bundles()
        data_bundle = state.get_data_bundle()
        default_data_bundle = state.get_default_data_bundle()

        def _endpoint_id(ep):
            return state.get_endpoint_identifier(ep) if ep else None

        def _same_bundle(a, b) -> bool:
            if not a and not b:
                return True
            if not a or not b:
                return False
            return a.key == b.key and _endpoint_id(a.endpoint) == _endpoint_id(
                b.endpoint
            )

        def _clear_bundle_widget_state() -> None:
            stale_keys = [
                key
                for key in st.session_state.keys()
                if key == "sidebar-data-bundle"
                or key.startswith("sidebar-data-bundle-")
            ]
            for key in stale_keys:
                del st.session_state[key]

        # Keep endpoint/data bundle coherent even when URL params or page transitions
        # restore a stale bundle from another endpoint.
        if endpoint:
            endpoint_id = _endpoint_id(endpoint)
            if data_bundle and _endpoint_id(data_bundle.endpoint) != endpoint_id:
                state.set_data_bundle(None)
                _clear_bundle_widget_state()
                state.set_query_params(["endpoint", "db", "uri"])
                st.rerun()

        # Sidebar title
        with st.sidebar.container(horizontal=True, vertical_alignment="bottom"):
            st.markdown(f"# Logre", width="content")
            st.markdown(
                f"<small>v{version}</small>", unsafe_allow_html=True, width="content"
            )

        if not data_bundle and default_data_bundle:
            default_label = default_data_bundle.name
            default_endpoint_name = default_data_bundle.endpoint.name
            if st.sidebar.button(
                "Use default Data Bundle",
                type="secondary",
                width="stretch",
                help=f"Select '{default_label}' on endpoint '{default_endpoint_name}'.",
            ):
                if state.select_default_data_bundle():
                    _clear_bundle_widget_state()
                    state.set_query_params(["endpoint", "db", "uri"])
                else:
                    state.set_toast(
                        "Default Data Bundle is no longer available.",
                        icon=":material/warning:",
                    )
                st.rerun()

        # Page links
        st.sidebar.write("\n")
        st.sidebar.page_link(
            "pages/dashboard.py", label="Dashboard", disabled=not data_bundle
        )
        st.sidebar.write("\n")
        # Data bundle commands
        if data_bundle:
            model_ready = data_bundle.has_usable_model()
            if not model_ready:
                st.sidebar.warning(
                    "Model not available yet. Import a model or verify endpoint and graph settings.",
                    icon=":material/warning:",
                )
            with st.sidebar.container(
                horizontal=False,
                horizontal_alignment="center",
                vertical_alignment="bottom",
                height="stretch",
            ):
                help_txt = (
                    "Your model does not have any classes with at least one property."
                    if not model_ready
                    else help_text("menu.find_entity")
                )
                if st.button(
                    "Find entity",
                    icon=":material/search:",
                    type="secondary",
                    width="stretch",
                    disabled=not model_ready,
                    help=help_txt,
                ):
                    dialog_find_entity()
                help_txt = (
                    "Your model does not have any classes with at least one property."
                    if not model_ready
                    else help_text("menu.create_entity")
                )
                if st.button(
                    "Create entity",
                    icon=":material/line_start_circle:",
                    type="secondary",
                    width="stretch",
                    disabled=not model_ready,
                    help=help_txt,
                ):
                    dialog_entity_creation()

        with st.sidebar.container(horizontal=True, horizontal_alignment="center"):
            st.sidebar.page_link(
                "pages/data-table.py",
                label="Data Table",
                icon=":material/table_chart:",
                disabled=not data_bundle,
            )
        st.sidebar.divider()
        st.sidebar.page_link(
            "pages/sparql-editor.py", label="SPARQL Editor", disabled=not endpoint
        )
        st.sidebar.page_link("pages/model.py", label="Model", disabled=not data_bundle)

        st.sidebar.divider()

        # SPARQL endpoint selection
        endpoints_names = [e.name for e in endpoints]
        endpoint_index = (
            endpoints_names.index(endpoint.name)
            if endpoint and endpoint.name in endpoints_names
            else None
        )
        endpoint_selected_name = st.sidebar.selectbox(
            label="SPARQL endpoint",
            options=endpoints_names,
            index=endpoint_index,
            placeholder="None selected",
            help=decorate_doc_links(
                "[What are SPARQL endpoints?](/documentation?section=what-is-a-sparql-endpoint)"
            ),
        )

        # Set the endpoint only if not yet the case
        if endpoint_selected_name and (
            (endpoint and endpoint_selected_name != endpoint.name) or not endpoint
        ):
            endpoint_selected_index = endpoints_names.index(endpoint_selected_name)
            endpoint_selected = endpoints[endpoint_selected_index]
            state.clear_endpoint_temporarily_unreachable(endpoint_selected)
            print(
                f"[menu] endpoint change: {endpoint.name if endpoint else None} -> {endpoint_selected.name}"
            )
            state.set_endpoint(endpoint_selected)

            # Keep endpoint and data bundle consistent to avoid URL/state loops.
            endpoint_id = state.get_endpoint_identifier(endpoint_selected)

            if (
                data_bundle
                and state.get_endpoint_identifier(data_bundle.endpoint) == endpoint_id
            ):
                target_bundle = data_bundle
            else:
                target_bundle = None

            if not _same_bundle(data_bundle, target_bundle):
                state.set_data_bundle(target_bundle)

            _clear_bundle_widget_state()

            state.set_query_params(["endpoint", "db", "uri"])
            st.rerun()

        # Data bundle selection
        if endpoint:
            endpoint_id = state.get_endpoint_key()
            endpoint_bundles = [
                db
                for db in data_bundles
                if state.get_endpoint_identifier(db.endpoint) == endpoint_id
            ]
            if endpoint_bundles:
                bundle_labels = [db.name for db in endpoint_bundles]
                bundle_index = (
                    bundle_labels.index(data_bundle.name)
                    if data_bundle and data_bundle.name in bundle_labels
                    else None
                )
                selected_label = st.sidebar.selectbox(
                    label="Data Bundle",
                    options=bundle_labels,
                    index=bundle_index,
                    key=f"sidebar-data-bundle-{endpoint_id}",
                    placeholder="None selected",
                    help=decorate_doc_links(
                        "[What are data bundles?](/documentation?section=what-are-data-bundles)"
                    ),
                )
                if selected_label:
                    selected_bundle = endpoint_bundles[
                        bundle_labels.index(selected_label)
                    ]
                    if not _same_bundle(data_bundle, selected_bundle):
                        state.set_data_bundle(selected_bundle)
                        state.set_query_params(["endpoint", "db", "uri"])
                        st.rerun()
            else:
                st.sidebar.warning(
                    "No Data Bundle configured for this endpoint.",
                    icon=":material/info:",
                )

        st.sidebar.page_link(
            "pages/import-export.py",
            label="Import, Export",
            disabled=not data_bundle,
        )

        st.sidebar.page_link("pages/configuration.py", label="Configuration")
        st.sidebar.page_link("pages/documentation.py", label="Documentation (FAQ)")

    except Exception as err:
        st.error(str(err))
        st.stop()
