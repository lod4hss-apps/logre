import streamlit as st
from components.init import init
from components.menu import menu


init()
menu()


# Read me
with st.expander('README'):
    readme_file = open('./README.md', 'r')
    content = readme_file.read()
    readme_file.close()
    st.markdown(content)

# Getting started
with st.expander('Get started'):
    getting_started_file = open('./GETTING-STARTED.md', 'r')
    content = getting_started_file.read()
    getting_started_file.close()
    st.markdown(content)

# Change log
with st.expander('Change Log'):
    chane_log_file = open('./CHANGELOG.md', 'r')
    content = chane_log_file.read()
    chane_log_file.close()
    st.markdown(content)
