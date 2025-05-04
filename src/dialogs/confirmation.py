from typing import Callable
import streamlit as st


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
    st.markdown(text, unsafe_allow_html=True)
    st.markdown('Do you confirm?')

    # Line with user commands: "Yes" and "No" buttons
    col1, col2 = st.columns([1, 1])

    if col1.button('No'):
        # Do nothing
        st.rerun()

    if col2.button('Yes', type='primary'):
        
        # Call the callback with given keywords args
        with st.spinner('Executing...'):
            result = callback(**kwargs)
        
        # If there is an error, the error message is already handled, 
        # thus, nothing to do especially not closing the dialog
        if result != 'error':
            # Finalization: validation message and reload
            st.rerun()
