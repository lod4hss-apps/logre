from typing import List, Dict
import streamlit as st
from os import getenv
from os.path import exists as path_exists
from pathlib import Path
from subprocess import check_output, CalledProcessError
from yaml import safe_load, dump
from graphly.schema import Prefixes, Prefix, Resource, Property
from streamlit import session_state as state, query_params
from schema.data_bundle import DataBundle
from schema.endpoint import Endpoint


##### INTERNAL HELPERS #####

def __build_endpoint_label(endpoint: Endpoint) -> str:
    """
    Build a human readable endpoint label for selectors.
    """
    label = endpoint.name or endpoint.url or 'Unknown endpoint'
    username = endpoint.username
    if username:
        return f"{label} ({endpoint.technology}, {username})"
    return f"{label} ({endpoint.technology})"


def __get_endpoint_by_key(endpoint_key: str) -> Endpoint | None:
    """
    Return the endpoint matching the provided key, if any.
    """
    for endpoint in state.get('endpoints', []):
        if endpoint.key == endpoint_key:
            return endpoint
    return None


def __ensure_active_selection() -> None:
    """
    Ensure the session always references a valid endpoint / data bundle pair.
    """
    endpoints = get_endpoints()
    if not endpoints:
        state.pop('endpoint_key', None)
        state.pop('data_bundle', None)
        __clear_caches()
        return

    endpoint_key = state.get('endpoint_key')
    if not endpoint_key or not __get_endpoint_by_key(endpoint_key):
        endpoint_key = endpoints[0].key
        state['endpoint_key'] = endpoint_key

    current_db = state.get('data_bundle')
    bundles = get_data_bundles_for_endpoint(endpoint_key)

    if bundles:
        if current_db and current_db in bundles:
            return

        default_db = state.get('default_data_bundle')
        if default_db and default_db in bundles:
            set_data_bundle(default_db)
            return

        set_data_bundle(bundles[0])
    else:
        state.pop('data_bundle', None)
        __clear_caches()


def __reattach_bundles_to_endpoints() -> None:
    """
    Rebind every Data Bundle to the currently stored endpoints (needed after endpoint edits).
    """
    endpoints_map = {endpoint.key: endpoint for endpoint in get_endpoints()}
    for data_bundle in get_data_bundles():
        endpoint = endpoints_map.get(data_bundle.endpoint_key)
        if endpoint:
            data_bundle.attach_endpoint(endpoint)


def __clear_caches() -> None:
    """Clear Streamlit caches when switching endpoints/bundles."""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass



##### PATHS #####

VERSION_FILE_PATH = getenv('LOGRE_VERSION_FILE')
if not VERSION_FILE_PATH:
    for candidate in ('./VERSION', './version'):
        if Path(candidate).exists():
            VERSION_FILE_PATH = candidate
            break
    else:
        VERSION_FILE_PATH = './VERSION'
CONFIG_FILE_PATH = getenv('LOGRE_CONFIG_PATH', './logre-config.yaml')
DEFAULT_CONFIG_FILE_PATH = getenv('LOGRE_DEFAULT_CONFIG_PATH', './logre-config-default.txt')
DEFAULTS_PREFIXES = getenv('LOGRE_DEFAULTS_PREFIXES', './defaults/prefixes.yaml')
DEFAULTS_SPARQL_QUERIES = getenv('LOGRE_DEFAULTS_SPARQL_QUERIES', './defaults/sparql-queries.yaml')

# Change config path if Logre runs from DEV branch
branch_name = None
skip_branch_detection = getenv('LOGRE_SKIP_BRANCH_DETECTION') == '1'
if not skip_branch_detection and getenv('LOGRE_CONFIG_PATH') is None and Path('.git').exists():
    try:
        branch_name = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    except (CalledProcessError, FileNotFoundError):
        branch_name = None

if branch_name == 'dev':
    CONFIG_FILE_PATH = './logre-config-dev.yaml'


def __load_yaml_file(path: str):
    if not Path(path).exists():
        return None
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read().strip()
    if not content:
        return None
    return safe_load(content)


def __default_prefix_entries() -> List[Prefix]:
    entries = __load_yaml_file(DEFAULTS_PREFIXES) or []
    return [Prefix(item.get('short'), item.get('long')) for item in entries]


