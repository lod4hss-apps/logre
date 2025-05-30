from typing import List, Any
from .sparql import SPARQL
from .sparql_allegrograph import Allegrograph
from .sparql_fuseki import Fuseki
from .sparql_graphdb import GraphDB
from .errors import EndpointTechnologyNotSupported
from .prefix import Prefix
from .data_bundle import DataBundle


class Endpoint:

    name: str
    base_uri: str
    sparql: SPARQL = None
    data_bundles: List[DataBundle] = None
    

    def __init__(self, technology: str, name: str, url: str, username: str, password: str, base_uri: str) -> 'Endpoint':

        # Set the right Endpoint technology (mandatory)
        Technology = Endpoint.get_entpoint_technology(technology)
        self.sparql = Technology(url, username, password)

        # Add the base prefix
        self.base_uri = base_uri
        if 'base' not in list(map(lambda p: p.short, self.sparql.prefixes)):
            self.sparql.prefixes.append(Prefix('base', base_uri))

        # Set other attributes
        self.name = name

        # Initialize others things
        self.data_bundles = []


    @staticmethod
    def get_entpoint_technology(technology_name: str) -> SPARQL:
        """Set the right Endpoint technology (mandatory)"""
        if technology_name == "Fuseki": return Fuseki
        elif technology_name == "Allegrograph": return Allegrograph
        elif technology_name == "GraphDB": return GraphDB
        else: raise EndpointTechnologyNotSupported(technology_name)

    @staticmethod
    def from_dict(obj: dict) -> 'Endpoint':
        """Convert an object into a Class instance."""

        endpoint = Endpoint(
            technology=obj.get('technology'), base_uri=obj.get('base_uri'),
            name=obj.get('name'), url=obj.get('url'),
            username=obj.get('username'), password=obj.get('password')
        )
        endpoint.data_bundles = [DataBundle.from_dict(obj_data_bundle, endpoint.sparql) for obj_data_bundle in obj.get('data_bundles')]

        prefixes_have = set(list(map(lambda p: p.short, endpoint.sparql.prefixes)))
        endpoint.sparql.prefixes += [Prefix.from_dict(obj_prefix) for obj_prefix in obj.get('prefixes', []) if obj_prefix.get('short') not in prefixes_have]
        
        return endpoint


    def to_dict(self) -> Any:
        """Convert the Class instance into a serializable object."""
        return {
            'name': self.name,
            'url': self.sparql.url,
            'technology': self.sparql.name,
            'username': self.sparql.username,
            'password': self.sparql.password,
            'base_uri': self.base_uri,
            'data_bundles': [data_bundle.to_dict() for data_bundle in self.data_bundles],
            'prefixes': [p.to_dict() for p in self.sparql.get_prefixes()],
        }
