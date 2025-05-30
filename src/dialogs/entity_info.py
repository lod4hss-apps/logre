import streamlit as st
from model import OntoEntity
from lib import state

@st.dialog('Entity information')
def dialog_entity_info(entity: OntoEntity) -> None:
    """Simple dialog to display basic information about an entity."""

    # From state
    endpoint = state.get_endpoint()


    # URI
    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{entity.uri}]({endpoint.sparql.unroll_uri(entity.uri)})")

    # Label
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(entity.label)

    # Comment 
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Comment**")
    col2.markdown(entity.comment or '')

    # Class
    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**Class**")
    col2.markdown(f"{entity.class_label} ([{entity.class_uri}]({endpoint.sparql.unroll_uri(entity.class_uri)}))")
