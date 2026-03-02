from typing import List, Dict
from datetime import datetime
import os
import re
import shutil
from os.path import exists as path_exists
from pathlib import Path
from yaml import safe_load, dump
from graphly.schema import Prefixes, Prefix, Resource, Property, Sparql
from streamlit import session_state as state, query_params
from schema.data_bundle import DataBundle
from schema.sparql_technologies import get_sparql
from lib.config_paths import get_config_path, get_default_config_path, ensure_parent_dir
from lib.config_migrations import migrate_config_if_needed
from lib.autoconfigure_data_graph import autoconfigure_config


##### PATHS #####

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)

VERSION_FILE_PATH = BASE_DIR + "/version"
VERSION_FALLBACK_PATH = BASE_DIR + "/VERSION"
CONFIG_FILE_PATH = get_config_path()
DEFAULT_CONFIG_PATH = get_default_config_path(BASE_DIR)
DEFAULTS_PREFIXES = BASE_DIR + "/defaults/prefixes.yaml"
DEFAULTS_DATA_BUNDLES = BASE_DIR + "/defaults/data-bundles.yaml"
DEFAULTS_DATA_BUNDLE_DEFAULT = BASE_DIR + "/defaults/default-data-bundle.yaml"
DEFAULTS_SPARQL_QUERIES = BASE_DIR + "/defaults/sparql-queries.yaml"

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def expand_env_value(value: str) -> tuple[str, List[str]]:
    missing: List[str] = []

    def repl(match: re.Match) -> str:
        var = match.group(1)
        env_value = os.getenv(var)
        if env_value is None:
            missing.append(var)
            return match.group(0)
        return env_value

    return ENV_PATTERN.sub(repl, value), missing


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
    if "version" not in state:
        # Read the version and set it into state
        version_path = (
            VERSION_FILE_PATH
            if path_exists(VERSION_FILE_PATH)
            else VERSION_FALLBACK_PATH
        )
        with open(version_path, "r", encoding="utf-8") as file:
            state["version"] = file.read()
    return state["version"]


##### TOAST #####


def set_toast(text: str, icon: str = None) -> None:
    """
    Set a toast notification message in the session state.

    Args:
        text (str): The message to display in the toast.
        icon (str, optional): An optional icon identifier to display alongside the toast.
    """
    state["toast-text"] = text
    if icon:
        state["toast-icon"] = icon


def get_toast() -> tuple[str, str]:
    """
    Retrieve the toast notification message and icon from the session state.

    Returns:
        tuple[str, str]: A tuple containing the toast message text and the icon.
                        Each element may be None if not set.
    """
    text = state["toast-text"] if "toast-text" in state else None
    icon = state["toast-icon"] if "toast-icon" in state else None
    return text, icon


def clear_toast() -> None:
    """
    Clear the toast notification message and icon from the session state.
    """
    if "toast-text" in state:
        del state["toast-text"]
    if "toast-icon" in state:
        del state["toast-icon"]


##### QUERY PARAMS #####


