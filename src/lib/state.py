from typing import List, Dict
from datetime import datetime
import os
import re
import shutil
from os.path import exists as path_exists
from pathlib import Path
from yaml import safe_load, dump
from requests.exceptions import ConnectionError, Timeout
from graphly.schema import Prefixes, Prefix, Resource, Property, Sparql
import streamlit as st
from streamlit import session_state as state, query_params
from schema.data_bundle import DataBundle
from schema.sparql_technologies import get_sparql
from lib.config_paths import get_config_path, get_default_config_path, ensure_parent_dir
from lib.config_migrations import migrate_config_if_needed
from lib.autoconfigure_data_graph import autoconfigure_config


##### PATHS #####

BASE_DIR = Path(__file__).resolve().parent.parent.parent

VERSION_FILE_PATH = BASE_DIR / "version"
VERSION_FALLBACK_PATH = BASE_DIR / "VERSION"
DEFAULTS_PREFIXES = BASE_DIR / "defaults" / "prefixes.yaml"
DEFAULTS_DATA_BUNDLES = BASE_DIR / "defaults" / "data-bundles.yaml"
DEFAULTS_DATA_BUNDLE_DEFAULT = BASE_DIR / "defaults" / "default-data-bundle.yaml"
DEFAULTS_SPARQL_QUERIES = BASE_DIR / "defaults" / "sparql-queries.yaml"

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
UNREACHABLE_ENDPOINT_KEYS = "unreachable_endpoint_keys"


def _resolve_config_path() -> Path:
    return get_config_path()


def _resolve_default_config_path() -> Path | None:
    return get_default_config_path(str(BASE_DIR))


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


def invalidate_caches(reason: str | None = None) -> None:
    try:
        st.cache_data.clear()
    except Exception as err:
        print(f"[cache] cache_data clear failed: {err}")
    try:
        st.cache_resource.clear()
    except Exception as err:
        print(f"[cache] cache_resource clear failed: {err}")
    if reason:
        print(f"[cache] cleared: {reason}")


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
        current_db_param = _get_query_param_value("db")
        selected_db_key = state.get("selected_db_key")

        print(f"[query] required db | state={selected_db_key} url={current_db_param}")

        if selected_db_key and current_db_param != selected_db_key:
            print(f"[query] set db param -> {selected_db_key}")
            query_params["db"] = selected_db_key

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


##### QUERY PARAMS #######


def __get_query_param_value(key: str) -> str | None:
    if key not in query_params:
        return None

    value = query_params[key]
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def set_query_params(query_param_keys: List[str]) -> None:
    # Keep endpoint in URL whenever endpoint or db are managed,
    # so links/new tabs keep the right backend context.
    sync_endpoint = "endpoint" in query_param_keys or "db" in query_param_keys

    # Endpoint key: from state to query param
    if sync_endpoint:
        endpoint_key = get_endpoint_key()
        if endpoint_key:
            query_params["endpoint"] = endpoint_key
        elif "endpoint" in query_params:
            del query_params["endpoint"]

    # Data bundle: from state to query param
    if "db" in query_param_keys:
        db = get_data_bundle()
        if db:
            query_params["db"] = db.key
        elif "db" in query_params:
            del query_params["db"]

    # Entity URI: from state to query param
    if "uri" in query_param_keys:
        uri = get_entity_uri()
        if uri:
            query_params["uri"] = uri
        elif "uri" in query_params:
            del query_params["uri"]


