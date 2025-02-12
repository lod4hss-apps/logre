from enum import Enum


class EndpointTechnology(Enum):
    NONE = 'None'
    FUSEKI = 'Fuseki'
    ALLEGROGRAPH = 'Allegrograph'

class OntologyFramework(Enum):
    NONE = 'None'
    SHACL = 'SHACL'