def handle_query_params(required_keys: List[str]) -> None:
    """
    Update the query parameters based on the current session state.

    For each key in `required_keys`, the corresponding value is retrieved
    from the session state and set in the query parameters if available.

    Args:
        required_keys (List[str]): A list of query parameter keys to update.
                                    Supported keys are "db", "uri".
    """

    def _get_query_param_value(name: str) -> str | None:
        if name not in query_params:
            return None
        value = query_params[name]
        if isinstance(value, list):
            return value[0] if value else None
        return value

    # If the 'db' query param is required
    if "db" in required_keys:
        db = get_data_bundle()
        current_db_param = _get_query_param_value("db")
        pending_db_name = state.get("pending_db_name")

        print(
            f"[query] required db | state={db.key if db else None} url={current_db_param}"
        )

        if pending_db_name:
            pending_db = next(
                (db2 for db2 in get_data_bundles() if db2.name == pending_db_name),
                None,
            )
            del state["pending_db_name"]
            if pending_db:
                print(f"[query] apply pending db change: {pending_db.key}")
                set_data_bundle(pending_db)
                query_params["db"] = pending_db.key
                if "uri" in query_params:
                    print(f"[query] purge uri due to db change: {query_params['uri']}")
                    del query_params["uri"]
                if "entity_uri" in state:
                    del state["entity_uri"]
                return

        if current_db_param:
            if not db or db.key != current_db_param:
                data_bundle = next(
                    (db2 for db2 in get_data_bundles() if db2.key == current_db_param),
                    None,
                )
                if data_bundle:
                    print(f"[query] set data bundle from url: {current_db_param}")
                    set_data_bundle(data_bundle)
                    if get_entity_uri() is not None:
                        print("[query] clear entity uri due to db change")
                        if "entity_uri" in state:
                            del state["entity_uri"]
                    if "uri" in query_params:
                        print(
                            f"[query] purge uri due to db change: {query_params['uri']}"
                        )
                        del query_params["uri"]
                elif db:
                    print(f"[query] db param not found, keep state -> {db.key}")
                    query_params["db"] = db.key
        elif db:
            print(f"[query] set db param -> {db.key}")
            query_params["db"] = db.key

    # If the 'uri' query param is required
    if "uri" in required_keys:
        uri = get_entity_uri()
        current_uri_param = _get_query_param_value("uri")

        print(
            f"[query] required uri | state={uri if uri else None} url={current_uri_param}"
        )

        # If it is in state but not in the URL: add it to URL
        if current_uri_param is None and uri is not None:
            print(f"[query] set uri param -> {uri}")
            query_params["uri"] = uri

        # If it is in URL, but not in state: add to state
        elif current_uri_param is not None and uri is None:
            print(f"[query] set entity uri from url: {current_uri_param}")
            set_entity_uri(current_uri_param)


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
    if "has_config" not in state:
        # Initialize state keys for local runs without a config file
        if "prefixes" not in state:
            set_prefixes(Prefixes())
        if "endpoints" not in state:
            set_endpoints([])
        if "data_bundles" not in state:
            set_data_bundles([])

        config_path = (
            CONFIG_FILE_PATH
            if isinstance(CONFIG_FILE_PATH, Path)
            else Path(CONFIG_FILE_PATH)
        )
        default_path = DEFAULT_CONFIG_PATH
        ensure_parent_dir(config_path)

        migrated = migrate_config_if_needed(config_path)
        if migrated:
            set_toast(
                "Configuration migrated to the latest format.",
                icon=":material/info:",
            )

        config_exists = path_exists(config_path)
        config_raw = None
        config_load_issue = False
        repaired = False
        obj: dict = {}

        if not config_exists and default_path and path_exists(default_path):
            try:
                shutil.copyfile(default_path, config_path)
                config_exists = True
                set_toast(
                    f"Configuration created at {config_path}",
                    icon=":material/info:",
                )
            except Exception:
                config_load_issue = True

        if os.getenv("LOGRE_AUTOCONFIGURE_GRAPH") == "1" and config_exists:
            try:
                autoconfigure_config(config_path)
            except Exception:
                set_toast(
                    "Failed to auto-configure data graph.",
                    icon=":material/warning:",
                )

        if config_exists:
            try:
                config_raw = config_path.read_text(encoding="utf-8")
                obj = safe_load(config_raw) or {}
            except Exception:
                config_load_issue = True
                obj = {}

        if not isinstance(obj, dict):
            config_load_issue = True
            obj = {}

        if (
            (not config_exists or config_load_issue)
            and default_path
            and path_exists(default_path)
        ):
            try:
                default_raw = default_path.read_text(encoding="utf-8")
                default_obj = safe_load(default_raw) or {}
                if isinstance(default_obj, dict):
                    obj = default_obj
                    if config_exists:
                        repaired = True
            except Exception:
                pass

        missing_env_vars = set()
        missing_endpoint_urls = []
        endpoints_raw = obj.get("endpoints", [])
        if isinstance(endpoints_raw, list):
            for endpoint in endpoints_raw:
                if not isinstance(endpoint, dict):
                    continue
                for key in ("username", "password", "url"):
                    value = endpoint.get(key)
                    if isinstance(value, str) and "${" in value:
                        new_value, missing = expand_env_value(value)
                        endpoint[key] = new_value
                        missing_env_vars.update(missing)
                url_value = endpoint.get("url")
                if not isinstance(url_value, str) or not url_value.strip():
                    missing_endpoint_urls.append(endpoint.get("name", "(unnamed)"))

        if missing_env_vars:
            missing_list = ", ".join(sorted(missing_env_vars))
            set_toast(
                f"Missing environment variables for endpoint config: {missing_list}",
                icon=":material/warning:",
            )
        if missing_endpoint_urls:
            names = ", ".join(sorted(set(missing_endpoint_urls)))
            set_toast(
                f"Skipping endpoints with missing URL: {names}",
                icon=":material/warning:",
            )

        # Extract SPARQL endpoints
        loaded_endpoints = []
        if not isinstance(endpoints_raw, list):
            endpoints_raw = []
            repaired = True
        for sparql in endpoints_raw:
            try:
                url = sparql.get("url") if isinstance(sparql, dict) else None
                if not isinstance(url, str) or not url.strip():
                    repaired = True
                    continue
                endpoint = get_sparql(sparql)
                loaded_endpoints.append(endpoint)
            except Exception:
                repaired = True
                set_toast(
                    "Skipped an invalid SPARQL endpoint configuration.",
                    icon=":material/warning:",
                )
        set_endpoints(loaded_endpoints)

        # Extract prefixes
        loaded_prefixes = Prefixes()
        seen_prefixes = set()
        prefixes_raw = obj.get("prefixes", [])
        if not isinstance(prefixes_raw, list):
            prefixes_raw = []
            repaired = True
        for prefix in prefixes_raw:
            if isinstance(prefix, dict):
                short = prefix.get("short")
                if short and short not in seen_prefixes:
                    loaded_prefixes.add(Prefix(short, prefix.get("long")))
                    seen_prefixes.add(short)
                else:
                    repaired = True
            else:
                repaired = True
        set_prefixes(loaded_prefixes)

        # Extract Data Bundles
        dbs = []
        bundles_raw = obj.get("data_bundles", [])
        if not isinstance(bundles_raw, list):
            bundles_raw = []
            repaired = True
        for db in bundles_raw:
            if not isinstance(db, dict):
                repaired = True
                continue
            try:
                dbs.append(
                    DataBundle.from_dict(db, state["prefixes"], state["endpoints"])
                )
            except Exception:
                repaired = True
                bundle_name = db.get("name", "(unnamed)")
                endpoint_name = db.get("endpoint_name", "(unknown)")
                set_toast(
                    f"Skipped data bundle '{bundle_name}' (endpoint '{endpoint_name}' not found).",
                    icon=":material/warning:",
                )
        set_data_bundles(dbs)

        # Extract default Data Bundle
        default_db_key = obj.get("default_data_bundle")
        if default_db_key:
            default_db = next(
                (
                    db
                    for _, db in enumerate(get_data_bundles())
                    if db.key == default_db_key
                ),
                None,
            )
            if default_db:
                set_default_data_bundle(default_db)
            else:
                repaired = True
                set_toast(
                    f"Default data bundle '{default_db_key}' not found. Please select another.",
                    icon=":material/warning:",
                )

        # Extract saved SPARQL Queries
        queries = obj.get("sparql_queries", [])
        if not isinstance(queries, list):
            queries = []
            repaired = True
        set_sparql_queries(queries)

        # Load the config version
        config_version = obj.get("version")
        if isinstance(config_version, str) and config_version:
            state["config_version"] = config_version
        else:
            state["config_version"] = "2.1"
            repaired = True

        def backup_config() -> None:
            if not config_raw:
                return
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = f"{config_path}.bak-{timestamp}"
            with open(backup_path, "w", encoding="utf-8") as file:
                file.write(config_raw)

        # Flag to know if something has been added from defaults
        need_save = False

        # Add all prefixes that are in the default, but not in (loaded or not) configuration
        with open(DEFAULTS_PREFIXES, "r", encoding="utf-8") as file:
            # Use YAML to parse the file content
            default_prefixes_raw = safe_load(file.read())

            # Parse Prefixes
            default_prefixes = Prefixes(
                [Prefix(p.get("short"), p.get("long")) for p in default_prefixes_raw]
            )

            # Check if all from default are in state
            loaded_prefixes = get_prefixes()
            have_prefixes = set([p.short for p in loaded_prefixes])
            for prefix in default_prefixes:
                if prefix.short not in have_prefixes:
                    loaded_prefixes.add(prefix)
                    set_prefixes(loaded_prefixes)
                    need_save = True

        # Add all sparql queries that are in the default, but not in (loaded or not) configuration
        with open(DEFAULTS_SPARQL_QUERIES, "r", encoding="utf-8") as file:
            # Use YAML to parse the file content
            default_sparql_queries = safe_load(file.read())

            # Here, there is no need to parse: For the model a SPARQL query is just an array with 2 elements: name, query

            # Check if all from default are in state
            loaded_queries = get_sparql_queries()
            have_queries = set([o[0] for o in loaded_queries])
            for query in default_sparql_queries:
                if query[0] not in have_queries:
                    loaded_queries.append(query)
                    set_sparql_queries(loaded_queries)
                    need_save = True

        # Add all Data Bundles that are in the default, but not in (loaded or not) configuration
        with open(DEFAULTS_DATA_BUNDLES, "r", encoding="utf-8") as file:
            # Use YAML to parse the file content
            default_db_raw = safe_load(file.read())

            # Parse
            default_db = [
                DataBundle.from_dict(obj, state["prefixes"], state["endpoints"])
                for obj in default_db_raw
            ]

            # Check if all from default are in state
            loaded_dbs = get_data_bundles()
            have_dbs = set([o.endpoint for o in loaded_dbs])
            for db in default_db:
                if db.endpoint not in have_dbs:
                    loaded_dbs.append(db)
                    set_data_bundles(loaded_dbs)
                    need_save = True

        # Add the default Data Bundle from the default, if not set in the configuration
        with open(DEFAULTS_DATA_BUNDLE_DEFAULT, "r", encoding="utf-8") as file:
            # Use YAML to parse the file content
            default_db_default = safe_load(file.read())

            # If a defaut Data Bundle is set
            if default_db_default:
                # Find the DataBundle with the right key
                default_db = next(
                    (
                        db
                        for _, db in enumerate(get_data_bundles())
                        if db.key == default_db_default
                    ),
                    None,
                )
                if default_db:
                    set_default_data_bundle(default_db)
                    need_save = True

        # If the default configuration changed the state, then save the configuration
        save_required = need_save or repaired or config_load_issue or not config_exists
        if save_required:
            if config_exists and (repaired or config_load_issue):
                backup_config()
            save_config()

        # Flag to know that state has loaded the configuration file
        state["has_config"] = True


