from typing import Any
import os
import toml
from schema import Endpoint, Query, Prefix
import lib.state as state

CONFIG_PATH = './logre-config.toml'


def unload_config() -> str:
    """Reads the state to create the config object, and returns the TOML string version of it."""

    # From state
    all_queries = state.get_queries()
    all_endpoints = state.get_endpoints()
    all_prefixes = state.get_prefixes()

    # Transform into serializable objects
    all_queries = [q.to_dict() for q in all_queries]
    all_endpoints = [e.to_dict() for e in all_endpoints]
    all_prefixes = [p.to_dict() for p in all_prefixes]

    # Build the object to be saved
    config = {
        'all_queries': all_queries, 
        'all_endpoints': all_endpoints,
        'all_prefixes': all_prefixes
    }

    return toml.dumps(config)


def load_config(file_content: str) -> str:
    """From a string (a file content) build a dictionnary, and put all the configuration in state."""

    config = toml.loads(file_content)

    if 'all_queries' in config: 
        # Parse into instances of Query
        all_queries = list(map(lambda obj: Query.from_dict(obj), config['all_queries']))
        state.set_queries(all_queries)
    if 'all_endpoints' in config: 
        # Parse into instances of Endpoint
        all_endpoints = list(map(lambda obj: Endpoint.from_dict(obj), config['all_endpoints']))
        state.set_endpoints(all_endpoints)
    if 'all_prefixes' in config:
        # Parse into instances of Prefix
        all_prefixes = list(map(lambda obj: Prefix.from_dict(obj), config['all_prefixes']))
        state.set_prefixes(all_prefixes)


def save_config() -> None:
    """
    In case Logre is started locally, and there is a config in the root folder, 
    Save the configuration.
    Otherwise, do nothing
    """

    # Safegard to avoid to save something on streamlit server
    if os.getenv('ENV') == 'streamlit': 
        return

    file = open(CONFIG_PATH, 'w')
    file.write(unload_config())
    file.close()


def read_config() -> None:
    """
    In case Logre is started locally, and there is a config in the root folder, 
    Save the configuration.
    Otherwise, do nothing
    """

    # Safegard: check if we are on streamlit or not
    if os.getenv('ENV') == 'streamlit': 
        return 
    
    if os.path.exists(CONFIG_PATH):
        file = open(CONFIG_PATH, 'r')
        load_config(file.read())
        file.close()
