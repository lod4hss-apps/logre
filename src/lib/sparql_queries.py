from typing import List, TypedDict, Dict
import streamlit as st
from lib.sparql_base import query, execute
from lib.utils import ensure_uri
from lib.schema import EntityDetailed, TripleDetailed
from schema import Graph, Triple, OntologyFramework, Entity
import lib.state as state
from lib.sparql_noframework import get_noframework_ontology
from lib.sparql_shacl import get_shacl_ontology
from schema.ontology import Ontology
from schema import DisplayTriple
import pandas as pd


@st.cache_data(ttl="1d", show_spinner=False)
def list_graphs() -> List[Graph]:
    """List all graphs available in the SPARQL endpoint."""

    # Prepare the query
    text = """
        SELECT DISTINCT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
            (COALESCE(?comment_, '') as ?comment)
        WHERE {
            GRAPH ?uri { ?s ?p ?o . }
            optional { ?uri rdfs:label ?label_ . }
            optional { ?uri rdfs:comment ?comment_ . }
        }
    """    

    # Execute the query
    response = query(text, caller='sparql_queries.list_graphs')
    
    # Transform list of objects into list of graphs
    if response: return list(map(lambda obj: Graph.from_dict(obj), response))
    # And ensure a list is returned
    else: return []


@st.cache_data(ttl=60, show_spinner=False)
def count_graph_triples(graph: str) -> int:
    """Count how much triples there is in the selected dataset/graph"""

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Prepare the query
    select = "SELECT (COUNT(*) as ?count)"
    where_begin = "WHERE {"
    where_end = "}"
    graph_begin = "GRAPH " + graph_uri + "{" if graph_uri else ''
    graph_end = "}" if graph_uri else ''
    triples = "?s ?p ?o."

    # Build the query
    text = f"""
    {select}
    {where_begin}
        {graph_begin}
            {triples}
        {graph_end}
    {where_end}
    """

    # Execute the query
    response = query(text)

    # Make sure a number is answered
    if not response: return 0
    return int(response[0]['count'])


def get_ontology() -> Ontology:

    # From state
    framework = state.get_endpoint().ontology_framework

    if framework == OntologyFramework.SHACL.value:
        return get_shacl_ontology()
    
    return get_noframework_ontology()
    

def find_entities(label_filter: str = None, class_filter: str = None, limit: int = None) -> List[Entity]:
    """
    Fetch the list of entities on the endpoint with:
    Args:
        label (str): the text that should be included in entity's rdfs:label. If None, fetch all entities.
        cls (str): entity's class. Filter by the given class, if specified
        limit (int): max number of retrived entities. If None, no limit is applied
    """

    # From state
    graph = state.get_graph()

    # Make sure the given class is a valid URI
    class_uri = ensure_uri(class_filter)

    text = """
        SELECT
            (?uri_ as ?uri)
            (COALESCE(?label_, '') as ?label)
            (COALESCE(?comment_, '') as ?comment)
            (COALESCE(?class_uri_, '""" + (class_uri if class_uri else "No Class URI")  + """') as ?class_uri)
        WHERE {
            """ + ("GRAPH " + ensure_uri(graph.uri) + " {" if graph.uri else "") + """
                ?uri_ a """ + (class_uri if class_uri else "?class_uri_")  + """ .
                OPTIONAL { ?uri_ rdfs:label ?label_ . }
                OPTIONAL { ?uri_ rdfs:comment ?comment_ . }
            """ + ("}" if graph.uri else "") + """
            """ + (f"FILTER(CONTAINS(LCASE(?label_), '{label_filter.lower()}')) ." if label_filter else "") + """
        }
        """ + (f"LIMIT {limit}" if limit else "") + """
    """


    # Execute on the endpoint
    response = query(text)

    # If there is no result, there is no point to go forward
    if not response: 
        return []

    # For each retrieved entity, look for the class label in the ontology, 
    # then transform into instances of "Entity"
    ontology = get_ontology()
    classes = list(map(lambda cls: {**cls, 'class_label': ontology.get_class_name(cls['class_uri'])}, response))
    entities = list(map(lambda cls: Entity.from_dict(cls), classes))
    
    return entities