def save_config() -> None:
    """
    Save the current session state configuration to the config file.
    """
    default_db = get_default_data_bundle()

    # Normalize prefixes (unique by short, skip base)
    prefixes_by_short: Dict[str, Prefix] = {}
    for prefix in get_prefixes():
        if not prefix.short or prefix.short == "base":
            continue
        prefixes_by_short[prefix.short] = prefix

    # Gather config
    config = {
        "endpoints": [e.to_dict() for e in get_endpoints()],
        "prefixes": [p.to_dict() for p in prefixes_by_short.values()],
        "data_bundles": [db.to_dict() for db in get_data_bundles()],
        "default_data_bundle": default_db.key if default_db else None,
        "sparql_queries": get_sparql_queries(),
        "version": state["config_version"] if "config_version" in state else None,
    }

    # To YAML string
    content = dump(config, sort_keys=False)

    # Write the config to disk
    config_path = (
        CONFIG_FILE_PATH
        if isinstance(CONFIG_FILE_PATH, Path)
        else Path(CONFIG_FILE_PATH)
    )
    ensure_parent_dir(config_path)
    with open(config_path, "w", encoding="utf-8") as file:
        file.write(content)


##### PREFIXES #####


def get_prefixes() -> Prefixes:
    """
    Retrieve the current prefixes from the session state.

    Returns:
        Prefixes: The stored prefixes object.
    """
    return state["prefixes"]


