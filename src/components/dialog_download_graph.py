from typing import List
import pandas as pd, io, zipfile
import streamlit as st
from schema import Graph, OntologyProperty
from lib.sparql_base import download_graph
from lib.sparql_queries import get_ontology, get_all_instances_of_class
from lib.utils import to_snake_case
import lib.state as state


def __get_uri_of_property(class_uri: str, property_label: str):
    """From a property label and a class, get the URI of it, looking at the ontology."""

    all_properties = get_ontology().properties
    selection = [prop for prop in all_properties if prop.domain_class_uri == class_uri]
    target = [prop for prop in selection if to_snake_case(prop.label) == property_label]

    if len(target): return f"{target[0].order}-{target[0].uri}"
    else: return ""


def get_all_class_dataframes() -> List[dict[str, str]]:
    """For each class listed in the ontology, generate a dataframe containing all instances with their properties as columns."""

    # Get all classes listed in the ontology
    all_classes = get_ontology().classes

    # For each class, fetch all instances of this class
    data = []
    for cls in all_classes:
        # Get all instances of this class
        instances = get_all_instances_of_class(cls)

        # Format the information
        name = to_snake_case(cls.label) + '.csv'
        df = pd.DataFrame(data=instances)

        # Rename all columns: add the properties URI
        new_cols = []
        for col in df.columns:
            if col == "uri":
                new_cols.append("0-uri")
            else:
                new_cols.append(f"{__get_uri_of_property(cls.uri, col)}-{col}")
        df.columns = new_cols

        # Make the column order same as the ontology
        df = df[sorted(new_cols)]
        df.columns = [col[2:] for col in df.columns]

        # Save the result
        data.append({'name': name, 'df': df})

    return data


def build_zip_file(dfs: List[dict[str, str]]):
    """Transform the result of the endpoint extract into one single zip file."""

    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for data in dfs:
            csv_buffer = io.StringIO()
            data['df'].to_csv(csv_buffer, index=False)
            zip_file.writestr(data['name'], csv_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer


@st.dialog('Download the graph')
def dialog_download_graph(graph: Graph):
    """Dialog function allowing the user download a graph in a specified format."""

    # From state
    endpoint = state.get_endpoint()

    col1, col2 = st.columns([1, 1], vertical_alignment='bottom')
    col1.markdown(f'#### Graph: **{graph.label}**')
    format = col2.selectbox('File format', options=['Turtle (.ttl)', 'Zipped spreadcheets (.csv)'], index=0)

    # Information for the user
    st.text('')
    st.markdown('Depending on the graph size, building the file could take a while.')

    st.divider()

    # In case the download is a turtle file
    if ".ttl" in format:
        col1, col2 = st.columns([1, 1])
        if col1.button('Build the turtle file'):
            try:
                data = download_graph(graph)
                col1.write('File generated')
                filename = f"logre-{endpoint.name}-{graph.label}.ttl".lower()
                col2.download_button(label="Click to Download", data=data, file_name=filename, mime="text/turtle")
            except Exception as e:
                st.error(f"Error: {e}")

    # In case the download is a Spreadsheet
    if ".csv" in format:
        col1, col2 = st.columns([1, 1])
        if col1.button('Build the CSV bundle'):
            data = get_all_class_dataframes()
            zip_file = build_zip_file(data)
            filename = f"logre-{endpoint.name}-{graph.label}.zip".lower()
            col2.download_button(label="Click to Download", data=zip_file, file_name=filename, mime="application/zip")
    