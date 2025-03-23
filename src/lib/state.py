from typing import List, Any, Literal
import os
import toml
from streamlit import session_state as state
from schema import Query, Endpoint, Graph, Entity, OntologyProperty, Prefix


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

def set_version(version: str) -> None:
    state['version'] = version

def get_version() -> str:
    if 'version' not in state: return None
    return state['version']

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

def set_prefixes(prefixes: List[Prefix]) -> None:
    state['all_prefixes'] = prefixes

def get_prefixes() -> List[Prefix]:
    if 'all_prefixes' not in state: return []
    return state['all_prefixes']

def delete_prefix(prefix: Prefix) -> None:
    all_prefixes = get_prefixes()
    if not all_prefixes:
        raise Exception('In lib.state.delete_prefix, there is no prefix in session')
    prefixes_shorts = [e.short for e in all_prefixes]
    index = prefixes_shorts.index(prefix.short)
    del state['all_prefixes'][index]

###

def set_endpoint(endpoint: Endpoint) -> None:
    state['endpoint'] = endpoint

def get_endpoint() -> Endpoint:
    if 'endpoint' not in state: return None
    return state['endpoint']

def clear_endpoint() -> None:
    if 'endpoint' in state:
        del state['endpoint']
        
###

def set_graphs(graphs: List[Graph]) -> None:
    state['all_graphs'] = graphs

def get_graphs() -> List[Graph]:
    if 'all_graphs' not in state: return None
    return state['all_graphs']

###

def clear_graphs() -> None:
    if 'all_graphs' in state:
        del state['all_graphs']

def get_graph() -> Graph:
    if 'activated_graph_index' not in state: return None
    return get_graphs()[state['activated_graph_index']]

###

def get_graph_index() -> int:
    if 'activated_graph_index' not in state: return None
    return state['activated_graph_index']

def set_graph_index(index: int) -> None:
    state['activated_graph_index'] = index

def clear_graph() -> None:
    if 'activated_graph_index' in state:
        del state['activated_graph_index']

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

def set_entity(entity: Entity) -> None:
    state['selected-entity'] = entity

def get_entity() -> Entity:
    if 'selected-entity' not in state: return None
    return state['selected-entity']

def clear_entity() -> None:
    if 'selected-entity' in state:
        del state['selected-entity']

### 

def set_create_triple_subject(entity: Entity) -> None:
    state['create-triple-subject'] = entity

def get_create_triple_subject() -> Entity:
    if 'create-triple-subject' not in state: return None
    return state['create-triple-subject']

def clear_create_triple_subject() -> None:
    if 'create-triple-subject' in state:
        del state['create-triple-subject']
### 

def set_create_triple_property(property: OntologyProperty) -> None:
    state['create-triple-property'] = property

def get_create_triple_property() -> Entity:
    if 'create-triple-property' not in state: return None
    return state['create-triple-property']

def clear_create_triple_predicate() -> None:
    if 'create-triple-predicate' in state:
        del state['create-triple-predicate']
### 

def set_create_triple_object(entity: Entity) -> None:
    state['create-triple-object'] = entity

def get_create_triple_object() -> Entity:
    if 'create-triple-object' not in state: return None
    return state['create-triple-object']

def clear_create_triple_object() -> None:
    if 'create-triple-object' in state:
        del state['create-triple-object']

### 

def set_data_table_page(page_nb: int) -> None:
    state['data-table-page'] = page_nb

def get_data_table_page() -> int:
    if 'data-table-page' not in state: return 1
    return state['data-table-page']