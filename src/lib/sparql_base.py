from typing import Dict, List
import requests
from urllib.error import URLError, HTTPError
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
import streamlit as st
from schema import Triple, EndpointTechnology
from lib.prefixes import get_prefixes_str, shorten_uri
from lib.utils import ensure_uri
import lib.state as state


def __handle_row(row: Dict[str, dict]) -> Dict[str, str]:
    """Transform an object coming from a SPARQL query (through SPARQLWrapper) into a dictionnary for better use."""

    obj: Dict[str, str] = {}
    for key in row.keys():
        obj[key] = shorten_uri(row[key]["value"])
        # obj[key] = row[key]["value"]
    return obj


def query(request: str, caller: str = None, add_prefix: bool = True) -> List[Dict[str, str]] | bool:
    """
    Execute the given request against the in session endpoint.
    Request needs to be only SELECT: won't work if it is an INSERT or a DELETE request.
    """

    # From session state
    endpoint = state.get_endpoint()

    # Init the endpoint
    sparql_endpoint = SPARQLWrapper(
        endpoint.url,
        agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    )
    sparql_endpoint.setReturnFormat(JSON)

    # If there is a user/password in selected endpoint, take it
    if endpoint.username != '' or endpoint.password != '':
        sparql_endpoint.setCredentials(endpoint.username, endpoint.password)

    # Prepare the query
    text = get_prefixes_str() + request if add_prefix else request
    sparql_endpoint.setQuery(text)

    # DEBUG
    print('==============')
    print(text)

    # Execute the query, handles errors,
    try: 
        response = sparql_endpoint.queryAndConvert()["results"]["bindings"]
    except SPARQLExceptions.QueryBadFormed as error:
        msg = error.msg
        if caller: msg += f' Called by <{caller}>'
        st.error(msg)
        print(error)
        return False
    except HTTPError as error:
        msg = f"HTTP Error {error.code}: {error.reason}."
        if caller: msg += f' Called by <{caller}>'
        st.error(msg)
        print(error)
        return False
    except URLError as error:
        msg = f"URL Error: {error.reason}"
        if caller: msg += f' Called by <{caller}>'
        st.error(msg)
        print(error)
    except Exception as error:
        msg = f"An error occured: {str(error)}"
        return False

    # and transform the object
    response = list(map(__handle_row, response))

    # Make sure to always return an array if there was no error, 
    # Event if there is no rows to return
    if response == [{}]: return []
    return response


def execute(request: str, caller: str = None, add_prefix: bool = True) -> bool:
    """
    Execute the given request against the previously set endpoint.
    Request needs to be only INSERTs or DELETEs.
    """

    # From session state
    endpoint = state.get_endpoint()
    
    # Init the endpoint
    sparql_endpoint = SPARQLWrapper(endpoint.url)
        
    # Prepare the query
    text = get_prefixes_str() + request if add_prefix else request
    sparql_endpoint.setQuery(text)
    sparql_endpoint.method = "POST"

    # If there is a user/password in selected endpoint, take it
    if endpoint.username != '' or endpoint.password != '':
        sparql_endpoint.setCredentials(endpoint.username, endpoint.password)
        
    # DEBUG
    print('==============')
    print(text)

    # Execute the query
    try: 
        sparql_endpoint.query()
    except SPARQLExceptions.QueryBadFormed as error:
        msg = error.msg
        if caller: msg += f' Called by <{caller}>'
        st.error(msg)
        print(error)
        return False
    except HTTPError as error:
        msg = f"HTTP Error {error.code}: {error.reason}."
        if caller: msg += f' Called by <{caller}>'
        st.error(msg)
        print(error)
        return False
    except URLError as error:
        msg = f"URL Error: {error.reason}"
        if caller: msg += f' Called by <{caller}>'
        st.error(msg)
        print(error)
        return False

    # The idea behind clearing the cache at this place is to make sure that executed 
    # (insert or delete) are taking into account for next queries.
    # Emptying the cache makes sure of that.
    st.cache_data.clear()
    st.cache_resource.clear()
    return True


def run(query_string: str, add_prefix: bool = True) -> bool | List[Dict[str, str]]:
    """Wrapper of "query" and "execute" function."""
    
    if 'delete' in query_string.lower() or 'insert' in query_string.lower():
        return execute(query_string, add_prefix=add_prefix)
    elif 'select' in query_string.lower() or 'construct' in query_string.lower():
        return query(query_string, add_prefix=add_prefix)
    else:
        st.error('Query error: Only "SELECT", "CONSTRUCT", "INSERT", "DELETE" are supported.')
        return False



def insert(triples: List[Triple] | Triple, graph: str = None, delete_before=True) -> None:
    """
    From a list (or unique) of Triple instances, insert them (it) 
    in the endpoint, in the given graph.
    """

    # Special use case for allegrograph: tt allows multiple same triples to exist simultaneously.
    # So on inserting, we first delete the existing, to be sure
    if delete_before and state.get_endpoint().technology == EndpointTechnology.ALLEGROGRAPH:
        delete(triples, graph)

    # If only a single triple is given, transform is into a list
    if isinstance(triples, Triple):
        triples = [triples]

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Since insert can be pretty huge, here we split them
    # in "smaller insert" of maximum 10k triples.

    chunk_size = 1000
    chunked_triples = [triples[i: i + chunk_size] for i in range(0, len(triples), chunk_size)]
    
    for small_triples in chunked_triples:
        # Transform the triples into strings
        triples_str = '\n'.join(map(lambda triple: triple.to_sparql(), small_triples))

        # Prepare the query
        text = """
            INSERT DATA {
                """ + ("GRAPH " + graph_uri + " {" if graph else "") + """
                """ + triples_str + """
                """ + ("}" if graph else "") + """
            }
        """

        # Insert the triples in the endpoint
        execute(text)


def delete(triples: List[Triple] | Triple, graph: str = None) -> None:
    """
    From a list (or unique) of Triple instances, delete them (it) 
    from the endpoint, from the given graph.
    Triples can here be either full URIs, or variables (to make deletion rules)
    """

    # If only a single triple is given, transform is into a list
    if isinstance(triples, Triple):
        triples = [triples]
        
    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Transform the triples into strings
    triples_str = '\n'.join(map(lambda triple: triple.to_sparql(), triples))

    # Prepare query
    text = """
        DELETE WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph else "") + """
                """ + triples_str + """
            """ + ("}" if graph else "") + """
        }
    """

    # Execute
    execute(text)


def dump_endpoint():

    # From state
    endpoint = state.get_endpoint()

    # Build the URL
    url = endpoint.url + '/statements'

    # Send GET request with Accept header for N-Quads format
    headers = {"Accept": "application/n-quads"}

    # Add Authentication
    if endpoint.username and endpoint.password: auth = (endpoint.username, endpoint.password)
    elif endpoint.username: auth = (endpoint.username, '')
    else: auth = None

    # Make the request
    response = requests.get(url, headers=headers, auth=auth)

    return response.text