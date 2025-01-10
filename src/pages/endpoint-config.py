import streamlit as st
from components.init import init
from components.menu import menu
from components.confirmation import dialog_confirmation


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


def write_endpoint_list() -> None:
    """Write all endpoint URLs that are in session memory on disk."""

    # Transform the list of objects into a string
    content = ""
    for endpoint in st.session_state['all_endpoints']:
        content += f"{endpoint['name']}: {endpoint['url']}\n"

    # Write the generated string on disk
    file = open('../data/saved_endpoints', 'w')
    file.write(content)
    file.close()


def select_endpoint_callback() -> None:
    """Callback function for the Endpoint select box"""
    index = endpoint_labels.index(selected_label)
    selected_url = endpoint_urls[index]
    st.session_state['endpoint'] = {'name': selected_label, 'url': selected_url}
    

def delete_endpoint(index: int):
    """Callback function to delete a endpoint from the list"""
    del st.session_state['endpoint']
    del st.session_state['all_endpoints'][index]
    write_endpoint_list()


##### Modals #####

@st.dialog('Add a new endpoint')
def dialog_add_new_endpoint():

    # User inputs
    new_name = st.text_input('Endpoint name')
    new_url = st.text_input('Endpoint URL')
    btn = st.button('Save')

    # If we have everything filled, and the user clicks on the button:
    if new_name and new_url and btn:
        # We need to verify that the endpoint is new (name and URL)
        endpoint_labels = list(map(lambda endpoint: endpoint['name'], st.session_state['all_endpoints']))
        endpoint_urls = list(map(lambda endpoint: endpoint['url'], st.session_state['all_endpoints']))
        if new_name in endpoint_labels:
            st.error('There is already an endpoint called like that.')
        elif new_url in endpoint_urls:
            st.error('There is already an endpoint with this URL')
        else:
            # If the endpoint is really new, add to the session, write on disk, and rerun the page
            st.session_state['all_endpoints'].append({'name': new_name, 'url': new_url})
            write_endpoint_list()
            st.rerun()


##### The page #####

init()
menu()

st.title("Endpoint configuration")

st.divider()

st.markdown("### Select your working endpoint")

# -- First part: Known Endpoints

col1, col2 = st.columns([3, 1], vertical_alignment='bottom')

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
    selected_label = col1.selectbox('Known endpoints', endpoint_labels, key="selectbox-endpoint", index=selected_index, placeholder="Choose an endpoint")
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
        st.rerun()

    # Allow the user to remove an endpoint from disk
    if col2.button('Remove endpoint'):
        dialog_confirmation(f'This will delete "{selected_label}" from your favorites.', delete_endpoint, index=selected_index)


# -- Second part: Allow user to write a new endpoint

st.text('') # Spacer
st.text('') # Spacer
st.markdown('Your endpoint is not in the list?')

if st.button('Add a new endpoint'):
    dialog_add_new_endpoint()
