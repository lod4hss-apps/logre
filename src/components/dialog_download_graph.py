import streamlit as st
from schema import Graph
from lib.sparql_base import download_graph

@st.dialog('Download the graph')
def dialog_download_graph(graph: Graph):


    col1, col2 = st.columns([1, 1], vertical_alignment='center')
    col1.markdown(f'#### Graph: **{graph.label}**')
    format = col2.selectbox('File format', options=['Turtle (.ttl)', 'Spreadcheet (.csv)'], index=0)

    st.text('')
    st.markdown('Depending on the graph size, building the file could take a while.')

    st.divider()

    col1, col2 = st.columns([1, 1])
    if col1.button('Build the file'):
        try:
            export_format = "ttl" if "ttl" in format else "csv"
            data, filename = download_graph(graph, export_format)
            col1.write('File created')
            col2.download_button(label="Click to Download", data=data, file_name=filename, mime="text/turtle" if "Turtle" in filename else "text/csv")
        except Exception as e:
            st.error(f"Error: {e}")

    