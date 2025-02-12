import streamlit as st
from schema import Entity
from lib.prefixes import explicits_uri

@st.dialog('Entity information')
def dialog_entity_info(entity: Entity) -> None:
    

    # URI
    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{entity.uri}]({explicits_uri(entity.uri)})")

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
    col2.markdown(f"{entity.class_label} ([{entity.class_uri}]({explicits_uri(entity.class_uri)}))")
