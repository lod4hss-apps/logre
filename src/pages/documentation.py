from pathlib import Path
import streamlit as st
from components.init import init
from components.menu import menu


def format_filename(filename: str) -> str:
    """Transform a filename in a usable title in the page"""
    name = filename[0:filename.rindex(".")] # Remove extension
    name = name.replace("-", " ").replace("_", " ")  # Replace separators
    return name.title()

# Fetch all files in the folder ./documentation
folder = Path('./documentation')
contents = {format_filename(f.name) : f.read_text() for f in folder.iterdir()}

init()
menu()

# Read me
with st.expander('README'):
    readme_file = open('./README.md', 'r', encoding='utf-8')
    content = readme_file.read()
    readme_file.close()
    st.markdown(content)


for name, content in contents.items():
    with st.expander(name):
        st.markdown(content)