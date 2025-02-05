from typing import List, TypedDict, Dict
import streamlit as st
from lib.sparql_base import query, execute
from lib.utils import ensure_uri
from lib.schema import Entity, EntityDetailed, Triple, TripleDetailed


def insert(triples: List[Triple], graph: str = None) -> None:
    """
    From a list of tuples containing the triples in tuple format
    (('subject', 'predicate', 'object)), insert them in the endpoint,
    in the given graph.
    """

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Since insert can be pretty huge, here we split 
    # in "smaller insert" of maximum 10k triples.
    step_nb = 10000
    for i in range(0, len(triples), step_nb):
        
        # Take only selected triples
        selected_triples = triples[i : i + step_nb]

        # Transform the triples into strings
        triples_str = '\n'.join(map(lambda triple: triple.to_sparql(), selected_triples))
        
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


def delete(triples: List[Triple], graph: str = None) -> None:
    """
    From a list of tuples containing the triples in ('subject', 'predicate', 'object')
    format, deleted from the endpoint.
    triples can be raw triple, or rules with variables.
    """

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
 

@st.cache_data(ttl="1d", show_spinner=False)
def list_used_classes(graph: str = None) -> List[Entity]:
    """
    List all classes available on the endpoint and graph, if specified. 
    Does not look at the ontology, but on how classes are used
    (ie: objects of 'subject a object' triples).
    """

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Prepare the query
    text = """
        SELECT DISTINCT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
        WHERE { 
            """ + ("GRAPH " + graph_uri + " {" if graph else "") + """
                ?s a ?uri .
                optional { ?uri rdfs:label ?label_ . }
            """ + ("}" if graph else "") + """
        }
    """

    # Execute on the endpoint
    response = query(text)

    # Ensure an array is returned
    if not response:
        return []
    return response


@st.cache_data(ttl='1d', show_spinner=False)
def list_used_properties(graph: str = None) -> List[Entity]:
    """
    List all properties available on the endpoint and graph. 
    Does not look at the ontology, but on how properties are used 
    (ie: properties of 'subject property object' triples).
    """

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Prepare the query
    text = """
        SELECT DISTINCT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
        WHERE { 
            """ + ("GRAPH " + graph_uri + " {" if graph else "") + """
                ?subject ?uri ?object .
                optional { ?uri rdfs:label ?label_ . }
            """ + ("}" if graph else "") + """
        }
    """

    # Execute on the endpoint
    response = query(text)

    # Ensure an array is returned
    if not response:
        return []
    return response


