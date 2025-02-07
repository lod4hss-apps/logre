from typing import List, Dict, Tuple
import streamlit as st
import pandas as pd
from lib.sparql_base import query, execute
from lib.utils import ensure_uri
from lib.schema import SHACLclass, TripleDetailed


@st.cache_data(ttl='1d', show_spinner=False)
def list_shacl_classes() -> List[SHACLclass]:
    """List all available classes from the SHACL model"""

    # Get the graph URI from the endpoint configuration
    graph_uri: str = ensure_uri(st.session_state['endpoint']['model_uri'])

    # Prepare the query
    text = """
        SELECT 
            ?node 
            ?uri 
            ?label
        WHERE {
            GRAPH """ + graph_uri + """ {
                ?node a sh:NodeShape .
                ?node sh:name ?label .
                ?node sh:targetClass ?uri .
            }
        }
    """

    # Execute the query
    response = query(text)

    # Ensure response is an array
    return response or []

@st.cache_data(ttl='1d', show_spinner=False)
def get_properties_infos_shacl():
    text = """
        SELECT
            ?domainClassURI
            ?domainClassName
            ?propertyURI
            (COALESCE(?propertyLabel_, '') as ?propertyLabel)
            (COALESCE(?propertyOrder_, '') as ?propertyOrder)
            (COALESCE(?propertyMinCount_, '') as ?propertyMinCount)
            (COALESCE(?propertyMaxCount_, '') as ?propertyMaxCount)
            (COALESCE(?rangeClassURI_1, ?rangeClassURI_2) as ?rangeClassURI)
            (COALESCE(?rangeClassName_, '') as ?rangeClassName)
        WHERE {
            ?shape sh:property ?propertyNode .
            ?shape sh:targetClass ?domainClassURI .
            ?shape sh:name ?domainClassName .
            ?propertyNode sh:path ?propertyURI .
            optional { 
                ?propertyNode sh:class ?rangeClassURI_1 . 
                ?rangeShape sh:targetClass ?rangeClassURI_1 .
                ?rangeShape sh:name ?rangeClassName_ .
            }
            optional { ?propertyNode sh:datatype ?rangeClassURI_2 . }
            optional { ?propertyNode sh:name ?propertyLabel_ . }
            optional { ?propertyNode sh:order ?propertyOrder_ . }
            optional { ?propertyNode sh:minCount ?propertyMinCount_ . }
            optional { ?propertyNode sh:maxCount ?propertyMaxCount_ . }
            FILTER(!isBlank(?propertyURI))
        }
    """

    # Execute the query
    response = query(text)

    # Ensure response is an array
    return response or []


def list_shacl_class_properties(cls: str):
    """Get all relevant information about a class: list of all properties, format, domain/range classes, ..."""

    # Get the graph URI from the endpoint configuration
    graph_uri: str = ensure_uri(st.session_state['endpoint']['model_uri'])
    cls_uri: str = ensure_uri(cls)

    # Prepare the query
    text = """
        SELECT 
            (COALESCE(?propertyURI_incoming, ?propertyURI_outgoing) as ?propertyURI)
            (COALESCE(?propertyName_, ?propertyURI) as ?propertyName) 
            (COALESCE(?order_, 1e9) as ?propertyOrder) 
            (COALESCE(?minCount_, '0') as ?propertyMinCount) 
            (COALESCE(?maxCount_, 'inf') as ?propertyMaxCount) 
            (COALESCE(?rangeDatatype_, '') as ?rangeDatatype) 
            (COALESCE(?rangeClassURI_, '') as ?rangeClassURI)
            (COALESCE(?rangeClassName_, '') as ?rangeClassName)
            (COALESCE(?domainClassURI_, '') as ?domainClassURI)
            (COALESCE(?domainClassName_, '') as ?domainClassName)
        WHERE {
            GRAPH """ + graph_uri + """ {
                ?nodeShape sh:targetClass """ + cls_uri + """ .
                ?nodeShape sh:property ?propertyNode .
                optional { ?propertyNode sh:path ?propertyURI_outgoing . }
                optional {
                    ?propertyNode sh:path / sh:inversePath ?propertyURI_incoming .
                    ?domainPropertyNode sh:path ?propertyURI_incoming .
                    ?domainClassNode sh:property ?domainPropertyNode .
                    ?domainClassNode sh:targetClass ?domainClassURI_ .
                    ?domainClassNode sh:name ?domainClassName_ .
                }
                optional { ?propertyNode sh:name ?propertyName_ . }
                optional { ?propertyNode sh:order ?order_ . }
                optional { ?propertyNode sh:minCount ?minCount_ . }
                optional { ?propertyNode sh:maxCount ?maxCount_ . }
                optional { ?propertyNode sh:datatype ?rangeDatatype_ . }
                optional {
                    ?propertyNode sh:class ?rangeClassURI_ .
                    ?rangeClassNode sh:targetClass ?rangeClassURI_ .
                    ?rangeClassNode sh:name ?rangeClassName_ .
                }
            }
        } order by ?propertyOrder
    """

    # Execute the query
    response = query(text)

    # Ensure response is an array
    return response or []