def parse_query_params() -> None:
    # Query params may bootstrap a new browser tab/session.
    # Once endpoint/bundle are already selected in state, state stays authoritative.

    current_endpoint_key = get_endpoint_key()

    # Endpoint: from query param to state only when endpoint is not already set.
    if not current_endpoint_key:
        endpoint_key = __get_query_param_value("endpoint")
        if endpoint_key:
            available_endpoints = [group["key"] for group in get_endpoint_groups()]
            if endpoint_key in available_endpoints:
                set_endpoint_key(endpoint_key)
                current_endpoint_key = endpoint_key

    # Data bundle: from query param to state only when no bundle is selected yet.
    if get_data_bundle() is None:
        bundle_key = __get_query_param_value("db")
        if bundle_key:
            matching_bundles = [db for db in get_data_bundles() if db.key == bundle_key]
            data_bundle = None

            # If endpoint is constrained (state or URL bootstrap), only accept matching bundles.
            if current_endpoint_key:
                data_bundle = next(
                    (
                        db
                        for db in matching_bundles
                        if get_endpoint_identifier(db.endpoint) == current_endpoint_key
                    ),
                    None,
                )
            # Without endpoint constraint, avoid ambiguous picks.
            elif len(matching_bundles) == 1:
                data_bundle = matching_bundles[0]

            if data_bundle:
                set_data_bundle(data_bundle)

    # Entity URI: from query param to state only when it is currently unset.
    uri = __get_query_param_value("uri")
    if uri and get_entity_uri() is None:
        set_entity_uri(uri)


