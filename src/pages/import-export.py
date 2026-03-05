import streamlit as st
from graphly.tools import prepare
from components.init import init
from components.doc_links import decorate_doc_links
from components.menu import menu
from lib import state
from dialogs.confirmation import dialog_confirmation

# Initialize
init()
menu()

# From state
data_bundle = state.get_data_bundle()

if not data_bundle:
    st.switch_page("server.py")

##### IMPORT #####

with st.expander("Import"):
    # File format
    with st.container(horizontal=True, horizontal_alignment="center"):
        file_format_str = st.radio(
            "Format",
            options=["n-Quads (.nq)", "Turtle (.ttl)"],
            horizontal=True,
            label_visibility="collapsed",
            key="radio-import",
        )
        file_format = file_format_str[
            file_format_str.index("(.") + 2 : file_format_str.index(")")
        ]

    st.divider()

    # File upload
    file = st.file_uploader(
        f"Load your {file_format_str} file:",
        type=[file_format],
        disabled=(file_format_str is None),
        accept_multiple_files=False,
    )
    if file:
        file_content = file.read().decode("utf-8")

        st.write("")
        st.write("")

        # Message for the user
        with st.container(horizontal=True, horizontal_alignment="center"):
            st.markdown(
                f"File will be imported in *{data_bundle.name}*.", width="content"
            )

        st.divider()

        # Handle the n-Quad format
        if file_format == "nq":
            # Upload button: insert triples
            with st.container(horizontal=True, horizontal_alignment="center"):
                if st.button(
                    "Upload n-Quads", type="primary", icon=":material/upload:"
                ):

                    def upload_nquads(nquad_content) -> None:
                        data_bundle.endpoint.upload_nquads(nquad_content)
                        state.set_toast("n-Quad file uploaded", icon=":material/done:")
                        st.session_state.clear()
                        st.rerun()

                    dialog_confirmation(
                        f"You are about to upload the file {file.name}.",
                        callback=upload_nquads,
                        nquad_content=file_content,
                    )

        # Otherwise (i.e. Turtle), the destination should be decided (data, model, metadata)
        else:
            # Radio button for the user to choose
            with st.container(horizontal=True, horizontal_alignment="center"):
                data_type = st.radio(
                    "What is in the file?",
                    options=["Data", "Model", "Metadata"],
                    horizontal=True,
                )

            st.divider()

            # Upload button: insert triples
            with st.container(horizontal=True, horizontal_alignment="center"):
                if st.button(
                    f"Upload Turtle file into the {data_type.upper()} named graph",
                    type="primary",
                    icon=":material/upload:",
                ):

                    def upload_turtle(turtle_content: str) -> None:
                        if data_type == "Data":
                            graph = data_bundle.data
                        if data_type == "Model":
                            graph = data_bundle.model
                        if data_type == "Metadata":
                            graph = data_bundle.metadata
                        graph.upload_turtle(turtle_content)
                        state.set_toast("Turtle file uploaded", icon=":material/done:")
                        st.session_state.clear()
                        st.rerun()

                    confirmation_text = f"You are about to upload the file *{file.name}* into the {data_type} named graph."
                    dialog_confirmation(
                        confirmation_text,
                        callback=upload_turtle,
                        turtle_content=file_content,
                    )

        st.write("")

with st.container(horizontal=True, horizontal_alignment="right"):
    st.markdown(
        decorate_doc_links(
            "More on data import in the [Documentation FAQ](/documentation?section=how-to-import-data-into-the-sparql-endpoint)"
        ),
        width="content",
    )

st.write("")
st.write("")


##### EXPORT #####

with st.expander("Export"):
    # File format
    with st.container(horizontal=True, horizontal_alignment="center"):
        file_format_str = st.radio(
            "Format",
            options=["n-Quads (.nq)", "Turtle (.ttl)"],
            horizontal=True,
            label_visibility="collapsed",
            key="radio-export",
        )
        file_format = file_format_str[
            file_format_str.index("(.") + 2 : file_format_str.index(")")
        ]

    st.divider()

    # Export as n-quads: take full endpoint
    if file_format == "nq":
        with st.container(
            horizontal=True, horizontal_alignment="center", vertical_alignment="center"
        ):
            # Build the file (download triples on the python server)
            if st.button("Build the file (can be long)"):
                with st.spinner("Building the file"):
                    file_content = data_bundle.dump_nq()
                    file_name = f"logre_{data_bundle.key}_dump.nq"

                # Create a file, and download button
                if st.download_button(
                    label="Download file",
                    data=file_content,
                    file_name=file_name,
                    mime="application/n-quads",
                    type="primary",
                ):
                    state.set_toast("File downloaded")
                    st.rerun()

    # Export as turtle: need a choice of what to download: data, model or metadata
    else:
        with st.container(horizontal=True, horizontal_alignment="center"):
            data_type = st.radio(
                "What should be downloaded?",
                options=["Data", "Model", "Metadata"],
                horizontal=True,
            )
            if data_type == "Data":
                graph = data_bundle.data
            elif data_type == "Model":
                graph = data_bundle.model
            elif data_type == "Metadata":
                graph = data_bundle.metadata

        st.divider()

        with st.container(
            horizontal=True, horizontal_alignment="center", vertical_alignment="center"
        ):
            # Build the file (download triples on the python server)
            if st.button("Build the file (can be long)"):
                with st.spinner("Building the file"):
                    file_content = graph.dump_turtle()
                    file_name = f"logre_{data_bundle.key}_{data_type.lower()}_dump.ttl"

                # Create a file, and download button
                if st.download_button(
                    label="Download file",
                    data=file_content,
                    file_name=file_name,
                    mime="application/n-quads",
                    type="primary",
                ):
                    state.set_toast("File downloaded")
                    st.rerun()

with st.container(horizontal=True, horizontal_alignment="right"):
    st.markdown(
        decorate_doc_links(
            "More on data export in the [Documentation FAQ](/documentation?section=how-to-export-my-data)"
        ),
        width="content",
    )

st.write("")
st.write("")


##### MODEL #####

with st.expander("Update model"):
    files = st.file_uploader(
        f"Load your SHACL file(s):", type=["ttl"], accept_multiple_files=True
    )
    if len(files):
        files_content = ""
        for file in files:
            file_content = file.read().decode("utf-8")
            files_content += "\n" + file_content

        st.write("")
        st.write("")

        # Message for the user
        with st.container(horizontal=True, horizontal_alignment="center"):
            st.markdown(
                f"Your SHACL files will be imported into the model graph.",
                width="content",
            )
            st.warning(
                f"Warning! If you model is in the same Named Graph as your data and/or metadata, this will delete everything. Only go ahead if you are sure your model is in a dedicated graph (check on the databundle configuration)."
            )

        st.divider()

        # Upload button: cleanse model and insert new one
        with st.container(horizontal=True, horizontal_alignment="center"):
            if st.button(
                f"Replace current model", type="primary", icon=":material/upload:"
            ):

                def replace_model(turtle_content: str) -> None:
                    data_bundle.model.delete([("?s", "?p", "?o")])
                    data_bundle.model.upload_turtle(turtle_content)
                    state.set_toast("Model replaced", icon=":material/done:")

                confirmation_text = f"You are about to replace the existing model by what you specified."
                dialog_confirmation(
                    confirmation_text,
                    callback=replace_model,
                    turtle_content=files_content,
                )

with st.container(horizontal=True, horizontal_alignment="right"):
    st.markdown(
        decorate_doc_links(
            "More on models and SHACL files in the [Documentation FAQ](/documentation?section=what-is-shacl)"
        ),
        width="content",
    )
