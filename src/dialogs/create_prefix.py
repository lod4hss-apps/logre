import streamlit as st
from model import Endpoint, Prefix
from lib.configuration import save_config



@st.dialog('Create prefix')
def dialog_create_prefix(endpoint: Endpoint) -> None:

    short = st.text_input('Short ❗️')
    long = st.text_input('Long ❗️')

    st.text('')
    st.text('')
    
    can_create = short and long
    if st.button('Create', disabled=not can_create):
        prefix = Prefix(short, long)
        endpoint.sparql.prefixes.append(prefix)
        save_config()
        st.rerun()