from typing import Literal, List
from pathlib import Path
import pandas as pd
from io import StringIO
import streamlit as st
from schema import EndpointTechnology, Triple, Graph
from lib.sparql_base import delete
from components.init import init
from components.menu import menu
from components.dialog_confirmation import dialog_confirmation
import requests
import lib.state as state
from lib.sparql_base import insert
from lib.prefixes import is_prefix

all_file_formats = ['Turtle (.ttl)', 'Spreadsheet (.csv)', 'n-Quads (.nq)']
all_file_types = ['ttl', 'csv', 'nq']


def __format_filename(filename: str) -> str:
    """Transform a filename in a usable title in the page"""

    name = filename[0:filename.rindex(".")] # Remove extension
    name = name.replace("-", " ").replace("_", " ")  # Replace separators
    return name.title()


def __get_import_url(graph_uri: str = "") -> str | None:
    """Depending on the technology, get the correct import URL"""

    # From state
    endpoint = state.get_endpoint()
    technology = endpoint.technology
    endpoint_url = endpoint.url

    # Allegrograph endpoint
    if technology == EndpointTechnology.ALLEGROGRAPH or technology == EndpointTechnology.ALLEGROGRAPH.value:
        # If in the Allegrograph endpoint, there is the trailing '/sparql', remove it: 
        # import does not work on this URL
        allegrograph_base_url = endpoint_url.replace('/sparql', '')

        # In a dedicated graph, create the correct URL
        if graph_uri: 
            graph_uri = graph_uri.replace('base:', endpoint.base_uri)
            # Make the graph URI URL compatible
            graph_uri = '%3C' + graph_uri.replace(':', '%3A').replace('/', '%2F') + '%3E'

            # Create and return  the import URL
            url = f"{allegrograph_base_url}/statements?context={graph_uri}"
        else: 
            # If it is in the default graph, nothing is needed to do
            url = f"{allegrograph_base_url}/statements"
        return url
    
    elif technology == EndpointTechnology.FUSEKI or technology == EndpointTechnology.FUSEKI.value:
        # If it is a Fuseki endpoint
        if graph_uri:
            graph_uri = graph_uri.replace('base:', 'http://geovistory.org/information/')
            return f"{endpoint_url}?graph={graph_uri}"
        else: 
            return endpoint_url


def __upload_turtle_file(ttl_datas: List[str], graph_uri: str, way: Literal['clear', 'append']) -> None | Literal['error']:
    """
    Function to import raw turtle data (as string) into the given graph.
    Specifying the graph is mandatory, otherwise import it into default graph.
    """

    # Clear the graph if needed
    if way == 'clear':
        # Delete all statements in the ontology graph    
        triple = Triple('?s', '?p', '?o')
        delete(triple, graph=graph_uri)
        # Delete all statement related to the graph itself from default graph
        triple = Triple(graph_uri, '?p', '?o')
        delete(triple)

    # Upload
    url = __get_import_url(graph_uri)
    headers = {"Content-Type": "text/turtle"}

    # Add Authentication
    if endpoint.username and endpoint.password: auth = (endpoint.username, endpoint.password)
    elif endpoint.username: auth = (endpoint.username, '')
    else: auth = None
    
    # Make the request
    for ttl_data in ttl_datas:
        response = requests.post(url, data=ttl_data, headers=headers, auth=auth)

        # Check response
        if response.status_code >= 400:
            st.error(f"Failed to upload file. Status code: {response.status_code}. Reason: {response.reason}. Message: {response.text}.")
            return 'error'
    
    # We clear the cache, because it needs to refetch the needed information: 
    # If for example, imported data is the model, we need to fetch it on next occasion
    # Which won't happen if the cache is not cleared.
    st.cache_data.clear()

    state.clear_graphs()
    state.set_toast('Data inserted', ':material/file_upload:')


