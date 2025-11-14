from typing import Dict, Any
from graphly.schema.property import Property
from graphly.schema.resource import Resource


class Statement:
    """
    Represents an RDF-like statement (triple) composed of a subject, a property, and an object.

    Attributes:
        subject (Resource): The subject resource of the statement.
        predicate (Property): The property linking the subject and object.
        object (Resource): The object resource of the statement.

    Methods:
        __init__(subject, predicate, object):
            Initialize a Statement instance with the given subject, property, and object.
        to_dict() -> Dict[str, Any]:
            Convert the statement into a dictionary representation.
        from_dict(obj: Dict[str, Any]) -> Statement:
            Create a Statement instance from a dictionary representation.
    """

    subject: Resource
    predicate: Property
    object: Resource


    def __init__(self, subject: Resource, predicate: Property, object: Resource) -> None:
        """
        Initializes a triple consisting of a subject, a property, and an object.

        Parameters:
            subject (Resource): The subject resource of the triple.
            property (Property): The property linking the subject and object.
            object (Resource): The object resource of the triple.
        """
        self.subject = subject
        self.predicate = predicate
        self.object = object


    def to_dict(self) -> Dict[str, Any]: 
        """
        Converts the triple into a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary with keys 'subject', 'property', and 'object',
            each containing the dictionary representation of the corresponding component.
        """
        return {
            'subject': self.subject.to_dict(),
            'predicate': self.predicate.to_dict(),
            'object': self.object.to_dict()
        }
    

    @staticmethod
    def from_dict(obj: Dict[str, Any]) -> 'Statement':
        """
        Creates a Statement instance from a dictionary representation.

        Parameters:
            obj (Dict[str, Any]): A dictionary containing 'subject', 'property', and 'object' data.

        Returns:
            Statement: An instance of the Statement class with its components populated from the dictionary.
        """
        return Statement(
            subject=Resource.from_dict(obj.get('subject')),
            predicate=Property.from_dict(obj.get('predicate')),
            object=Resource.from_dict(obj.get('object')),
        )