from typing import List, Dict

from .graph import Graph
from .onto_entity import OntoEntity
from .onto_property import OntoProperty

class Ontology:

    name: str
    graph: Graph

    def __init__(self, graph: Graph, *args, **kwargs) -> None:
        self.graph = graph


    def get_classes(self) -> List[OntoEntity]:
        raise Exception(f'Method <get_classes> not implemented in {self.name}')
    

    def get_properties(self) -> List[OntoProperty]:
        raise Exception(f'Method <get_properties> not implemented in {self.name}')
    

    def get_classes_dict(self) -> Dict[str, OntoEntity]:
        """Get the classes list in a named dictionary format, for fast acces during joins for example."""
        return { item.uri: item.to_dict() for item in self.get_classes() }


    def get_properties_dict(self) -> Dict[str, OntoProperty]:
        """Get the properties list in a named dictionary format, for fast acces during joins for example."""
        return { item.get_key(): item.to_dict() for item in self.get_properties() }


    def get_class_name(self, class_uri: str) -> str:
        """From a given class URI, fetch the class name saved in the ontology."""
        selection = [cls for cls in self.get_classes() if cls.uri == class_uri]
        if len(selection): return selection[0].label
        else: return class_uri


    def is_property_mandatory(self, class_uri: str, property_uri: str) -> str:
        """For a given class and property, look if the latter is mandatory for those class instances (with property outgoing)."""
        selection = [property for property in self.get_properties() if property.domain_class_uri == class_uri and property.uri == property_uri]
        if len(selection) == 0: return False
        else: return selection[0].is_mandatory()