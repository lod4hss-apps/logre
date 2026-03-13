import streamlit as st
from components.init import init
from lib import state

init()

state.resolve_startup_context()
data_bundle = state.get_data_bundle()

if data_bundle:
    st.switch_page("pages/dashboard.py")
else:
    st.switch_page("pages/documentation.py")
