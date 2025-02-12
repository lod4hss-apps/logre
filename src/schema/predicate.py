from typing import Optional, Dict
from pydantic import BaseModel, Field, model_validator

class Predicate(BaseModel):
    """An predicate (edge) from a graph"""

    uri: str
    label: Optional[str] = None

    order: Optional[int] = None
    min_count: Optional[int] = None
    max_count: Optional[int] = None

    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    
    display_label: str = Field(init=False)


    @model_validator(mode="before")
    @classmethod
    def set_display_label(cls, values):
        label = values.get("label") or "Unknown Label"
        uri = values.get("uri")
        values["display_label"] = f"{label} ({uri})"
        return values
    
    def to_dict(self) -> dict:
        """Convert the Predicate instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, str], prefix=None) -> 'Predicate':
        """Create an Predicate instance from a dictionary"""
        if prefix:
            data_to_take = {}
            for key, value in data.items():
                if key.startswith(prefix):
                    data_to_take[key.replace(prefix, '')] = value
            return cls(**data_to_take)
        return cls(**data)