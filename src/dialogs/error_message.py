from typing import Callable
import streamlit as st


@st.dialog("Error message")
def dialog_error_message(text: str) -> None:

    # Display information
    st.markdown(text, unsafe_allow_html=True)

    with st.container(horizontal=True, horizontal_alignment='center'):
        if st.button("Ok"):
            st.rerun()