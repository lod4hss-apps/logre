from pydantic import BaseModel, field_validator

class OntologyProperty(BaseModel):

    uri: str
    label: str
    order: int
    min_count: int
    max_count: int

    domain_class_uri: str 
    range_class_uri: str
    card_of_class_uri: str

    @field_validator("order", mode="before")
    @classmethod
    def validate_order(cls, value):
        if value == '': return 10**18
        return int(value) if isinstance(value, str) else value

    @field_validator("min_count", mode="before")
    @classmethod
    def validate_min_count(cls, value):
        if value == '': return 0
        return int(value) if isinstance(value, str) else value

    @field_validator("max_count", mode="before")
    @classmethod
    def validate_max_count(cls, value):
        if value == '': return 10**18
        return int(value) if isinstance(value, str) else value


    def to_dict(self) -> dict:
        """Convert the OntologyProperty instance to a dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'OntologyProperty':
        """Create an OntologyProperty instance from a dictionary"""
        return cls(**data)
    
    def get_key(self) -> str:
        """Create a key to identify a property and its vision for a class (eg "was born" on the Person class, but "brought into life" for a Birth card)"""
        return f"{self.domain_class_uri or self.range_class_uri}-{self.uri}"