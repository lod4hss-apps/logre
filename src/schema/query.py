from pydantic import BaseModel

class Query(BaseModel):
    """A query object representing a query with its name, value etc"""

    name: str = None
    text: str = None

    def to_dict(self) -> dict:
        """Convert the Query instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Query':
        """Create a Query instance from a dictionary"""
        return cls(**data)