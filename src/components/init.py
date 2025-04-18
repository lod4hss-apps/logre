from typing import Literal
import os
import streamlit as st
import lib.state as state
from lib.configuration import read_config


def init(layout: Literal['centered', 'wide'] = 'centered') -> None:
    """Initialization function that runs on each page. Has to be the first thing to be called."""

    # Tab/page infos
    st.set_page_config(
        page_title='Logre',
        page_icon='👹',
        layout=layout
    )

    # Hide anchor link for titles
    st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")

    # Load version number
    if 'VERSION' not in st.session_state:
        file = open('./VERSION', 'r')
        version = file.read()
        file.close()
        state.set_version(version)

    # If it is a local instance and there is a config, load it
    if os.getenv('ENV') != 'streamlit' and os.path.exists('./logre-config.toml') and not state.get_endpoints():
        read_config()

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


    # Load information from the query params
    if state.has_query_params():

        # Load the right endpoint
        endpoint_url = state.get_query_param('endpoint')
        all_endpoints = state.get_endpoints()
        endpoint = [x for x in all_endpoints if x.url == endpoint_url][0] # We are sure there is at least one result
        state.set_endpoint(endpoint)

        # At this point, graph can't be selected, the graph list has not been created yet
        # Because of that, query params need to be kept for now, they will be removed after graph selection, and entity setting
        # state.clear_query_param()