def list_shacl_card(entity):
    """Get all relevant information about a class: list of all properties, format, domain/range classes, ..."""

    # Get the graph URI from the endpoint configuration
    graph_uri: str = ensure_uri(st.session_state['all_graphs'][st.session_state['activated_graph_index']]['uri'])
    entity_uri: str = ensure_uri(entity)

    # Prepare the query
    text = """
        SELECT 
            #?propertyURI
            #?objectURI
            *
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                """ + entity_uri + """ a ?cls_uri .
                ?nodeShape sh:targetClass ?cls_uri .
                ?nodeShape sh:property ?propertyNode .
                optional { ?propertyNode sh:path ?propertyURI_outgoing . }
                optional {
                    ?propertyNode sh:path / sh:inversePath ?propertyURI_incoming .
                    ?domainPropertyNode sh:path ?propertyURI_incoming .
                    ?domainClassNode sh:property ?domainPropertyNode .
                    ?domainClassNode sh:targetClass ?domainClassURI_ .
                    ?domainClassNode sh:name ?domainClassName_ .
                }
                optional { ?propertyNode sh:name ?propertyName_ . }
                optional { ?propertyNode sh:order ?order_ . }
                optional { ?propertyNode sh:minCount ?minCount_ . }
                optional { ?propertyNode sh:maxCount ?maxCount_ . }
                optional { ?propertyNode sh:datatype ?rangeDatatype_ . }
                optional {
                    ?propertyNode sh:class ?rangeClassURI_ .
                    ?rangeClassNode sh:targetClass ?rangeClassURI_ .
                    ?rangeClassNode sh:name ?rangeClassName_ .
                }
                """ + entity_uri + """ ?propertyURI ?objectURI .
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the query
    response = query(text)

    # Ensure response is an array
    return response or []


def build_shacl_card(entity: str, cls: str, graph: str = None):

    entity_uri = ensure_uri(entity)
    graph_uri: str = ensure_uri(graph)

    properties = list_shacl_class_properties(cls)
    properties_str = ' '.join(list(map(lambda property: ensure_uri(property['propertyURI']), properties)))


    text = """
        SELECT
            (COALESCE(?subject_, '') as ?subject)
            (COALESCE(?subjectLabel_, ?subject_, '') as ?subjectLabel)
            ?propertyURI 
            ?object 
            (COALESCE(?objectLabel_, ?object) as ?objectLabel)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                { 
                    """ + entity_uri + """ ?propertyURI ?object . 
                    optional { ?object rdfs:label ?objectLabel_ . }
                } UNION { 
                    ?subject_ ?propertyURI """ + entity_uri + """ .
                    optional { ?subject_ rdfs:label ?subjectLabel_ . }
                }
                VALUES ?propertyURI {""" + properties_str + """}
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the query
    response = query(text)

    if not response:
        return []
    else:
        properties_df = pd.DataFrame(properties)
        response_df = pd.DataFrame(response)
        response_df = response_df.merge(properties_df, on='propertyURI', how='outer')
        response_df['propertyOrder'] = response_df['propertyOrder'].apply(lambda x: int(float(x)))
        return response_df.sort_values('propertyOrder').fillna('')

