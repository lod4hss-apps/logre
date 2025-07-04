from typing import Literal
from dotenv import load_dotenv, find_dotenv
import streamlit as st
import lib.state as state
from lib.configuration import read_config
from lib.version import read_version
from model import NotExistingEndpoint, NotExistingDataBundle


def init(layout: Literal['centered', 'wide'] = 'centered') -> None:
    """Initialization function that runs on each page. Has to be the first thing to be called."""

    # Load .env file only if it exists
    dotenv_path = find_dotenv()
    if dotenv_path: load_dotenv(dotenv_path)

    try:

        # Tab/page infos
        st.set_page_config(
            page_title='Logre',
            page_icon='👹',
            layout=layout
        )

        # Hide anchor link for titles
        st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")

        # Load version number if not in state
        if not state.get_version():
            read_version()

        # If there is no config in state, read it
        if not state.get_has_config():
            read_config()

        # State initialization
        if not state.get_queries(): state.set_queries([])
        if not state.get_endpoints(): state.set_endpoints([])

        # Handle toasts: if some is asked, display it, and clear the state
        text, icon = state.get_toast()
        if text: 
            st.toast(text, icon=icon if icon else ':material/info:')
            state.clear_toast()

        # On each page load, clear the confirmation, 
        # so that it is not prefilled on new confirmation
        state.clear_confirmation()

    except BaseException as error:

        print('ERROR CAUGHT IN init.py/init():')
        print(error)

        st.error(str(error))
        st.stop()