def set_prefixes(prefixes: Prefixes) -> None:
    """
    Stores the given prefixes in the application state.

    Args:
        prefixes (Prefixes): Prefix mappings to be saved.

    Returns:
        None
    """
    state["prefixes"] = prefixes


def update_prefix(old_prefix: Prefix | None, new_prefix: Prefix | None) -> None:
    """
    Add, remove, or update a prefix in the session state and save the configuration.

    Args:
        old_prefix (Prefix | None): The existing prefix to update or remove. If None, a new prefix is added.
        new_prefix (Prefix | None): The new prefix to add or replace the old one. If None, the old prefix is removed.
    """
    # Create a new Prefix
    if old_prefix is None:
        state["prefixes"].add(new_prefix)

    # Remove a prefix
    elif new_prefix is None:
        state["prefixes"].remove(old_prefix)

    # Update a prefix
    else:
        for prefix in state["prefixes"]:
            if prefix.short == old_prefix.short and prefix.long == old_prefix.long:
                prefix.short = new_prefix.short
                prefix.long = new_prefix.long

    # Write to disk
    save_config()


##### ENDPOINTS #####


def get_endpoints() -> List[Sparql]:
    """
    Retrieve the list of endpoints from the session state, ensuring the configuration is loaded.

    Returns:
        List[Sparql]: A list of Sparql endpoints objects stored in the session state.
    """
    return state["endpoints"]


