import streamlit as st
from requests.exceptions import HTTPError
from components.init import init
from components.menu import menu
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.confirmation import dialog_confirmation

try:

    # Initialize    
    init()
    menu()

    # From state
    data_bundle = state.get_data_bundle()

    # Make verifications
    if not data_bundle:
        st.warning('No Data Bundle selected')
    else:

        ##### IMPORT #####

        with st.expander('Import'):
            
            # File format
            with st.container(horizontal=True, horizontal_alignment='center'):
                file_format_str = st.radio('Format', options=['n-Quads (.nq)', 'Turtle (.ttl)'], horizontal=True, label_visibility='collapsed', key='radio-import')
                file_format = file_format_str[file_format_str.index('(.') + 2:file_format_str.index(')')]

            st.divider()

            # File upload
            file = st.file_uploader(f"Load your {file_format_str} file:", type=[file_format], disabled=(file_format_str is None), accept_multiple_files=False)
            if file:
                file_content = file.read().decode("utf-8")
                
                st.write('')
                st.write('')

                # Message for the user
                with st.container(horizontal=True, horizontal_alignment='center'):
                    st.markdown(f'File will be imported in *{data_bundle.name}*.', width='content')

                st.divider()

                # Handle the n-Quad format
                if file_format == 'nq':

                    # Upload button: insert triples
                    with st.container(horizontal=True, horizontal_alignment='center'):
                        if st.button('Upload n-Quads', type='primary', icon=':material/upload:'):
                            def upload_nquads(nquad_content) -> None:
                                data_bundle.endpoint.upload_nquads(nquad_content)
                                state.set_toast('n-Quad file uploaded', icon=':material/done:')
                            dialog_confirmation(f'You are about to upload the file {file.name}.', callback=upload_nquads, nquad_content=file_content)

                # Otherwise (i.e. Turtle), the destination should be decided (data, model, metadata)
                else:  
                    # Radio button for the user to choose
                    with st.container(horizontal=True, horizontal_alignment='center'):
                        data_type = st.radio('What is in the file?', options=['Data', 'Model', 'Metadata'], horizontal=True)
                    
                    st.divider()

                    # Upload button: insert triples
                    with st.container(horizontal=True, horizontal_alignment='center'):
                        if st.button(f'Upload Turtle file into the {data_type.upper()} named graph', type='primary', icon=':material/upload:'):
                            def upload_turtle(turtle_content: str) -> None:
                                if data_type == "Data": graph = data_bundle.graph_data
                                if data_type == "Model": graph = data_bundle.graph_model
                                if data_type == "Metadata": graph = data_bundle.graph_metadata
                                graph.upload_turtle(turtle_content)
                                state.set_toast('Turtle file uploaded', icon=':material/done:')
                            confirmation_text = f'You are about to upload the file *{file.name}* into the {data_type} named graph.'
                            dialog_confirmation(confirmation_text, callback=upload_turtle, turtle_content=file_content)

                st.write('')

        with st.container(horizontal=True, horizontal_alignment='right'):
            st.markdown("More on data import in the [Documentation FAQ](/documentation#how-to-import-data-into-the-sparql-endpoint)", width='content')


        ##### EXPORT #####

        with st.expander('Export'):

            # File format
            with st.container(horizontal=True, horizontal_alignment='center'):
                file_format_str = st.radio('Format', options=['n-Quads (.nq)', 'Turtle (.ttl)'], horizontal=True, label_visibility='collapsed', key='radio-export')
                file_format = file_format_str[file_format_str.index('(.') + 2:file_format_str.index(')')]

            st.divider()

            # Export as n-quads: take full endpoint
            if file_format == 'nq':
                with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment='center'):

                    # Build the file (download triples on the python server)
                    if st.button('Build the file (can be long)'):
                        with st.spinner("Building the file"):
                            file_content = data_bundle.dump_nq()
                            file_name =f"logre_{data_bundle.key}_dump.nq"

                        # Create a file, and download button
                        if st.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads", type='primary'):
                            state.set_toast('File downloaded')
                            st.rerun()
            
            # Export as turtle: need a choice of what to download: data, model or metadata
            else:
                with st.container(horizontal=True, horizontal_alignment='center'):
                    data_type = st.radio('What should be downloaded?', options=['Data', 'Model', 'Metadata'], horizontal=True)
                    if data_type == 'Data': graph = data_bundle.graph_data
                    elif data_type == 'Model': graph = data_bundle.graph_model
                    elif data_type == 'Metadata': graph = data_bundle.graph_metadata
                    
                st.divider()

                with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment='center'):

                    # Build the file (download triples on the python server)
                    if st.button('Build the file (can be long)'):
                        with st.spinner("Building the file"):
                            file_content = graph.dump_turtle(data_bundle.prefixes)
                            file_name =f"logre_{data_bundle.key}_{data_type}_dump.ttl"

                        # Create a file, and download button
                        if st.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads", type='primary'):
                            state.set_toast('File downloaded')
                            st.rerun()

        with st.container(horizontal=True, horizontal_alignment='right'):
            st.markdown("More on data export in the [Documentation FAQ](/documentation#how-to-export-my-data)", width='content')

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))