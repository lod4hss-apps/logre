from typing import List, TypedDict, Tuple
import streamlit as st
from tools.sparql_base import query
from tools.utils import ensure_uri


class Class(TypedDict):
    uri: str
    label: str

@st.cache_data(ttl=300, show_spinner=False)
def list_used_classes() -> bool | List[Class]:
    """
    List all classes available on the endpoint. 
    Only those from the default endpoint: does not look at the ontology, 
    but on how classes are used (ie: objects of 'subject a object' triples)
    """

    text = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?uri ?label
        WHERE { 
            ?subject a ?uri .
            ?uri rdfs:label ?label .
        }
    """

    return query(text)


class Entity(TypedDict):
    uri: str
    label: str
    cls: str
    class_label: str


def list_entities(label: str, cls: str = None, limit: int = 20) -> bool | List[Entity]:
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
    entity_class = f"?uri a {class_uri} ." if cls else f"?uri a ?cls ."
    # Get the class label
    class_label = f"{class_uri} rdfs:label ?class_label ." if cls else f"?cls rdfs:label ?class_label ."
    # Filter the result with the provided string
    label_filter = f"FILTER(CONTAINS(LCASE(?label), '{label.lower()}')) ."

    text = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?uri ?label ?cls ?class_label
        WHERE {
            """ + entity_class + """
            """ + label_filter + """
            """ + entity_label + """
            """ + class_label + """
        }
        LIMIT """ + str(limit) + """
    """

    return query(text)


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


@st.cache_data(ttl=300, show_spinner=False)
def list_entity_triples(entity: str) -> bool | List[Triple]:

    entity_uri = ensure_uri(entity)
    text = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?subject ?subject_label ?subject_class ?subject_class_label ?predicate ?predicate_label ?object ?object_label ?object_class ?object_class_label (isLiteral(?object) as ?object_literal)
        WHERE {
            {
                """ + entity_uri + """ ?predicate ?object . 
                optional { """ + entity_uri + """ rdfs:label ?subject_label . }
                optional { 
                    """ + entity_uri + """ a ?subject_class .
                    optional {
                        ?subject_class rdfs:label ?subject_class_label .
                    }
                }
                optional { ?predicate rdfs:label ?predicate_label . }
                optional { ?object rdfs:label ?object_label . }
                optional { 
                    ?object a ?object_class .
                    optional {
                        ?object_class rdfs:label ?object_class_label .
                    }
                }
            }
            UNION
            {
                ?subject ?predicate """ + entity_uri + """ . 
                optional { ?subject rdfs:label ?subject_label . }
                optional { 
                    ?subject a ?subject_class .
                    optional {
                        ?subject_class rdfs:label ?subject_class_label .
                    }
                }
                optional { ?predicate rdfs:label ?predicate_label . }
                optional { """ + entity_uri + """ rdfs:label ?object_label . }
                optional { 
                    """ + entity_uri + """ a ?object_class .
                    optional {
                        ?object_class rdfs:label ?object_class_label .
                    }
                }
            }
        }
        ORDER BY ASC(?predicate)
    """

    return query(text)