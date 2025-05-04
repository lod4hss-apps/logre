import streamlit as st
from model import Endpoint
from lib import state
from lib.configuration import save_config

@st.dialog('Create Endpoint')
def dialog_create_endpoint(server_technologies: list[str]) -> None:
    
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
        all_endpoints.append(Endpoint(technology, name, url, username, password, base_uri))
        save_config()
        st.rerun()