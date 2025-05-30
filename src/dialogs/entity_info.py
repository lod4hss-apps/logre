import streamlit as st
from model import OntoEntity
from lib import state
import pyperclip

@st.dialog('Entity information')
def dialog_entity_info(entity: OntoEntity) -> None:
    """Simple dialog to display basic information about an entity."""

    # From state
    endpoint = state.get_endpoint()


    # URI
    col1, col2, col3 = st.columns([1, 3, 1], vertical_alignment='center')
    col1.markdown(f"**URI**")
    col2.markdown(f"[{entity.uri}]({endpoint.sparql.unroll_uri(entity.uri)})")
    if col3.button('', icon=":material/content_copy:", type='tertiary', key='entity-info-btn-1'):
        pyperclip.copy(entity.uri)

    # Label
    col1, col2, col3 = st.columns([1, 3, 1], vertical_alignment='center')
    col1.markdown("**Label**")
    col2.markdown(entity.label)
    col3.button('', type='tertiary', key='entity-info-btn-2')

    # Comment 
    col1, col2, col3 = st.columns([1, 3, 1], vertical_alignment='center')
    col1.markdown("**Comment**")
    col2.markdown(entity.comment or '')
    col3.button('', type='tertiary', key='entity-info-btn-3')

    # Class
    col1, col2, col3 = st.columns([1, 3, 1], vertical_alignment='center')
    col1.markdown(f"**Class**")
    col2.markdown(f"{entity.class_label} ([{entity.class_uri}]({endpoint.sparql.unroll_uri(entity.class_uri)}))")
    col3.button('', type='tertiary', key='entity-info-btn-4')
