from typing import Dict, Any
from graphly.schema.resource import Resource


class Property(Resource):
    """
    Represents an RDF/OWL property, extending the Resource class with domain, range, 
    cardinality, and ordering information.

    Attributes:
        domain (Resource): The domain class of the property.
        range (Resource): The range class of the property.
        card_of (Resource): The class for which this property defines a cardinality constraint.
        order (int): Optional ordering index of the property.
        min_count (int): Minimum cardinality of the property.
        max_count (int): Maximum cardinality of the property.

    Methods:
        __init__: Initializes a Property with URI, label, comment, domain, range, cardinality, and order.
        get_key: Generates a unique key based on domain, predicate, and range URIs.
        is_mandatory: Checks if the property is mandatory based on min_count.
        to_dict: Converts the Property instance into a dictionary representation.
        from_dict: Creates a Property instance from a dictionary representation.
    """

    domain: Resource
    range: Resource
    card_of: Resource

    order: int
    min_count: int
    max_count: int


    def __init__(self, uri: str, label: str = None, comment: str = None, domain: Resource = None, range: Resource = None, card_of: Resource = None, order: int = None, min_count: int = 0, max_count: int = None) -> None:
        """
        Initialize a Property instance representing an RDF/OWL property.

        Inherits from `Resource` and adds additional attributes specific to 
        properties, including domain, range, cardinality, and order.

        Args:
            uri (str): The URI of the property.
            label (str, optional): A human-readable label for the property.
            comment (str, optional): A description or comment about the property.
            domain (Resource, optional): The domain class of the property.
            range (Resource, optional): The range class of the property.
            card_of (Resource, optional): The class for which this property defines a cardinality constraint.
            order (int, optional): An optional ordering value for the property.
            min_count (int, optional): Minimum cardinality of the property. Defaults to 0.
            max_count (int, optional): Maximum cardinality of the property. Defaults to None.
        """
        super().__init__(uri, label, comment, 'owl:Property', resource_type='iri')

        self.domain = domain
        self.range = range
        self.card_of = card_of

        self.order = order
        self.min_count = min_count
        self.max_count = max_count


    def get_key(self) -> str:
        """
        Generates a unique key for the property based on its domain, predicate, and range URIs.

        Returns:
            str: A string key in the format 'domainURI-predicateURI-rangeURI', using 'unknown' for missing domain or range.
        """
        part1 = self.domain.uri if self.domain else 'unknown'
        part2 = self.uri
        part3 = self.range.uri if self.range else 'unknown'
        return f"{part1}-{part2}-{part3}"
        

    def is_mandatory(self) -> str:
        """
        Checks if the property is mandatory based on its minimum count.

        Returns:
            bool: True if min_count is not zero (property is mandatory), False otherwise.
        """
        return self.min_count and self.min_count != 0


    def to_dict(self, prefix='') -> Dict[str, Any]:
        """
        Converts the Property instance into a dictionary representation.

        Parameters:
            prefix (str): Optional string to prepend to each key in the dictionary.

        Returns:
            dict: A dictionary containing the property's predicate, domain, range, cardinality, order, and min/max counts.
        """
        to_return = {}
        to_return[prefix + 'uri'] = self.uri
        to_return[prefix + 'label'] = self.label
        to_return[prefix + 'comment'] = self.comment
        if self.domain: to_return[prefix + 'domain'] = self.domain.to_dict(prefix)
        if self.range: to_return[prefix + 'range'] = self.range.to_dict(prefix)
        if self.card_of: to_return[prefix + 'card_of'] = self.card_of.to_dict(prefix)
        if self.order: to_return[prefix + 'order'] = self.order
        if self.min_count: to_return[prefix + 'min_count'] = self.min_count
        if self.max_count: to_return[prefix + 'max_count'] = self.max_count
        return to_return
    

    @staticmethod
    def from_dict(obj: Dict[str, Any], prefix: str = '') -> 'Property':
        """
        Creates a Property instance from a dictionary representation.

        Parameters:
            obj (Dict[str, Any]): A dictionary containing property data.
            prefix (str): Optional string that was prepended to keys in the dictionary.

        Returns:
            Property: An instance of the Property class with attributes populated from the dictionary.
        """
        domain_dict = obj.get(prefix + 'domain', None)
        range_dict = obj.get(prefix + 'range', None)
        card_of_dict = obj.get(prefix + 'card_of', None)

        return Property(
            uri= obj.get('uri', ''),
            label= obj.get('label', ''),
            comment= obj.get('comment', ''),
            domain=Resource.from_dict(domain_dict) if domain_dict else None,
            range=Resource.from_dict(range_dict) if range_dict else None,
            card_of=Resource.from_dict(card_of_dict) if card_of_dict else None,
            order = obj.get(prefix + 'order', None),
            min_count = obj.get(prefix + 'min_count', None),
            max_count = obj.get(prefix + 'max_count', None)
        )