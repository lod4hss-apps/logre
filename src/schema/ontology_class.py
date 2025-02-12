from pydantic import BaseModel, Field, model_validator

class OntologyClass(BaseModel):

    uri: str = "No uri"
    label: str = "No class name"

    display_label: str = Field(init=False)

    @model_validator(mode="before")
    @classmethod
    def set_display_label(cls, values):
        label = values.get("label") or "Unknown class name"
        uri = values.get("uri") or "Unknown class URI"
        values["display_label"] = f"{label} ({uri})" if uri else label
        return values

    def to_dict(self) -> dict:
        """Convert the OntologyClass instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'OntologyClass':
        """Create an OntologyClass instance from a dictionary"""
        return cls(**data)