def __ensure_endpoint_prefixes(endpoints: List[Endpoint]) -> bool:
    """
    Ensure every endpoint includes the default prefixes.
    """
    default_prefixes = __default_prefix_entries()
    changed = False
    for endpoint in endpoints:
        existing = set(prefix.short for prefix in endpoint.prefixes)
        for prefix in default_prefixes:
            if prefix.short not in existing:
                endpoint.prefixes.add(Prefix(prefix.short, prefix.long))
                changed = True
    return changed


def __normalize_endpoint_entries(raw) -> List[Endpoint]:
    if not raw:
        return []
    entries: List[dict]
    if isinstance(raw, dict):
        entries = []
        for key, value in raw.items():
            entry = dict(value or {})
            entry.setdefault('key', key)
            entries.append(entry)
    else:
        entries = list(raw)
    return [Endpoint.from_dict(entry) for entry in entries]


def __normalize_bundle_entries(raw) -> List[dict]:
    if not raw:
        return []
    if isinstance(raw, dict):
        entries = []
        for key, value in raw.items():
            entry = dict(value or {})
            entry.setdefault('key', key)
            entries.append(entry)
        return entries
    return list(raw)


def __legacy_bundle_signature(bundle: dict) -> str:
    technology = bundle.get('endpoint_technology') or ''
    url = bundle.get('endpoint_url') or ''
    username = bundle.get('username') or ''
    return f"{technology}|{url}|{username}"


def __migrate_legacy_configuration(config: dict) -> tuple[List[Endpoint], List[dict], str | None]:
    """
    Build endpoint entries + bundle dicts from the legacy (pre-refactor) configuration.
    """
    legacy_prefixes = config.get('prefixes', [])
    prefix_objects = Prefixes([Prefix(p.get('short'), p.get('long')) for p in legacy_prefixes]) if legacy_prefixes else Prefixes()

    endpoints_by_signature: Dict[str, Endpoint] = {}
    bundles: List[dict] = []

    for bundle in config.get('data_bundles', []):
        signature = __legacy_bundle_signature(bundle)
        if signature not in endpoints_by_signature:
            endpoint_name = bundle.get('endpoint_url') or bundle.get('name') or 'Endpoint'
            endpoint = Endpoint(
                name=endpoint_name,
                technology=bundle.get('endpoint_technology'),
                url=bundle.get('endpoint_url'),
                username=bundle.get('username'),
                password=bundle.get('password'),
                prefixes=Prefixes(prefix_objects.prefix_list.copy()) if prefix_objects else Prefixes(),
            )
            endpoints_by_signature[signature] = endpoint

        endpoint = endpoints_by_signature[signature]
        bundles.append({
            'name': bundle.get('name'),
            'base_uri': bundle.get('base_uri'),
            'endpoint_key': endpoint.key,
            'model_framework': bundle.get('model_framework'),
            'prop_type_uri': bundle.get('prop_type_uri'),
            'prop_label_uri': bundle.get('prop_label_uri'),
            'prop_comment_uri': bundle.get('prop_comment_uri'),
            'graph_data_uri': bundle.get('graph_data_uri'),
            'graph_model_uri': bundle.get('graph_model_uri'),
            'graph_metadata_uri': bundle.get('graph_metadata_uri'),
        })

    return list(endpoints_by_signature.values()), bundles, config.get('default_data_bundle')


def get_default_endpoint_prefixes() -> Prefixes:
    """
    Return the default prefix template used when creating new endpoints.
    """
    if 'default_endpoint_prefixes' not in state:
        state['default_endpoint_prefixes'] = Prefixes(__default_prefix_entries())
    return state['default_endpoint_prefixes']


def __parse_configuration(config: dict) -> tuple[List[Endpoint], List[dict], str | None]:
    """
    Parse the configuration dictionary and return endpoints, bundles and the default bundle key.
    """
    endpoints_raw = config.get('endpoints')

    if endpoints_raw:
        endpoints = __normalize_endpoint_entries(endpoints_raw)
        bundles = __normalize_bundle_entries(config.get('data_bundles', []))
        default_bundle_key = config.get('default_data_bundle')
    else:
        endpoints, bundles, default_bundle_key = __migrate_legacy_configuration(config)

    __ensure_endpoint_prefixes(endpoints)
    return endpoints, bundles, default_bundle_key


