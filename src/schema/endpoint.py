from typing import Optional
from pydantic import BaseModel, Field
from schema.enums import EndpointTechnology, OntologyFramework


class Endpoint(BaseModel):
    "A SPARQL endpoint and all its needed information"

    # For Pydantic
    model_config = {
        "use_enum_values": True # Make sure the enums are saved as values
    }

    name: str
    url: str
    technology: Optional[EndpointTechnology] = EndpointTechnology.NONE
    base_uri: Optional[str] = 'http://www.example.org/'
    ontology_uri: Optional[str] = None
    ontology_framework: Optional[OntologyFramework] = OntologyFramework.NONE
    username: Optional[str] = None
    password: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the Endpoint instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Endpoint':
        """Create an Endpoint instance from a dictionary"""

        # Parse the object 
        parsed = cls(**data)

        # Parse the enums correctly
        if parsed.technology: parsed.technology = EndpointTechnology(parsed.technology)
        else: parsed.technology = EndpointTechnology.NONE
        if parsed.ontology_framework: parsed.ontology_framework = OntologyFramework(parsed.ontology_framework)
        else: parsed.ontology_framework = OntologyFramework.NONE

        return parsed
