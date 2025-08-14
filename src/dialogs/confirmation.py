from typing import Callable
import streamlit as st


@st.dialog("Confirmation")
def dialog_confirmation(text: str, callback: Callable, **kwargs) -> None:
    """
    Dialog function that ask confirmation on any given action.
    Allow caller to give information (as string) and a callback to execute if the user clicks on "Yes".
    Clicking on "No" has no actions.
    Callback should handle errors; if there is any, it will be forwarded upwards.

    Args:
        text (str): The text to display in the confirmation. "Do you confirm?" will be appended.
        callback (function): function to execute if the user clicks "Yes".
        **kwargs: parameters that will be given to the callback.
    """
    
    # Display information
    st.markdown(text, unsafe_allow_html=True)
    st.markdown('Do you confirm?')

    # Line with user commands: "Yes" and "No" buttons
    col1, col2 = st.columns([1, 1])

    # Button "No": do nothing
    if col1.button('No'):
        # Do nothing
        st.rerun()

    # Button "Yes": exewcute callback
    if col2.button('Yes', type='primary'):

        # Callback should handle errors, but in case it does not, handle it here
        try:
            # Call the callback with given keywords args
            with st.spinner('Executing...'):
                result = callback(**kwargs)

            # Only rerun when there was no errors in the callback execution
            st.rerun()

        # Forward the error upwards
        except BaseException as error:
            raise error
