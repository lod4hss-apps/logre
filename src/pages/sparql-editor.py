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

    if not data_bundle:
        st.switch_page("server.py")

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

        # Find the selected one
        sparql_queries_names = [sq[0] for sq in sparql_queries]
        index = (
            sparql_queries_names.index(sparql_query_name) if sparql_query_name else 0
        )

        # Allow user to change the selected queries
        with st.container(horizontal=True, vertical_alignment="bottom"):
            sparql_query_name = st.selectbox(
                "SPARQL query",
                options=sparql_queries_names,
                index=index,
                width=300,
                help=help_text("sparql_editor.saved_query"),
            )
            state.set_sparql_query(sparql_query_name)

            # And have a delete button for this query
            if st.button("", icon=":material/delete:", type="tertiary"):

                def callback_delete_query(sq_name: str) -> None:
                    state.delete_sparql_query(sq_name)
                    state.set_toast("Query removed", icon=":material/delete:")

                dialog_confirmation(
                    f"You are about to delete the query *{sparql_query_name}*.",
                    callback=callback_delete_query,
                    sq_name=sparql_query_name,
                )

        # Get the query content
        sparql_query_content = (
            sparql_queries[sparql_queries_names.index(sparql_query_name)][1]
            if sparql_query_name
            else ""
        )

        editor_content_key = "sparql-editor-content"
        editor_query_key = "sparql-editor-selected-query"
        if st.session_state.get(editor_query_key) != sparql_query_name:
            st.session_state[editor_content_key] = sparql_query_content
            st.session_state[editor_query_key] = sparql_query_name

        if not data_bundle:
            st.info(
                "No Data Bundle selected. Queries will run against the entire endpoint.",
                icon=":material/info:",
            )

        prefixes = data_bundle.prefixes if data_bundle else endpoint.prefixes
        prefixes_str = "`, `".join([p.short for p in prefixes])
        st.markdown("Available prefixes are: `" + prefixes_str + "`")

        # Code editor
        editor = code_editor(
            lang="sparql",
            code=st.session_state.get(editor_content_key, sparql_query_content),
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
            key="sparql-editor-code",
        )

        if editor and isinstance(editor, dict) and "text" in editor:
            st.session_state[editor_content_key] = editor["text"]

        st.write("")

        # When submit button is clicked
        if (
            isinstance(editor, dict)
            and editor.get("type") == "submit"
            and editor.get("id")
            and editor.get("id") != state.get_last_executed_sparql_id()
        ):
            # Run the query
            result = endpoint.run(
                st.session_state.get(editor_content_key, ""), prefixes
            )
            state.set_last_executed_sparql_id(editor["id"])

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
                    kwargs={"query_text": st.session_state.get(editor_content_key, "")},
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
