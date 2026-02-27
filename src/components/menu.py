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
                st.sidebar.warning(
                    "Model not available yet. Import SHACL or verify endpoint and graph settings.",
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
            help="[What are SPARQL endpoints?](/documentation#what-is-a-sparql-endpoint)",
        )

        # Set the endpoint only if not yet the case
        if endpoint_selected_name and (
            (endpoint and endpoint_selected_name != endpoint.name) or not endpoint
        ):
            endpoint_selected_index = endpoints_names.index(endpoint_selected_name)
            endpoint_selected = endpoints[endpoint_selected_index]
            state.set_endpoint(endpoint_selected)
            st.rerun()

        # When an endpoint is selected, allow to select all related data bundles
        if endpoint:
            # Filter data bundles only on those with the current endpoint
            data_bundles = list(
                filter(lambda db: db.endpoint.name == endpoint.name, data_bundles)
            )

            # Data bundle selection
            db_names = [db.name for db in data_bundles]
            db_index = (
                db_names.index(data_bundle.name)
                if data_bundle and data_bundle.name in db_names
                else None
            )
            db_selected_name = st.sidebar.selectbox(
                label="Data Bundle",
                options=db_names,
                index=db_index,
                placeholder="None selected",
                help="[What are data bundles?](/documentation#what-are-data-bundles)",
            )

            # Put Data Bundle in state only if not yet the case
            if db_selected_name and (
                (data_bundle and db_selected_name != data_bundle.name)
                or not data_bundle
            ):
                db_selected_index = db_names.index(db_selected_name)
                db_selected = data_bundles[db_selected_index]
                state.set_data_bundle(db_selected)
                st.rerun()
                data_bundle = db_selected

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