def set_endpoints(endpoints):
    """
    Stores the provided endpoints in the application state.

    Args:
        endpoints (List[Sparql]): List of Sparql endpoints objects to be saved.

    Returns:
        None
    """
    state["endpoints"] = endpoints


def get_endpoint() -> Sparql | None:
    """
    Retrieve the currently selected SPARQL endpoint from the session state.

    If no SPARQL endpoint is selected, returns None.

    Returns:
        Sparql | None: The selected SPARQL endpoint, or None if not found.
    """
    # If there is none in state
    if "endpoint" not in state:
        return None
    else:
        return state["endpoint"]


def set_endpoint(endpoint: Sparql) -> None:
    """
    Set the active endpoint in the session state.

    Args:
        endpoint (Sparql): The SPARQL endpoint to set as active.
    """
    state["endpoint"] = endpoint


def update_endpoint(old_endpoint: Sparql | None, new_endpoint: Sparql | None) -> None:
    """
    Add, remove, or update an endpoint in the session state and save the configuration.

    Args:
        old_db (Sparql | None): The existing endpoint to update or remove. If None, a new endpoint is added.
        new_db (Sparql | None): The new endpoint to add or replace the old one. If None, the old endpoint is removed.
    """
    # Create a new Data Bundle
    if old_endpoint is None:
        state["endpoints"].append(new_endpoint)

    # Remove a Data Bundle
    elif new_endpoint is None:
        state["endpoints"] = [
            endpoint
            for endpoint in state["endpoints"]
            if endpoint.name != old_endpoint.name
        ]

    # Update a Data Bundle
    else:
        db_index = next(
            i
            for i, endpoint in enumerate(state["endpoints"])
            if endpoint.name == old_endpoint.name
        )
        state["endpoints"][db_index] = new_endpoint

    # Write to disk
    save_config()