def __upload_nquads_file(nq_data:str) -> None | Literal['error']:
    """
    Function to import raw n-Quads data (as string) into the endpoint.
    As n-quads already include the graph, data can't be imported into a specified graph.
    """

    # Upload
    url = __get_import_url()
    headers = {"Content-Type": "application/n-quads"}

    # Add Authentication
    if endpoint.username and endpoint.password: auth = (endpoint.username, endpoint.password)
    elif endpoint.username: auth = (endpoint.username, '')
    else: auth = None

    # Make the request
    response = requests.post(url, data=nq_data, headers=headers, auth=auth)

    # Check response
    if response.status_code >= 400:
        st.error(f"Failed to upload file. Status code: {response.status_code}. Reason: {response.reason}. Message: {response.text}.")
        return 'error'
    else:
        # We clear the cache, because it needs to refetch the needed information: 
        # If for example, imported data is the model, we need to fetch it on next occasion
        # Which won't happen if the cache is not cleared.
        st.cache_data.clear()
        state.clear_graphs()

    state.set_toast('Data inserted', ':material/file_upload:')


def __upload_spreadsheet_file(csv_datas: str, graph_uri: str) -> None:
    """
    Function to import CSV raw file into the endpoint.
    Specifying the graph is mandatory, otherwise import it into default graph.
    """

    # Prepare all the triples to be imported
    triples = []
    
    # Loop on each given file content
    for csv_data in csv_datas:
        
        try: 
            # For better handling, transform into a dataframe
            df = pd.read_csv(StringIO(csv_data))

            for _, row in df.iterrows():
                # Get the URI of the entity
                uri = row['uri']
                # For each properties available
                for col in df.columns:
                    # Do not do anything with the uri
                    if col == 'uri': continue
                    # If the cell is empty, skip
                    if pd.isna(row[col]) or row[col] is None or row[col] == '': continue
                    # Extract the property URI from the column name, and save it as a triple
                    property_uri = col[:col.index('_') if '_' in col else len(col)]

                    # Is the range a URI or a literal?
                    if (':' in row[col] and is_prefix(row[col][:row[col].index(':')])) or row[col].startswith('http://'):
                        triples.append(Triple(uri, property_uri, row[col]))
                    else:
                        triples.append(Triple(uri, property_uri, f"'{row[col]}'"))
        except Exception:
            st.error('CSV import went wrong, the file is probably malformed: the file format (column names) needs to be respected in order to import those files.')
            return

    # Insert all data into the file
    insert(triples, graph_uri)

    # Validation message
    state.set_toast('Data inserted', ':material/file_upload:')



##### The page #####

init()
menu()

# From state
endpoint = state.get_endpoint()
all_graphs = state.get_graphs()

# Title
st.title("Import")
st.text('')

# Can't import anything if there is no endpoint
if not endpoint:

    st.warning('You need to select an endpoint first (menu on the left).')

