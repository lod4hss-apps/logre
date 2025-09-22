from enum import Enum
from graphly.schema import Sparql
from graphly.sparql import Fuseki, Allegrograph, GraphDB


class SPARQLTechnology(str, Enum):
    """
    Enum representing supported SPARQL endpoint technologies.

    Attributes:
        FUSEKI: Apache Jena Fuseki endpoint.
        ALLEGROGRAPH: AllegroGraph endpoint.
        GRAPHDB: GraphDB endpoint.
    """
    FUSEKI = "Fuseki"
    ALLEGROGRAPH = "Allegrograph"
    GRAPHDB = "GraphDB"


def get_sparql_technology(sparql_technology_name: str) -> Sparql:
    """
    Returns the corresponding SPARQL technology class based on the given technology name.

    Args:
        sparql_technology_name (str): The name of the SPARQL technology (e.g., 'FUSEKI', 'ALLEGROGRAPH', 'GRAPHDB').

    Returns:
        Sparql: The class representing the specified SPARQL technology.

    Raises:
        ValueError: If the provided technology name does not match any known SPARQL technology.
    """
    technology = SPARQLTechnology(sparql_technology_name)

    if technology == SPARQLTechnology.FUSEKI:
        return Fuseki
    elif technology == SPARQLTechnology.ALLEGROGRAPH:
        return Allegrograph
    elif technology == SPARQLTechnology.GRAPHDB:
        return GraphDB