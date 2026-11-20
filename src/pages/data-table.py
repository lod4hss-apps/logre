import streamlit as st
from urllib.parse import quote_plus
from requests.exceptions import HTTPError, ConnectionError, Timeout
from components.init import init
from components.menu import menu
from lib import state
from lib.data_table import (
    EntityFilter,
    export_data_table_csv,
    find_relation_paths,
    hide_empty_model_columns,
)
from lib.errors import get_HTTP_ERROR_message
from lib.utils import get_widget_key

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

# Initialize
init(layout="wide", required_query_params=["endpoint", "db"])
menu()

try:
    # From state
    data_bundle = state.get_data_bundle()
    if not data_bundle:
        st.switch_page("server.py")
    assert data_bundle is not None

    # Title
    st.title("Data tables")
    st.text("")

    # The first filter row selects the class returned by the table.
    not_value_classes = [
        cls for cls in data_bundle.model.classes if cls.class_uri != "rdfs:Datatype"
    ]
    class_by_uri = {cls.uri: cls for cls in not_value_classes}
    class_uris = list(class_by_uri)
    class_names = {uri: cls.get_text() for uri, cls in class_by_uri.items()}
    limit = st.selectbox("Limit", [10, 20, 50, 100], index=0, width=100)

    filter_context = (state.get_endpoint_key(), data_bundle.key)
    if st.session_state.get("data_table_filter_context") != filter_context:
        st.session_state["data_table_filter_context"] = filter_context
        st.session_state["data_table_filter_ids"] = [0]
        st.session_state["data_table_filter_next_id"] = 1

    filter_ids = st.session_state["data_table_filter_ids"]
    first_filter_id = filter_ids[0] if filter_ids else None
    selected_class = None
    filters = []

    def reset_current_page() -> None:
        if selected_class:
            state.data_table_set_page(selected_class.uri, 1)

    def remove_filter(filter_id: int) -> None:
        st.session_state["data_table_filter_ids"] = [
            current_id for current_id in filter_ids if current_id != filter_id
        ]
        reset_current_page()

    def add_filter() -> None:
        next_id = st.session_state["data_table_filter_next_id"]
        st.session_state["data_table_filter_ids"] = [*filter_ids, next_id]
        st.session_state["data_table_filter_next_id"] = next_id + 1
        reset_current_page()

    for filter_id in filter_ids:
        with st.container(horizontal=True, vertical_alignment="bottom"):
            filter_class_uri = st.selectbox(
                "Entity class",
                class_uris,
                index=None,
                format_func=lambda uri: class_names[uri],
                key=get_widget_key("data-table-filter-class", *filter_context, filter_id),
                on_change=reset_current_page,
                width=200,
            )
            filter_class = class_by_uri.get(filter_class_uri)
            if filter_id == first_filter_id:
                selected_class = filter_class

            filter_columns = (
                data_bundle.get_data_table_columns_names(filter_class)
                if filter_class
                else []
            )
            filter_col = st.selectbox(
                "Filter on",
                filter_columns,
                index=None,
                key=get_widget_key(
                    "data-table-filter-column",
                    *filter_context,
                    filter_id,
                    filter_class_uri,
                ),
                on_change=reset_current_page,
                disabled=filter_class is None,
                width=200,
            )
            if filter_col and selected_class:
                paths = find_relation_paths(
                    data_bundle.model.properties,
                    selected_class.uri,
                    filter_class_uri,
                )
                if not paths:
                    st.warning(
                        "No relation of up to 3 steps in the model connects "
                        "this class to the table class."
                    )
                    selected_path = None
                elif len(paths) == 1:
                    selected_path = paths[0]
                else:
                    selected_path = st.selectbox(
                        "Relation path",
                        paths,
                        index=0 if filter_class_uri == selected_class.uri else None,
                        format_func=lambda path: (
                            "Same entity"
                            if not path
                            else " / ".join(
                                f"{step.label} [{step.property_uri}] "
                                f"{'←' if step.reverse else '→'} {class_names.get(step.to_class_uri, step.to_class_uri)}"
                                for step in path
                            )
                        ),
                        key=get_widget_key(
                            "data-table-filter-path",
                            *filter_context,
                            filter_id,
                            selected_class.uri,
                            filter_class_uri,
                        ),
                        on_change=reset_current_page,
                    )
                    if selected_path is None:
                        st.info("Choose a relation path to activate this filter.")
            else:
                selected_path = None

            filter_value = st.text_input(
                "Filter value",
                key=get_widget_key(
                    "data-table-filter-value",
                    *filter_context,
                    filter_id,
                    filter_class_uri,
                ),
                on_change=reset_current_page,
                disabled=filter_col is None or selected_path is None,
                width=200,
            )
            st.button(
                "Remove",
                key=get_widget_key("data-table-remove-filter", *filter_context, filter_id),
                icon=":material/delete:",
                type="tertiary",
                on_click=remove_filter,
                args=(filter_id,),
            )
            if filter_col and filter_value.strip() and selected_path is not None:
                filters.append(
                    EntityFilter(
                        filter_class_uri, filter_col, filter_value.strip(), selected_path
                    )
                )

    st.button("+ Add filter", on_click=add_filter)

    filter_operator = (
        st.radio(
            "Combine filters",
            ["AND", "OR"],
            horizontal=True,
            key=get_widget_key("data-table-filter-operator", *filter_context),
            on_change=reset_current_page,
            help="AND: match every filter. OR: match at least one filter.",
        )
        if len(filter_ids) > 1
        else "AND"
    )

    table_context = (*filter_context, selected_class.uri) if selected_class else None
    if st.session_state.get("data_table_table_context") != table_context:
        st.session_state["data_table_table_context"] = table_context
        reset_current_page()

    if selected_class is None:
        st.info("Choose an Entity class in the first filter to display a table.")
    else:
        columns = data_bundle.get_data_table_columns_names(selected_class)
        current_page = state.data_table_get_page(selected_class.uri)
        offset = (current_page - 1) * limit
        st.text("")

        # Fetch the data table
        df_instances = data_bundle.get_data_table(
            selected_class,
            limit=limit,
            offset=offset,
            filters=filters,
            filter_operator=filter_operator,
        )

        # Display information if there are some
        if len(df_instances) > 0:
            df_instances.columns = (
                ["URI"]
                + data_bundle.get_data_table_columns_names(selected_class)
                + ["Outgoing count", "Incoming count"]
            )
            df_instances.index += (
                1 * (limit * (current_page - 1)) + 1
            )  # So that indexes appears to start at 1
            if len(df_instances):
                endpoint_key = state.get_endpoint_key()
                endpoint_qs = (
                    f"&endpoint={quote_plus(endpoint_key)}" if endpoint_key else ""
                )
                df_instances["Open in Logre"] = [
                    f"/entity?db={quote_plus(data_bundle.key)}{endpoint_qs}&uri={quote_plus(uri)}"
                    for uri in df_instances["URI"]
                ]
                df_instances["Open external"] = [
                    data_bundle.prefixes.lengthen(uri) for uri in df_instances["URI"]
                ]

            st.caption("Click a column header to sort the displayed page.")
            st.dataframe(
                hide_empty_model_columns(df_instances, columns),
                width="stretch",
                column_config={
                    "URI": st.column_config.TextColumn(width="small"),
                    "Outgoing count": st.column_config.NumberColumn(width="small"),
                    "Incoming count": st.column_config.NumberColumn(width="small"),
                    "Open in Logre": st.column_config.LinkColumn(
                        display_text="Open", width="small"
                    ),
                    "Open external": st.column_config.LinkColumn(
                        display_text="External", width="small"
                    ),
                },
            )
        else:
            st.markdown("*No records found*")

        export_key = (
            state.get_endpoint_key(),
            data_bundle.key,
            selected_class.uri,
            tuple(filters),
            filter_operator,
        )
        if st.button("Prepare full CSV export"):
            st.session_state.pop("data_table_csv_export", None)
            with st.spinner("Exporting all matching results..."):
                csv_content = export_data_table_csv(
                    data_bundle,
                    selected_class,
                    filters,
                    filter_operator,
                )
            st.session_state["data_table_csv_export"] = (export_key, csv_content)

        saved_export = st.session_state.get("data_table_csv_export")
        if saved_export and saved_export[0] == export_key:
            st.download_button(
                "Download all results (CSV)",
                data=saved_export[1],
                file_name=f"logre_{data_bundle.key}_data-table.csv",
                mime="text/csv",
            )

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.toast("Unable to load this entity table", icon=":material/error:")
    print(message.replace("\n\n", "\n"))

except (ConnectionError, Timeout):
    state.deselect_bundle_after_endpoint_failure()
    st.rerun()

except Exception as err:
    st.toast("Unexpected error while loading table", icon=":material/error:")
    print(f"[DATA TABLE ERROR] {err}")
