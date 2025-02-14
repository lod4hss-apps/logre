from typing import Optional
from pydantic import BaseModel
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

        # Ensure enums are correctly parsed
        if isinstance(data.get("technology"), str):
            data["technology"] = EndpointTechnology(data["technology"])
        if isinstance(data.get("ontology_framework"), str):
            data["ontology_framework"] = OntologyFramework(data["ontology_framework"])

        return cls(**data)