def get_endpoint_groups() -> List[Dict[str, object]]:
    """
    Build endpoint group information based on configured data bundles.

    Returns:
        List[dict]: Each dict contains "key", "label" and "data_bundles".
    """
    groups: List[Dict[str, object]] = []
    endpoints = get_endpoints()
    for endpoint in endpoints:
        bundles = [db for db in get_data_bundles() if db.endpoint.key == endpoint.key]
        groups.append(
            {
                "key": endpoint.key,
                "label": endpoint.name,
                "endpoint": endpoint,
                "data_bundles": bundles,
            }
        )
    return sorted(groups, key=lambda endpoint: endpoint["label"])


##### DATA BUNDLES #####


def get_data_bundles() -> List[DataBundle]:
    """
    Retrieve the list of data bundles from the session state, ensuring the configuration is loaded.

    Returns:
        List[DataBundle]: A list of data bundle objects stored in the session state.
    """
    return state["data_bundles"]


def set_data_bundles(dbs: List[DataBundle]) -> None:
    """
    Stores the provided data bundles in the application state.

    Args:
        dbs (List[DataBundle]): List of data bundle objects to be saved.

    Returns:
        None
    """
    state["data_bundles"] = dbs


def get_data_bundle() -> DataBundle | None:
    """
    Retrieve the currently selected data bundle from the session state.

    If no data bundle is selected, the default data bundle is returned if available.
    Returns None if no selection or default exists.

    Returns:
        DataBundle | None: The selected data bundle, or None if not found.
    """
    # If there is none in state
    if "data_bundle" not in state:
        # Return the default one, only if it exists
        db = get_default_data_bundle()
        if db:
            # If the default data bundle is accessed, it is possible that no endpoint is selected
            # (most probably), so set it if it is the case
            if not get_endpoint():
                set_endpoint(db.endpoint)

            return db
    else:
        return state["data_bundle"]


def set_data_bundle(data_bundle: DataBundle) -> None:
    """
    Set the active data bundle in the session state and load its associated model.

    Args:
        data_bundle (DataBundle): The data bundle to set as active.
    """
    state["data_bundle"] = data_bundle

    # When a data bundle is chosen, load its model
    if data_bundle:
        try:
            data_bundle.load_model()
        except Exception as err:
            set_toast(
                f"Failed to load model for data bundle '{data_bundle.name}'.",
                icon=":material/warning:",
            )
            print(f"[data_bundle] load_model failed: {err}")


def update_data_bundle(old_db: DataBundle | None, new_db: DataBundle | None) -> None:
    """
    Add, remove, or update a data bundle in the session state and save the configuration.

    Args:
        old_db (DataBundle | None): The existing data bundle to update or remove. If None, a new data bundle is added.
        new_db (DataBundle | None): The new data bundle to add or replace the old one. If None, the old data bundle is removed.
    """
    # Create a new Data Bundle
    if old_db is None:
        state["data_bundles"].append(new_db)

    # Remove a Data Bundle
    elif new_db is None:
        default_db = get_default_data_bundle()
        if default_db and default_db.key == old_db.key:
            state["default_data_bundle"] = None
        state["data_bundles"] = [
            db for db in state["data_bundles"] if db.key != old_db.key
        ]

    # Update a Data Bundle
    else:
        db_index = next(
            i for i, db in enumerate(state["data_bundles"]) if db.key == old_db.key
        )
        state["data_bundles"][db_index] = new_db

    # Write to disk
    save_config()


def get_default_data_bundle() -> DataBundle | None:
    """
    Retrieve the key of the default data bundle from the session state.

    Returns:
        str: The default data bundle key, or an empty string if not set.
    """
    if "default_data_bundle" in state:
        return state["default_data_bundle"]
    else:
        return None


