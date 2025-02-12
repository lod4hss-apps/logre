from typing import Optional
from pydantic import BaseModel
from .entity import Entity
from .predicate import Predicate


class DisplayTriple(BaseModel):

    subject: Entity
    predicate: Predicate
    object: Entity


    def to_dict(self) -> dict:
        """Convert the DisplayTriple instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'DisplayTriple':
        """Create an DisplayTriple instance from a dictionary"""
        data['subject'] = Entity.from_dict(data, prefix="subject_")
        data['predicate'] = Predicate.from_dict(data, prefix="predicate_")
        data['object'] = Entity.from_dict(data, prefix="object_")
        return cls(**data)