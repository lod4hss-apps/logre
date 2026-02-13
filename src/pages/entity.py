import streamlit as st
from components.init import init

init(required_query_params=['db', 'uri'])

st.switch_page("pages/entity-card.py")
