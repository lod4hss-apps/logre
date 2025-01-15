import streamlit as st
from tools.sparql_queries import list_graphs

def read_endpoint_list() -> dict[str:str]:
    """Put in session the content of the data/saved_endpoints file."""

    # Read the file content
    file = open('../data/saved_endpoints', 'r')
    content = file.read().strip()
    file.close()

    # Parse the content into a list of objects
    endpoint_list = content.split('\n')
    endpoints = []
    for raw_endpoint in endpoint_list:
        # If an error occurs here, it is because the file has the wrong format
        try:
            if raw_endpoint.strip() != "":
                colon_index = raw_endpoint.index(':')
                name = raw_endpoint[0:colon_index].strip()
                url = raw_endpoint[colon_index+1:].strip()
                endpoints.append({'name':name, 'url':url})
        except Exception:
            st.error('File "data/saved_endpoints" is wrongly formatted. Correct it then reload the page.')

    # Put the endpoints information in session
    st.session_state['all_endpoints'] = endpoints


def menu() -> None:
    """Component function: the sidebar"""

    col1, col2 = st.sidebar.columns([2, 1], vertical_alignment='bottom')
    col1.markdown(f"# Logre")
    col2.markdown(f"<small>v{st.session_state['VERSION']}</small>", unsafe_allow_html=True)

    st.sidebar.page_link("pages/home.py", label="Presentation")
    st.sidebar.page_link("pages/endpoint-config.py", label="Endpoint configuration")
    st.sidebar.page_link("pages/sparql-editor.py", label="SPARQL editor")
    st.sidebar.page_link("pages/explore.py", label="Explore")


    st.sidebar.divider()

    ### Endpoint Selection part ###

    # Here we read and parse the disk, display endpoints, and allow user to choose which one he wants
    read_endpoint_list()
    endpoint_labels = list(map(lambda endpoint: endpoint['name'], st.session_state['all_endpoints']))
    endpoint_urls = list(map(lambda endpoint: endpoint['url'], st.session_state['all_endpoints']))

    # If an endpoint is already selected, find it, otherwise just init to Nothing
    if 'endpoint' in st.session_state:
        selected_index = endpoint_labels.index(st.session_state['endpoint']['name'])
    else:
        selected_index = None

    # If there are endpoints on disk, allow selection, otherwise display a message
    if len(endpoint_labels):
        selected_label = st.sidebar.selectbox('Selected endpoint', endpoint_labels, index=selected_index, placeholder="None selected")
    else:
        st.info('No endpoints are saved on disk')
        selected_label = None

    # If there is a selected endpoint, 
    if selected_label :
        # That is different that the one in session
        if 'endpoint' not in st.session_state or selected_label != st.session_state['endpoint']['name']:
            # Update the one in session (or set)
            selected_index = endpoint_labels.index(selected_label)
            selected_url = endpoint_urls[selected_index]
            st.session_state['endpoint'] = {'name': selected_label, 'url': selected_url}
            if 'all_graphs' in st.session_state:
                del st.session_state['all_graphs']
            # Clear the cache
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()


        # Fetch all graphs from the endpoint, and add the default one
        if "all_graphs" not in st.session_state:
            st.session_state["all_graphs"] = [{
                'uri': None,
                'label': 'Default',
                'comment': "Comment not set",
                'activated': True
            }]
            graphs = list_graphs()
            import json
            print(json.dumps(graphs, indent=4))
            for i, graph in enumerate(graphs):
                st.session_state["all_graphs"].append({
                    'uri': graph['uri'],
                    'label': graph['label'] if 'label' in graph else "Unknown label",
                    'comment': graph['comment'] if 'comment' in graph else "Comment not set",
                    'activated': False
                })


        # Allow user to activate/deactivate a graph (in queries)
        st.sidebar.markdown('#### Endpoint graph List:')
        for i, graph in enumerate(st.session_state["all_graphs"]):
            if st.sidebar.checkbox(graph['label'], value=graph['activated']):
                if st.session_state['all_graphs'][i]['activated'] != True:
                    st.session_state['all_graphs'][i]['activated'] = True
                    st.rerun()

            else:
                if st.session_state['all_graphs'][i]['activated'] != False:
                    st.session_state['all_graphs'][i]['activated'] = False
                    st.rerun()
