from typing import Tuple, List
import os, yaml
import streamlit as st

# Local imports
from model import Endpoint, Query, Prefix
import lib.state as state

"""
This module is a wrapper to handle configuration accross Logre.

Features: 
    - Read and parse default configuration
    - Read configuration
    - Load configuration (populate correctly state)
    - Unload configuration (get it from state)
    - Write configuration
"""


# Path on disk from default configuration (saved in the repo)
DEFAULT_PATH = './default-config.yaml'

# Path on disk from user configuration (git ignored)
CONFIG_PATH = './logre-config.yaml'


def unload_config() -> str:
    """
    Extract information from state, create the configuration object and returns the YAML version of it.

    Returns:
        string: the YAML version of the configuration
    """

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

    # Transform and return the YAML version
    return yaml.dump(config, sort_keys=False)


def load_config(file_content: str) -> None:
    """
    Extract configuration from the YAML version of it, build the configuration object, and put information in state.

    Args:
        file_content (string): The string verison (in YAML format) of the configuration.
    """

    # Inform the state that a configuration is present
    state.set_has_config(True)

    # Transform the string into a dictionnary
    config: dict = yaml.safe_load(file_content)

    # Load saved query texts
    if 'queries' in config: 
        # Parse into instances of Query
        all_queries = list(map(lambda obj: Query.from_dict(obj), config.get('queries', [])))
        state.set_queries(all_queries)

    # In any case, add default queries at the beginning (coming from the default configuration)
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

        # If there is only one endpoint listed, select it by default
        if len(all_endpoints) == 1:
            state.set_endpoint(all_endpoints[0])


def parse_defaults() -> None:
    """Parse the queries and prefixes from the default configuration, and put them in the state."""
    
    # Read default configuration content
    with open(DEFAULT_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Transform the YAML content into a dictionnary
    obj = yaml.safe_load(content)

    # Extract the queries (with building instances of "Query")
    queries = []
    for query_raw in obj.get('queries', []):
        queries.append(Query(query_raw['name'], query_raw['query']))

    # Extract the prefixes (with building instances of "Prefix")
    prefixes = []
    for prefix_raw in obj.get('prefixes', []):
        prefixes.append(Prefix(prefix_raw['short'], prefix_raw['long']))

    # Put all parsed queries and prefixes to state
    state.set_defaults(queries, prefixes)


def save_config() -> None:
    """
    Does nothing if ENV VAR "ENV" is set to "streamlit".
    Otherwise, save information present in state on disk.
    """

    # Safegard to avoid to save something on streamlit server
    if os.getenv('ENV') == 'streamlit': 
        return

    # Extract configuration from state, and write it to disk
    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
        file.write(unload_config())

    # Clear caches
    st.cache_data.clear()
    st.cache_resource.clear()


def read_config() -> None:
    """
    Load default configuration.
    If ENV VAR "ENV" is set to "streamlit", does nothing more.
    Otherwise, load configuration.
    """

    # Put default configuration to state
    parse_defaults()

    # Safegard: check if we are on streamlit or not
    if os.getenv('ENV') == 'streamlit': 
        return 
    
    # Read and load from disk
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            content = file.read()

        # Put configuration to state
        load_config(content)
    