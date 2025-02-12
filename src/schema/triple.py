from pydantic import BaseModel
from lib.utils import ensure_uri

class Triple(BaseModel):
    "Represents a graph triple"

    subject_uri: str
    predicate_uri: str
    object_uri: str

    def __init__(self, subject: str, predicate: str, object: str):
        super().__init__(subject_uri=subject, predicate_uri=predicate, object_uri=object)


    def to_sparql(self) -> str:
        """Transform the object into a proper SPARQL triple, ready to be injected into a query"""
        s = ensure_uri(self.subject_uri)
        p = ensure_uri(self.predicate_uri)
        o = ensure_uri(self.object_uri)
        return f"{s} {p} {o} ."
    
    def to_dict(self) -> dict:
        """Convert the Triple instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Triple':
        """Create a Triple instance from a dictionary"""
        return cls(**data)