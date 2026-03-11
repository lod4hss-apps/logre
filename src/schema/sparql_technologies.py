from enum import Enum
from graphly.schema import Sparql
import graphly.schema.sparql as graphly_sparql
from graphly.sparql import Fuseki, Allegrograph, GraphDB, RDF4J
from lib.sparql_results import parse_sparql_json_response


def _patch_graphly_parser() -> None:
    graphly_sparql.parse_sparql_json_response = parse_sparql_json_response


_patch_graphly_parser()


class SPARQLTechnology(str, Enum):
    """
    Enum representing supported SPARQL endpoint technologies.

    Attributes:
        FUSEKI: Apache Jena Fuseki endpoint.
        ALLEGROGRAPH: AllegroGraph endpoint.
        GRAPHDB: GraphDB endpoint.
        RDF4J: Eclipse RDF4J endpoint.
    """

    FUSEKI = "Fuseki"
    ALLEGROGRAPH = "Allegrograph"
    GRAPHDB = "GraphDB"
    RDF4J = "RDF4J"


def get_sparql(
    sparql_dict: dict[str, str],
) -> Allegrograph | Fuseki | GraphDB | RDF4J | None:
    """
    Returns the right Sparql instance given a rightfull dictionnary

    Args:
        sparql_dict (dict[str, str]): the dictionnary version of a Sparql endpoint

    Returns:
        Sparql: Instance of the right Sparql endpoint
    """

    if sparql_dict["technology"] == SPARQLTechnology.ALLEGROGRAPH:
        return Allegrograph(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )
    if sparql_dict["technology"] == SPARQLTechnology.FUSEKI:
        return Fuseki(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )
    if sparql_dict["technology"] == SPARQLTechnology.GRAPHDB:
        return GraphDB(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )
    if sparql_dict["technology"] == SPARQLTechnology.RDF4J:
        return RDF4J(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )


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
    elif technology == SPARQLTechnology.RDF4J:
        return RDF4J
