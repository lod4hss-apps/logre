import streamlit as st
import pandas as pd
from requests.exceptions import HTTPError, ConnectionError, Timeout
from code_editor import code_editor
from components.init import init
from components.doc_links import decorate_doc_links
from components.menu import menu
from components.help import help_text
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.confirmation import dialog_confirmation
from dialogs.query_name import dialog_query_name


RESULT_KIND_KEY = "sparql-editor-result-kind"
RESULT_TABLE_KEY = "sparql-editor-result-table"
RESULT_TEXT_KEY = "sparql-editor-result-text"
EDITOR_SELECTED_BY_ENDPOINT_KEY = "sparql-editor-selected-query-by-endpoint"
EDITOR_DRAFTS_BY_ENDPOINT_KEY = "sparql-editor-drafts-by-endpoint"


def _normalize_binding_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        if "value" in value:
            return _normalize_binding_value(value["value"])
        return str(value)
    return str(value)


def _normalize_table_rows(result) -> list[dict]:
    rows = []
    for item in result:
        if isinstance(item, dict):
            rows.append(
                {
                    str(column): _normalize_binding_value(value)
                    for column, value in item.items()
                }
            )
        else:
            rows.append({"value": _normalize_binding_value(item)})
    return rows


# Initialize
init(layout="wide", required_query_params=["endpoint", "db"])
menu()

