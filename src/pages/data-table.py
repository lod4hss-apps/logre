import streamlit as st
from requests.exceptions import HTTPError
from urllib.parse import quote
from components.init import init
from components.menu import menu
from components.help import help_text, info as help_info
from lib import state
from lib.errors import get_HTTP_ERROR_message

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

# Initialize
init(layout='wide', query_param_keys=['endpoint', 'db'])
menu()

try:

    # From state
    data_bundle = state.get_data_bundle()

    # Make verifications
    if not data_bundle:
        st.warning('No Data Bundle selected')
    else:

        # Title
        st.title("Data tables")
        help_info('data_table.overview')
        st.text('')

        row_container = st.container(horizontal=True, horizontal_alignment='distribute')

        with row_container.container(horizontal=True):
            # Class filter: only "real" classes (no value classes)
            not_value_classes = [c for c in data_bundle.model.classes if c.class_uri != "rdfs:Datatype"]
            classes_labels = [c.get_text() for c in not_value_classes]
            class_label = st.selectbox('Get entity table of class:', options=classes_labels, index=None, width=200, help=help_text('data_table.class_filter'))

            # Number fetched by request
            limit = st.selectbox('Limit', [10, 20, 50, 100], index=0, width=100, help=help_text('data_table.limit'))

        if class_label:
            class_index = classes_labels.index(class_label)
            selected_class = not_value_classes[class_index]
            columns = data_bundle.get_data_table_columns_names(selected_class)

            # Saved page
            current_page = state.data_table_get_page(selected_class.uri)

            # Offset calculation
            offset = (current_page - 1) * limit

            # Sort by
            sort_ways = ['ASC', 'DESC'] 
            with row_container.container(horizontal=True, horizontal_alignment='center'):
                sort_col = st.selectbox('Sort on', columns, index=None, on_change=lambda: state.data_table_set_page(selected_class.uri, 1), width=200, help=help_text('data_table.sort'))
                sort_way = st.radio('Sort way', sort_ways, horizontal=True, help=help_text('data_table.sort'))

            # Filter by
            with row_container.container(horizontal=True, horizontal_alignment='center'):
                filter_col = st.selectbox('Filter on', columns, index=None, on_change=lambda: state.data_table_set_page(selected_class.uri, 1), width=200, help=help_text('data_table.filter'))
                filter_value = st.text_input('Filter value', on_change=lambda: state.data_table_set_page(selected_class.uri, 1), disabled=filter_col is None, width=200, help=help_text('data_table.filter'))
            
            st.text('')

            # Fetch the data table
            df_instances = data_bundle.get_data_table(selected_class, limit, offset, sort_col, sort_way, filter_col, filter_value)

            # Display information if there are some
            if len(df_instances) > 0:
                df_instances.index += 1 * (limit * (current_page - 1)) + 1 # So that indexes appears to start at 1
                base_url = st.get_option("browser.serverAddress") or "localhost"
                base_port = st.get_option("browser.serverPort") or "8501"
                if isinstance(base_url, str) and base_url.startswith("http"):
                    origin = base_url
                else:
                    origin = f"http://{base_url}:{base_port}"
                df_instances['Open'] = [
                    f"{origin}/entity-card?db={data_bundle.key}&uri={quote(uri, safe='')}"
                    for uri in df_instances['URI']
                ]
                st.dataframe(df_instances, width='stretch', column_config={
                    'URI': st.column_config.TextColumn(width='small'),
                    'Outgoing Count': st.column_config.NumberColumn(width='small'),
                    'Incoming Count': st.column_config.NumberColumn(width='small'),
                    'Open': st.column_config.LinkColumn(display_text="Open", width='small'),
                })

                export_df = df_instances.drop(columns=['Open'], errors='ignore')
                file_name = f"logre_{data_bundle.key}_{selected_class.get_text().replace(' ', '_')}_table.csv"
                st.download_button(
                    "Export this view (CSV)",
                    data=export_df.to_csv(index=False).encode('utf-8'),
                    file_name=file_name,
                    mime="text/csv",
                    icon=":material/download:",
                    help=help_text('data_table.export'),
                    key=f"csv-export-{selected_class.uri}"
                )

                with st.expander("Advanced exports (graphs & full bundle)"):
                    st.markdown("**Export a graph as Turtle (.ttl)**")
                    data_type = st.radio('Named graph', options=['Data', 'Model', 'Metadata'], horizontal=True, key=f"graph-radio-{selected_class.uri}")
                    graph = data_bundle.graph_data if data_type == 'Data' else data_bundle.graph_model if data_type == 'Model' else data_bundle.graph_metadata
                    if st.button('Generate Turtle file', key=f'build-ttl-{selected_class.uri}'):
                        with st.spinner('Building Turtle export...'):
                            file_content = graph.dump_turtle(data_bundle.prefixes)
                            graph_file_name = f"logre_{data_bundle.key}_{data_type}_dump.ttl"
                        st.download_button(
                            label="Download Turtle file",
                            data=file_content,
                            file_name=graph_file_name,
                            mime="text/turtle",
                            icon=":material/download:",
                            key=f'download-ttl-{selected_class.uri}'
                        )

                    st.markdown('---')
                    st.markdown("**Export the whole bundle as n-Quads (.nq)**")
                    if st.button('Generate n-Quads dump', key=f'build-nq-{selected_class.uri}'):
                        with st.spinner('Building n-Quads export...'):
                            file_content = data_bundle.dump_nq()
                            nq_file_name = f"logre_{data_bundle.key}_dump.nq"
                        st.download_button(
                            label="Download n-Quads file",
                            data=file_content,
                            file_name=nq_file_name,
                            mime="application/n-quads",
                            icon=":material/download:",
                            key=f'download-nq-{selected_class.uri}'
                        )
            else:
                st.markdown('*No records found*')
                
except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))
