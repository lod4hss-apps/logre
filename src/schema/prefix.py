from pydantic import BaseModel

class Prefix(BaseModel):

    short: str
    url: str


    def to_sparql(self) -> str:
        """Return a SPARQL ready string for the prefix"""

        return f"PREFIX {self.short}: <{self.url}>"
    
    def to_turtle(self) -> str:
        """Return a Turtle ready string for the prefix"""

        return f"@prefix {self.short}: <{self.url}> ."

    def shorten(self, uri: str) -> str:
        """Replace the given long uri by its short prefix, if present."""
        return uri.replace(self.url, self.short + ':')
    
    def explicit(self, short: str) -> str:
        """Replace the given short uri by its explicit version."""
        return short.replace(self.short + ':', self.url)
    

    def to_dict(self) -> dict:
        """Convert the Prefix instance to a dictionary"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Prefix':
        """Create an Prefix instance from a dictionary"""
        return cls(**data)