def set_default_data_bundle(db: DataBundle) -> None:
    """
    Set the default data bundle in the session state and save the configuration.

    Args:
        db (DataBundle): The data bundle to set as the default.
    """
    state["default_data_bundle"] = db
    save_config()


##### SPARQL QUERIES #####


def get_sparql_queries() -> List[List[str]]:
    """
    Retrieve the list of saved SPARQL queries from the session state.

    Returns:
        List[List[str]]: A list of SPARQL queries, where each query is represented as a list of strings.
                        Returns an empty list if no queries are saved.
    """
    if "sparql_queries" in state:
        return state["sparql_queries"]
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
    state["sparql_queries"] = queries


def get_sparql_query() -> str:
    """
    Retrieve the currently active SPARQL query from the session state.

    If no query is currently selected, the first saved query (if any) is set as active.
    Returns an empty string if no queries are available.

    Returns:
        str: The name of the active SPARQL query.
    """
    if "sparql_query" in state:
        return state["sparql_query"]

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
            return ""


def set_sparql_query(name: str) -> None:
    """
    Set the active SPARQL query in the session state.

    Args:
        name (str): The name of the SPARQL query to set as active.
    """
    state["sparql_query"] = name


def update_sparql_query(sq: List[str]) -> None:
    """
    Add a new SPARQL query or update an existing one in the session state and save the configuration.

    Args:
        sq (List[str]): The SPARQL query to add or update, where the first element is the query name.
    """
    # List all existing SPARQL queries
    all_queries_names = [sq[0] for sq in state["sparql_queries"]]

    # If it is a creation
    if sq[0] not in all_queries_names:
        state["sparql_queries"].append(sq)

    # If it is an update
    else:
        sparql_query_index = all_queries_names.index(sq[0])
        state["sparql_queries"][sparql_query_index] = sq

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
    state["sparql_queries"] = [sq for sq in state["sparql_queries"] if sq[0] != sq_name]

    # Remove selected one.
    # How Logre is built makes it so that when deleting a query, it HAS to be selected
    del state["sparql_query"]

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
    state["last_sparql_executed_id"] = id


def get_last_executed_sparql_id() -> str:
    """
    Retrieve the ID of the last executed SPARQL query.

    Returns:
        str | None: The identifier of the last executed SPARQL query,
        or None if no query has been executed yet.
    """
    if "last_sparql_executed_id" in state:
        return state["last_sparql_executed_id"]
    else:
        return None


##### SELECTED ENTITY #####


def get_entity_uri() -> str:
    """
    Retrieve the currently selected entity URI from the session state.

    Returns:
        str | None: The entity URI if set, otherwise None.
    """
    if "entity_uri" not in state:
        return None
    return state["entity_uri"]


def set_entity_uri(uri: str) -> None:
    """
    Set the current entity URI in the session state.

    Args:
        uri (str): The entity URI to store.
    """
    state["entity_uri"] = uri


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
    key = f"offset_{entity_uri}_{property_key}"
    if key not in state:
        return 0
    else:
        return state[f"offset_{entity_uri}_{property_key}"]


def set_offset(entity_uri: str, property_key: str, value: int) -> None:
    """
    Set the offset value for a specific entity and property in the session state.

    Args:
        entity_uri (str): The URI of the entity.
        property_key (str): The property key associated with the offset.
        value (int): The offset value to store.
    """
    state[f"offset_{entity_uri}_{property_key}"] = value


##### ENTITY CHART INCOMING #####


def entity_chart_inc_get_list() -> List[Resource]:
    """
    Retrieve the list of incoming entities for charting from the session state.

    Returns:
        List[Resource]: A list of incoming entities, or an empty list if none are set.
    """
    if "chart_entity_inc_list" in state:
        return state["chart_entity_inc_list"]
    else:
        return []