@st.cache_data(ttl="1d", show_spinner=False)
def list_entities(label: str = None, cls: str = None, limit: int = None, graph = None) -> List[EntityDetailed]:
    """
    Fetch the list of entities on the endpoint with:
    Args:
        label (str): the text that should be included in entity's rdfs:label. If None, fetch all entities.
        cls (str): entity's class. Filter by the given class, if specified
        limit (int): max number of retrived entities. If None, no limit is applied
    """

    # Make sure the given class is a valid URI
    class_uri = ensure_uri(cls)
    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Create parts of the request, depending on args:

    # Get the entity label
    entity_label = f"?uri rdfs:label ?label ."
    # Only result of the given class if provided, else fetch the class
    entity_class = f"?uri a {class_uri} ." if cls else "optional { ?uri a ?cls_ . }"
    # Get the class label
    class_label = "optional { " + (f"{class_uri} rdfs:label ?class_label_ ." if cls else f"?cls_ rdfs:label ?class_label_ .") + " }"
    # Filter the result with the provided string
    label_filter = f"FILTER(CONTAINS(LCASE(?label), '{label.lower()}')) ." if label else ""
    # Limit
    limit = f"LIMIT {limit}" if limit else ""

    # Build the query
    text = """
        SELECT DISTINCT 
            ?uri 
            ?label 
            (COALESCE(?cls_, '""" + (cls or 'Unknown') + """') as ?cls) 
            (COALESCE(?class_label_, ?cls) as ?class_label)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph else "") + """
                """ + entity_class + """
                """ + label_filter + """
                """ + entity_label + """
                """ + class_label + """
            """ + ("}" if graph else "") + """
        }
        """ + limit + """
    """

    # Execute on the endpoint
    response = query(text)

    # Ensure an array is returned
    if not response:
        return []
    return response


@st.cache_data(ttl="1d", show_spinner=False)
def list_entity_triples(entity: str, graph=None) -> List[Triple]:
    """
    Get the list of triples linked to the Entity.
    Make a union of all triples where the entity is subject, 
    and all triples where entity is object.
    Finally order by property ASC (alpha).
    """

    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity)

    # Only if the graph is not default (None)
    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

    # Prepare the query
    text = """
        SELECT  
            ?subject 
            (COALESCE(?subject_label_, 'No label') as ?subject_label) 
            (COALESCE(?subject_class_, 'No class') as ?subject_class) 
            (COALESCE(?subject_class_label_, ?subject_class) as ?subject_class_label)
            ?predicate 
            (COALESCE(?predicate_label_, ?predicate) as ?predicate_label)
            ?object 
            (COALESCE(?object_label_, ?object) as ?object_label) 
            (COALESCE(?object_class_, 'No class') as ?object_class) 
            (COALESCE(?object_class_label_, ?object_class) as ?object_class_label)
            (isLiteral(?object) as ?object_literal)
        WHERE {
            """ + graph_begin + """
            {
                """ + entity_uri + """ ?predicate ?object . 
                optional { """ + entity_uri + """ rdfs:label ?subject_label_ . }
                optional { 
                    """ + entity_uri + """ a ?subject_class_ .
                    optional {
                        ?subject_class_ rdfs:label ?subject_class_label_ .
                    }
                }
                optional { ?predicate rdfs:label ?predicate_label_ . }
                optional { ?object rdfs:label ?object_label_ . }
                optional { 
                    ?object a ?object_class_ .
                    optional {
                        ?object_class_ rdfs:label ?object_class_label_ .
                    }
                }
            }
            UNION
            {
                ?subject ?predicate """ + entity_uri + """ . 
                optional { ?subject rdfs:label ?subject_label_ . }
                optional { 
                    ?subject a ?subject_class_ .
                    optional {
                        ?subject_class_ rdfs:label ?subject_class_label_ .
                    }
                }
                optional { ?predicate rdfs:label ?predicate_label_ . }
                optional { """ + entity_uri + """ rdfs:label ?object_label_ . }
                optional { 
                    """ + entity_uri + """ a ?object_class_ .
                    optional {
                        ?object_class_ rdfs:label ?object_class_label_ .
                    }
                }
            }
            """ + graph_end + """
        }
        ORDER BY ASC(?predicate)
    """
    
    # Ensure response is an array
    response = query(text)
    if not response:
        return []
    return response


@st.cache_data(ttl="1d", show_spinner=False)
def list_graphs(_error_location) -> List[Entity]:
    """
    List all graphs available in the dataset.
    Leading underscore for "_error_location" arg is to tell streamlit to not serialize the argument.
    """

    # Prepare the query
    text = """
        SELECT DISTINCT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
            (COALESCE(?comment_, 'No comment') as ?comment)
        WHERE {
            GRAPH ?uri { ?s ?p ?o . }
            optional { ?uri rdfs:label ?label_ . }
            optional { ?uri rdfs:comment ?comment_ . }
        }
    """    

    # Ensure response is an array
    response = query(text, _error_location=_error_location)
    if not response:
        return []
    return response


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

    # Ensure response is an array
    response = query(text)
    if not response:
        return 0
    return int(response[0]['count'])


def get_objects_of(subject: str, property: str = None):
    """
    Fetch all objects of the given subject. 
    If the property is mentioned, only filter of subject of the given property.
    """

    subject_uri = ensure_uri(subject)
    property_uri = ensure_uri(property)

    select_line = f"?object" if property_uri else "?property ?object"
    query_line = f"{subject_uri} {property_uri} ?object" if property_uri else f"{subject_uri} ?property ?object"

    text = """
        SELECT """ + select_line + """
        WHERE { """ + query_line + """ . }
    """
    
    # Ensure response is an array
    response = query(text)
    if not response:
        return []
    return response



def get_subjects_of(object: str, property: str = None):
    """
    Fetch all subjects of the given object. 
    If the property is mentioned, only filter of object of the given property.
    """

    object_uri = ensure_uri(object)
    property_uri = ensure_uri(property)

    select_line = f"?subject" if property_uri else "?subject ?property"
    query_line = f"?subject {property_uri} {object_uri}" if property_uri else f"?subject ?property {object_uri}"

    text = """
        SELECT """ + select_line + """
        WHERE { """ + query_line + """ . }
    """
    
    # Ensure response is an array
    response = query(text)
    if not response:
        return []
    return response