else:

    graphs_labels = [graph.label for graph in all_graphs]
    tab_data, tab_ontologies = st.tabs(['Data', 'Ontologies'])

    ### TAB DATA ###

    tab_data.text('')
    col1, col2 = tab_data.columns([1, 1]) 
    

    # File format selection
    format = col1.selectbox('Select the file format', options=all_file_formats)
    if format:
        format_index = all_file_formats.index(format)
        file_type = all_file_types[format_index]

        # Only provide graph selection if it makes sense
        if file_type != 'nq': 
            
            # Graph selection
            graph_label = col2.selectbox('Select the graph', options=graphs_labels, index=None, key='import-data-graph-selection')  

            # Target the graph
            if graph_label:
                graph_index = graphs_labels.index(graph_label)
                selected_graph = all_graphs[graph_index]


        # File uploader
        files = tab_data.file_uploader(f"Load your {format} file:", type=[file_type], disabled=(format is None), accept_multiple_files=(file_type != 'nq'))
        tab_data.text('')

        # In case format is CSV, provide additional informations:
        # Explaination for the user, in order to build a specific table
        if file_type == 'csv':
            st.markdown('## Tip:')
            st.markdown("""
                        To make the CSV import work, you will need to provide a specific format. 
                        In short, you should provide one table per class, and all triples in it should be outgoing.
                        If you would like to import incoming statements, you should then have a table for the domain class.
            """)
            st.markdown('Separator is comma.')
            st.markdown("""
                        Also, the content of the file itself should have a specific format.
                        First of all, there should be a column named `uri` (generally the first column).
                        Then each other column name should be `<predicate>_<label>` like `rdfs:label_has-name`: 
                        first the predicate as an URI, followed by an underscore, and then you're free to put the name you want.
                        If, for some lines you do not have all the properties, no problem, just let an empty string or None instead.
            """)
            st.markdown('**Example of CSV to import person instances:**')
            st.markdown('`my-persons.csv`')
            st.dataframe(pd.DataFrame(data=[
                {'uri':'base:1234', 'rdf:type':'crm:E21', 'rdfs:label_name':'John Doe', 'rdfs:comment_description':'Unknown person', 'sdh:P23_gender':'base:SAHIIne'},
                {'uri':'base:1235', 'rdf:type':'crm:E21', 'rdfs:label_name':'Jeane Doe', 'rdfs:comment_description':'Unknown person', 'sdh:P23_gender':None},
                {'uri':'base:1236', 'rdf:type':'crm:E21', 'rdfs:label_name':'Albert', 'rdfs:comment_description':'King of some country', 'sdh:P23_gender':'base:SAHIIne'},
            ]), use_container_width=True, hide_index=True)


        # If everything is ready for the TTL import
        if format and file_type == 'ttl' and len(files) != 0 and graph_label and tab_data.button('Upload Turtle file', icon=':material/upload:'):
            dialog_confirmation(
                f'You are about to upload **{", ".join([file.name.upper() for file in files])}** into **{graph_label.upper()}**.', 
                callback=__upload_turtle_file, 
                ttl_datas=[file.read().decode("utf-8") for file in files],
                graph_uri=selected_graph.uri
            )

        # If everything is ready for the CSV import
        if format and file_type == 'csv' and len(files) != 0 and graph_label and tab_data.button('Upload Spreadsheet', icon=':material/upload:'):
            dialog_confirmation(
                f'You are about to upload **{", ".join([file.name.upper() for file in files])}** into **{graph_label.upper()}**.', 
                callback=__upload_spreadsheet_file, 
                csv_datas=[file.read().decode("utf-8") for file in files],
                graph_uri=selected_graph.uri
            )

        # If everything is ready for the NQuad import
        # In this case, files is actually not a list, but a single file
        if format and files and file_type == 'nq' and tab_data.button('Upload n-Quads', icon=':material/upload:'):
            dialog_confirmation(
                f'You are about to upload **{files.name.upper()}**.', 
                callback=__upload_nquads_file, 
                nq_data=files.read().decode("utf-8")
            )


    ### TAB ONTOLOGIES ###
    
    tab_ontologies.text('')

    # Loop through all ontologies files
    folder = Path('./ontologies')
    files = [{ 'name': __format_filename(f.name), 'path': f.name } for f in folder.iterdir()]
    files.sort(key=lambda x: x['name'])
    onto_names = [file['name'] for file in files]
    onto_paths = [file['path'] for file in files]
    
    # Graph selection
    has_onto_graph = endpoint.ontology_uri != ''
    if has_onto_graph:
        selected_graph_uri = endpoint.ontology_uri
    else:
        graph_label = tab_ontologies.selectbox('Select the graph', options=graphs_labels, index=None, key='import-ontology-graph-selection')  

        # Fetch the graph
        if graph_label:
            graph_index = graphs_labels.index(graph_label)
            selected_graph_uri = all_graphs[graph_index].uri

    # Ontology selection
    ontology_name = tab_ontologies.selectbox('Choose an ontology', options=onto_names, index=None)
    if ontology_name:
        onto_index = onto_names.index(ontology_name)
        onto_path = './ontologies/' + onto_paths[onto_index]
        f = open(onto_path, 'r')
        file_content = f.read()
        f.close()
        tab_ontologies.text('')

        upload_way = tab_ontologies.radio('', ['Append to current ontology', 'Clear current ontology'], label_visibility='collapsed')
        tab_ontologies.text('')

        if file_content and tab_ontologies.button('Upload ontology', icon=':material/upload:'):
            dialog_confirmation(
                f'You are about to upload the ontology named **{ontology_name.upper()}** into **{selected_graph_uri}**. The way is: **{upload_way}**', 
                callback=__upload_turtle_file, 
                ttl_datas=[file_content],
                graph_uri=selected_graph_uri,
                way='append' if upload_way == 'Append to current ontology' else 'clear'
            )

