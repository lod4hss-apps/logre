import streamlit as st


def init() -> None:
    """Initialization function that runs on each page. Has to be the first thing to be called."""

    # Tab/page infos
    st.set_page_config(
        page_title='Logre',
        page_icon='👹'
    )