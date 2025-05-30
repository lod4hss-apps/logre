import streamlit as st, pandas as pd, io
from components.init import init
from components.menu import menu
from dialogs import dialog_confirmation
from lib import state
from lib import to_snake_case, build_zip_file


def __upload_turtle(turtle_content: str, named_graph_uri: str) -> None:
    endpoint.sparql.upload_turtle(turtle_content, named_graph_uri)
    state.set_toast('Turtle file uploaded', icon=':material/done:')


init()
menu()


# From state
endpoint = state.get_endpoint()


# Can't import if there is no endpoint
if not endpoint:

    st.title("Import and Export")
    st.text('')
    st.warning('You need to select an endpoint first (menu on the left).')

else:

    #### IMPORT ####

    with st.expander('Import'):

        st.text('')
        file_format_str = st.radio("Format", options=['n-Quads (.nq)', 'Turtle (.ttl)'], horizontal=True, label_visibility='collapsed')
        st.text('')
        file_format = file_format_str[file_format_str.index('(.') + 2:file_format_str.index(')')]
        file = st.file_uploader(f"Load your {file_format_str} file:", type=[file_format], disabled=(file_format_str is None), accept_multiple_files=False)
        st.text('')

        if file:
            file_content = file.read().decode("utf-8")

            if file_format == 'nq':
                if st.button('Upload n-Quads', icon=':material/upload:'):
                    dialog_confirmation(
                        f'You are about to upload the file {file.name}.', 
                        callback=endpoint.sparql.upload_nquads, 
                        nquad_content=file_content
                    )

            else:
                data_bundle_labels = [data_bundle.name for data_bundle in endpoint.data_bundles]
                selected_data_bundle_label = st.selectbox('Data Bundle to import to:', options=data_bundle_labels, index=None)
                st.text('')

                if selected_data_bundle_label:
                    selected_data_bundle = endpoint.data_bundles[data_bundle_labels.index(selected_data_bundle_label)]
                    graph = st.radio('Select the named graph:', options=[f'Data ({selected_data_bundle.graph_data.uri})', f'Ontology ({selected_data_bundle.graph_ontology.uri})', f'Metadata ({selected_data_bundle.graph_metadata.uri})'])
                    st.text('')

                    if graph:
                        if graph.startswith('Data'): graph_uri = selected_data_bundle.graph_data.uri
                        if graph.startswith('Ontology'): graph_uri = selected_data_bundle.graph_ontology.uri
                        if graph.startswith('Metadata'): graph_uri = selected_data_bundle.graph_metadata.uri

                        if file_format == 'ttl':
                            if st.button('Upload Turtle', icon=':material/upload:'):
                                dialog_confirmation(
                                    f'You are about to upload the file {file.name}.', 
                                    callback=__upload_turtle, 
                                    turtle_content=file_content,
                                    named_graph_uri=graph_uri
                                )


    #### EXPORT ####

    with st.expander('Export'):

        export_type_options = ['Export the Endpoint', 'Export a Data Bundle']
        export_type = st.radio('Export target', options=export_type_options, label_visibility='collapsed', horizontal=True)

        # Export the full endpoint
        col1, col2 = st.columns([1, 1])
        if export_type == export_type_options[0] and col1.button('Build the file (can be long)'):

            with st.spinner("Building the file"):
                file_content = endpoint.sparql.dump()
                file_name =f"logre_{to_snake_case(endpoint.name)}_dump.nq".lower()

            if col2.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads"):
                # Validation and rerun
                state.set_toast('File downloaded')
                st.rerun()

        # Export a Data Bundle
        if export_type == export_type_options[1]:

            data_bundle_labels = [data_bundle.name for data_bundle in endpoint.data_bundles]
            selected_data_bundle_label = st.selectbox('Data Bundle to export:', options=data_bundle_labels, index=None)
            st.text('')

            if selected_data_bundle_label:
                selected_data_bundle = endpoint.data_bundles[data_bundle_labels.index(selected_data_bundle_label)]
                format = st.radio("Export format", ['n-Quads (.nq)', 'Turtle (.ttl)', 'Tables (.csv)'], horizontal=True)
                file_format = format[format.index('(.') + 2:format.index(')')]
                st.text('')

                col1, col2 = st.columns([1, 1])
                if col1.button('Build file (can be long)'):

                    with st.spinner("Building the file"):
                        dump = selected_data_bundle.dump(file_format)

                        if file_format == 'nq':
                            file_content = dump
                            file_name = f"logre_{to_snake_case(endpoint.name)}_{to_snake_case(selected_data_bundle.name)}_dump.nq".lower()
                        
                        if file_format == 'ttl':
                            file_names = [key + '.ttl' for key in dump.keys()]
                            file_contents = [value for value in dump.values()]
                            file_content = build_zip_file(file_names, file_contents)
                            file_name = f"logre_{to_snake_case(endpoint.name)}_{to_snake_case(selected_data_bundle.name)}_ttl-dump.zip".lower()

                        if file_format == 'csv':
                            file_names = [key + '.csv' for key in dump.keys()]
                            file_contents = []
                            for df in dump.values():
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                file_contents.append(csv_buffer.getvalue())
                            file_content = build_zip_file(file_names, file_contents)
                            file_name = f"logre_{to_snake_case(endpoint.name)}-{to_snake_case(selected_data_bundle.name)}_csv-dump.zip".lower()

                    
                    if col2.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads"):
                        # Validation and rerun
                        state.set_toast('File downloaded')
                        st.rerun()