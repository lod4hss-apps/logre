from typing import List, Any
from streamlit import session_state as state, cache_data, cache_resource

# Local imports
from model import Query, Endpoint, DataBundle, OntoEntity, Prefix


### LOWER LEVEL STATE ACCESSOR

def get_element(key: str) -> Any:
    if key not in state: return None
    return state[key]

def set_element(key: str, value: Any):
    state[key] = value


### DEFAULT CONFIGURATION

def set_defaults(queries: List[Query], prefixes: List[Prefix]) -> None:
    state['defaults_queries'] = queries
    state['defaults_prefixes'] = prefixes

def get_default_queries() -> List[Query]:
    if 'defaults_queries' not in state: return []
    return state['defaults_queries']

def get_default_prefixes() -> List[Prefix]:
    if 'defaults_prefixes' not in state: return []
    return state['defaults_prefixes']


### HAS CONFIG

def set_has_config(has: bool) -> None:
    state['has_config'] = has

def get_has_config() -> bool:
    if 'has_config' not in state: return False
    return state['has_config']


### CONFIRMATION

def set_confirmation(index: int, name:str) -> None:
    state['confirmation-index'] = index
    state['confirmation-name'] = name

def get_confirmation() -> tuple[int, str]:
    index = None
    name = None
    if 'confirmation-index' in state:
        index = state['confirmation-index']
    if 'confirmation-name' in state:
        name = state['confirmation-name']

    return index, name

def clear_confirmation() -> None:
    if 'confirmation-index' in state: 
        del state['confirmation-index']
    if 'confirmation-name' in state: 
        del state['confirmation-name']


### TOAST

def set_toast(text: str, icon: str = None) -> None:
    state['toast-text'] = text
    if icon: state['toast-icon'] = icon

def get_toast() -> tuple[str, str]:
    text = state['toast-text'] if 'toast-text' in state else None
    icon = state['toast-icon'] if 'toast-icon' in state else None
    return text, icon

def clear_toast() -> None:
    if 'toast-text' in state: del state['toast-text']
    if 'toast-icon' in state: del state['toast-icon']


### VERSION

def set_version(version: str) -> None:
    state['version'] = version

def get_version() -> str:
    if 'version' not in state: return None
    return state['version']
### QUERIES

def set_queries(queries: List[Query]) -> None:
    state['all_queries'] = queries

def get_queries() -> List[Query]:
    if 'all_queries' not in state: return None
    return state['all_queries']


### ENDPOINTS

def set_endpoints(endpoints: List[Endpoint]) -> None:
    state['all_endpoints'] = endpoints

def get_endpoints() -> List[Endpoint]:
    if 'all_endpoints' not in state: return None
    return state['all_endpoints']

def delete_endpoint(endpoint: Endpoint) -> None:
    all_endpoints = get_endpoints()
    if not all_endpoints:
        raise Exception('In lib.state.delete_endpoint, there is no endpoint in session')
    endpoints_labels = [e.name for e in all_endpoints]
    index = endpoints_labels.index(endpoint.name)
    del state['all_endpoints'][index]


### ENDPOINT

def set_endpoint(endpoint: Endpoint) -> None:
    state['endpoint'] = endpoint
    clear_data_bundle()

def get_endpoint() -> Endpoint:
    if 'endpoint' not in state: return None
    return state['endpoint']

def clear_endpoint() -> None:
    if 'endpoint' in state:
        del state['endpoint']


### DATA BUNDLE

def set_data_bundle(data_bundle: DataBundle) -> None:
    state['data_bundle'] = data_bundle
    
    # Also, when a Data Bundle is selected, Cache need to be cleared
    cache_resource.clear()
    cache_data.clear()

def get_data_bundle() -> DataBundle:
    if 'data_bundle' not in state: return None
    return state['data_bundle']

def clear_data_bundle() -> None:
    if 'data_bundle' in state:
        del state['data_bundle']


### ENTITY

def set_entity(entity: OntoEntity) -> None:
    state['selected-entity'] = entity

def get_entity() -> OntoEntity:
    if 'selected-entity' not in state: return None
    return state['selected-entity']

def clear_entity() -> None:
    if 'selected-entity' in state:
        del state['selected-entity']


### DATA TABLE OFFSET

def set_data_table_page(page_nb: int) -> None:
    state['data-table-page'] = page_nb

def get_data_table_page() -> int:
    if 'data-table-page' not in state: return 1
    return state['data-table-page']