def resolve_startup_context() -> bool:
    """
    Resolve an initial working context when the app lands on server.py.

    Priority order:
    1. Existing selected data bundle in state
    2. Last used data bundle from persisted config
    3. Configured default data bundle

    Returns:
        bool: True when a bundle is selected, False otherwise.
    """
    current = get_data_bundle()
    if current is not None:
        return True

    # If endpoint is already constrained (e.g. URL bootstrap), keep it coherent.
    constrained_endpoint_key = get_endpoint_key()

    last_used_key = get_last_used_data_bundle_key()
    if last_used_key:
        last_used_bundle = next(
            (db for db in get_data_bundles() if db.key == last_used_key),
            None,
        )
        if (
            last_used_bundle
            and (
                not constrained_endpoint_key
                or get_endpoint_identifier(last_used_bundle.endpoint)
                == constrained_endpoint_key
            )
            and not is_endpoint_temporarily_unreachable(last_used_bundle.endpoint)
        ):
            set_data_bundle(last_used_bundle)
            return True

    default_bundle = get_default_data_bundle()
    if (
        default_bundle
        and (
            not constrained_endpoint_key
            or get_endpoint_identifier(default_bundle.endpoint)
            == constrained_endpoint_key
        )
        and not is_endpoint_temporarily_unreachable(default_bundle.endpoint)
    ):
        return select_default_data_bundle()

    return False


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

        config_path = _resolve_config_path()
        default_path = _resolve_default_config_path()
        print(f"[config] path={config_path}")
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
        need_save = False
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

        # Add all prefixes from defaults before creating Data Bundles
        with open(DEFAULTS_PREFIXES, "r", encoding="utf-8") as file:
            default_prefixes_raw = safe_load(file.read())
            if isinstance(default_prefixes_raw, list):
                for default_prefix in default_prefixes_raw:
                    if not isinstance(default_prefix, dict):
                        continue
                    short = default_prefix.get("short")
                    long_uri = default_prefix.get("long")
                    if short and short not in seen_prefixes:
                        loaded_prefixes.add(Prefix(short, long_uri))
                        seen_prefixes.add(short)
                        need_save = True

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

        # Extract last used Data Bundle (optional)
        last_used_db_key = obj.get("last_used_data_bundle")
        if isinstance(last_used_db_key, str) and last_used_db_key:
            if any(db.key == last_used_db_key for db in get_data_bundles()):
                state["last_used_data_bundle"] = last_used_db_key
            else:
                repaired = True

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

    def normalize_sparql_queries(queries: object) -> List[List[str]]:
        normalized: List[List[str]] = []
        if not isinstance(queries, list):
            return normalized

        for query in queries:
            if not isinstance(query, list) or len(query) < 2:
                continue

            name, text = query[0], query[1]
            if not isinstance(name, str) or not name.strip():
                continue

            if text is None:
                text = ""
            if not isinstance(text, str):
                text = str(text)

            normalized.append([name, text])

        return normalized

    def merge_sparql_queries_with_disk(config_path: Path) -> List[List[str]]:
        # Keep disk queries so a stale in-memory state cannot drop them,
        # while allowing current in-memory edits to override same-name queries.
        merged_by_name: Dict[str, str] = {}
        deleted_query_names = set(state.get("deleted_sparql_queries", []))

        if path_exists(config_path):
            try:
                disk_obj = safe_load(config_path.read_text(encoding="utf-8")) or {}
                if isinstance(disk_obj, dict):
                    for query_name, query_text in normalize_sparql_queries(
                        disk_obj.get("sparql_queries", [])
                    ):
                        if query_name in deleted_query_names:
                            continue
                        merged_by_name[query_name] = query_text
            except Exception as err:
                print(f"[config] failed to read existing SPARQL queries: {err}")

        for query_name, query_text in normalize_sparql_queries(get_sparql_queries()):
            merged_by_name[query_name] = query_text

        return [
            [query_name, query_text]
            for query_name, query_text in merged_by_name.items()
        ]

    default_db = get_default_data_bundle()

    # Normalize prefixes (unique by short, skip base)
    prefixes_by_short: Dict[str, Prefix] = {}
    for prefix in get_prefixes():
        if not prefix.short or prefix.short == "base":
            continue
        prefixes_by_short[prefix.short] = prefix

    # Gather config
    config_path = _resolve_config_path()
    merged_sparql_queries = merge_sparql_queries_with_disk(config_path)
    config = {
        "endpoints": [e.to_dict() for e in get_endpoints()],
        "prefixes": [p.to_dict() for p in prefixes_by_short.values()],
        "data_bundles": [db.to_dict() for db in get_data_bundles()],
        "default_data_bundle": default_db.key if default_db else None,
        "last_used_data_bundle": get_last_used_data_bundle_key(),
        "sparql_queries": merged_sparql_queries,
        "version": state["config_version"] if "config_version" in state else None,
    }

    # To YAML string
    content = dump(config, sort_keys=False)

    # Write the config to disk
    ensure_parent_dir(config_path)
    with open(config_path, "w", encoding="utf-8") as file:
        file.write(content)

    # Clear one-shot tombstones after successful write.
    if "deleted_sparql_queries" in state:
        del state["deleted_sparql_queries"]


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

    # Rebuild data bundles so graph/model/metadata prefixes stay in sync.
    current_prefixes = get_prefixes()
    current_endpoints = get_endpoints()
    rebuilt_bundles: List[DataBundle] = []
    previous_selected = state.get("data_bundle")
    previous_default = state.get("default_data_bundle")

    for bundle in get_data_bundles():
        try:
            rebuilt_bundles.append(
                DataBundle.from_dict(
                    bundle.to_dict(), current_prefixes, current_endpoints
                )
            )
        except Exception:
            rebuilt_bundles.append(bundle)

    set_data_bundles(rebuilt_bundles)

    if previous_selected:
        selected_endpoint = get_endpoint_identifier(previous_selected.endpoint)
        selected_bundle = next(
            (
                bundle
                for bundle in rebuilt_bundles
                if bundle.key == previous_selected.key
                and get_endpoint_identifier(bundle.endpoint) == selected_endpoint
            ),
            None,
        )
        state["data_bundle"] = selected_bundle

    if previous_default:
        default_endpoint = get_endpoint_identifier(previous_default.endpoint)
        default_bundle = next(
            (
                bundle
                for bundle in rebuilt_bundles
                if bundle.key == previous_default.key
                and get_endpoint_identifier(bundle.endpoint) == default_endpoint
            ),
            None,
        )
        state["default_data_bundle"] = default_bundle

    invalidate_caches("prefix_change")

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
    previous = state.get("endpoint")
    previous_name = previous.name if previous else None
    new_name = endpoint.name if endpoint else None
    state["endpoint"] = endpoint
    if previous_name is not None and previous_name != new_name:
        invalidate_caches("endpoint_change")