def __instantiate_data_bundles(bundles_raw: List[dict], endpoints: List[Endpoint]) -> List[DataBundle]:
    """
    Instantiate DataBundle objects from dictionaries.
    """
    data_bundles: List[DataBundle] = []
    endpoints_map = {endpoint.key: endpoint for endpoint in endpoints}

    for bundle in bundles_raw:
        endpoint_key = bundle.get('endpoint_key') or bundle.get('endpoint')
        if not endpoint_key:
            continue
        endpoint = endpoints_map.get(endpoint_key)
        if not endpoint:
            continue
        data_bundles.append(DataBundle.from_dict(bundle, endpoint, endpoint.prefixes))

    return data_bundles


def __merge_default_queries() -> bool:
    """
    Ensure default SPARQL queries exist alongside user-defined ones.
    """
    default_queries = __load_yaml_file(DEFAULTS_SPARQL_QUERIES) or []
    if not default_queries:
        return False

    loaded_queries = get_sparql_queries()
    have_queries = set(query[0] for query in loaded_queries)
    changed = False
    for query in default_queries:
        if query[0] not in have_queries:
            loaded_queries.append(query)
            changed = True

    if changed:
        set_sparql_queries(loaded_queries)
    return changed

##### VERSION #####
# Version is only on read mode, no setter needed

def get_version() -> str:
    """
    Retrieve the application version from the session state.

    If the version is not already stored in the session state, it is read from
    the version file and cached for future calls.

    Returns:
        str: The application version.
    """
    # If the version is not yet loaded
    if 'version' not in state:
        # Read the version and set it into state
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as file:
            state['version'] = file.read()
    return state['version']



##### TOAST #####

def set_toast(text: str, icon: str = None) -> None:
    """
    Set a toast notification message in the session state.

    Args:
        text (str): The message to display in the toast.
        icon (str, optional): An optional icon identifier to display alongside the toast.
    """
    state['toast-text'] = text
    if icon: state['toast-icon'] = icon


def get_toast() -> tuple[str, str]:
    """
    Retrieve the toast notification message and icon from the session state.

    Returns:
        tuple[str, str]: A tuple containing the toast message text and the icon.
                        Each element may be None if not set.
    """
    text = state['toast-text'] if 'toast-text' in state else None
    icon = state['toast-icon'] if 'toast-icon' in state else None
    return text, icon


def clear_toast() -> None:
    """
    Clear the toast notification message and icon from the session state.
    """
    if 'toast-text' in state: del state['toast-text']
    if 'toast-icon' in state: del state['toast-icon']



##### QUERY PARAMS #####

def set_query_params(query_param_keys: List[str]) -> None:
    """
    Update the query parameters based on the current session state.

    For each key in `query_param_keys`, the corresponding value is retrieved
    from the session state and set in the query parameters if available.

    Args:
        query_param_keys (List[str]): A list of query parameter keys to update.
                                    Supported keys are "endpoint", "db", "uri".
    """
    # Endpoint key: from state to query param
    if 'endpoint' in query_param_keys:
        endpoint_key = get_endpoint_key()
        if endpoint_key:
            query_params['endpoint'] = endpoint_key
        elif 'endpoint' in query_params:
            del query_params['endpoint']

    # Data bundle: from state to query param
    if 'db' in query_param_keys:
        db = get_data_bundle()
        if db:
            query_params['db'] = db.key
        elif 'db' in query_params:
            del query_params['db']

    # Entity URI: from state to query param
    if 'uri' in query_param_keys:
        uri = get_entity_uri()
        if uri:
            query_params['uri'] = uri
        elif 'uri' in query_params:
            del query_params['uri']


