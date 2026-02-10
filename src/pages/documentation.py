from pathlib import Path
import streamlit as st
from components.init import init
from components.menu import menu


init(avoid_anchor_titles=False)
menu()


BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
folder_path = BASE_DIR + '/documentation/faq.md'

with open(folder_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
st.markdown(content)