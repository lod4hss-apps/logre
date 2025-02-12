from schema import Prefix
import lib.state as state

prefixes = [
    Prefix(short='xsd', url='http://www.w3.org/2001/XMLSchema#'),
    Prefix(short='rdf', url='http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    Prefix(short='rdfs', url='http://www.w3.org/2000/01/rdf-schema#'),
    Prefix(short='owl', url='http://www.w3.org/2002/07/owl#'),
    Prefix(short='sh', url='http://www.w3.org/ns/shacl#'),
    Prefix(short='crm', url='http://www.cidoc-crm.org/cidoc-crm/'),
    Prefix(short='sdh', url='https://sdhss.org/ontology/core/'),
    Prefix(short='sdh-shortcut', url='https://sdhss.org/ontology/shortcuts/'),
    Prefix(short='sdh-shacl', url='https://sdhss.org/shacl/profiles/'),
    Prefix(short='ontome', url='https://ontome.net/ontology/'),
]



def get_sparql_prefixes() -> str:
    """
    Transform the list of prefixes into a valid SPARQL.
    Done to avoid to put manually all prefixes everywhere.
    """
    # Add the dynamic one (base)
    all_prefixes = prefixes + [Prefix(short='base', url=state.get_endpoint().base_uri)]

    # Transform to list of string
    prefixes_str = list(map(lambda p: p.to_sparql(), all_prefixes))

    # Transform into a single string
    return '\n'.join(prefixes_str)


def shorten_uri(uri: str) -> str:
    """
    Replace all long URIs by its short prefix.
    Usefull to display in the GUI.
    """

    # Add the dynamic one (base)
    all_prefixes = prefixes + [Prefix(short='base', url=state.get_endpoint().base_uri)]
    
    for prefix in all_prefixes:
        uri = prefix.shorten(uri)
    return uri

def explicits_uri(uri: str) -> str:
    """
    Replace the short URIs by its explicit version.
    Usefull to display in the GUI.
    """

    # Add the dynamic one (base)
    all_prefixes = prefixes + [Prefix(short='base', url=state.get_endpoint().base_uri)]
    
    for prefix in all_prefixes:
        uri = prefix.explicit(uri)
    return uri

