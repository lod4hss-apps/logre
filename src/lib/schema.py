from typing import TypedDict
from lib.utils import ensure_uri

class Entity(TypedDict):
    """Any type of entity."""
    uri: str
    label: str
    comment: str


class Triple:
    """The basic object representing a triple."""
    subject: str
    predicate: str
    object: str

    def __init__(self, subject: str, predicate: str, object: str):
        self.subject = subject
        self.predicate = predicate
        self.object = object

    def to_sparql(self) -> str:
        s = ensure_uri(self.subject)
        p = ensure_uri(self.predicate)
        o = ensure_uri(self.object)
        return f"{s} {p} {o} ."


class EntityDetailed(Entity):
    """Any type of entity with class (and class label)."""
    cls: str
    class_label: str


class TripleDetailed(Triple):
    """All needed information of a triple."""
    subject_label: str
    subject_class: str
    subject_class_label: str
    predicate_label: str
    object_label: str
    object_class: str
    object_class_label: str
    isliteral: str


class SHACLclass(TypedDict):
    node: str # NodeShape uri. Corresponds to "information about a class"
    uri: str # Class URI eg Person, Birth, ...
    name: str # Label (sh:name) given to the class

