from typing import Literal, List
import logging
import streamlit as st
from lib import state
from dotenv import load_dotenv
from components.errors import error_text

logger = logging.getLogger(__name__)


def init(
    layout: Literal["centered", "wide"] = "centered",
    required_query_params: List[str] = [],
    avoid_anchor_titles: bool = True,
) -> None:
    """
    Initializes the page with configuration, query parameters, and UI settings.

    Args:
        layout (Literal['centered', 'wide'], optional): The page layout style. Defaults to 'centered'.
        required_query_params (List[str], optional): List of query parameter keys to manage in the URL. Defaults to [].

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
    try:
        state.load_config()
    except Exception as err:
        logger.exception("Failed to load configuration")
        st.error(error_text("configuration.load", str(err)))
        st.stop()

    # Parse the query params first (handles direct links/new tabs)
    state.parse_query_params()

    # Then reflect the current state back into the URL if needed
    state.set_query_params(required_query_params)

    # Tab/page infos
    st.set_page_config(page_title="Logre", page_icon="👹", layout=layout)

    # Hide anchor link for titles
    if avoid_anchor_titles:
        st.html(
            "<style>[data-testid='stHeaderActionElements'] {display: none;}</style>"
        )

    # Handle toasts: if a toast is asked, display it, and clear the state, so that it does not appear next rerun
    text, icon = state.get_toast()
    if text:
        st.toast(
            text, icon=icon if icon else ":material/info:"
        )  # By default, icon is "info"
        state.clear_toast()