def parse_query_params() -> None:
    """
    Parse query parameters and update the session state accordingly.

    For each recognized query parameter ("endpoint", "db", "uri"), the corresponding
    value is retrieved from `query_params` and stored in the session state.

    - "endpoint": Matches the provided key with available endpoints and sets the selected endpoint.
    - "db": Matches the provided key with available data bundles and sets the selected bundle.
    - "uri": Sets the current entity URI.
    """
    # Endpoint: from query param to state
    if 'endpoint' in query_params:
        endpoint_key = query_params['endpoint']
        available_endpoints = [group['key'] for group in get_endpoint_groups()]
        if endpoint_key in available_endpoints:
            set_endpoint_key(endpoint_key)

    # Data bundle: from query param to state
    if 'db' in query_params:
        data_bundle = next((db for db in get_data_bundles() if db.key == query_params['db']), None)
        if data_bundle:
            set_data_bundle(data_bundle)

    # Entity URI: from query param to state
    if 'uri' in query_params:
        uri = query_params['uri']
        set_entity_uri(uri)



##### CONFIGURATION #####    

def load_config() -> None:
    """
    Load the application configuration into the session state.

    If the configuration has not yet been loaded, it is read from the config 
    file if present, otherwise the default one. YAML is used to parse the 
    file, and the following values are extracted:

    - Prefixes: Stored as a `Prefixes` object.
    - Data bundles: Loaded into the session state, using parsed prefixes.
    - Default data bundle: Stored if specified.
    - SPARQL queries: Loaded into the session state if defined.
    """
    if 'has_config' in state:
        return

    raw_config = {}
    if path_exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as file:
            raw_config = safe_load(file.read()) or {}

    endpoints, bundles_raw, default_bundle_key = __parse_configuration(raw_config)
    set_endpoints(endpoints)

    data_bundles = __instantiate_data_bundles(bundles_raw, endpoints)
    set_data_bundles(data_bundles)

    if default_bundle_key:
        default_db = next((db for db in data_bundles if db.key == default_bundle_key), None)
        if default_db:
            set_default_data_bundle(default_db)

    queries = raw_config.get('sparql_queries', [])
    set_sparql_queries(queries)

    if raw_config.get('default_endpoint'):
        set_endpoint_key(raw_config['default_endpoint'])

    changed = __merge_default_queries()
    if changed:
        save_config()

    __ensure_active_selection()
    state['has_config'] = True


def save_config() -> None:
    """
    Save the current session state configuration to the config file.
    """
    default_db =  get_default_data_bundle()
    default_endpoint_key = get_endpoint_key()

    # Gather config
    config = {
        'endpoints': [endpoint.to_dict() for endpoint in get_endpoints()],
        'data_bundles': [db.to_dict() for db in get_data_bundles()],
        'default_data_bundle': default_db.key if default_db else None,
        'default_endpoint': default_endpoint_key,
        'sparql_queries': get_sparql_queries()
    }

    # To YAML string
    content = dump(config)

    # Write the config to disk
    with open(CONFIG_FILE_PATH, 'w') as file:
        file.write(content)



##### ENDPOINTS #####

def get_endpoints() -> List[Endpoint]:
    """
    Retrieve the list of endpoints from the session state.
    """
    if 'endpoints' in state:
        return state['endpoints']
    return []


def set_endpoints(endpoints: List[Endpoint]) -> None:
    """
    Store endpoints in the session state and keep selections in sync.
    """
    state['endpoints'] = endpoints
    __reattach_bundles_to_endpoints()
    __ensure_active_selection()


def update_endpoint(old_endpoint: Endpoint | None, new_endpoint: Endpoint | None) -> None:
    """
    Add, remove or update an endpoint and persist the configuration.
    """
    endpoints = get_endpoints()

    if old_endpoint is None and new_endpoint is not None:
        endpoints.append(new_endpoint)
    elif new_endpoint is None and old_endpoint is not None:
        endpoints = [endpoint for endpoint in endpoints if endpoint.key != old_endpoint.key]
    elif old_endpoint is not None and new_endpoint is not None:
        idx = next(i for i, endpoint in enumerate(endpoints) if endpoint.key == old_endpoint.key)
        endpoints[idx] = new_endpoint

    set_endpoints(endpoints)
    save_config()


def get_endpoint(endpoint_key: str | None = None) -> Endpoint | None:
    """
    Retrieve a specific endpoint by key (defaults to the active one).
    """
    key = endpoint_key or get_endpoint_key()
    if not key:
        return None
    return __get_endpoint_by_key(key)


##### DATA BUNDLES #####

def get_data_bundles() -> List[DataBundle]:
    """
    Retrieve the list of data bundles from the session state, ensuring the configuration is loaded.

    Returns:
        List[DataBundle]: A list of data bundle objects stored in the session state.
    """
    if 'data_bundles' in state:
        return state['data_bundles']
    else:
        return []


