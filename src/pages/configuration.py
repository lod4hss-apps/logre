import os, streamlit as st
import lib.state as state
from typing import Any
from model import Endpoint, DataBundle, Prefix
from lib.configuration import save_config, unload_config, CONFIG_PATH
from components.init import init
from components.menu import menu
from dialogs import dialog_confirmation, dialog_create_prefix, dialog_create_data_bundle, dialog_create_endpoint


all_technologies = ['Fuseki', 'Allegrograph', 'GraphDB']
all_onto_frameworks = ['SHACL']

def __save() -> None:
    save_config()
    state.set_toast('Configuration saved', icon=':material/done:')
    st.rerun()

def __del_endpoint(endpoint: Endpoint) -> None:
    all_endpoints = state.get_endpoints()
    all_endpoints = list(filter(lambda e: e != endpoint, all_endpoints))
    state.set_endpoints(all_endpoints)
    state.clear_endpoint()
    save_config()

def __del_data_bundle(endpoint: Endpoint, data_bundle: DataBundle) -> None:
    endpoint.data_bundles = list(filter(lambda d: d != data_bundle, endpoint.data_bundles))
    save_config()

def __del_prefix(endpoint: Endpoint, prefix: Prefix) -> None:
    endpoint.sparql.prefixes = list(filter(lambda p: p != prefix, endpoint.sparql.prefixes))
    save_config()


##### The page #####

init()
menu()

# From state
all_endpoints = state.get_endpoints()


### CONFIGURATION ###

col1, col2 = st.columns([6, 2], vertical_alignment='bottom')
col1.title("Configuration")
if os.getenv('ENV') != "local":
    col2.download_button(
        label='Download', 
        data=unload_config(), 
        disabled=os.getenv('ENV') == 'local',
        file_name=CONFIG_PATH.replace('./', ''),
        help='Download this configuration as a YAML file. If Logre is running locally, it will be updated automatically.',
        icon=':material/download:'
    )

st.text('')
if st.button('Add a new Endpoint', icon=':material/add:', key="configuration-endpoint-add"):
    dialog_create_endpoint(all_technologies)


