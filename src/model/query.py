
class Query:
    """A query object representing a query with its name and value"""

    name: str
    text: str


    def __init__(self, name: str, text: str) -> None:
        self.name = name
        self.text = text


    def to_dict(self) -> dict:
        return {
            "name": self.name, 
            "text": self.text
        }
    
    
    @staticmethod
    def from_dict(obj: dict) -> 'Query':
        return Query(obj.get('name'), obj.get('text'))
