import streamlit as st
from requests.exceptions import HTTPError
from components.init import init
from components.menu import menu
from lib import state

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

try:
    # Initialize
    init(layout='wide', query_param_keys=['db'])
    menu()

    # From state
    data_bundle = state.get_data_bundle()

    # Make verifications
    if not data_bundle:
        st.warning('No Data Bundle selected')
    else:

        # Title
        st.title("Data tables")
        st.text('')

        row_container = st.container(horizontal=True, horizontal_alignment='distribute')

        with row_container.container(horizontal=True):
            # Class filter: only "real" classes (no value classes)
            not_value_classes = [c for c in data_bundle.model.classes if c.class_uri != "rdfs:Datatype"]
            classes_labels = [c.get_text() for c in not_value_classes]
            class_label = st.selectbox('Get entity table of class:', options=classes_labels, index=None, width=200)

            # Number fetched by request
            limit = st.selectbox('Limit', [10, 20, 50, 100], index=0, width=100)

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
                sort_col = st.selectbox('Sort on', columns, index=None, on_change=lambda: state.data_table_set_page(selected_class.uri, 1), width=200)
                sort_way = st.radio('Sort way', sort_ways, horizontal=True)

            # Filter by
            with row_container.container(horizontal=True, horizontal_alignment='center'):
                filter_col = st.selectbox('Filter on', columns, index=None, on_change=lambda: state.data_table_set_page(selected_class.uri, 1), width=200)
                filter_value = st.text_input('Filter value', on_change=lambda: state.data_table_set_page(selected_class.uri, 1), disabled=filter_col is None, width=200)
            
            st.text('')

            # Fetch the data table
            df_instances = data_bundle.get_data_table(selected_class, limit, offset, sort_col, sort_way, filter_col, filter_value)

            # Display information if there are some
            if len(df_instances) > 0:
                df_instances.columns = ['URI'] + data_bundle.get_data_table_columns_names(selected_class) + ['Outgoing count', 'Incoming count']
                df_instances.index += 1 * (limit * (current_page - 1)) + 1 # So that indexes appears to start at 1
                if len(df_instances):
                    df_instances['Link'] = [f"/entity?db={data_bundle.key}&uri={uri}" for uri in df_instances['URI']]
                
                st.dataframe(df_instances, width='stretch', column_config={
                    'URI': st.column_config.TextColumn(width='small'),
                    'Outgoing Count': st.column_config.NumberColumn(width='small'),
                    'Incoming Count': st.column_config.NumberColumn(width='small'),
                    'Link':st.column_config.LinkColumn(display_text="Open", width='small'),
                })
            else:
                st.markdown('*No records found*')
                
except HTTPError as err:
    message = f"""[HTTP ERROR]\n\n{err.args[0]}"""
    st.error(message)
    print(message.replace('\n\n', ' - '))