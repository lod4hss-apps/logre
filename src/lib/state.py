from typing import List
from os.path import exists as path_exists
from os import getenv
from yaml import safe_load, dump
from graphly.schema import Prefixes, Prefix, Resource, Property
from streamlit import session_state as state, query_params
from schema.data_bundle import DataBundle



##### PATHS #####

VERSION_FILE_PATH = './version'
CONFIG_FILE_PATH = './logre-config.yaml'
DEFAULT_CONFIG_FILE_PATH = './logre-config-default.yaml'



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
                                    Supported keys are "db", "uri", and "query".
    """
    # Data bundle: from state to query param
    if 'db' in query_param_keys and 'db' not in query_params:
        db = get_data_bundle()
        if db: query_params['db'] = db.key

    # Entity URI: from state to query param
    if 'uri' in query_param_keys and 'uri' not in query_params:
        uri = get_entity_uri()
        if uri: query_params['uri'] = uri


def parse_query_params() -> None:
    """
    Parse query parameters and update the session state accordingly.

    For each recognized query parameter ("db", "uri", "query"), the corresponding
    value is retrieved from `query_params` and stored in the session state.

    - "db": Matches the provided key with available data bundles and sets the selected bundle.
    - "uri": Sets the current entity URI.
    - "query": Sets the active SPARQL query name.
    """
    # Data bundle: from query param to state
    if 'db' in query_params:
        data_bundle = next(db for db in get_data_bundles() if db.key == query_params['db'])
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
    # If the config is not yet loaded
    if 'has_config' not in state:

        # Read the file on disk, if any, else read default config
        file_to_read = CONFIG_FILE_PATH if path_exists(CONFIG_FILE_PATH) else DEFAULT_CONFIG_FILE_PATH

        # Only load the configuration if the file exists (normal or default one)
        if path_exists(file_to_read):
            with open(file_to_read, 'r', encoding='utf-8') as file:

                # Use YAML to parse the file content
                obj: dict = safe_load(file.read())

                # Extract prefixes
                if 'prefixes' in obj.keys():
                    prefixes = Prefixes([Prefix(p.get('short'), p.get('long')) for p in obj['prefixes']])
                else:
                    prefixes = Prefixes()
                set_prefixes(prefixes)
                
                # Extract Data Bundles
                if 'data_bundles' in obj.keys():
                    dbs = [DataBundle.from_dict(db, state['prefixes']) for db in obj['data_bundles']]
                else:
                    dbs = []
                set_data_bundles(dbs)

                # Extract default Data Bundle
                if "default_data_bundle" in obj.keys():
                    default_db = next(db for _, db in enumerate(get_data_bundles()) if db.key == obj['default_data_bundle'])
                    if default_db: set_default_data_bundle(default_db)
            
                # Extract saved SPARQL Queries
                if 'sparql_queries'in obj.keys():
                    queries = obj['sparql_queries']
                else:
                    queries = []
                set_sparql_queries(queries)

                # Flag to know that state has loaded the configuration file
                state['has_config'] = True


def save_config() -> None:
    """
    Save the current session state configuration to the config file.
    """
    # Gather config
    config = {
        'prefixes': [p.to_dict() for p in get_prefixes()],
        'data_bundles': [db.to_dict() for db in get_data_bundles()],
        'default_data_bundle': get_default_data_bundle().key,
        'sparql_queries': get_sparql_queries()
    }

    # To YAML string
    content = dump(config)

    # Write the config to disk
    with open(CONFIG_FILE_PATH, 'w') as file:
        file.write(content)



##### PREFIXES #####

def get_prefixes() -> Prefixes:
    """
    Retrieve the current prefixes from the session state.

    Returns:
        Prefixes: The stored prefixes object.
    """
    return state['prefixes']


def set_prefixes(prefixes: Prefixes) -> None:
    """
    Stores the given prefixes in the application state.

    Args:
        prefixes (Prefixes): Prefix mappings to be saved.

    Returns:
        None
    """
    state['prefixes'] = prefixes


def update_prefix(old_prefix: Prefix | None, new_prefix: Prefix | None) -> None:
    """
    Add, remove, or update a prefix in the session state and save the configuration.

    Args:
        old_prefix (Prefix | None): The existing prefix to update or remove. If None, a new prefix is added.
        new_prefix (Prefix | None): The new prefix to add or replace the old one. If None, the old prefix is removed.
    """
    # Create a new Prefix
    if old_prefix is None:
        state['prefixes'].add(new_prefix)
    
    # Remove a prefix
    elif new_prefix is None:
        state['prefixes'].remove(old_prefix)

    # Update a prefix
    else:
        for prefix in state['prefixes']:
            if prefix.short == old_prefix.short and prefix.long == old_prefix.long:
                prefix.short = new_prefix.short
                prefix.long = new_prefix.long

    # Write to disk
    save_config()



##### DATA BUNDLES #####

def get_data_bundles() -> List[DataBundle]:
    """
    Retrieve the list of data bundles from the session state, ensuring the configuration is loaded.

    Returns:
        List[DataBundle]: A list of data bundle objects stored in the session state.
    """
    return state['data_bundles']


def set_data_bundles(dbs: List[DataBundle]) -> None:
    """
    Stores the provided data bundles in the application state.

    Args:
        dbs (List[DataBundle]): List of data bundle objects to be saved.

    Returns:
        None
    """
    state['data_bundles'] = dbs


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
        # Return the default one, only if it exists
        db = get_default_data_bundle()
        db.load_model()
        return db
    else:
        return state['data_bundle']
    

def set_data_bundle(data_bundle: DataBundle) -> None:
    """
    Set the active data bundle in the session state and load its associated model.

    Args:
        data_bundle (DataBundle): The data bundle to set as active.
    """
    state['data_bundle'] = data_bundle

    # When a data bundle is chosen, load its model
    data_bundle.load_model()


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
    all_queries_names = set([sq[0] for sq in state['sparql_queries']])

    # If it is a creation
    if sq[0] not in all_queries_names:
        state['sparql_queries'].append(sq)

    # If it is an update
    else:
        sparql_query_index = all_queries_names.index(sq[0])
        state['spraql_queries'][sparql_query_index] = sq
    
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