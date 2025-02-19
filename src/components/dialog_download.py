from typing import List
import pandas as pd, io, zipfile
import streamlit as st
from schema import Graph
from lib.sparql_queries import get_ontology, get_all_instances_of_class, download_graph
from lib.sparql_base import dump_endpoint
from lib.utils import to_snake_case
import lib.state as state


def __get_uri_of_property(class_uri: str, property_label: str):
    """From a property label and a class, get the URI of it, looking at the ontology."""

    all_properties = get_ontology().properties
    selection = [prop for prop in all_properties if prop.domain_class_uri == class_uri]
    target = [prop for prop in selection if to_snake_case(prop.label) == property_label]

    if len(target): return f"{target[0].order}-{target[0].uri}"
    else: return ""


def __get_all_class_dataframes(graph: Graph) -> List[dict[str, pd.DataFrame]]:
    """For each class listed in the ontology, generate a dataframe containing all instances with their properties as columns."""

    # Get all classes listed in the ontology
    all_classes = get_ontology().classes

    # For each class, fetch all instances of this class
    data = []
    for cls in all_classes:
        # Get all instances of this class
        instances = get_all_instances_of_class(cls, graph)

        # Format the information
        name = to_snake_case(cls.label) + '.csv'
        df = pd.DataFrame(data=instances)

        # Rename all columns: add the properties URI
        new_cols = []
        for col in df.columns:
            if col == "uri": new_cols.append("00-uri")
            elif col == "type": new_cols.append("01-rdf:type")
            else: new_cols.append(f"{__get_uri_of_property(cls.uri, col)}_{col.replace('_', '-')}")
        df.columns = new_cols

        # Make the column order same as the ontology
        df = df[sorted(new_cols)]
        df.columns = [col[col.index('-')+1:] for col in df.columns]


        # Save the result
        data.append({'name': name, 'value': df})

    return data


def __build_zip_file(datas: List[dict[str, str | pd.DataFrame]]):
    """Transform the result of the endpoint extract into one single zip file."""

    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for data in datas:
            if isinstance(data['value'], pd.DataFrame):
                csv_buffer = io.StringIO()
                data['value'].to_csv(csv_buffer, index=False)
                zip_file.writestr(data['name'], csv_buffer.getvalue())
            if isinstance(data['value'], str):
                zip_file.writestr(data['name'], data['value'])

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
                datas = download_graph(graph)
                col1.write('File generated')
                filename = f"logre-{endpoint.name}-{graph.label}.ttl".lower()
                col2.download_button(label="Click to Download", data=datas, file_name=filename, mime="text/turtle")
            except Exception as e:
                st.error(f"Error: {e}")

    # In case the download is a Spreadsheet
    if ".csv" in format:
        col1, col2 = st.columns([1, 1])
        if col1.button('Build the CSV bundle'):
            datas = __get_all_class_dataframes(graph)
            zip_file = __build_zip_file(datas)
            filename = f"logre-{endpoint.name}-{graph.label}.zip".lower()
            col2.download_button(label="Click to Download", data=zip_file, file_name=filename, mime="application/zip")
    


@st.dialog('Download the graph')
def dialog_dump_endpoint():
    """Dialog function allowing the user download the full endpoint as an n-quads file."""

    # From state
    endpoint = state.get_endpoint()

    # Information for the user
    st.markdown('Depending on the endpoint size, building the dump file could take a while.')

    st.divider()

    # First we need to generate the dump file
    col1, col2 = st.columns([1, 1])
    if col1.button('Build the dump file'):
        file_content = dump_endpoint()
        file_name =f"logre-{endpoint.name}-dump.nq".lower()

        # And then the user can download it
        col2.download_button(label="Click to Download", data=file_content, file_name=file_name, mime="application/n-quads")

        # Validation and rerun
        state.set_toast('Dump file downloaded')
        st.rerun()
