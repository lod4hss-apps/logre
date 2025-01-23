from typing import List, Dict, Tuple
import streamlit as st
from lib.sparql_base import query, execute
from lib.utils import ensure_uri


@st.cache_data(ttl='1d', show_spinner=False)
def list_available_classes() -> List[Dict[str, str]]:

    text = """
        SELECT ?node ?uri ?label
        WHERE {
            GRAPH infocean:model {
                ?node a sh:NodeShape .
                ?node rdfs:label ?label .
                ?node sh:targetClass ?uri .
            }
        }
    """

    # Ensure response is an array
    response = query(text)
    if not response:
        return []
    return response


def list_properties_of_node(node: str):

    text = """ 
        SELECT ?propertyNode ?uri (COALESCE(?label_, ?uri) as ?label) (COALESCE(?datatype_, '') as ?datatype) (COALESCE(?class_, COALESCE(?inverseClass_, '')) as ?class) (COALESCE(?order_, 'inf') as ?order) (COALESCE(?minCount_, '0') as ?minCount) (COALESCE(?maxCount_, 'inf') as ?maxCount) (COALESCE(?inverseUri_, '') as ?inverseUri)
        WHERE {
            GRAPH infocean:model {
                """ + ensure_uri(node) + """ sh:property ?propertyNode .
                ?propertyNode sh:path ?uri .
                optional { ?uri sh:inversePath ?inverseUri_ . }
                optional { ?uri sh:class ?inverseClass_ . }

                optional { ?propertyNode rdfs:label ?label_ . }
                optional { ?propertyNode sh:datatype ?datatype_ . }
                optional { ?propertyNode sh:class ?class_ .}
                optional { ?propertyNode sh:order ?order_ . }
                optional { ?propertyNode sh:minCount ?minCount_ . }
                optional { ?propertyNode sh:maxCount ?maxCount_ . }
            }
        }
    """

    # Ensure response is an array
    response = query(text)
    if not response:
        return []
    return response
