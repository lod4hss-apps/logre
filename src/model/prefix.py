
class Prefix:

    short: str
    long: str


    def __init__(self, short: str, url: str) -> None:
        self.short = short
        self.long = url


    def to_sparql(self) -> str:
        """Return a SPARQL ready string for the prefix."""
        return f"PREFIX {self.short}: <{self.long}>"
    

    def to_turtle(self) -> str:
        """Return a Turtle ready string for the prefix."""
        return f"@prefix {self.short}: <{self.long}> ."


    def shorten(self, uri: str) -> str:
        """Replace the given long uri by its short prefix, if present."""
        if self.long in uri:
            if uri.startswith('<'): uri = uri[1:]
            if uri.endswith('>'): uri = uri[:-1]
            return uri.replace(self.long, self.short + ':')
        return uri
    

    def lengthen(self, short: str) -> str:
        """Replace the given short uri by its explicit version."""
        return str(short).replace(self.short + ':', self.long)
    

    def to_dict(self) -> dict[str, str]:
        """Convert the Prefix instance to a dictionary."""
        return {
            "short": self.short,
            "long": self.long
        }
    

    @staticmethod
    def from_dict(obj: dict[str, str]) -> 'Prefix':
        """Create an Prefix instance from a dictionary."""
        return Prefix(obj['short'], obj['long'])