import streamlit as st
from components.init import init
from components.menu import menu


def get_getting_started_content() -> str:
    readme_file = open('./GETTING-STARTED.md', 'r')
    content = readme_file.read()
    readme_file.close()
    return content


##### The page #####

init()
menu()

st.markdown(get_getting_started_content())