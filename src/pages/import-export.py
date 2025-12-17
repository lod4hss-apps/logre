import streamlit as st
from requests.exceptions import HTTPError
from graphly.tools import prepare
from components.init import init
from components.menu import menu
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.confirmation import dialog_confirmation

# Initialize    
init(query_param_keys=['endpoint', 'db'])
menu()

try:

    # From state
    endpoint = state.get_endpoint()
    data_bundle = state.get_data_bundle()

    if not endpoint:
        st.warning('Select an endpoint from the sidebar to use this page.')
    else:

        st.info("L’import des données se fait désormais dans la page Configuration (section “Importer des données”).")
        st.write('')

        if not data_bundle:
            st.warning('Select a Data Bundle to export its graphs. Only endpoint-wide features remain available.', icon=":material/info:")
            st.stop()

        ##### EXPORT #####

        with st.expander('Export'):

            if not data_bundle:
                st.info('No Data Bundle selected. Exporting the entire endpoint as N-Quads.', icon=":material/info:")
                with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment='center'):
                    if st.button('Build the file (can be long)', key='export-endpoint'):
                        with st.spinner("Building the file"):
                            file_content = endpoint.sparql.dump()
                            file_name = f"logre_{endpoint.key}_endpoint_dump.nq"
                        if st.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads", type='primary', key='endpoint-download'):
                            state.set_toast('File downloaded')
                            st.rerun()
            else:
                with st.container(horizontal=True, horizontal_alignment='center'):
                    file_format_str = st.radio('Format', options=['n-Quads (.nq)', 'Turtle (.ttl)'], horizontal=True, label_visibility='collapsed', key='radio-export')
                    file_format = file_format_str[file_format_str.index('(.') + 2:file_format_str.index(')')]

                st.divider()

                if file_format == 'nq':
                    with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment='center'):
                        if st.button('Build the file (can be long)', key='bundle-export-nq'):
                            with st.spinner("Building the file"):
                                file_content = data_bundle.dump_nq()
                                file_name =f"logre_{data_bundle.key}_dump.nq"

                            if st.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads", type='primary', key='bundle-download-nq'):
                                state.set_toast('File downloaded')
                                st.rerun()
                else:
                    with st.container(horizontal=True, horizontal_alignment='center'):
                        data_type = st.radio('What should be downloaded?', options=['Data', 'Model', 'Metadata'], horizontal=True)
                        if data_type == 'Data': graph = data_bundle.graph_data
                        elif data_type == 'Model': graph = data_bundle.graph_model
                        else: graph = data_bundle.graph_metadata
                        
                    st.divider()

                    with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment='center'):
                        if st.button('Build the file (can be long)', key='bundle-export-ttl'):
                            with st.spinner("Building the file"):
                                file_content = graph.dump_turtle(data_bundle.prefixes)
                                file_name =f"logre_{data_bundle.key}_{data_type}_dump.ttl"

                            if st.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads", type='primary', key='bundle-download-ttl'):
                                state.set_toast('File downloaded')
                                st.rerun()

        with st.container(horizontal=True, horizontal_alignment='right'):
            st.markdown("More on data export in the [Documentation FAQ](/documentation#how-to-export-my-data)", width='content')

        st.divider()


        ##### ONTOLOGY #####
        if data_bundle:
            with st.expander('Update model'):
                files = st.file_uploader(f"Load your SHACL file(s):", type=['ttl'], accept_multiple_files=True)
                if len(files):
                    files_content = ''
                    for file in files:
                        file_content = file.read().decode("utf-8")
                        files_content += '\n' + file_content
                    
                    st.write('')
                    st.write('')

                    with st.container(horizontal=True, horizontal_alignment='center'):
                        st.markdown(f'Your SHACL files will be imported into the model graph.', width='content')
                        st.warning(f'Warning! If your model is in the same Named Graph as your data and/or metadata, this will delete everything.')

                    st.divider()

                    with st.container(horizontal=True, horizontal_alignment='center'):
                        if st.button(f'Replace current model', type='primary', icon=':material/upload:'):
                            def replace_model(turtle_content: str) -> None:
                                data_bundle.delete('model', [('?s', '?p', '?o')] )
                                data_bundle.graph_model.upload_turtle(turtle_content)
                                state.set_toast('Model replaced', icon=':material/done:')
                            confirmation_text = f'You are about to replace the existing model by what you specified.'
                            dialog_confirmation(confirmation_text, callback=replace_model, turtle_content=files_content)

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))
