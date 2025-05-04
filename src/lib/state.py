from typing import List, Any, Dict
from streamlit import session_state as state
from model import Query, Endpoint, DataSet, OntoEntity

###

def set_query_params(query_params: Dict[str, str]) -> None:
    state['query_params'] = {}
    for key, value in query_params.items():
        state['query_params'][key] = value

def has_query_params(param_name: str) -> bool:
    if 'query_params' not in state: return False
    return param_name in state['query_params']

def get_query_param(param: str) -> str | None:
    if 'query_params' not in state: return None
    return state['query_params'][param]

def clear_query_param() -> None:
    if 'query_params' in state:
        del state['query_params']

###

def set_version(version: str) -> None:
    state['version'] = version

def get_version() -> str:
    if 'version' not in state: return None
    return state['version']

###

def get_element(key: str) -> Any:
    if key not in state: return None
    return state[key]

def set_element(key: str, value: Any):
    state[key] = value

###

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

###

def set_queries(queries: List[Query]) -> None:
    state['all_queries'] = queries

def get_queries() -> List[Query]:
    if 'all_queries' not in state: return None
    return state['all_queries']

###

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

###

def set_endpoint(endpoint: Endpoint) -> None:
    state['endpoint'] = endpoint
    clear_data_set()

def get_endpoint() -> Endpoint:
    if 'endpoint' not in state: return None
    return state['endpoint']

def clear_endpoint() -> None:
    if 'endpoint' in state:
        del state['endpoint']

###

def set_data_set(data_set: DataSet) -> None:
    state['data_set'] = data_set

def get_data_set() -> DataSet:
    if 'data_set' not in state: return None
    return state['data_set']

def clear_data_set() -> None:
    if 'data_set' in state:
        del state['data_set']

###

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

###

def set_entity(entity: OntoEntity) -> None:
    state['selected-entity'] = entity

def get_entity() -> OntoEntity:
    if 'selected-entity' not in state: return None
    return state['selected-entity']

def clear_entity() -> None:
    if 'selected-entity' in state:
        del state['selected-entity']

###

def set_has_config(has: bool) -> None:
    state['has_config'] = has

def get_has_config() -> bool:
    if 'has_config' not in state: return False
    return state['has_config']

### 

def set_data_table_page(page_nb: int) -> None:
    state['data-table-page'] = page_nb

def get_data_table_page() -> int:
    if 'data-table-page' not in state: return 1
    return state['data-table-page']

### 