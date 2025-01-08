import streamlit as st
from typing import Callable


@st.dialog("Confirmation")
def confirmation(text: str, callback: Callable, **kwargs) -> None:
    """
    Dialog function that ask confirmation on any given action.
    Dialog will close if the user clicks on "Yes" or "No".
    Page will be reloaded on user click

    Args:
        text (str): The text to display in the confirmation. "Do you confirm?" will be appended.
        callback (function): function to execute if the user clicks "Yes"
        **kwargs: parameters that will be given to the callback
    """
    
    st.markdown(text)
    st.markdown('Do you confirm?')
    col1, col2 = st.columns([1, 1])
    if col1.button('No'):
        st.rerun()
    if col2.button('Yes', type='primary'):
        callback(**kwargs)
        st.rerun()
