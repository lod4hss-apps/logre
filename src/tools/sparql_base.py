from typing import Dict, List
import streamlit as st
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
from urllib.error import HTTPError


def __get_prefixes() -> str:
    """
    Gives the string prefixes needed for the queries.
    This function exists to avoid to have prefixes in spreaded places.
    """

    return f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX ontome: <https://ontome.net/ontology/>
        PREFIX infocean: <http://geovistory.org/information/>

    """


def __replace_prefixes(uri: str):
    """
    This function allows to have short and concise query results,
    displays a prefix instead of a full URI.
    """

    uri = uri.replace('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf:')
    uri = uri.replace('http://www.w3.org/2000/01/rdf-schema#', 'rdfs:')
    uri = uri.replace('http://www.w3.org/2002/07/owl#', 'owl:')
    uri = uri.replace('https://ontome.net/ontology/', 'ontome:')
    uri = uri.replace('http://geovistory.org/information/', 'infocean:')
    return uri


def __handle_row(row: Dict[str, dict]) -> Dict[str, str]:
    """Transform an object coming from a SPARQL query (through SPARQLWrapper) into a dictionnary for better use."""

    obj: Dict[str, str] = {}
    for key in row.keys():
        obj[key] = __replace_prefixes(row[key]["value"])
    return obj


def query(request: str, _error_location=None) -> List[Dict[str, str]] | bool:
    """
    Execute the given request against the in session endpoint.
    Request needs to be only SELECT: won't work if it is a INSERT or DELETE request.
    Leading underscore for "_error_location" arg is to tell streamlit to not serialize the argument.
    """

    # Init the endpoint
    sparql_endpoint = SPARQLWrapper(
        st.session_state['endpoint']['url'],
        agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    )
    sparql_endpoint.setReturnFormat(JSON)

    # Prepare the query
    sparql_endpoint.setQuery(__get_prefixes() + request)

    # DEBUG
    print('==============')
    print(__get_prefixes() + request)

    # Execute the query, handles errors,
    try: 
        response = sparql_endpoint.queryAndConvert()["results"]["bindings"]
    except SPARQLExceptions.QueryBadFormed as error:
        if _error_location:
            _error_location.error(error.msg)
        else:
            st.error(error.msg)
        return False
    except HTTPError as error:
        if _error_location:
            _error_location.error(f"HTTP Error {error.code}: {error.reason}")
        else:
            st.error(f"HTTP Error {error.code}: {error.reason}")
        return False
    # and transform the object
    response = list(map(__handle_row, response))

    # If the answer is empty, return an actual empty array
    if response == [{}]: 
        return []
    
    return response


def execute(request: str) -> bool:
    """
    Execute the given request against the previously set endpoint.
    Request needs to be only INSERTs or DELETEs.
    """
    
    # Init the endpoint
    sparql_endpoint = SPARQLWrapper(st.session_state['endpoint']['url'])
        
    # Prepare the query
    sparql_endpoint.setQuery(__get_prefixes() + request)
    sparql_endpoint.method = "POST"

    # DEBUG
    print('==============')
    print(__get_prefixes() + request)

    # Execute the query
    try: 
        sparql_endpoint.query()
    except SPARQLExceptions.QueryBadFormed as error:
        st.error(error.msg)
        return False
    except HTTPError as error:
        st.error(f"HTTP Error {error.code}: {error.reason}")
        return False

    # The idea behind clearing the cache at this place is to make sure that executed 
    # (insert or delete) are taking into account for next queries.
    # Emptying the cache makes sure of that.
    st.cache_data.clear()
    st.cache_resource.clear()
    return True


def run(query_string: str) -> bool | List[Dict[str, str]]:
    """ Wrapper of "query" and "execute" function."""
    
    if 'delete' in query_string.lower() or 'insert' in query_string.lower():
        return execute(query_string)
    elif 'select' in query_string.lower():
        return query(query_string)
    else:
        st.error('Query error: Only "SELECT", "INSERT", "DELETE" are supported.')
        return False
