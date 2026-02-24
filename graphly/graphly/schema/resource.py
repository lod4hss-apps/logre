from typing import Literal, Dict, Any

class Resource:
    """
    Represents a resource that can be an IRI, a literal, or a blank node.

    Attributes:
        resource_type (Literal['blank', 'iri', 'literal']):
            The type of the resource.
        value (Any):
            The value itself (URI, string, number, ...).
        uri (str):
            The URI of the resource, if applicable.
        label (str):
            A human-readable label for the resource (eg: object of rdfs:label).
        comment (str):
            Additional descriptive information about the resource (eg: object of rdfs:comment).
        class_uri (str):
            The URI of the class this resource belongs to, if any (eg: object of rdf:type).

    Methods:
        __init__(value, label=None, comment=None, class_uri=None, resource_type='iri'):
            Initialize a Resource instance with the given attributes.
        get_text(comment: bool = False) -> str:
            Get a human-readable string representation of the resource, optionally including the comment.
        to_dict(prefix: str = '') -> dict:
            Convert the resource into a dictionary representation, with an optional key prefix.
        from_dict(obj: dict, prefix: str = '') -> Resource:
            Create a Resource instance from a dictionary representation.
    """

    # To define the type of resource it is
    resource_type: Literal['blank', 'iri', 'literal']

    # Information about the resource
    literal: str | int | float
    uri: str
    label: str 
    comment: str
    class_uri: str 


    def __init__(self, value: Any, label: str = None, comment: str = None, class_uri: str = None, resource_type: Literal['blank', 'iri', 'literal'] = 'iri') -> None:
        """
        Initialize a Resource object.

        Args:
            value (Any): The URI of the resource if it's an IRI,
                or the literal value if the resource is a literal. Defaults to None.
            label (str, optional): A human-readable label for the resource (eg: object of rdfs:label). Defaults to None.
            comment (str, optional): Additional information or description of the resource (eg: object of rdfs:comment). Defaults to None.
            resource_type (Literal['blank', 'iri', 'literal'], optional): 
                Specifies the type of the resource. Defaults to 'iri'.
            class_uri (str, optional): The URI of the class this resource belongs to (if any) (eg: object of rdf:type). Defaults to None.

        Attributes set based on type:
            - If the resource is a literal, `self.value` is set.
            - If the resource is an entity or blank node, `self.uri`, `self.label`, `self.comment`, 
            and `self.class_uri` are set.
        """

        self.resource_type = resource_type

        if self.resource_type == 'literal':
            self.literal = value
            self.text = f"{self.literal}"
            self.class_uri = class_uri or None
        else: 
            self.uri = value
            self.label = label or None
            self.comment = comment or None
            self.class_uri = class_uri or None


    def get_text(self, comment: bool = False) -> str:
        """
        Get a string representation of the resource.

        For literal resources, returns the literal as a string.
        For entity or blank resources, returns the label if available, otherwise the URI.
        Optionally appends the comment if `comment=True` and a comment exists.

        Args:
            comment (bool, optional): Whether to include the resource's comment in the output. Defaults to False.

        Returns:
            str: The textual representation of the resource.
        """

        # If the Resource is a literal, just returns it
        if self.resource_type == 'literal': 
            return f"{self.literal}"

        # But if it is an Entity, construct a Text
        text = f"{self.label or self.uri}"
        # And append the comment if asked
        if comment and self.comment: 
            return f"{text}: {self.comment}"
        # Otherwise just return the text without the comment
        return text


    def to_dict(self, prefix: str= '') -> Dict[str, Any]:
        """
        Converts the object into a dictionary representation.

        Parameters:
            prefix (str): Optional string to prepend to each key in the dictionary.

        Returns:
            dict: A dictionary containing the object's properties. Includes 'literal' if the object represents a literal,
                or 'uri', 'label', 'comment', and 'class_uri' if it represents an entity.
        """

        # Create the properties that there is all the time
        to_return = { prefix + 'resource_type': self.resource_type }
        # If it is a literal, add the literal part
        if self.resource_type == 'literal': to_return[prefix + 'literal'] = self.literal
        # And otherwise, add the Entity part
        else: 
            to_return[prefix + 'uri'] = self.uri
            to_return[prefix + 'label'] = self.label
            if self.comment: to_return[prefix + 'comment'] = self.comment
            if self.class_uri: to_return[prefix + 'class_uri'] = self.class_uri
        return to_return
    
    
    @staticmethod
    def from_dict(obj: Dict[str, Any], prefix: str= '') -> 'Resource':
        """
        Creates a Resource instance from a dictionary representation.

        Parameters:
            obj (dict): The dictionary containing resource data.
            prefix (str): Optional string that was prepended to keys in the dictionary.

        Returns:
            Resource: An instance of the Resource class with properties populated from the dictionary.
        """
        
        resource_type = obj.get(prefix + 'resource_type', 'iri')
        is_value = resource_type == "literal"

        # Parse the object and return a Resource instance
        return Resource(
            resource_type=resource_type,
            value=obj.get(prefix + 'literal') if is_value else obj.get(prefix + 'uri'),
            label=obj.get(prefix + 'label', None),
            comment=obj.get(prefix + 'comment', None),
            class_uri=obj.get(prefix + 'class_uri', None)
        )
    
    def __str__(self):
        return self.uri