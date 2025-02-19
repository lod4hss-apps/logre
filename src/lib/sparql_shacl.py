from typing import List
import streamlit as st
from schema import OntologyClass, OntologyProperty, Ontology
from lib.utils import ensure_uri
from lib.sparql_base import query
import lib.state as state


@st.cache_data(ttl='1d', show_spinner=False)
def get_shacl_classes() -> List[OntologyClass]:
    """Get the list of classes listed with the SHACL framework."""

    # From state
    endpoint = state.get_endpoint()

    text = """
        SELECT 
            ?uri 
            (COALESCE(?label_, 'Unknown Class Name') as ?label)
        WHERE {
            """ + ("GRAPH " + ensure_uri(endpoint.ontology_uri) + " {" if endpoint.ontology_uri else "") + """
                ?node a sh:NodeShape .
                ?node sh:name ?label_ .
                ?node sh:targetClass ?uri .
            """ + ("}" if endpoint.ontology_uri else "") + """
        }
    """

    # Execute the query
    response = query(text)

    # Transform into a list of OntologyClass instances, or an empty list
    classes = list(map(lambda cls: OntologyClass.from_dict(cls), response)) if response else []

    return classes


@st.cache_data(ttl='1d', show_spinner=False)
def get_shacl_properties() -> OntologyProperty:
    """Get the list of properties listed with the SHACL framework."""
    
    # From state
    endpoint = state.get_endpoint()

    text = """
        SELECT
            ?uri
            (COALESCE(?label_, ?uri) as ?label)
            (COALESCE(?order_, '') as ?order)
            (COALESCE(?min_count_, '') as ?min_count)
            (COALESCE(?max_count_, '') as ?max_count)
            ?domain_class_uri
            (COALESCE(?range_class_uri_1, ?range_class_uri_2, '') as ?range_class_uri)
        WHERE {
            """ + ("GRAPH " + ensure_uri(endpoint.ontology_uri) + " {" if endpoint.ontology_uri else "") + """
                ?shape sh:property ?node .
                ?node sh:path ?uri .  
                ?shape sh:targetClass ?domain_class_uri .
                OPTIONAL { ?node sh:name ?label_ . }
                OPTIONAL { ?node sh:order ?order_ . }
                OPTIONAL { ?node sh:minCount ?min_count_ . }
                OPTIONAL { ?node sh:maxCount ?max_count_ . }
                OPTIONAL {
                    ?node sh:class ?range_class_uri_1 .
                    ?range_shape sh:targetClass ?range_class_uri_1 .
                }
                OPTIONAL { ?node sh:datatype ?range_class_uri_2 . }
            """ + ("}" if endpoint.ontology_uri else "") + """
            FILTER(!isBlank(?uri))
        }
    """

    # Execute the query
    response = query(text)

    # Transform into a list of OntologyClass instances, or an empty list
    properties = list(map(lambda prop: OntologyProperty.from_dict(prop), response)) if response else []

    return properties


def get_shacl_ontology() -> Ontology:
    """
    Get all the classes, and properties from the shacl ontology.
    Fetch them from the right graph, thanks to the state.
    """

    classes = get_shacl_classes()
    properties = get_shacl_properties()

    return Ontology(classes=classes, properties=properties)