def mark_endpoint_temporarily_unreachable(endpoint: Sparql | None) -> None:
    endpoint_key = get_endpoint_identifier(endpoint)
    if not endpoint_key:
        return
    keys = set(state.get(UNREACHABLE_ENDPOINT_KEYS, []))
    keys.add(endpoint_key)
    state[UNREACHABLE_ENDPOINT_KEYS] = sorted(keys)


def clear_endpoint_temporarily_unreachable(endpoint: Sparql | None) -> None:
    endpoint_key = get_endpoint_identifier(endpoint)
    if not endpoint_key:
        return
    keys = set(state.get(UNREACHABLE_ENDPOINT_KEYS, []))
    if endpoint_key in keys:
        keys.remove(endpoint_key)
        state[UNREACHABLE_ENDPOINT_KEYS] = sorted(keys)


def is_endpoint_temporarily_unreachable(endpoint: Sparql | None) -> bool:
    endpoint_key = get_endpoint_identifier(endpoint)
    if not endpoint_key:
        return False
    keys = set(state.get(UNREACHABLE_ENDPOINT_KEYS, []))
    return endpoint_key in keys


def deselect_bundle_after_endpoint_failure() -> None:
    endpoint = get_endpoint()
    endpoint_name = endpoint.name if endpoint else "(unknown)"

    mark_endpoint_temporarily_unreachable(endpoint)

    if get_data_bundle() is not None:
        set_data_bundle(None)

    state["last_used_data_bundle"] = None
    if "has_config" in state:
        save_config()

    timeout_seconds = os.getenv("LOGRE_SPARQL_TIMEOUT", "12")
    set_toast(
        f"Endpoint '{endpoint_name}' is unreachable (timeout {timeout_seconds}s). Data Bundle deselected.",
        icon=":material/warning:",
    )


def get_endpoint_identifier(endpoint: Sparql | None) -> str | None:
    if not endpoint:
        return None
    if hasattr(endpoint, "key"):
        return getattr(endpoint, "key")
    if hasattr(endpoint, "name"):
        return getattr(endpoint, "name")
    return None


def get_endpoint_key() -> str | None:
    endpoint = get_endpoint()
    return get_endpoint_identifier(endpoint)


def set_endpoint_key(endpoint_key: str) -> None:
    if not endpoint_key:
        return
    endpoint = next(
        (ep for ep in get_endpoints() if get_endpoint_identifier(ep) == endpoint_key),
        None,
    )
    if endpoint:
        set_endpoint(endpoint)


