import streamlit as st
from requests.exceptions import HTTPError
from graphly.schema import Prefixes, Prefix
from lib import state
from lib.errors import get_HTTP_ERROR_message
from schema.data_bundle import DataBundle
from schema.model_framework import ModelFramework
from schema.endpoint import Endpoint
from components.help import help_text
from dialogs.confirmation import dialog_confirmation


MODEL_FRAMEWORKS_STR = [e.value for e in list(ModelFramework)]

@st.dialog("Data Bundle", width='medium')
def dialog_data_bundle_form(endpoint: Endpoint, db: DataBundle = None) -> None:
    """
    Displays a dialog form for creating or editing a Data Bundle.

    Args:
        endpoint (Endpoint): Parent endpoint to attach the bundle to.
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
    new_name = col_name.text_input('Name ❗️', value=db.name if db else '')

    st.write('')
    st.write('')

    # Data Bundle base URI
    new_base_uri = st.text_input(
        'Base URI ❗️',
        value=db.base_uri if db else 'http://www.example.org/resource/',
        help=help_text("data_bundle_form.base_uri") or "[what does 'Base URI' refers to?](/documentation#in-the-data-bundle-creation-what-does-base-uri-refers-to)"
    )

    st.write('')
    st.write('')

    # List current named graph
    popover = st.popover(
        'List of existing named graph',
        help=help_text("data_bundle_form.named_graphs") or "[Why am I given the list of existing graphs?](/documentation#in-the-data-bundle-creation-why-am-i-given-the-list-of-existing-graphs)"
    )
    try: 
        graphs = __get_graph_list(endpoint, new_base_uri) or []
        popover.markdown('*(Default graph)*')
        for graph in graphs:
            popover.markdown(f"{graph}")
    except HTTPError as err:
        message = get_HTTP_ERROR_message(err)
        popover.error(message)
        print(message.replace('\n\n', '\n'))

    # Data Bundle graphs
    col_data, col_model, col_metadata = st.columns([1, 1, 1])
    new_graph_data_uri = col_data.text_input(
        'Data graph URI',
        value=db.graph_data.uri if db else 'base:data',
        help=help_text("data_bundle_form.graph_data") or "[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)"
    )
    new_graph_model_uri = col_model.text_input(
        'Model graph URI',
        value=db.graph_model.uri if db else 'base:model',
        help=help_text("data_bundle_form.graph_model") or "[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)"
    )
    new_graph_metadata_uri = col_metadata.text_input(
        'Metadata graph URI',
        value=db.graph_metadata.uri if db else 'base:metadata',
        help=help_text("data_bundle_form.graph_metadata") or "[Why should I provide 3 graphs URIs (data, model, metadata)?](/documentation#in-the-data-bundle-creation-why-should-i-provide-3-graphs-uris-data-model-metadata)"
    )

    st.write('')
    st.write('')

    # Data Bundle framework used for model
    col_framework, _ = st.columns([1, 2])
    new_framework = col_framework.selectbox(
        'Model framework ❗️',
        options=MODEL_FRAMEWORKS_STR,
        index=MODEL_FRAMEWORKS_STR.index(db.model.framework_name) if db else None,
        help=help_text("data_bundle_form.model_framework") or "[What are the supported model framework supported?](/documentation#what-are-the-supported-model-framework-supported)"
    )

    # Data Bundle basic properties (type, label, comment)
    col_type, col_label, col_comment = st.columns([1, 1, 1])
    new_type_prop_uri = col_type.text_input(
        'Type property ❗️',
        value=db.model.type_property if db else 'rdf:type',
        help=help_text("data_bundle_form.type_property") or "[Why should I provide type, label and comment properties URIs?](documentation#in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)"
    )
    new_label_prop_uri = col_label.text_input(
        'Label property ❗️',
        value=db.model.label_property if db else 'rdfs:label',
        help=help_text("data_bundle_form.label_property") or "[Why should I provide type, label and comment properties URIs?](documentation#in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)"
    )
    new_comment_prop_uri = col_comment.text_input(
        'Comment property ❗️',
        value=db.model.comment_property if db else 'rdfs:comment',
        help=help_text("data_bundle_form.comment_property") or "[Why should I provide type, label and comment properties URIs?](documentation#in-the-data-bundle-creation-why-should-i-provide-type-label-and-comment-properties-uris)"
    )

    st.write('')
    st.write('')

    with st.container(horizontal=True, horizontal_alignment='center'):
        # Disabled if some required fields are missing
        disabled = not(new_name and new_base_uri and new_framework and new_type_prop_uri and new_label_prop_uri and new_comment_prop_uri)
        if st.button('Save' if db else 'Create', type='primary', width=200, disabled=disabled):

            # Create the Data Bundle
            new_db = DataBundle.from_dict({
                'name': new_name,
                'base_uri': new_base_uri,
                'model_framework': new_framework,
                'prop_type_uri': new_type_prop_uri,
                'prop_label_uri': new_label_prop_uri,
                'prop_comment_uri': new_comment_prop_uri,
                'graph_data_uri': new_graph_data_uri,
                'graph_model_uri': new_graph_model_uri,
                'graph_metadata_uri': new_graph_metadata_uri,
                'endpoint_key': endpoint.key,
            }, endpoint=endpoint, prefixes=endpoint.prefixes)

            # And add it to state
            state.update_data_bundle(db, new_db)

            st.rerun()

    if not db:
        return

    st.divider()
    st.markdown("### Import data")

    file_format_str = st.radio(
        'Format',
        options=['n-Quads (.nq)', 'Turtle (.ttl)'],
        horizontal=True,
        label_visibility='collapsed',
        key=f'data-bundle-import-format-{db.key}'
    )
    file_format = file_format_str[file_format_str.index('(.') + 2:file_format_str.index(')')]

    import_file = st.file_uploader(
        f"Load your {file_format_str} file:",
        type=[file_format],
        accept_multiple_files=False,
        key=f'data-bundle-import-file-{db.key}'
    )

    if import_file:
        file_content = import_file.read().decode("utf-8")

        st.write('')
        st.markdown(f'The file will be imported into *{db.name}*.', width='content')
        st.write('')

        if file_format == 'nq':
            if st.button('Upload n-Quads', type='primary', icon=':material/upload:', key=f'import-nq-btn-{db.key}'):
                def upload_nquads(nquad_content: str) -> None:
                    db.endpoint.upload_nquads(nquad_content)
                    state.set_toast('n-Quad file uploaded', icon=':material/done:')
                dialog_confirmation(
                    f'You are about to upload the file *{import_file.name}* into *{db.name}*.',
                    callback=upload_nquads,
                    nquad_content=file_content
                )
        else:
            data_type = st.radio(
                'What is in the file?',
                options=['Data', 'Model', 'Metadata'],
                horizontal=True,
                key=f'data-bundle-import-type-{db.key}'
            )

            graph = db.graph_data if data_type == "Data" else db.graph_model if data_type == "Model" else db.graph_metadata

            if st.button(
                f'Upload Turtle into the {data_type.upper()} graph',
                type='primary',
                icon=':material/upload:',
                key=f'import-ttl-btn-{db.key}'
            ):
                def upload_turtle(turtle_content: str) -> None:
                    graph.upload_turtle(turtle_content)
                    state.set_toast('Turtle file uploaded', icon=':material/done:')
                dialog_confirmation(
                    f'You are about to upload the file *{import_file.name}* into the {data_type} graph.',
                    callback=upload_turtle,
                    turtle_content=file_content
                )

    st.divider()
    st.markdown("### Update the model (SHACL)")

    try:
        with st.spinner("Extracting the current model..."):
            current_model = db.graph_model.dump_turtle(db.prefixes)
        st.download_button(
            "Download current model (.ttl)",
            data=current_model,
            file_name=f"logre_{db.key}_model.ttl",
            mime="text/turtle",
            icon=":material/download:",
            key=f'download-model-btn-{db.key}'
        )
    except Exception:
        st.warning("Unable to download the current model.")

    if st.button("Delete current model", type="secondary", icon=":material/delete:", key=f'delete-model-btn-{db.key}'):
        def clear_model() -> None:
            db.delete('model', [('?s', '?p', '?o')])
            state.set_toast('Model cleared', icon=':material/delete:')
            db.load_model()
        dialog_confirmation(
            "You are about to delete every triple from the model graph.",
            callback=clear_model
        )

    files = st.file_uploader(
        "Upload your SHACL files (.ttl)",
        type=['ttl'],
        accept_multiple_files=True,
        key=f'shacl-upload-{db.key}'
    )
    if files:
        files_content = ''
        for file in files:
            files_content += '\n' + file.read().decode("utf-8")

        st.write('')
        st.markdown("Files will be imported into the configured **model graph**.")
        st.warning("If your model shares the same named graph as your data, this operation will delete everything in that graph.", icon=":material/warning:")

        if st.button('Replace current model', type='primary', icon=':material/upload:', key=f'replace-model-btn-{db.key}'):
            def replace_model(turtle_content: str) -> None:
                db.delete('model', [('?s', '?p', '?o')])
                db.graph_model.upload_turtle(turtle_content)
                state.set_toast('Model replaced', icon=':material/done:')
                db.load_model()
            dialog_confirmation(
                'You are about to replace the existing model with the provided files.',
                callback=replace_model,
                turtle_content=files_content
            )

def __get_graph_list(endpoint: Endpoint, base_uri: str | None) -> list[str]:

    if not base_uri:
        return []

    try:
        prefixes = Prefixes([prefix for prefix in endpoint.prefixes.prefix_list if prefix.short != 'base'])
        prefixes.add(Prefix('base', base_uri))

        with st.spinner('Fetching existing named graph'):
            graphs = endpoint.sparql.run("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o . } }", prefixes=prefixes) or []

        return [g['g'] for g in graphs]

    except HTTPError as err:
        raise err
    except Exception:
        return []
