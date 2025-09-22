from typing import Callable
import streamlit as st


@st.dialog("Confirmation")
def dialog_confirmation(text: str, callback: Callable, **kwargs) -> None:
    """
    Displays a confirmation dialog with "Yes" and "No" options, executing a callback if confirmed.

    Args:
        text (str): The message or information to display in the dialog.
        callback (Callable): The function to execute if the user confirms by clicking "Yes".
        **kwargs: Additional keyword arguments to pass to the callback function.

    Returns:
        None

    Behavior:
        - Shows the provided text and asks for user confirmation.
        - "No" button cancels the action and reruns the page.
        - "Yes" button executes the callback with provided kwargs inside a spinner and reruns the page if successful.
        - Any exceptions raised during callback execution are propagated.
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
