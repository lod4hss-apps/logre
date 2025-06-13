from typing import Any, Tuple, List
import os
import yaml
from model import Endpoint, Query, Prefix
import lib.state as state
import streamlit as st

DEFAULT_PATH = './defaults.yaml'
CONFIG_PATH = './logre-config.yaml'


def unload_config() -> str:
    """Reads the state to create the config object, and returns the TOML string version of it."""

    # From state
    all_queries = state.get_queries()
    all_endpoints = state.get_endpoints()

    # Transform into serializable objects
    all_queries = [q.to_dict() for q in all_queries]
    all_endpoints = [e.to_dict() for e in all_endpoints]

    # Build the object to be saved
    config = {
        'endpoints': all_endpoints,
        'queries': all_queries, 
    }

    return yaml.dump(config, sort_keys=False)


def load_config(file_content: str) -> str:
    """From a string (a file content) build a dictionnary, and put all the configuration in state."""

    config: dict = yaml.safe_load(file_content)
    state.set_has_config(True)

    # Load saved query texts
    if 'queries' in config: 
        # Parse into instances of Query
        all_queries = list(map(lambda obj: Query.from_dict(obj), config.get('queries', [])))
        state.set_queries(all_queries)

    # In any case, add default queries at the beginning
    all_queries = state.get_queries()
    have_queries = set(list(map(lambda q: q.name, all_queries)))
    for query in state.get_default_queries():
        if query.name not in have_queries: 
            all_queries.insert(0, query)
    state.set_queries(all_queries)

    # Load saved endpoints
    if 'endpoints' in config: 
        # Parse into instances of Endpoint
        all_endpoints = list(map(lambda obj: Endpoint.from_dict(obj), config.get('endpoints', [])))

        # For all endpoints, add all default prefixes
        for endpoint in all_endpoints: 
            have_prefixes = set(list(map(lambda p: p.short, endpoint.sparql.prefixes)))
            for prefix in state.get_default_prefixes():
                if prefix.short not in have_prefixes:
                    endpoint.sparql.prefixes.append(prefix)

        # Save all endpoints in state
        state.set_endpoints(all_endpoints)

        # By default, select the first endpoint
        if len(all_endpoints) == 1:
            state.set_endpoint(all_endpoints[0])


def save_config() -> None:
    """
    In case Logre is started locally, and there is a config in the root folder, 
    Save the configuration.
    Otherwise, do nothing
    """

    # Safegard to avoid to save something on streamlit server
    if os.getenv('ENV') == 'streamlit': 
        return

    # Unload and write on disk
    file = open(CONFIG_PATH, 'w')
    file.write(unload_config())
    file.close()

    # Clear caches
    st.cache_data.clear()
    st.cache_resource.clear()


def read_config() -> None:
    """
    In case Logre is started locally, and there is a config in the root folder, 
    Save the configuration.
    Otherwise, do nothing
    """

    # Load defaults
    default_file = open(DEFAULT_PATH, 'r')
    parse_defaults(default_file.read())
    default_file.close()

    # Safegard: check if we are on streamlit or not
    if os.getenv('ENV') == 'streamlit': 
        return 
    
    # Read and load from disk
    if os.path.exists(CONFIG_PATH):
        file = open(CONFIG_PATH, 'r')
        content = file.read()
        file.close()

        load_config(content)
        

def parse_defaults(default_content: str) -> Tuple[List[Query], List[Prefix]]:
    
    obj = yaml.safe_load(default_content)
    queries = []
    prefixes = []

    for query_raw in obj.get('queries', []):
        queries.append(Query(query_raw['name'], query_raw['query']))
    
    for prefix_raw in obj.get('prefixes', []):
        prefixes.append(Prefix(prefix_raw['short'], prefix_raw['long']))

    state.set_defaults(queries, prefixes)