from typing import List
import streamlit as st
from schema import OntologyClass, OntologyProperty, Ontology
from lib.utils import ensure_uri
from lib.sparql_base import query
import lib.state as state


def get_shacl_classes() -> List[OntologyClass]:
    """Get the list of classes listed with the SHACL framework."""

    # From state
    endpoint = state.get_endpoint()

    text = """
        SELECT 
            ?uri 
            (COALESCE(?label_, '') as ?label)
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


def get_shacl_properties() -> OntologyProperty:
    """Get the list of properties listed with the SHACL framework."""
    
    # From state
    endpoint = state.get_endpoint()

    text = """
        SELECT DISTINCT
            (COALESCE(?target_class_, '') as ?card_of_class_uri)
            (COALESCE(?label_, ?uri) as ?label)
            (COALESCE(?order_, '') as ?order)
            (COALESCE(?min_count_, '') as ?min_count)
            (COALESCE(?max_count_, '') as ?max_count)
            (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
            ?uri
            (COALESCE(?range_class_uri_, ?datatype_, '') as ?range_class_uri)
        WHERE {
            """ + ("GRAPH " + ensure_uri(endpoint.ontology_uri) + " {" if endpoint.ontology_uri else "") + """               
                ?shape sh:property ?node .
                ?node sh:path ?supposed_uri .  
                OPTIONAL { ?shape sh:targetClass ?target_class_ . }
                OPTIONAL { ?supposed_uri sh:inversePath ?inverse_property_uri . }
                OPTIONAL { ?node sh:name ?label_ . }
                OPTIONAL { ?node sh:order ?order_ . }
                OPTIONAL { ?node sh:minCount ?min_count_ . }
                OPTIONAL { ?node sh:maxCount ?max_count_ . }
                OPTIONAL { ?node sh:datatype ?datatype_ . }
                OPTIONAL { ?node sh:class ?class . }

                BIND(IF(isBlank(?supposed_uri), '', ?target_class_) as ?domain_class_uri_)
                BIND(IF(isBlank(?supposed_uri), ?target_class_, ?class) as ?range_class_uri_)
                BIND(IF(isBlank(?supposed_uri), ?inverse_property_uri, ?supposed_uri) as ?uri)
            """ + ("}" if endpoint.ontology_uri else "") + """
        }
    """

    # Execute the query
    response = query(text)

    # Transform into a list of OntologyClass instances, or an empty list
    properties = list(map(lambda prop: OntologyProperty.from_dict(prop), response)) if response else []

    return properties

@st.cache_data(show_spinner=False, ttl='1 day')
def get_shacl_ontology() -> Ontology:
    """
    Get all the classes, and properties from the shacl ontology.
    Fetch them from the right graph, thanks to the state.
    """

    classes = get_shacl_classes()
    properties = get_shacl_properties()

    return Ontology(classes=classes, properties=properties)


