import streamlit as st
import lib.state as state

# Load default page
if 'page' not in st.query_params:
    st.switch_page("pages/documentation.py")

# If it comes from an internal link
else:
    # Load the parameters
    state.set_query_params(st.query_params)

    # Redirect to asked page
    asked_page = state.get_query_param('page')
    st.switch_page(f"pages/{asked_page}.py")
