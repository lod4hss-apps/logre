import streamlit as st, pandas as pd, io
from components.init import init
from components.menu import menu
from dialogs import dialog_confirmation
from lib import state
from lib import to_snake_case, build_zip_file


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

    with st.expander('Import'):

        st.text('')
        file_format_str = st.radio("Format", options=['n-Quads (.nq)', 'Turtle (.ttl)', 'Tables (.csv)'], horizontal=True, label_visibility='collapsed')
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
                data_set_labels = [data_set.name for data_set in endpoint.data_sets]
                selected_data_set_label = st.selectbox('Data set to import to:', options=data_set_labels, index=None)
                st.text('')

                if selected_data_set_label:
                    selected_data_set = endpoint.data_sets[data_set_labels.index(selected_data_set_label)]
                    graph = st.radio('Select the named graph:', options=[f'Data ({selected_data_set.graph_data.uri})', f'Ontology ({selected_data_set.graph_ontology.uri})', f'Metadata ({selected_data_set.graph_metadata.uri})'])
                    st.text('')

                    if graph:
                        if graph.startswith('Data'): graph_uri = selected_data_set.graph_data.uri
                        if graph.startswith('Ontology'): graph_uri = selected_data_set.graph_ontology.uri
                        if graph.startswith('Metadata'): graph_uri = selected_data_set.graph_metadata.uri

                        if file_format == 'ttl':
                            if st.button('Upload Turtle', icon=':material/upload:'):
                                dialog_confirmation(
                                    f'You are about to upload the file {file.name}.', 
                                    callback=endpoint.sparql.upload_turtle, 
                                    turtle_content=file_content,
                                    named_graph_uri=graph_uri
                                )
                        
                        if file_format == 'csv':
                            if st.button('Upload Table', icon=':material/upload:'):
                                dialog_confirmation(
                                    f'You are about to upload the file {file.name}.', 
                                    callback=endpoint.sparql.upload_csv, 
                                    csv_content=file_content,
                                    named_graph_uri=graph_uri
                                )


        if file_format == 'csv':
            # In case format is CSV, provide additional informations:
            # Explaination for the user, in order to build a specific table
            st.divider()
            st.markdown('## Tip:')
            st.markdown("""
                        To make the CSV import work, you will need to provide a specific format. 
                        In short, the table should only concern one class, and all triples in it should be outgoing.
                        If you would like to import incoming statements, you should then have a table for the domain class.
            """)
            st.markdown('Separator is comma.')
            st.markdown("""
                        Also, the content of the file itself should have a specific format.
                        First of all, there should be a column named "uri" (generally the first column).
                        Then each other column name should be a property uri (eg: "rdfs:label"): 
                        If, for some lines you do not have all the properties, no problem, just let an empty string or None instead.
            """)
            st.markdown('**Example of CSV to import person instances:**')
            st.markdown('`my-persons.csv`')
            st.dataframe(pd.DataFrame(data=[
                {'uri':'base:1234', 'rdf:type':'crm:E21', 'rdfs:label':'John Doe', 'rdfs:comment':'Unknown person', 'sdh:P23':'base:SAHIIne'},
                {'uri':'base:1235', 'rdf:type':'crm:E21', 'rdfs:label':'Jeane Doe', 'rdfs:comment':'Unknown person', 'sdh:P23':None},
                {'uri':'base:1236', 'rdf:type':'crm:E21', 'rdfs:label':'Albert', 'rdfs:comment':'King of some country', 'sdh:P23':'base:SAHIIne'},
            ]), use_container_width=True, hide_index=True)



    with st.expander('Export'):

        export_type_options = ['Export the Endpoint', 'Export a Data Set']
        export_type = st.radio('Export target', options=export_type_options, label_visibility='collapsed', horizontal=True)

        # Export the full endpoint
        col1, col2 = st.columns([1, 1])
        if export_type == export_type_options[0] and col1.button('Build the n-Quad file (can be long)'):

            with st.spinner("Building the n-quad", show_time=True):
                file_content = endpoint.sparql.dump()
                file_name =f"logre_{to_snake_case(endpoint.name)}_dump.nq".lower()

            if col2.download_button(label="Download file", data=file_content, file_name=file_name, mime="application/n-quads"):
                # Validation and rerun
                state.set_toast('File downloaded')
                st.rerun()

        # Export a data set
        if export_type == export_type_options[1]:

            data_set_labels = [data_set.name for data_set in endpoint.data_sets]
            selected_data_set_label = st.selectbox('Data set to export:', options=data_set_labels, index=None)
            st.text('')

            if selected_data_set_label:
                selected_data_set = endpoint.data_sets[data_set_labels.index(selected_data_set_label)]
                format = st.radio("Export format", ['n-Quads (.nq)', 'Turtle (.ttl)', 'Tables (.csv)'], horizontal=True)
                file_format = format[format.index('(.') + 2:format.index(')')]
                st.text('')

                col1, col2 = st.columns([1, 1])
                if col1.button('Build export file (can be long)'):

                    with st.spinner("Building the export file", show_time=True):
                        dump = selected_data_set.dump(file_format)

                        if file_format == 'nq':
                            file_content = dump
                            file_name = f"logre-{to_snake_case(endpoint.name)}-{to_snake_case(selected_data_set.name)}-dump.nq".lower()
                        
                        if file_format == 'ttl':
                            file_names = [key + '.ttl' for key in dump.keys()]
                            file_contents = [value for value in dump.values()]
                            file_content = build_zip_file(file_names, file_contents)
                            file_name = f"logre-{to_snake_case(endpoint.name)}-{to_snake_case(selected_data_set.name)}-ttl_dump.zip".lower()

                        if file_format == 'csv':
                            file_names = [key + '.csv' for key in dump.keys()]
                            file_contents = []
                            for df in dump.values():
                                print(df)
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                file_contents.append(csv_buffer.getvalue())
                            file_content = build_zip_file(file_names, file_contents)
                            file_name = f"logre-{to_snake_case(endpoint.name)}-{to_snake_case(selected_data_set.name)}-csv_dump.zip".lower()

                    
                    if col2.download_button(label="Download export file", data=file_content, file_name=file_name, mime="application/n-quads"):
                        # Validation and rerun
                        state.set_toast('File downloaded')
                        st.rerun()