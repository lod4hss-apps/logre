import streamlit as st


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
        file = open('../VERSION', 'r')
        version = file.read()
        file.close()
        st.session_state['VERSION'] = version