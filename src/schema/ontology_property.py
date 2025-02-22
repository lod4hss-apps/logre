from pydantic import BaseModel, field_validator

class OntologyProperty(BaseModel):

    uri: str
    label: str
    order: int
    min_count: int
    max_count: int

    domain_class_uri: str 
    range_class_uri: str

    is_blank: bool


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

        instance = cls(**data)
        instance.is_blank = True if data['is_blank'] == 'true' else False

        return instance
    
    def get_key(self) -> str:
        return f"{self.domain_class_uri}-{self.uri}"