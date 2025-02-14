from typing import Literal
import os
import streamlit as st
import lib.state as state


def init(layout: Literal['centered', 'wide'] = 'centered') -> None:
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
        state.set_version(version)

    # If there is a local config, load it
    if os.path.exists('./logre-config.toml') and not state.get_endpoints():
        file = open('./logre-config.toml', 'r')
        content = file.read()
        file.close()
        state.load_config(content, 'local')

    # State initialization
    if not state.get_queries(): state.set_queries([])
    if not state.get_endpoints(): state.set_endpoints([])

    # Toasts
    text, icon = state.get_toast()
    if text: 
        st.toast(text, icon=icon if icon else ':material/info:')
        state.clear_toast()

    # On each page load, clear the confirmation
    state.clear_confirmation()
