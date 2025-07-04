import streamlit as st
from model import Endpoint
from lib import state
from lib.configuration import save_config

@st.dialog('Add Endpoint')
def dialog_add_endpoint(server_technologies: list[str]) -> None:
    
    name = st.text_input('Name ❗️')
    technology = st.selectbox('Server technology ❗️', options=server_technologies, index=None)
    url = st.text_input('URL ❗️')
    base_uri = st.text_input('Base URI ❗️', value='http://example.org/')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    st.text('')
    st.text('')

    can_create = name and technology and url and base_uri
    if st.button('Create', disabled=not can_create):
        all_endpoints = state.get_endpoints()

        new_endpoint = Endpoint(technology, name, url, username, password, base_uri)

        # Add all default prefixes
        have_prefixes = set(list(map(lambda p: p.short, new_endpoint.sparql.prefixes)))
        for prefix in state.get_default_prefixes():
            if prefix.short not in have_prefixes:
                new_endpoint.sparql.prefixes.append(prefix)

        all_endpoints.append(new_endpoint)
        save_config()
        st.rerun()