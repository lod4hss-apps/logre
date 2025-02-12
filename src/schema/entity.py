from typing import Optional, Dict
from pydantic import BaseModel, Field, model_validator

class Entity(BaseModel):
    """An entity (node) from a graph"""

    uri: str = None
    label: Optional[str] = None
    comment: Optional[str] = None
    is_literal: bool = False

    class_uri: Optional[str] = None
    class_label: Optional[str] = None

    display_label: str = Field(init=False)
    display_label_comment: str = Field(init=False)


    @model_validator(mode="before")
    @classmethod
    def set_labels(cls, values):
        if values.get('is_literal') == 'true':
            uri = values.get('uri')
            values["uri"] = ""
            values["label"] = uri
            values["display_label"] = uri
            values["display_label_comment"] = uri
            values["is_literal"] = True
        else:
            uri = values.get('uri')
            label = values.get("label") or uri
            class_label = values.get("class_label") or values.get("class_uri") or "Unknown Class"
            comment = values.get("comment") or ""
            display_label = f"{label} ({class_label})" if class_label else label
            display_label_comment = display_label if not comment else display_label + ": " + comment
            values["display_label"] = display_label
            values["display_label_comment"] = display_label_comment
            values["is_literal"] = False
        return values

    def to_dict(self) -> dict:
        """Convert the Entity instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, str], prefix=None) -> 'Entity':
        """Create an Entity instance from a dictionary"""
        if prefix:
            data_to_take = {}
            for key, value in data.items():
                if key.startswith(prefix):
                    data_to_take[key.replace(prefix, '')] = value
            return cls(**data_to_take)
        return cls(**data)