import streamlit as st
import lib.state as state

# Load the query parameters
state.set_query_params(st.query_params)

# Dispatch to right page
if 'page' not in st.query_params:
    st.switch_page("pages/documentation.py")
else:
    st.switch_page(f"pages/{st.query_params['page']}.py")