def set_data_bundles(dbs: List[DataBundle]) -> None:
    """
    Stores the provided data bundles in the application state.

    Args:
        dbs (List[DataBundle]): List of data bundle objects to be saved.

    Returns:
        None
    """
    state['data_bundles'] = dbs
    __ensure_active_selection()


def get_data_bundle() -> DataBundle | None:
    """
    Retrieve the currently selected data bundle from the session state.

    If no data bundle is selected, the default data bundle is returned if available.
    Returns None if no selection or default exists.

    Returns:
        DataBundle | None: The selected data bundle, or None if not found.
    """
    # If there is none in state
    if 'data_bundle' not in state:
        __ensure_active_selection()
    return state.get('data_bundle')
    

def set_data_bundle(data_bundle: DataBundle) -> None:
    """
    Set the active data bundle in the session state and load its associated model.

    Args:
        data_bundle (DataBundle): The data bundle to set as active.
    """
    state['data_bundle'] = data_bundle
    state['endpoint_key'] = data_bundle.endpoint_key

    __clear_caches()

    # When a data bundle is chosen, load its model
    data_bundle.load_model()


def get_endpoint_groups() -> List[Dict[str, object]]:
    """
    Build endpoint group information based on configured data bundles.

    Returns:
        List[dict]: Each dict contains "key", "label" and "data_bundles".
    """
    groups: List[Dict[str, object]] = []
    endpoints = get_endpoints()
    for endpoint in endpoints:
        bundles = [db for db in get_data_bundles() if db.endpoint_key == endpoint.key]
        groups.append({
            'key': endpoint.key,
            'label': __build_endpoint_label(endpoint),
            'endpoint': endpoint,
            'data_bundles': bundles,
        })
    return sorted(groups, key=lambda endpoint: endpoint['label'])


def get_endpoint_key() -> str | None:
    """
    Retrieve the currently selected endpoint key from the session state.
    """
    if 'endpoint_key' not in state:
        endpoints = get_endpoints()
        if len(endpoints) == 1:
            set_endpoint_key(endpoints[0].key)
    return state.get('endpoint_key')


def set_endpoint_key(endpoint_key: str) -> None:
    """
    Set the active endpoint in session state. If the current Data Bundle does not belong
    to this endpoint, the first bundle from that endpoint is selected.
    """
    if state.get('endpoint_key') == endpoint_key:
        return

    state['endpoint_key'] = endpoint_key
    __ensure_active_selection()


def get_data_bundles_for_endpoint(endpoint_key: str) -> List[DataBundle]:
    """
    Return all data bundles assigned to the provided endpoint key.
    """
    return [db for db in get_data_bundles() if db.endpoint_key == endpoint_key]


def update_data_bundle(old_db: DataBundle | None, new_db: DataBundle | None) -> None:
    """
    Add, remove, or update a data bundle in the session state and save the configuration.

    Args:
        old_db (DataBundle | None): The existing data bundle to update or remove. If None, a new data bundle is added.
        new_db (DataBundle | None): The new data bundle to add or replace the old one. If None, the old data bundle is removed.
    """
    # Create a new Data Bundle
    if old_db is None:
        state['data_bundles'].append(new_db)

    # Remove a Data Bundle
    elif new_db is None:
        state['data_bundles'] = [db for db in state['data_bundles'] if db.key != old_db.key]

    # Update a Data Bundle
    else:
        db_index = next(i for i, db in enumerate(state['data_bundles']) if db.key == old_db.key)
        state['data_bundles'][db_index] = new_db

    # Write to disk
    save_config()
    __ensure_active_selection()


def get_default_data_bundle() -> DataBundle | None:
    """
    Retrieve the key of the default data bundle from the session state.

    Returns:
        str: The default data bundle key, or an empty string if not set.
    """
    if 'default_data_bundle' in state:
        return state['default_data_bundle']
    else:
        return None


def set_default_data_bundle(db: DataBundle) -> None:
    """
    Set the default data bundle in the session state and save the configuration.

    Args:
        db (DataBundle): The data bundle to set as the default.
    """
    state['default_data_bundle'] = db
    save_config()
    __ensure_active_selection()



