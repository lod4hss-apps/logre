from .graphdb import GraphDB


class RDF4J(GraphDB):
    """RDF4J implementation built on top of the GraphDB wrapper."""

    def __init__(self, url: str, username: str, password: str) -> None:
        super().__init__(url, username, password)
        self.technology_name = 'RDF4J'
