from typing import List, TypedDict, Tuple
import streamlit as st
from tools.sparql_base import query, execute
from tools.utils import ensure_uri


class Entity(TypedDict):
    uri: str
    label: str
    comment: str

class EntityWithClass(TypedDict):
    uri: str
    label: str
    cls: str
    class_label: str

class Triple:
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


@st.cache_data(ttl="1d", show_spinner=False)
def list_used_classes(graph = None) -> bool | List[Entity]:
    """
    List all classes available on the endpoint. 
    Only those from the default endpoint: does not look at the ontology, 
    but on how classes are used (ie: objects of 'subject a object' triples)
    """

    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

    text = """
        SELECT DISTINCT ?uri (COALESCE(?label_, ?uri) as ?label)
        WHERE { 
        """ + graph_begin + """
            ?subject a ?uri .
            optional { ?uri rdfs:label ?label_ . }
        """ + graph_end + """
        }
    """

    return query(text)


@st.cache_data(ttl="1d", show_spinner=False)
def list_entities(label: str, cls: str = None, limit: int = 20, graph = None) -> bool | List[EntityWithClass]:
    """
    Fetch the list of entities on the endpoint with:
    Args:
        label (str): the text that should be included in entity's rdfs:label 
        cls (str): entity's class, optional
        limit (int): max number of retrived entities
    """
    class_uri = ensure_uri(cls)

    # Get the entity label
    entity_label = f"?uri rdfs:label ?label ."
    # Only result of the given class if provided, else fetch the class
    entity_class = f"?uri a {class_uri} ." if cls else f"?uri a ?cls_ ."
    # Get the class label
    class_label = "optional { " + (f"{class_uri} rdfs:label ?class_label_ ." if cls else f"?cls_ rdfs:label ?class_label_ .") + " }"
    # Filter the result with the provided string
    label_filter = f"FILTER(CONTAINS(LCASE(?label), '{label.lower()}')) ."

    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

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
        LIMIT """ + str(limit) + """
    """

    return query(text)


@st.cache_data(ttl="1d", show_spinner=False)
def list_entity_triples(entity: str, graph=None) -> bool | List[Triple]:

    graph_begin = "GRAPH " + ensure_uri(graph) + " {" if graph else ""
    graph_end = "}" if graph else ""

    entity_uri = ensure_uri(entity)
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

    return query(text)


@st.cache_data(ttl="1d", show_spinner=False)
def list_graphs() -> bool | List[Entity]:
    """List all graphs available in the dataset."""

    text = """
        SELECT DISTINCT ?uri ?label ?comment
        WHERE {
            GRAPH ?uri {
                optional { ?uri rdfs:label ?label . }
                optional { ?uri rdfs:comment ?comment . }
            }
        }
    """
    return query(text)

@st.cache_data(ttl=60, show_spinner=False)
def count_graph_triples(graph: str):
    """Count how much triples there is in the selected dataset"""

    graph_uri = ensure_uri(graph)

    select = "SELECT (COUNT(*) as ?count)"
    where_begin = "WHERE {"
    where_end = "}"
    graph_begin = "GRAPH " + graph_uri + "{" if graph_uri else ''
    graph_end = "}" if graph_uri else ''
    triples = "?s ?p ?o."

    text = f"""
    {select}
    {where_begin}
        {graph_begin}
            {triples}
        {graph_end}
    {where_end}
    """
    return int(query(text)[0]['count'])



def insert(triples: List[tuple], graph:str="default") -> None:
    """
    From a list of tuples containing the triples in ('subject', 'predicate', 'object')
    format, insert them in the endpoint.
    """
    
    if graph != "default":
        graph_uri = ensure_uri(graph)
    else:
        graph_uri = "default"

    req_insert_begin = "INSERT DATA {"
    req_insert_end = "}"
    req_graph_begin = "GRAPH " + graph_uri + " {" if graph_uri != "default" else ""
    req_graph_end = "}" if graph_uri != "default" else ""


    step_nb = 10000

    for i in range(0, len(triples), step_nb):
            
        selected_triples = triples[i : i + step_nb]
        
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
        for triple in selected_triples:
            subject = ensure_uri(triple[0])
            predicate = ensure_uri(triple[1])
            object = ensure_uri(triple[2])
            texts_triples.append(f"{subject} {predicate} {object} .")

        # Build the request text
        text = text_begin + "\n".join(texts_triples) + text_end

        # Execute
        execute(text)


def delete(triples: List[tuple], graph:str="default") -> None:
    """
    From a list of tuples containing the triples in ('subject', 'predicate', 'object')
    format, deleted from the endpoint.
    """

    if graph != "default":
        graph_uri = ensure_uri(graph)
    else:
        graph_uri = "default"

    req_insert_begin = "DELETE WHERE {"
    req_insert_end = "}"
    req_graph_begin = "GRAPH " + graph_uri + " {" if graph_uri != "default" else ""
    req_graph_end = "}" if graph_uri != "default" else ""

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