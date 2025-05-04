
from .sparql import SPARQL

class GraphDB(SPARQL):
    
    def __init__(self, url: str, username: str, password: str) -> None:
        super().__init__(url, username, password)
        self.name = 'GraphDB'