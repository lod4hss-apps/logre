from typing import Dict, List
import streamlit as st
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
from urllib.error import HTTPError



def get_prefixes() -> str:
    """Gives the string prefixes needed for the queries"""

    return f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX ontome: <https://ontome.net/ontology/>
        PREFIX infocean: <http://geovistory.org/information/>

    """

def replace_prefixes(uri: str):
    uri = uri.replace('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf:')
    uri = uri.replace('http://www.w3.org/2000/01/rdf-schema#', 'rdfs:')
    uri = uri.replace('http://www.w3.org/2002/07/owl#', 'owl:')
    uri = uri.replace('https://ontome.net/ontology/', 'ontome:')
    uri = uri.replace('http://geovistory.org/information/', 'infocean:')
    return uri


def __handle_row(row: Dict[str, dict]) -> Dict[str, str]:
    """Transform a returning object into a dictionnary for better use."""
    obj: Dict[str, str] = {}
    for key in row.keys():
        obj[key] = replace_prefixes(row[key]["value"])
    return obj


def query(request: str) -> List[Dict[str, str]] | bool:
    """
    Execute the given request against the in session endpoint.
    Request needs to be only SELECT: won't work if it is a INSERT or DELETE request.
    """

    # If no endpoint is selected, do not do anything
    if 'endpoint' not in st.session_state:
        st.error('No endpoint has been selected, set it in "Endpoint configuration" page')
        return False

    # Init the endpoint
    sparql_endpoint = SPARQLWrapper(
        st.session_state['endpoint']['url'],
        agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    )
    sparql_endpoint.setReturnFormat(JSON)

    # Prepare the query
    sparql_endpoint.setQuery(get_prefixes() + request)

    print('==============')
    print(get_prefixes() + request)

    # Execute the query, and transform the object
    response = sparql_endpoint.queryAndConvert()["results"]["bindings"]
    response = list(map(__handle_row, response))

    if response == [{}]: 
        return []
    
    return response


def execute(request: str) -> bool:
    """
    Execute the given request agains the previously set endpoint.
    Request needs to be only INSERTs or DELETEs.
    """

    # If no endpoint is selected, do not do anything
    if 'endpoint' not in st.session_state:
        st.error('No endpoint has been selected, set it in "Endpoint configuration" page')
        return False
    
    # Init the endpoint
    sparql_endpoint = SPARQLWrapper(st.session_state['endpoint']['url'])
        
    # Prepare the query
    sparql_endpoint.setQuery(get_prefixes() + request)
    sparql_endpoint.method = "POST"

    print('==============')
    print(get_prefixes() + request)

    # Execute the query
    sparql_endpoint.query()

    st.cache_data.clear()
    st.cache_resource.clear()
    return True


def run(query_string: str) -> bool | List[Dict[str, str]]:
    """
    Dispatch between "select" queries and "insert" or "delete" queries.
    In case the query is a select, returns a DataFrame.
    Otherwise returns nothing.
    """
    try: 
        if 'delete' in query_string.lower() or 'insert' in query_string.lower():
            return execute(query_string)
        elif 'select' in query_string.lower():
            return query(query_string)
        else:
            st.error('Query error: Only "SELECT", "INSERT", "DELETE" are supported.')
            return False
    except SPARQLExceptions.QueryBadFormed as error:
        st.error(error.msg)
        return False
    except HTTPError as error:
        st.error(f"HTTP Error {error.code}: {error.reason}")
        return False