# Display all endpoints from configuration
for index_endpoint, endpoint in enumerate(all_endpoints):
    
    # Separators between endpoints
    # st.divider()

    with st.expander(f"Endpoint *{endpoint.name}*"):

        # Endpoint Title
        col1, col2, _ = st.columns([9, 3, 1], vertical_alignment='bottom')
        col1.markdown(f"## Endpoint *{endpoint.name}*:")
        if col2.button('Delete Endpoint', icon=':material/delete:', type='tertiary', key=f"configuration-endpoint-{index_endpoint}-del"):
            dialog_confirmation(f"You are about to delete the Endpoint:\n{endpoint.name}", __del_endpoint, endpoint=endpoint)

        st.text('')

        ### ENDPOINT GENERAL ### 

        # Name & Technology
        col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
        name = col1.text_input(label='Name', value=endpoint.name, key=f'configuration-endpoint-name-{index_endpoint}')
        if name != endpoint.name and col1_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-endpoint-name-{index_endpoint}-save'): 
            endpoint.name = name
            __save()
        technology = col2.selectbox('Server technology', options=all_technologies, index=all_technologies.index(endpoint.sparql.name), key=f'configuration-endpoint-technology-{index_endpoint}')
        if technology != endpoint.sparql.name and col2_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-endpoint-name-{index_endpoint}-save'): 
            Technology = Endpoint.get_entpoint_technology(technology)
            prefixes = endpoint.sparql.prefixes
            endpoint.sparql = Technology(endpoint.sparql.url, endpoint.sparql.username, endpoint.sparql.password)
            endpoint.sparql.prefixes = prefixes
            __save()

        # URL
        col, col_save = st.columns([11, 1], vertical_alignment='bottom')
        url = col.text_input(label='URL', value=endpoint.sparql.url, key=f'configuration-endpoint-url-{index_endpoint}')
        if url != endpoint.sparql.url and col_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-endpoint-url-{index_endpoint}-save'): 
            endpoint.sparql.url = url
            __save()

        # Username & Password
        col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
        username = col1.text_input('Username', value=endpoint.sparql.username, key=f'configuration-endpoint-username-{index_endpoint}')
        if username != endpoint.sparql.username and col1_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-endpoint-username-{index_endpoint}-save'): 
            endpoint.sparql.username = username
            __save()
        password = col2.text_input('Password', value=endpoint.sparql.password, type='password', key=f'configuration-endpoint-password-{index_endpoint}')
        if password != endpoint.sparql.password and col2_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-endpoint-name-{index_endpoint}-save'): 
            endpoint.sparql.password = password
            __save()

        # Base URI
        col, col_save = st.columns([11, 1], vertical_alignment='bottom')
        base_uri = col.text_input(label='Base URI', value=endpoint.base_uri, key=f'configuration-endpoint-base-uri-{index_endpoint}')
        if endpoint.base_uri != base_uri and col_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-endpoint-base-uri-{index_endpoint}-save'): 
            endpoint.base_uri = base_uri
            __save()

        st.text('')
        st.text('')

        ### DATA BUNDLE ###

        st.markdown("### Data Bundles")

        for index_data_bundle, data_bundle in enumerate(endpoint.data_bundles):
            
            # Title and delete feature
            col1, col2, _ = st.columns([9, 4, 1], vertical_alignment='center')
            col1.markdown(f"##### *{data_bundle.name}*")
            if col2.button('Delete Data Bundle', icon=':material/delete:', type='tertiary', key=f'configuration-data-bundle-{index_endpoint}-{index_data_bundle}-del'):
                dialog_confirmation(f"You are about to delete the Data Bundle:\n{data_bundle.name}", __del_data_bundle, endpoint=endpoint, data_bundle=data_bundle)

            # DataBundle name & DataBundle Ontology framework
            col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
            name = col1.text_input(label='Name', value=data_bundle.name, key=f'configuration-data-bundle-name-{index_endpoint}-{index_data_bundle}')
            if name != data_bundle.name and col1_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-name-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].name = name
                __save()
            onto_framework = col2.selectbox('Ontology framework', all_onto_frameworks, all_onto_frameworks.index(data_bundle.ontology.name), key=f'configuration-data-bundle-onto-{index_endpoint}-{index_data_bundle}')
            if onto_framework != data_bundle.ontology.name and col2_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-onto-{index_endpoint}-{index_data_bundle}-save'):
                OntologyClass = DataBundle.get_ontology_framework(onto_framework)
                endpoint.data_bundles[index_data_bundle].ontology = OntologyClass(endpoint.data_bundles[index_data_bundle].graph_ontology)
                __save()

            # Label property (path) and Comment property (path)
            col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
            label_property = col1.text_input(label='Label property', value=data_bundle.label_property, key=f'configuration-data-bundle-label-prop-{index_endpoint}-{index_data_bundle}')
            if label_property != data_bundle.label_property and col1_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-label-prop-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].label_property = label_property
                __save()
            comment_property = col2.text_input(label='Comment property', value=data_bundle.comment_property, key=f'configuration-data-bundle-comment-prop-{index_endpoint}-{index_data_bundle}')
            if comment_property != data_bundle.comment_property and col2_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-comment-prop-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].comment_property = comment_property
                __save()

            # Type property (path) and Comment property (path)
            col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
            type_property = col1.text_input(label='Type property', value=data_bundle.type_property, key=f'configuration-data-bundle-type-prop-{index_endpoint}-{index_data_bundle}')
            if type_property != data_bundle.type_property and col1_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-type-prop-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].type_property = type_property
                __save()
            
            # Data Named Graph URI
            col, col_save = st.columns([11, 1], vertical_alignment='bottom')
            data_graph_uri = col.text_input(label='Data Named Graph URI', value=data_bundle.graph_data.uri, key=f'configuration-data-bundle-data-graph-{index_endpoint}-{index_data_bundle}')
            if data_graph_uri != data_bundle.graph_data.uri and col_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-data-graph-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].graph_data.uri = data_graph_uri
                __save()

            # Ontology Named Graph URI 
            col, col_save = st.columns([11, 1], vertical_alignment='bottom')
            ontology_graph_uri = col.text_input(label='Ontology Named Graph URI', value=data_bundle.graph_ontology.uri, key=f'configuration-data-bundle-onto-graph-{index_endpoint}-{index_data_bundle}')
            if ontology_graph_uri != data_bundle.graph_ontology.uri and col_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-onto-graph-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].graph_ontology.uri = ontology_graph_uri
                __save()

            # Metadata Named Graph URI 
            col, col_save = st.columns([11, 1], vertical_alignment='bottom')
            metadata_graph_uri = col.text_input(label='Metadata Named Graph URI', value=data_bundle.graph_metadata.uri, key=f'configuration-data-bundle-metadata-graph-{index_endpoint}-{index_data_bundle}')
            if metadata_graph_uri != data_bundle.graph_metadata.uri and col_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-data-bundle-metadata-graph-{index_endpoint}-{index_data_bundle}-save'):
                endpoint.data_bundles[index_data_bundle].graph_metadata.uri = metadata_graph_uri
                __save()

            st.text('')

        st.text('')

        if st.button('Add a new Data Bundle', icon=':material/add:', key=f"configuration-data-bundle-{index_endpoint}-add"):
            dialog_create_data_bundle(endpoint, all_onto_frameworks)

    st.text('')

    ### PREFIXES ###

    with st.expander(f"### Prefixes"):

        col1, col2 = st.columns([10, 3])
        for index_prefix, prefix in enumerate(sorted(endpoint.sparql.get_prefixes(), key=lambda p: p.short)):
            col1, col1_save, col2, col2_save, col_delete = st.columns([2, 1, 8, 1, 1], vertical_alignment='bottom')

            short = col1.text_input(label='Short', value=prefix.short, key=f'configuration-prefix-short-{index_endpoint}-{index_prefix}')
            if short != prefix.short and col1_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-prefix-short-{index_endpoint}-{index_prefix}-save'):
                endpoint.sparql.prefixes[index_prefix].short = short
                __save()

            long = col2.text_input(label='Long', value=prefix.long, key=f'configuration-prefix-long-{index_endpoint}-{index_prefix}')
            if long != prefix.long and col2_save.button('', icon=':material/save:', type='tertiary', key=f'configuration-prefix-long-{index_endpoint}-{index_prefix}-save'):
                endpoint.sparql.prefixes[index_prefix].long = long
                __save()

            if col_delete.button('', icon=':material/delete:', type='tertiary', key=f'configuration-prefix-{index_endpoint}-{index_prefix}-del'):
                dialog_confirmation(f'You are about to delete prefix\n{prefix.short}: {prefix.long}', __del_prefix, endpoint=endpoint, prefix=prefix)
            
        st.text('')

        if st.button('Add a new Prefix', icon=':material/add:', key=f"configuration-prefix-{index_endpoint}-add"):
            dialog_create_prefix(endpoint)