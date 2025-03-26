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
    file = open('./README.md', 'r')
    content = file.read()
    file.close()
    st.markdown(content)


# Get started
with st.expander('Get started'):
    file = open('./documentation/get-started.md', 'r')
    content = file.read()
    file.close()
    st.markdown(content)


# Configuration
with st.expander('Configuration'):
    file = open('./documentation/configuration.md', 'r')
    content = file.read()
    file.close()
    st.markdown(content)


# Changelog
with st.expander('Changes log'):
    file = open('./documentation/changelog.md', 'r')
    content = file.read()
    file.close()
    st.markdown(content)