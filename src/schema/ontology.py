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
        selection = [cls for cls in self.classes if cls.uri == class_uri]
        if len(selection): return selection[0].label
        else: return class_uri