try:
    # From state
    sparql_queries = state.get_sparql_queries()
    sparql_query_name = state.get_sparql_query()
    endpoint = state.get_endpoint()
    data_bundle = state.get_data_bundle()

    if not endpoint:
        st.markdown("# SPARQL Editor")
        st.warning("Select an endpoint from the sidebar to run queries.")
    else:
        # Title
        st.markdown("# SPARQL Editor")
        st.markdown(
            decorate_doc_links(
                "[More about the edior in the Documentation FAQ](/documentation?section=what-type-of-queries-can-i-write-in-the-sparql-editor)"
            )
        )
        st.caption(
            "Results reflect exactly the graphs and filters used in your query. "
            "Counts can differ from Dashboard or Model views."
        )

        st.markdown("")

        endpoint_key = state.get_endpoint_key() or endpoint.name
        endpoint_widget_suffix = endpoint_key

        selected_by_endpoint = st.session_state.get(EDITOR_SELECTED_BY_ENDPOINT_KEY)
        if not isinstance(selected_by_endpoint, dict):
            selected_by_endpoint = {}
            st.session_state[EDITOR_SELECTED_BY_ENDPOINT_KEY] = selected_by_endpoint

        drafts_by_endpoint = st.session_state.get(EDITOR_DRAFTS_BY_ENDPOINT_KEY)
        if not isinstance(drafts_by_endpoint, dict):
            drafts_by_endpoint = {}
            st.session_state[EDITOR_DRAFTS_BY_ENDPOINT_KEY] = drafts_by_endpoint

        endpoint_drafts = drafts_by_endpoint.get(endpoint_key)
        if not isinstance(endpoint_drafts, dict):
            endpoint_drafts = {}
            drafts_by_endpoint[endpoint_key] = endpoint_drafts

        sparql_queries_names = [sq[0] for sq in sparql_queries]
        sparql_queries_by_name = {
            sq[0]: sq[1]
            for sq in sparql_queries
            if isinstance(sq, list) and len(sq) >= 2
        }

        if not sparql_queries_names:
            st.warning("No SPARQL query is available.")
            st.stop()

        selected_for_endpoint = selected_by_endpoint.get(endpoint_key)
        if selected_for_endpoint not in sparql_queries_names:
            if sparql_query_name in sparql_queries_names:
                selected_for_endpoint = sparql_query_name
            else:
                selected_for_endpoint = sparql_queries_names[0]
            selected_by_endpoint[endpoint_key] = selected_for_endpoint

        index = sparql_queries_names.index(selected_for_endpoint)
        selectbox_key = f"sparql-editor-query-select-{endpoint_widget_suffix}"
        if st.session_state.get(selectbox_key) not in sparql_queries_names:
            st.session_state.pop(selectbox_key, None)

        # Allow user to change the selected queries
        with st.container(horizontal=True, vertical_alignment="bottom"):
            sparql_query_name = st.selectbox(
                "SPARQL query",
                options=sparql_queries_names,
                index=index,
                key=selectbox_key,
                width=300,
                help=help_text("sparql_editor.saved_query"),
            )
            selected_by_endpoint[endpoint_key] = sparql_query_name
            state.set_sparql_query(sparql_query_name)

            # And have a delete button for this query
            if st.button("", icon=":material/delete:", type="tertiary"):

                def callback_delete_query(sq_name: str) -> None:
                    for ep_key, selected_name in list(selected_by_endpoint.items()):
                        if selected_name == sq_name:
                            del selected_by_endpoint[ep_key]

                    for drafts in drafts_by_endpoint.values():
                        if isinstance(drafts, dict) and sq_name in drafts:
                            del drafts[sq_name]

                    state.delete_sparql_query(sq_name)
                    state.set_toast("Query removed", icon=":material/delete:")

                dialog_confirmation(
                    f"You are about to delete the query *{sparql_query_name}*.",
                    callback=callback_delete_query,
                    sq_name=sparql_query_name,
                )

        sparql_query_content = sparql_queries_by_name.get(sparql_query_name, "")
        if sparql_query_name not in endpoint_drafts:
            endpoint_drafts[sparql_query_name] = sparql_query_content

        editor_content = endpoint_drafts.get(sparql_query_name, sparql_query_content)
        editor_widget_key = (
            f"sparql-editor-code-{endpoint_widget_suffix}-{sparql_query_name or 'none'}"
        )

        if not data_bundle:
            st.info(
                "No Data Bundle selected. You can still run any SPARQL query on this endpoint; Data Bundles are used for dashboard and model context.",
                icon=":material/info:",
            )

        if data_bundle:
            prefixes = data_bundle.prefixes
        else:
            # Some endpoint implementations do not expose per-endpoint prefixes.
            prefixes = getattr(endpoint, "prefixes", None) or state.get_prefixes()

        prefixes_list = [p.short for p in prefixes] if prefixes else []
        if prefixes_list:
            prefixes_str = "`, `".join(prefixes_list)
            st.markdown("Available prefixes are: `" + prefixes_str + "`")
        else:
            st.caption("No prefixes configured.")

        # Code editor
        editor = code_editor(
            lang="sparql",
            code=editor_content,
            height="400px",
            buttons=[
                {
                    "name": "Run",
                    "hasText": True,
                    "alwaysOn": True,
                    "style": {"top": "350px", "right": "0.4rem"},
                    "commands": ["submit"],
                }
            ],
            key=editor_widget_key,
        )

        if editor and isinstance(editor, dict) and "text" in editor:
            endpoint_drafts[sparql_query_name] = editor["text"]

        st.write("")

        # When submit button is clicked
        if (
            isinstance(editor, dict)
            and editor.get("type") == "submit"
            and editor.get("id")
            and f"{endpoint_key}:{editor.get('id')}"
            != state.get_last_executed_sparql_id()
        ):
            # Run the query
            result = endpoint.run(endpoint_drafts.get(sparql_query_name, ""), prefixes)
            state.set_last_executed_sparql_id(f"{endpoint_key}:{editor['id']}")

            # If there is a result
            if result is not None:
                if isinstance(result, list):
                    st.session_state[RESULT_KIND_KEY] = "table"
                    st.session_state[RESULT_TABLE_KEY] = _normalize_table_rows(result)
                    st.session_state[RESULT_TEXT_KEY] = None
                else:
                    st.session_state[RESULT_KIND_KEY] = "code"
                    st.session_state[RESULT_TEXT_KEY] = str(result)
                    st.session_state[RESULT_TABLE_KEY] = []

            # When there is no result: a insert/delete query
            else:
                st.session_state.pop(RESULT_KIND_KEY, None)
                st.session_state.pop(RESULT_TABLE_KEY, None)
                st.session_state.pop(RESULT_TEXT_KEY, None)
                # Inform user that the request went through
                state.set_toast("Query executed", icon=":material/done:")
                st.rerun()

        result_kind = st.session_state.get(RESULT_KIND_KEY)
        if result_kind:
            option_line = st.container(
                horizontal=True,
                horizontal_alignment="distribute",
                vertical_alignment="bottom",
            )

            # Option line: title, shape, and buttons
            with option_line.container(
                horizontal=True,
                horizontal_alignment="left",
                vertical_alignment="bottom",
            ):
                st.markdown("### Response", width="content")
                comment_place = st.empty()

            # Options buttons: download and save query
            with option_line.container(
                horizontal=True,
                horizontal_alignment="right",
                vertical_alignment="bottom",
            ):
                download_btn_place = st.empty()
                st.button(
                    "Save query",
                    icon=":material/reorder:",
                    on_click=dialog_query_name,
                    kwargs={"query_text": endpoint_drafts.get(sparql_query_name, "")},
                )

            if result_kind == "table":
                rows = st.session_state.get(RESULT_TABLE_KEY, [])
                df = pd.DataFrame(rows)
                if not df.empty:
                    df = df.where(pd.notna(df), "")

                comment_place.markdown(
                    f"Shape: {df.shape[0]}x{df.shape[1]}", width="content"
                )
                download_btn_place.download_button(
                    "Download CSV",
                    data=df.to_csv(index=False),
                    file_name="logre-download.csv",
                    mime="text/csv",
                    icon=":material/download:",
                )

                table_place = st.empty()
                table_place.dataframe(df, hide_index=True, width="stretch")

            elif result_kind == "code":
                st.code(st.session_state.get(RESULT_TEXT_KEY, ""), "turtle")

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace("\n\n", "\n"))

except (ConnectionError, Timeout):
    state.deselect_bundle_after_endpoint_failure()
    st.rerun()