def update_endpoint(old_endpoint: Sparql | None, new_endpoint: Sparql | None) -> None:
    """
    Add, remove, or update an endpoint in the session state and save the configuration.

    Args:
        old_db (Sparql | None): The existing endpoint to update or remove. If None, a new endpoint is added.
        new_db (Sparql | None): The new endpoint to add or replace the old one. If None, the old endpoint is removed.
    """
    # Create a new endpoint
    if old_endpoint is None:
        state["endpoints"].append(new_endpoint)

    # Remove an endpoint
    elif new_endpoint is None:
        old_endpoint_id = get_endpoint_identifier(old_endpoint)
        state["endpoints"] = [
            endpoint
            for endpoint in state["endpoints"]
            if endpoint.name != old_endpoint.name
        ]

        # Clear current endpoint selection if it points to the deleted endpoint.
        if get_endpoint_identifier(state.get("endpoint")) == old_endpoint_id:
            state["endpoint"] = None

    # Update an endpoint
    else:
        old_endpoint_id = get_endpoint_identifier(old_endpoint)
        db_index = next(
            i
            for i, endpoint in enumerate(state["endpoints"])
            if endpoint.name == old_endpoint.name
        )
        state["endpoints"][db_index] = new_endpoint

        # Rebind every data bundle that points to the edited endpoint so that
        # data/model/metadata graphs all use the refreshed SPARQL client.
        for data_bundle in state.get("data_bundles", []):
            if get_endpoint_identifier(data_bundle.endpoint) == old_endpoint_id:
                data_bundle.attach_endpoint(new_endpoint)

        # Preserve endpoint selection when editing the currently selected one.
        if get_endpoint_identifier(state.get("endpoint")) == old_endpoint_id:
            state["endpoint"] = new_endpoint

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
        endpoint_id = get_endpoint_identifier(endpoint)
        bundles = [
            db
            for db in get_data_bundles()
            if get_endpoint_identifier(db.endpoint) == endpoint_id
        ]
        groups.append(
            {
                "key": endpoint_id,
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

    Returns None if no bundle has been explicitly selected.

    Returns:
        DataBundle | None: The selected data bundle, or None if not found.
    """
    return state.get("data_bundle")


def set_data_bundle(data_bundle: DataBundle | None) -> None:
    """
    Set the active data bundle in the session state and load its associated model.

    Args:
        data_bundle (DataBundle): The data bundle to set as active.
    """
    previous = state.get("data_bundle")
    previous_key = previous.key if previous else None
    previous_endpoint_key = (
        get_endpoint_identifier(previous.endpoint) if previous else None
    )
    new_key = data_bundle.key if data_bundle else None
    new_endpoint_key = (
        get_endpoint_identifier(data_bundle.endpoint) if data_bundle else None
    )
    previous_last_used_key = get_last_used_data_bundle_key()
    state["data_bundle"] = data_bundle
    if data_bundle:
        state["selected_db_name"] = data_bundle.name
        state["selected_db_key"] = data_bundle.key
        state["last_used_db_key"] = data_bundle.key
        state["last_used_data_bundle"] = data_bundle.key
        set_endpoint(data_bundle.endpoint)
        state["last_used_db_endpoint_key"] = get_endpoint_identifier(
            data_bundle.endpoint
        )
    else:
        if "selected_db_name" in state:
            del state["selected_db_name"]
        if "selected_db_key" in state:
            del state["selected_db_key"]
    bundle_changed = previous_key is not None and (
        previous_key != new_key or previous_endpoint_key != new_endpoint_key
    )
    if bundle_changed:
        invalidate_caches("data_bundle_change")
        # Avoid keeping an entity URI that may not exist in the new bundle.
        if get_entity_uri() is not None:
            set_entity_uri(None)

    # Persist last used bundle only when it actually changes and config is loaded.
    if (
        data_bundle
        and previous_last_used_key != data_bundle.key
        and "has_config" in state
    ):
        save_config()

    # When a data bundle is chosen, load its model
    if data_bundle:
        try:
            data_bundle.load_model()
        except (ConnectionError, Timeout):
            deselect_bundle_after_endpoint_failure()
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


def get_last_used_data_bundle_key() -> str | None:
    """
    Retrieve the persisted key of the last used data bundle.

    Returns:
        str | None: Data bundle key if available, otherwise None.
    """
    value = state.get("last_used_data_bundle")
    if isinstance(value, str) and value:
        return value
    return None


def select_default_data_bundle() -> bool:
    """
    Select the configured default data bundle explicitly.

    Returns:
        bool: True when a default bundle exists and has been selected, False otherwise.
    """
    default_db = get_default_data_bundle()
    if not default_db:
        return False

    resolved_default = next(
        (
            db
            for db in get_data_bundles()
            if db.key == default_db.key
            and get_endpoint_identifier(db.endpoint)
            == get_endpoint_identifier(default_db.endpoint)
        ),
        None,
    )
    if not resolved_default:
        return False

    set_data_bundle(resolved_default)
    return True


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

    deleted_queries = set(state.get("deleted_sparql_queries", []))
    deleted_queries.add(sq_name)
    state["deleted_sparql_queries"] = sorted(deleted_queries)

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


def get_entity_uri() -> str | None:
    """
    Retrieve the currently selected entity URI from the session state.

    Returns:
        str | None: The entity URI if set, otherwise None.
    """
    if "entity_uri" not in state:
        return None
    return state["entity_uri"]


def set_entity_uri(uri: str | None) -> None:
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
