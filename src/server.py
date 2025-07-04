import streamlit as st
import os

if 'ENV' not in os.environ:
    os.environ["ENV"] = "local"
if 'LOGRE_MODE' not in os.environ:
    os.environ["LOGRE_MODE"] = "normal"

st.switch_page("pages/documentation.py")