def get_entity_card(entity: Entity, graph: Graph = None) -> List[DisplayTriple]:
    """Fetch all relevant triples (according to the ontology) from the given graph about the given entity."""

    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity.uri)
    graph_uri = ensure_uri(graph.uri)

    # Fetch only the wanted properties
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()
    wanted_properties = [ensure_uri(prop.uri) for prop in ontology.properties]

    # Prepare the query (Outgoing properties)
    text = """
        SELECT DISTINCT
            ('""" + entity.uri + """' as ?subject_uri)
            ('""" + entity.label + """' as ?subject_label)
            ('""" + entity.class_uri + """' as ?subject_class_uri)
            ('""" + (entity.comment or '') + """' as ?subject_comment)
            ?predicate_uri
            ?object_uri
            (COALESCE(?object_label_, '') as ?object_label)
            (COALESCE(?object_class_uri_, '') as ?object_class_uri)
            (isLiteral(?object_uri) as ?object_is_literal)
            (COALESCE(?object_comment_, '') as ?object_comment)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                """ + entity_uri + """ ?predicate_uri ?object_uri . 
                OPTIONAL { ?object_uri rdfs:label ?object_label_ . }
                OPTIONAL { ?object_uri a ?object_class_uri_ . }
                OPTIONAL { ?object_uri rdfs:comment ?object_comment_ . }
                VALUES ?predicate_uri { """ + ' '.join(wanted_properties) + """ }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Outgoing properties)
    outgoing_props = query(text)


    # Prepare que query (Incoming properties)
    text = """
        SELECT DISTINCT
            ?subject_uri
            (COALESCE(?subject_label_, '') as ?subject_label)
            (COALESCE(?subject_class_uri_, '') as ?subject_class_uri)
            (COALESCE(?subject_comment_, '') as ?subject_comment)
            ?predicate_uri
            ('""" + entity.uri + """' as ?object_uri)
            ('""" + entity.label + """' as ?object_label)
            ('""" + entity.class_uri + """' as ?object_class_uri)
            ('""" + (entity.comment or '') + """' as ?object_comment)
            ('false' as ?object_is_literal)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                ?subject_uri ?predicate_uri """ + entity_uri + """ . 
                ?subject_uri rdfs:label ?subject_label_ .
                OPTIONAL { ?subject_uri a ?subject_class_uri_ . }
                OPTIONAL { ?subject_uri rdfs:comment ?subject_comment_ . }
                VALUES ?predicate_uri { """ + ' '.join(wanted_properties) + """ }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Incoming properties)
    incoming_props = query(text)

    # Merge the data (left joins)
    display_triples_list = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}) ,
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in outgoing_props + incoming_props]

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    # Sort on predicate order
    display_triples.sort(key=lambda item: item.predicate.order)

    return display_triples



def get_entity_outgoing_triples(entity: Entity, graph: Graph = None) -> List[DisplayTriple]:
    """Fetch all outgoing triples from the given graph about the given entity."""

    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity.uri)
    graph_uri = ensure_uri(graph.uri)

    # Fetch only the wanted properties
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()

    # Prepare the query (Outgoing properties)
    text = """
        SELECT DISTINCT
            ('""" + entity.uri + """' as ?subject_uri)
            ('""" + entity.label + """' as ?subject_label)
            ('""" + entity.class_uri + """' as ?subject_class_uri)
            ('""" + (entity.comment or '') + """' as ?subject_comment)
            ?predicate_uri
            ?object_uri
            (COALESCE(?object_label_, '') as ?object_label)
            (COALESCE(?object_class_uri_, '') as ?object_class_uri)
            (isLiteral(?object_uri) as ?object_is_literal)
            (COALESCE(?object_comment_, '') as ?object_comment)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                """ + entity_uri + """ ?predicate_uri ?object_uri . 
                OPTIONAL { ?object_uri rdfs:label ?object_label_ . }
                OPTIONAL { ?object_uri a ?object_class_uri_ . }
                OPTIONAL { ?object_uri rdfs:comment ?object_comment_ . }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Outgoing properties)
    outgoing_props = query(text)

    # Merge the data (left joins)
    display_triples_list = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}) ,
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in outgoing_props]

    # Here, since we are making a left join, some of the triples are not in the onotlogy, so we need to make sure that some information are set
    display_triples_list = [{
        **triple, 
        "predicate_order": triple["predicate_order"] if "predicate_order" in triple and triple["predicate_order"] is not None else 1000000000000000000
    } for triple in display_triples_list]

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    # Sort on predicate order
    display_triples.sort(key=lambda item: item.predicate.order)

    return display_triples


def get_entity_incoming_triples(entity: Entity, graph: Graph = None) -> List[DisplayTriple]:
    """Fetch all incoming triples from the given graph about the given entity."""

    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity.uri)
    graph_uri = ensure_uri(graph.uri)

    # Fetch only the wanted properties
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()

    # Prepare the query (Outgoing properties)
    text = """
        SELECT DISTINCT
            ?subject_uri
            (COALESCE(?subject_label_, 'No label') as ?subject_label)
            (COALESCE(?subject_class_uri_, '') as ?subject_class_uri)
            (COALESCE(?subject_comment_, '') as ?subject_comment)
            ?predicate_uri
            ('""" + entity.uri + """' as ?object_uri)
            ('""" + entity.label + """' as ?object_label)
            ('""" + entity.class_uri + """' as ?object_class_uri)
            ('""" + (entity.comment or '') + """' as ?object_comment)
            ('false' as ?object_is_literal)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                ?subject_uri ?predicate_uri """ + entity_uri + """ . 
                ?subject_uri rdfs:label ?subject_label_ .
                OPTIONAL { ?subject_uri a ?subject_class_uri_ . }
                OPTIONAL { ?subject_uri rdfs:comment ?subject_comment_ . }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Outgoing properties)
    outgoing_props = query(text)

    # Merge the data (left joins)
    display_triples_list = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}) ,
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in outgoing_props]

    # Here, since we are making a left join, some of the triples are not in the onotlogy, so we need to make sure that some information are set
    display_triples_list = [{
        **triple, 
        "predicate_order": triple["predicate_order"] if "predicate_order" in triple and triple["predicate_order"] is not None else 1000000000000000000
    } for triple in display_triples_list]

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    # Sort on predicate order
    display_triples.sort(key=lambda item: item.predicate.order)

    return display_triples