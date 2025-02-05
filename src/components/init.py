import streamlit as st
import os
from lib.utils import load_config


def init(layout='centered') -> None:
    """Initialization function that runs on each page. Has to be the first thing to be called."""

    # Tab/page infos
    st.set_page_config(
        page_title='Logre',
        page_icon='👹',
        layout=layout
    )

    # Load version number
    if 'VERSION' not in st.session_state:
        file = open('./VERSION', 'r')
        version = file.read()
        file.close()
        st.session_state['VERSION'] = version

    # If there is a local config, load it
    if os.path.exists('./logre-config.toml') and 'all_endpoints' not in st.session_state:
        file = open('./logre-config.toml', 'r')
        content = file.read()
        file.close()
        load_config(content)

    # Session state initialization
    if 'configuration' not in st.session_state: st.session_state['configuration'] = False
    if 'all_queries' not in st.session_state: st.session_state['all_queries'] = []
    if 'all_endpoints' not in st.session_state: st.session_state['all_endpoints'] = []


