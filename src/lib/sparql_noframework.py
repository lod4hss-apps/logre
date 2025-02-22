from typing import List
from schema import OntologyClass, OntologyProperty, Ontology
from lib.sparql_base import query
import lib.state as state


def get_noframework_classes() -> List[OntologyClass]:
    """Since there is no framework on the endpoint, trust the used ones."""

    # From state
    graph = state.get_graph()

    # Prepare the query
    text = """
        SELECT DISTINCT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
        WHERE { 
            """ + ("GRAPH " + graph.uri + " {" if graph.uri else "") + """
                ?s a ?uri .
                optional { ?uri rdfs:label ?label_ . }
            """ + ("}" if graph.uri else "") + """
        }
    """

    # Execute on the endpoint
    response = query(text)

    # Transform into a list of OntologyClass instances, or an empty list
    classes = list(map(lambda cls: OntologyClass.from_dict(cls), response)) if response else []

    return classes


def get_noframework_properties() -> List[OntologyProperty]:
    """Since there is no framework on the endpoint, trust the used ones."""

    # From state
    graph = state.get_graph()

    # Prepare the query
    text = """
        SELECT DISTINCT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
            (0 as ?order)
            (0 as ?min_count)
            (0 as ?max_count)
            (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
            (COALESCE(?range_class_uri_, 'Literal') as ?range_class_uri)
        WHERE { 
            """ + ("GRAPH " + graph.uri + " {" if graph.uri else "") + """
                ?subject_uri ?uri ?object_uri .
                optional { ?uri rdfs:label ?label_ . }
                optional { ?subject_uri a ?domain_class_uri_ . }
                optional { ?object_uri a ?range_class_uri_ . }
            """ + ("}" if graph.uri else "") + """
        }
    """

    # Execute the query
    response = query(text)

    # Transform into a list of OntologyClass instances, or an empty list
    properties = list(map(lambda prop: OntologyProperty.from_dict(prop), response)) if response else []

    return properties


def get_noframework_ontology() -> Ontology:
    """
    Get all the classes, and properties used in the selected graph,
    thanks to the state
    """

    classes = get_noframework_classes()
    properties = get_noframework_properties()

    return Ontology(classes=classes, properties=properties)