##### SPARQL QUERIES #####

def get_sparql_queries() -> List[List[str]]:
    """
    Retrieve the list of saved SPARQL queries from the session state.

    Returns:
        List[List[str]]: A list of SPARQL queries, where each query is represented as a list of strings.
                        Returns an empty list if no queries are saved.
    """
    if 'sparql_queries' in state:
        return state['sparql_queries']
    else:
        return []
    

def set_sparql_queries(queries: List[List[str]]) -> None:
    """
    Stores the provided SPARQL queries in the application state.

    Args:
        queries (List[List[str]]): A list of SPARQL query groups, where each group is a list of query strings.

    Returns:
        None
    """
    state['sparql_queries'] = queries


def get_sparql_query() -> str:
    """
    Retrieve the currently active SPARQL query from the session state.

    If no query is currently selected, the first saved query (if any) is set as active.
    Returns an empty string if no queries are available.

    Returns:
        str: The name of the active SPARQL query.
    """
    if 'sparql_query' in state:
        return state['sparql_query']
    
    # If none is selected
    else:
        # And if there is any in the config
        queries = get_sparql_queries()

        if len(queries): 
            # Set the first one as selected
            first_name = queries[0][0]
            set_sparql_query(first_name)
            return first_name
        else: 
            return ''


def set_sparql_query(name: str) -> None:
    """
    Set the active SPARQL query in the session state.

    Args:
        name (str): The name of the SPARQL query to set as active.
    """
    state['sparql_query'] = name
    

def update_sparql_query(sq: List[str]) -> None:
    """
    Add a new SPARQL query or update an existing one in the session state and save the configuration.

    Args:
        sq (List[str]): The SPARQL query to add or update, where the first element is the query name.
    """
    # List all existing SPARQL queries
    all_queries_names = [sq[0] for sq in state['sparql_queries']]

    # If it is a creation
    if sq[0] not in all_queries_names:
        state['sparql_queries'].append(sq)

    # If it is an update
    else:
        sparql_query_index = all_queries_names.index(sq[0])
        state['sparql_queries'][sparql_query_index] = sq
    
    # Write to disk
    save_config()


def delete_sparql_query(sq_name: str) -> None:
    """
    Delete a SPARQL query from the session state and save the configuration.

    Removes the query with the given name from the list of saved queries and
    clears the currently selected SPARQL query, which is required for deletion.

    Args:
        sq_name (str): The name of the SPARQL query to delete.
    """
    # Remove it from list
    state['sparql_queries'] = [sq for sq in state['sparql_queries'] if sq[0] != sq_name]

    # Remove selected one. 
    # How Logre is built makes it so that when deleting a query, it HAS to be selected
    del state['sparql_query']

    # Write on disk
    save_config()


def set_last_executed_sparql_id(id: str) -> None:
    """
    Set the ID of the last executed SPARQL query.

    Args:
        id (str): The identifier of the executed SPARQL query.

    Returns:
        None
    """
    state['last_sparql_executed_id'] = id


def get_last_executed_sparql_id() -> str:
    """
    Retrieve the ID of the last executed SPARQL query.

    Returns:
        str | None: The identifier of the last executed SPARQL query,
        or None if no query has been executed yet.
    """
    if 'last_sparql_executed_id' in state: 
        return state['last_sparql_executed_id']
    else:
        return None


##### SELECTED ENTITY #####

def get_entity_uri() -> str:
    """
    Retrieve the currently selected entity URI from the session state.

    Returns:
        str | None: The entity URI if set, otherwise None.
    """
    if 'entity_uri' not in state:
        return None
    return state['entity_uri']


def set_entity_uri(uri: str) -> None:
    """
    Set the current entity URI in the session state.

    Args:
        uri (str): The entity URI to store.
    """
    state['entity_uri'] = uri



##### FIELDS #####

def get_offset(entity_uri: str, property_key: str) -> int:
    """
    Retrieve the offset value for a specific entity and property from the session state.

    Args:
        entity_uri (str): The URI of the entity.
        property_key (str): The property key associated with the offset.

    Returns:
        int: The stored offset value, or 0 if not set.
    """
    key = f'offset_{entity_uri}_{property_key}'
    if key not in state: 
        return 0
    else:
        return state[f'offset_{entity_uri}_{property_key}']
    

