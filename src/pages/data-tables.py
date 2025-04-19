import streamlit as st
from components.init import init
from components.menu import menu
from lib.prefixes import explicits_uri
from lib.sparql_queries import get_ontology, get_data_table_columns, get_data_table, get_class_number
import lib.state as state


##### The page #####

init(layout='wide')
menu()

# From state
endpoint = state.get_endpoint()
graph = state.get_graph()
current_page = state.get_data_table_page()


# Can't make a SPARQL query if there is no endpoint
if not endpoint:

    st.title("Data tables")
    st.text('')
    st.warning('You need to select an endpoint first (menu on the left).')

else:

    ontology = get_ontology()

    # Title
    st.title("Data tables")
    st.text('')

    col1, col2, _, col3, _, col4, col5 = st.columns([2, 1, 1, 2, 1, 2, 2])

    # Class filter
    classes_labels = list(map(lambda cls: cls.display_label , ontology.classes))
    class_label = col1.selectbox('Get entity table of class:', options=classes_labels, index=None)

    # Number fetched by request
    limit = col2.selectbox('Limit', [10, 20, 50, 100], index=0)

    # Find the selected entity from the selected label
    if class_label:
        class_index = classes_labels.index(class_label)
        selected_class_uri = ontology.classes[class_index].uri

        # Offset calculation
        offset = (current_page - 1) * limit

        # Sort by
        sort_col, sort_way = None, None
        sort_options = list(map(lambda col: (f"{col}: ASC", f"{col}: DESC"), list(get_data_table_columns().values())))
        sort_options = [x for tpl in sort_options for x in tpl]
        sort_option = col3.selectbox('Column to sort on', sort_options, index=None)
        if sort_option: 
            sort_col = sort_option[0:sort_option.rindex(':')].strip()
            sort_way = sort_option[sort_option.rindex(':') + 1:].strip()


        # Filter by
        filter_col, filter_value = None, None
        filter_col = col4.selectbox('Column to filter by', list(get_data_table_columns().values()), index=None)
        if filter_col:
            filter_value = col5.text_input('Value to filter by')
        
        # Fetch and display data
        st.text('')
        df_instances = get_data_table(graph, selected_class_uri, limit, offset, sort_col=sort_col, sort_way=sort_way, filter_col=filter_col, filter_value=filter_value)
        df_instances.index += 1 * (limit * (current_page - 1)) + 1 # So that indexes appears to start at 1
        if len(df_instances):
            df_instances['Link'] = [f"/?page=entity&endpoint={explicits_uri(endpoint.url)}&graph={explicits_uri(graph.uri)}&entity={explicits_uri(uri)}" for uri in df_instances['URI']]
        
        st.dataframe(df_instances, use_container_width=True, column_config={'Link':st.column_config.LinkColumn(display_text="Open", width='small')})

        # Pagination
        st.text('')
        col1, col2 = st.columns([8, 1], vertical_alignment='top')
        col1.markdown(f'Total number of instances: {get_class_number(graph, selected_class_uri)} - Current page: {current_page}')
        page_choice = col2.number_input('Go to page', value=current_page, min_value=1)
        if page_choice != current_page:
            state.set_data_table_page(page_choice)
            st.rerun()
        
