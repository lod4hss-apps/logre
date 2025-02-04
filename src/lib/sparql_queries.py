from typing import List, TypedDict, Dict
import streamlit as st
from lib.sparql_base import query, execute
from lib.utils import ensure_uri


##### Model #####

class Entity(TypedDict):
    """Any type of entity."""

    uri: str
    label: str
    comment: str


class EntityWithClass(TypedDict):
    """Any type of entity with class (and class label)."""

    uri: str
    label: str
    cls: str
    class_label: str


class Triple:
    """All needed information of a triple."""

    subject: str
    subject_label: str
    subject_class: str
    subject_class_label: str
    predicate: str
    predicate_label: str
    object: str
    object_label: str
    object_class: str
    object_class_label: str
    isliteral: str


##### Functions #####    

@st.cache_data(ttl="1d", show_spinner=False)
def list_used_classes(graph: str = None) -> List[Entity]:
    """
    List all classes available on the endpoint and graph, if specified. 
    Does not look at the ontology, but on how classes are used
    (ie: objects of 'subject a object' triples).
    """

    # Only if the graph is not default (None)
    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

    # Prepare the query
    text = """
        SELECT DISTINCT ?uri (COALESCE(?label_, ?uri) as ?label)
        WHERE { 
        """ + graph_begin + """
            ?subject a ?uri .
            optional { ?uri rdfs:label ?label_ . }
        """ + graph_end + """
        }
    """

    # Ensure response is an array
    response = query(text)
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

    # Only if the graph is not default (None)
    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

    # Prepare the query
    text = """
        SELECT DISTINCT ?uri (COALESCE(?label_, ?uri) as ?label)
        WHERE { 
        """ + graph_begin + """
            ?subject ?uri ?object .
            optional { ?uri rdfs:label ?label_ . }
        """ + graph_end + """
        }
    """

    # Ensure response is an array
    response = query(text)
    if not response:
        return []
    return response


@st.cache_data(ttl="1d", show_spinner=False)
def list_entities(label: str = None, cls: str = None, limit: int = None, graph = None) -> List[EntityWithClass]:
    """
    Fetch the list of entities on the endpoint with:
    Args:
        label (str): the text that should be included in entity's rdfs:label. If None, fetch all entities.
        cls (str): entity's class. Filter by the given class, if specified
        limit (int): max number of retrived entities. If None, no limit is applied
    """

    # Make sure the given class is a valid URI
    class_uri = ensure_uri(cls)

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

    # Only if the graph is not default (None)
    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

    # Build the query
    text = """
        SELECT DISTINCT ?uri ?label (COALESCE(?cls_, '""" + (cls or 'Unknown') + """') as ?cls) (COALESCE(?class_label_, ?cls) as ?class_label)
        WHERE {
            """ + graph_begin + """
            """ + entity_class + """
            """ + label_filter + """
            """ + entity_label + """
            """ + class_label + """
            """ + graph_end + """
        }
        """ + limit + """
    """

    # Ensure response is an array
    response = query(text)
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
        SELECT  ?subject (COALESCE(?subject_label_, 'No label') as ?subject_label) (COALESCE(?subject_class_, 'No class') as ?subject_class) (COALESCE(?subject_class_label_, ?subject_class) as ?subject_class_label)
                ?predicate (COALESCE(?predicate_label_, ?predicate) as ?predicate_label)
                ?object (COALESCE(?object_label_, ?object) as ?object_label) (COALESCE(?object_class_, 'No class') as ?object_class) (COALESCE(?object_class_label_, ?object_class) as ?object_class_label)
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
    # text = """
    #     SELECT DISTINCT ?uri ?label ?comment 
    #     WHERE {
    #         GRAPH ?uri {
    #             optional { ?uri rdfs:label ?label . }
    #             optional { ?uri rdfs:comment ?comment . }
    #         }
    #     }
    # """

    text = """
        SELECT DISTINCT ?uri (CONCAT(COALESCE(?name, ?last_part), ' (', STR(?number), ')') as ?label) ?comment
        WHERE {
        {
            SELECT ?uri ?name (COUNT(*) as ?number) 
            WHERE {
                GRAPH ?uri { 
                    ?s ?p ?o 
                }
                OPTIONAL {?uri rdfs:label ?name .}
                OPTIONAL {?uri rdfs:comment ?comment .}
            }
            GROUP BY ?uri  ?name
        }
        UNION
        {
            SELECT (URI('http://my.org/default') as ?uri) (COUNT(*) as ?number) ('DEFAULT' as ?name) ('Default graph' as ?comment)
            WHERE {
                { ?s ?p ?o }
            }
        }
        ### noter qu'en Python il faut *2 de antislashes par rapport à SPARQL
        # en SPARQL \\/ 
        BIND (replace(str(?uri), "^(.*)(\\\\/)", "") as ?last_part)  
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


def insert(triples: List[tuple], graph: str = None) -> None:
    """
    From a list of tuples containing the triples in tuple format
    (('subject', 'predicate', 'object)), insert them in the endpoint,
    in the given graph.
    """

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Prepare the query
    req_insert_begin = "INSERT DATA {"
    req_insert_end = "}"
    req_graph_begin = "GRAPH " + graph_uri + " {" if graph else ""
    req_graph_end = "}" if graph else ""

    # Since insert can be pretty huge, here we split 
    # in "smaller insert" of maximum 10k triples.
    step_nb = 10000
    for i in range(0, len(triples), step_nb):
        
        # Take only selected triples
        selected_triples = triples[i : i + step_nb]
        
        # Prepare the query
        text_begin = f"""
        {req_insert_begin}
            {req_graph_begin}
        """
        text_end = f"""
            {req_graph_end}
        {req_insert_end}
        """

        # Generate triples
        texts_triples = []
        for triple in selected_triples:
            subject = ensure_uri(triple[0])
            predicate = ensure_uri(triple[1])
            object = ensure_uri(triple[2])
            texts_triples.append(f"{subject} {predicate} {object} .")

        # Build the request text
        text = text_begin + "\n".join(texts_triples) + text_end

        # Insert the triples in the endpoint
        execute(text)


def delete(triples: List[tuple], graph: str = None) -> None:
    """
    From a list of tuples containing the triples in ('subject', 'predicate', 'object')
    format, deleted from the endpoint.
    triples can be raw triple, or rules with variables.
    """

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph)

    # Prepare the query
    req_insert_begin = "DELETE WHERE {"
    req_insert_end = "}"
    req_graph_begin = "GRAPH " + graph_uri + " {" if graph else ""
    req_graph_end = "}" if graph else ""

    # Prepare the request
    text_begin = f"""
    {req_insert_begin}
        {req_graph_begin}
    """
    text_end = f"""
        {req_graph_end}
    {req_insert_end}
    """

    # Generate all triples
    texts_triples = []
    for triple in triples:
        subject = ensure_uri(triple[0])
        predicate = ensure_uri(triple[1])
        object = ensure_uri(triple[2])
        texts_triples.append(f"{subject} {predicate} {object} .")

    # Build the request text
    text = text_begin + "\n".join(texts_triples) + text_end

    # Execute
    execute(text)


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