import streamlit as st
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

        # If there is a data bundle set as default one
        # But if the default DB has a unexisting endpoint, do nothing
        if (
            data_bundle
            and not endpoint
            and data_bundle.endpoint.name in list(map(lambda e: e.name, endpoints))
        ):
            endpoint = data_bundle.endpoint

        # Sidebar title
        with st.sidebar.container(horizontal=True, vertical_alignment="bottom"):
            st.markdown(f"# Logre", width="content")
            st.markdown(
                f"<small>v{version}</small>", unsafe_allow_html=True, width="content"
            )

        # Page links
        st.sidebar.write("\n")
        st.sidebar.page_link(
            "pages/dashboard.py", label="Dashboard", disabled=not data_bundle
        )
        st.sidebar.write("\n")
        # Data bundle commands
        if data_bundle:
            model_ready = False
            try:
                data_bundle.load_model()
                model_ready = data_bundle.has_usable_model()
            except Exception:
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
        endpoint_index = endpoints_names.index(endpoint.name) if endpoint else None
        endpoint_selected_name = st.sidebar.selectbox(
            label="SPARQL endpoint",
            options=endpoints_names,
            index=endpoint_index,
            placeholder="None selected",
            help="[What are SPARQL endpoints?](/documentation?section=what-is-a-sparql-endpoint)",
        )

        # Set the endpoint only if not yet the case
        if endpoint_selected_name and (
            (endpoint and endpoint_selected_name != endpoint.name) or not endpoint
        ):
            endpoint_selected_index = endpoints_names.index(endpoint_selected_name)
            endpoint_selected = endpoints[endpoint_selected_index]
            print(
                f"[menu] endpoint change: {endpoint.name if endpoint else None} -> {endpoint_selected.name}"
            )
            state.set_endpoint(endpoint_selected)

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
                    else 0
                )
                selected_label = st.sidebar.selectbox(
                    label="Data Bundle",
                    options=bundle_labels,
                    index=bundle_index,
                    key="sidebar-data-bundle",
                    help="[What are data bundles?](/documentation?section=what-are-data-bundles)",
                )
                selected_bundle = endpoint_bundles[bundle_labels.index(selected_label)]
                if not data_bundle or data_bundle.key != selected_bundle.key:
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
