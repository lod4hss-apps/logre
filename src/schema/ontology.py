from typing import List, Dict
from pydantic import BaseModel
from .ontology_class import OntologyClass
from .ontology_property import OntologyProperty

class Ontology(BaseModel):

    classes: List[OntologyClass] = []
    properties: List[OntologyProperty] = []

    def get_classes_named_dict(self) -> Dict[str, OntologyClass]:
        """Get the classes list in a named dictionary format, for fast acces during joins for example."""
        return { item.uri: item.to_dict() for item in self.classes }


    def get_properties_named_dict(self) -> Dict[str, OntologyProperty]:
        """Get the properties list in a named dictionary format, for fast acces during joins for example."""
        return { item.get_key(): item.to_dict() for item in self.properties }


    def get_class_name(self, class_uri: str) -> str:
        """From a given class URI, fetch the class name saved in the ontology."""
        selection = [cls for cls in self.classes if cls.uri == class_uri]
        if len(selection): return selection[0].label
        else: return class_uri

    def is_property_mandatory(self, class_uri: str, property_uri: str) -> str:
        """For a given class and property, look if the latter is mandatory for those class instances (with property outgoing)."""
        selection = [property for property in self.properties if property.domain_class_uri == class_uri and property.uri == property_uri]
        if len(selection) == 0: return False
        else: return selection[0].is_mandatory()