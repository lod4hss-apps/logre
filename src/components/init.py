from typing import Literal, List
import streamlit as st
from lib import state
from dotenv import load_dotenv

def init(layout: Literal['centered', 'wide'] = 'centered', query_param_keys: List[str] = []) -> None:
    """
    Initializes the page with configuration, query parameters, and UI settings.

    Args:
        layout (Literal['centered', 'wide'], optional): The page layout style. Defaults to 'centered'.
        query_param_keys (List[str], optional): List of query parameter keys to manage in the URL. Defaults to [].

    Returns:
        None

    Side Effects:
        - Loads and parses application configuration.
        - Updates and processes query parameters.
        - Configures the Streamlit page (title, icon, layout).
        - Injects custom CSS to hide header anchor links.
        - Displays a toast notification if one is present in the state, then clears it.
    """
    load_dotenv()

    # On each run, make sure that the configuration is loaded
    state.load_config()
    
    # Put the needed query params in the page URL, if available
    state.set_query_params(query_param_keys)

    # Parse the query params, for the page (like in a link, reload etc)
    state.parse_query_params()

    # Tab/page infos
    st.set_page_config(page_title='Logre', page_icon='👹', layout=layout)

    # Hide anchor link for titles
    st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")

    # Handle toasts: if a toast is asked, display it, and clear the state, so that it does not appear anymore
    text, icon = state.get_toast()
    if text: 
        st.toast(text, icon=icon if icon else ':material/info:') # By default, icon is "info"
        state.clear_toast()