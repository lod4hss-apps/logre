from pathlib import Path
import streamlit as st
from components.init import init
from components.menu import menu


# def format_filename(filename: str) -> str:
#     """Transform a filename in a usable title in the page"""
#     filename = filename[3:]
#     name = filename[0:filename.rindex(".")] # Remove extension
#     name = name.replace("-", " ").replace("_", " ")  # Replace separators
#     return name.title()

# # Fetch all files in the folder ./documentation
# folder = Path('./documentation')

# contents = {format_filename(f.name) : f.read_text(encoding='utf-8') for f in folder.iterdir()}

init()
menu()

# for name, content in contents.items():
#     with st.expander(name):
#         st.markdown(content)

import os

folder_path = './documentation'

file_objects = []
for filename in sorted(os.listdir(folder_path)):

    if filename != "99-changelog.md":

        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            filename = filename[3:]
            name = filename[0:filename.rindex(".")] # Remove extension
            name = name.replace("-", " ").replace("_", " ")  # Replace separators
            name = name.title() if name.lower() != "faq" else 'FAQ'

            with st.expander(name):
                st.markdown(content)

    