from enum import Enum

class EndpointTechnology(Enum):
    NONE = 'None'
    FUSEKI = 'Fuseki'
    ALLEGROGRAPH = 'Allegrograph'
    GRAPHDB = 'GraphDB'

class OntologyFramework(Enum):
    NONE = 'None'
    SHACL = 'SHACL'

class EntityType(Enum):
    RESOURCE = "resource"
    GRAPH = "graph"