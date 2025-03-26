import streamlit as st
from lib.sparql_queries import get_ontology
import lib.state as state

@st.dialog("Add an data table configuration")
def dialog_config_data_tables() -> None:
    """Dialog function to provide a formular for the data tables configuration creation/edition."""

    ontology = get_ontology()

    # Class filter
    classes_labels = list(map(lambda cls: cls.display_label , ontology.classes))
    class_label = st.selectbox('Get entity table of class:', options=classes_labels, index=None)