def set_offset(entity_uri: str, property_key: str, value: int) -> None:
    """
    Set the offset value for a specific entity and property in the session state.

    Args:
        entity_uri (str): The URI of the entity.
        property_key (str): The property key associated with the offset.
        value (int): The offset value to store.
    """
    state[f'offset_{entity_uri}_{property_key}'] = value


    
##### ENTITY CHART INCOMING #####

def entity_chart_inc_get_list() -> List[Resource]:
    """
    Retrieve the list of incoming entities for charting from the session state.

    Returns:
        List[Resource]: A list of incoming entities, or an empty list if none are set.
    """
    if 'chart_entity_inc_list' in state:
        return state['chart_entity_inc_list']
    else: 
        return []
    

def entity_chart_inc_list_add(entity: Resource) -> None:
    """
    Add an incoming entity to the chart's incoming entity list in the session state.

    Ensures that the entity is not added more than once.

    Args:
        entity (Resource): The incoming entity to add.
    """
    if 'chart_entity_inc_list' in state:
        has_entities = set([e.uri for e in state['chart_entity_inc_list']])
        if entity.uri not in has_entities:
            state['chart_entity_inc_list'].append(entity)
    else:
        state['chart_entity_inc_list'] = [entity]
        

def entity_chart_inc_list_remove(entity: Resource) -> None:
    """
    Remove an incoming entity from the chart's incoming entity list in the session state.

    Args:
        entity (Resource): The incoming entity to remove.
    """
    if 'chart_entity_inc_list' in state:
        state['chart_entity_inc_list'] = [resource for resource in state['chart_entity_inc_list'] if resource.uri != entity.uri]


def entity_chart_inc_list_init(entity: Resource) -> None:
    """
    Initialize the chart's incoming entity list with a given entity.

    Prevents re-initialization if the same entity is already initialized,
    and replaces the list if a different entity is provided.

    Args:
        entity (Resource): The entity to initialize the incoming entity list with.
    """
    # If the initialized one is the same, do not re-initialize:
    # User might have changed the Fetched selection (incoming / outgoing)
    # And this prevent to st.rerun() indefinitly
    initiated = entity_chart_get_inc_initialized()
    if initiated and initiated.uri == entity.uri:
        return
    
    # If already been initialized, check if it is the same or not
    if 'chart_entity_inc_list' in state:
        has_entities = set([e.uri for e in state['chart_entity_inc_list']])
        if entity.uri not in has_entities:
            # If it is another one, replace it
            state['chart_entity_inc_list'] = [entity]
            entity_chart_set_inc_initialized(entity)
    else:
        # If it is first initialization, set it
        entity_chart_inc_list_add(entity)
        entity_chart_set_inc_initialized(entity)


def entity_chart_set_inc_initialized(entity: Resource) -> None:
    """
    Mark a specific entity as the initialized incoming entity for the chart.

    Args:
        entity (Resource): The entity to mark as initialized.
    """
    state['chart_entity_inc_initialized'] = entity
    

def entity_chart_get_inc_initialized() -> Resource | None:
    """
    Retrieve the entity marked as the initialized incoming entity for the chart.

    Returns:
        Resource | None: The initialized incoming entity, or None if not set.
    """
    if 'chart_entity_inc_initialized' in state:
        return state['chart_entity_inc_initialized']
    else:
        return None



##### ENTITY CHART OUTGOING #####

def entity_chart_out_get_list() -> List[Resource]:
    """
    Retrieve the list of outgoing entities for charting from the session state.

    Returns:
        List[Resource]: A list of outgoing entities, or an empty list if none are set.
    """
    if 'chart_entity_out_list' in state:
        return state['chart_entity_out_list']
    else: 
        return []

    
def entity_chart_out_list_add(entity: Resource) -> None:
    """
    Add an outgoing entity to the chart's outgoing entity list in the session state.

    Ensures that the entity is not added more than once.

    Args:
        entity (Resource): The outgoing entity to add.
    """
    if 'chart_entity_out_list' in state:
        has_entities = set([e.uri for e in state['chart_entity_out_list']])
        if entity.uri not in has_entities:
            state['chart_entity_out_list'].append(entity)
    else:
        state['chart_entity_out_list'] = [entity]


