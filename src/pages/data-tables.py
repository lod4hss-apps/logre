import streamlit as st
from components.init import init
from components.menu import menu
from lib.sparql_queries import get_ontology, get_class_tables, get_class_number
import lib.state as state


##### The page #####

init(layout='wide')
menu()

# From state
endpoint = state.get_endpoint()
graph = state.get_graph()
current_page = state.get_data_table_page()

ontology = get_ontology()


# Can't make a SPARQL query if there is no endpoint
if not endpoint:

    st.title("Data tables")
    st.text('')
    st.warning('You need to select an endpoint first (menu on the left).')

else:

    # Title
    st.title("Data tables")
    st.text('')

    col1, col2 = st.columns([5, 1])

    # Class filter
    classes_labels = list(map(lambda cls: cls.display_label , ontology.classes))
    class_label = col1.selectbox('Get entity table of class:', options=classes_labels, index=None)

    # Number fetched by request
    limit = col2.selectbox('Limit fetched by request', [10, 20, 50, 100], index=0)

    # Find the selected entity from the selected label
    if class_label:
        class_index = classes_labels.index(class_label)
        selected_class_uri = ontology.classes[class_index].uri

        # Offset calculation
        offset = (current_page - 1) * limit

        # Fetch and display data
        st.text('')
        df_instances = get_class_tables(graph, selected_class_uri, limit, offset)
        df_instances.index += 1 * (limit * (current_page - 1)) + 1 # So that indexes appears to start at 1
        st.dataframe(df_instances, use_container_width=True)

        # Pagination
        st.text('')
        col1, col2 = st.columns([8, 1], vertical_alignment='top')
        col1.markdown(f'Total number of instances: {get_class_number(graph, selected_class_uri)} - Current page: {current_page}')
        page_choice = col2.number_input('Go to page', value=current_page, min_value=1)
        if page_choice != current_page:
            state.set_data_table_page(page_choice)
            st.rerun()
        