def entity_chart_inc_list_add(entity: Resource) -> None:
    """
    Add an incoming entity to the chart's incoming entity list in the session state.

    Ensures that the entity is not added more than once.

    Args:
        entity (Resource): The incoming entity to add.
    """
    if "chart_entity_inc_list" in state:
        has_entities = set([e.uri for e in state["chart_entity_inc_list"]])
        if entity.uri not in has_entities:
            state["chart_entity_inc_list"].append(entity)
    else:
        state["chart_entity_inc_list"] = [entity]


def entity_chart_inc_list_remove(entity: Resource) -> None:
    """
    Remove an incoming entity from the chart's incoming entity list in the session state.

    Args:
        entity (Resource): The incoming entity to remove.
    """
    if "chart_entity_inc_list" in state:
        state["chart_entity_inc_list"] = [
            resource
            for resource in state["chart_entity_inc_list"]
            if resource.uri != entity.uri
        ]


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
    if "chart_entity_inc_list" in state:
        has_entities = set([e.uri for e in state["chart_entity_inc_list"]])
        if entity.uri not in has_entities:
            # If it is another one, replace it
            state["chart_entity_inc_list"] = [entity]
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
    state["chart_entity_inc_initialized"] = entity


def entity_chart_get_inc_initialized() -> Resource | None:
    """
    Retrieve the entity marked as the initialized incoming entity for the chart.

    Returns:
        Resource | None: The initialized incoming entity, or None if not set.
    """
    if "chart_entity_inc_initialized" in state:
        return state["chart_entity_inc_initialized"]
    else:
        return None


##### ENTITY CHART OUTGOING #####


def entity_chart_out_get_list() -> List[Resource]:
    """
    Retrieve the list of outgoing entities for charting from the session state.

    Returns:
        List[Resource]: A list of outgoing entities, or an empty list if none are set.
    """
    if "chart_entity_out_list" in state:
        return state["chart_entity_out_list"]
    else:
        return []


def entity_chart_out_list_add(entity: Resource) -> None:
    """
    Add an outgoing entity to the chart's outgoing entity list in the session state.

    Ensures that the entity is not added more than once.

    Args:
        entity (Resource): The outgoing entity to add.
    """
    if "chart_entity_out_list" in state:
        has_entities = set([e.uri for e in state["chart_entity_out_list"]])
        if entity.uri not in has_entities:
            state["chart_entity_out_list"].append(entity)
    else:
        state["chart_entity_out_list"] = [entity]


def entity_chart_out_list_remove(entity: Resource) -> None:
    """
    Remove an outgoing entity from the chart's outgoing entity list in the session state.

    Args:
        entity (Resource): The outgoing entity to remove.
    """
    if "chart_entity_out_list" in state:
        state["chart_entity_out_list"] = [
            resource
            for resource in state["chart_entity_out_list"]
            if resource.uri != entity.uri
        ]


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
    if "chart_entity_out_list" in state:
        has_entities = set([e.uri for e in state["chart_entity_out_list"]])
        if entity.uri not in has_entities:
            # If it is another one, replace it
            state["chart_entity_out_list"] = [entity]
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
    state["chart_entity_out_initialized"] = entity


def entity_chart_get_out_initialized() -> Resource | None:
    """
    Retrieve the entity marked as the initialized outgoing entity for the chart.

    Returns:
        Resource | None: The initialized outgoing entity, or None if not set.
    """
    if "chart_entity_out_initialized" in state:
        return state["chart_entity_out_initialized"]
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
    state[f"data_table_page_{class_uri}"] = page_nb


def data_table_get_page(class_uri: str) -> int:
    """
    Retrieve the current page number for a data table associated with a specific class URI.

    Args:
        class_uri (str): The URI of the class for which the page number is retrieved.

    Returns:
        int: The current page number, or 1 if not set.
    """
    key = f"data_table_page_{class_uri}"
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
    if key in state:
        return state[key]
    else:
        return 1


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
    if key in state:
        return state[key]
    else:
        return 0
