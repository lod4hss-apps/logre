
class OntoProperty:

    uri: str
    label: str
    order: int
    min_count: int
    max_count: int

    domain_class_uri: str 
    range_class_uri: str
    card_of_class_uri: str

    display_label: str

    def __init__(self, uri: str = None, label: str = None, order: int = None, min_count: int = None, max_count: int = None, domain_class_uri: str = None, range_class_uri: str = None, card_of_class_uri: str = None) -> None:
        self.uri = uri
        self.label = label or uri
        self.display_label = f"{label} ({uri})"
        self.order = order or 1000
        self.min_count = min_count or 0
        self.max_count = max_count or 1000
        self.domain_class_uri = domain_class_uri
        self.range_class_uri = range_class_uri
        self.card_of_class_uri = card_of_class_uri


    def get_key(self) -> str:
        """Create a key to identify a property and its vision for a class (eg "was born" on the Person class, but "brought into life" for a Birth card)"""
        return f"{self.domain_class_uri or self.range_class_uri}-{self.uri}"
    

    def is_mandatory(self) -> str:
        """Check to have the information: is the property mandatory for those instances?"""
        return self.min_count != 0


    def to_dict(self, prefix='') -> dict:
        return {
            prefix + 'uri': self.uri,
            prefix + 'label': self.label,
            prefix + 'order': self.order,
            prefix + 'min_count': self.min_count,
            prefix + 'max_count': self.max_count,
            prefix + 'domain_class_uri': self.domain_class_uri,
            prefix + 'range_class_uri': self.range_class_uri,
            prefix + 'card_of_class_uri': self.card_of_class_uri
        }
    
    
    @staticmethod
    def from_dict(obj: dict, prefix='') -> 'OntoProperty':
        return OntoProperty(
            uri=obj.get(prefix + 'uri'),
            label=obj.get(prefix + 'label'),
            order=obj.get(prefix + 'order', 1000),
            min_count=obj.get(prefix + 'min_count'),
            max_count=obj.get(prefix + 'max_count'),
            domain_class_uri=obj.get(prefix + 'domain_class_uri'),
            range_class_uri=obj.get(prefix + 'range_class_uri'),
            card_of_class_uri=obj.get(prefix + 'card_of_class_uri'),
        )