def entity_chart_out_list_remove(entity: Resource) -> None:
    """
    Remove an outgoing entity from the chart's outgoing entity list in the session state.

    Args:
        entity (Resource): The outgoing entity to remove.
    """
    if 'chart_entity_out_list' in state:
        state['chart_entity_out_list'] = [resource for resource in state['chart_entity_out_list'] if resource.uri != entity.uri]


def entity_chart_out_list_init(entity: Resource) -> None:
    """
    Initialize the chart's outgoing entity list with a given entity.

    Prevents re-initialization if the same entity is already initialized,
    and replaces the list if a different entity is provided.

    Args:
        entity (Resource): The entity to initialize the outgoing entity list with.
    """
    # If the initialized one is the same, do not re-initialize:
    # User might have changed the Fetched selection (incoming / outgoing)
    # And this prevent to st.rerun() indefinitly
    initiated = entity_chart_get_out_initialized()
    if initiated and initiated.uri == entity.uri:
        return
    
    # If already been initialized, check if it is the same or not
    if 'chart_entity_out_list' in state:
        has_entities = set([e.uri for e in state['chart_entity_out_list']])
        if entity.uri not in has_entities:
            # If it is another one, replace it
            state['chart_entity_out_list'] = [entity]
            entity_chart_set_out_initialized(entity)
    else:
        # If it is first initialization, set it
        entity_chart_out_list_add(entity)
        entity_chart_set_out_initialized(entity)


def entity_chart_set_out_initialized(entity: Resource) -> None:
    """
    Mark a specific entity as the initialized outgoing entity for the chart.

    Args:
        entity (Resource): The entity to mark as initialized.
    """
    state['chart_entity_out_initialized'] = entity


def entity_chart_get_out_initialized() -> Resource | None:
    """
    Retrieve the entity marked as the initialized outgoing entity for the chart.

    Returns:
        Resource | None: The initialized outgoing entity, or None if not set.
    """
    if 'chart_entity_out_initialized' in state:
        return state['chart_entity_out_initialized']
    else:
        return None



##### DATA TABLES #####

def data_table_set_page(class_uri: str, page_nb: int) -> None:
    """
    Set the current page number for a data table associated with a specific class URI.

    Args:
        class_uri (str): The URI of the class for which the page number is being set.
        page_nb (int): The page number to set.
    """
    state[f'data_table_page_{class_uri}'] = page_nb


def data_table_get_page(class_uri: str) -> int:
    """
    Retrieve the current page number for a data table associated with a specific class URI.

    Args:
        class_uri (str): The URI of the class for which the page number is retrieved.

    Returns:
        int: The current page number, or 1 if not set.
    """
    key = f'data_table_page_{class_uri}'
    if key in state: 
        return state[key]
    else:
        return 1



##### DIALOG ENTITY CREATION #####

def entity_creation_set_input_number(property: Property, input_number: int) -> None:
    """
    Set the input number for a specific property during entity creation.

    Args:
        property (Property): The property for which the input number is set.
        input_number (int): The input number to store.
    """
    key = f"entity-creation-input-number-{property.get_key()}"
    state[key] = input_number


def entity_creation_get_input_number(property: Property) -> int:
    """
    Retrieve the input number for a specific property during entity creation.

    Args:
        property (Property): The property for which the input number is retrieved.

    Returns:
        int: The stored input number, or 1 if not set.
    """
    key = f"entity-creation-input-number-{property.get_key()}"
    if key in state: return state[key]
    else: return 1



##### DIALOG ENTITY EDITION #####

def entity_edition_set_input_number(property: Property, input_number: int) -> None:
    """
    Set the input number for a specific property during entity edition.

    Args:
        property (Property): The property for which the input number is set.
        input_number (int): The input number to store.
    """
    key = f"entity-edition-input-number-{property.get_key()}"
    state[key] = input_number

    
def entity_edition_get_input_number(property: Property) -> int:
    """
    Retrieve the input number for a specific property during entity edition.

    Args:
        property (Property): The property for which the input number is retrieved.

    Returns:
        int: The stored input number, or 0 if not set.
    """
    key = f"entity-edition-input-number-{property.get_key()}"
    if key in state: return state[key]
    else: return 0
