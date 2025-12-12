from graphly.schema.prefix import Prefix


class Ontology:
    """
    Represents an ontology with a name and associated prefix.

    Attributes:
        name (str): The name of the ontology.
        prefix (Prefix): The prefix object containing the short name and URI.

    Methods:
        __init__: Initializes the Ontology with a name, short prefix, and URI.
    """

    name: str
    prefix: Prefix


    def __init__(self, name, prefix_short, url) -> None:
        """
        Initialize an Ontology instance with a name and prefix.

        Args:
            name (str): The name of the ontology.
            prefix_short (str): The short prefix to identify the ontology.
            url (str): The full URI associated with the ontology prefix.
        """
        self.name = name
        self.prefix = Prefix(prefix_short, url)