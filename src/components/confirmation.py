import streamlit as st
import time
from typing import Callable


@st.dialog("Confirmation")
def dialog_confirmation(text: str, callback: Callable, **kwargs) -> None:
    """
    Dialog function that ask confirmation on any given action.
    Allow caller to give information (as string) and a callback to execute if the user clicks on "Yes".
    Clicking on "No" will have no actions

    Args:
        text (str): The text to display in the confirmation. "Do you confirm?" will be appended.
        callback (function): function to execute if the user clicks "Yes"
        **kwargs: parameters that will be given to the callback
    """
    
    # Display information
    st.markdown(text)
    st.markdown('Do you confirm?')

    # Line with user commands: "Yes" and "No" buttons
    col1, col2 = st.columns([1, 1])

    if col1.button('No'):
        # Do nothing
        st.rerun()

    if col2.button('Yes', type='primary'):
        # Call the callback with given keywords args
        callback(**kwargs)

        # Finalization: validation message and reload
        st.success('Done.')
        time.sleep(1)
        st.rerun()
