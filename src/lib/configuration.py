import os
import lib.state as state
import toml

CONFIG_PATH = './logre-config.toml'


def get_config_toml() -> str:

    # From state
    all_queries = state.get_queries()
    all_endpoints = state.get_endpoints()

    # Transform into serializable objects
    all_queries = [q.to_dict() for q in all_queries]
    all_endpoints = [e.to_dict() for e in all_endpoints]

    # Build the object to be saved
    config = {
        'all_queries': all_queries, 
        'all_endpoints': all_endpoints
    }

    return toml.dumps(config)


def save_config() -> None:
    """
    In case Logre is started locally, and there is a config in the root folder, 
    Save the configuration.
    Otherwise, do nothing
    """

    file = open(CONFIG_PATH, 'w')
    file.write(get_config_toml())
    file.close()