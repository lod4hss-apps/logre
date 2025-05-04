from typing import Any
import os
import yaml
from model import Endpoint, Query, Prefix
import lib.state as state

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

    # Load saved endpoints
    if 'endpoints' in config: 
        # Parse into instances of Endpoint
        all_endpoints = list(map(lambda obj: Endpoint.from_dict(obj), config.get('endpoints', [])))
        state.set_endpoints(all_endpoints)


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


def read_config() -> None:
    """
    In case Logre is started locally, and there is a config in the root folder, 
    Save the configuration.
    Otherwise, do nothing
    """

    # Safegard: check if we are on streamlit or not
    if os.getenv('ENV') == 'streamlit': 
        return 
    
    # Read and load from disk
    if os.path.exists(CONFIG_PATH):
        file = open(CONFIG_PATH, 'r')
        content = file.read()
        file.close()

        load_config(content)
