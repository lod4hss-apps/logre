from typing import List
from .sparql import SPARQL


class Graph:

    sparql: SPARQL
    name: str
    uri: str
    uri_: str # This is the prepared URI, to avoid to prepare it each time


    def __init__(self, sparql: SPARQL, name: str, uri: str = None) -> None:
        self.sparql = sparql
        self.name = name
        self.uri = uri
        self.uri_ = self.sparql.prepare_uri(self.uri)


    def insert(self, triples: List[tuple[str, str, str]] | tuple[str, str, str]) -> None:
        self.sparql.insert(triples, self.uri)


    def delete(self, triples: List[tuple[str, str, str]] | tuple[str, str, str]) -> None:
        self.sparql.delete(triples, self.uri)


    def dump(self) -> list[dict]:
        """Dump the graph."""

        # Prepare the query
        graph_begin = "GRAPH " + self.uri_ + " {" if self.uri else ""
        graph_end = "}" if self.uri else ""
        query = """
            # DataSet.download_graph_turtle()
            SELECT 
                (COALESCE(?subject , '') as ?s)
                (COALESCE(?predicate , '') as ?p)
                (COALESCE(?object, '') as ?o)
                (isLiteral(?object) as ?literal)
            WHERE {
                """ + graph_begin + """
                    ?subject ?predicate ?object 
                """ + graph_end + """
            }
        """

        # Execute the query
        result = self.sparql.run(query)

        return result
    
    def dump_turtle(self) -> str:

        # Get all the triples
        triples = self.dump()

        # Format them for turtle file
        content = '\n'.join(list(map(lambda prefix: prefix.to_turtle(), self.sparql.prefixes))) + '\n\n'

        # Build the output: add all triples
        for triple in triples:
            subject = self.sparql.prepare_uri(triple.get('s'))
            predicate = self.sparql.prepare_uri(triple.get('p'))
            if triple.get('literal') == 'true': object = f"'{triple.get('o')}'"
            else: object = self.sparql.prepare_uri(triple.get('o'))

            content += f"{subject} {predicate} {object} .\n"

        return content


    def dump_nquad(self) -> str:

        # Get all the triples
        triples = self.dump()

        # Build the output: add all quads
        graph_uri = self.sparql.prepare_uri(self.sparql.lenghten_prefix(self.uri_)) if self.uri else ''
        content = ""
        for triple in triples:
            subject = self.sparql.prepare_uri(self.sparql.lenghten_prefix(triple.get('s')))
            predicate = self.sparql.prepare_uri(self.sparql.lenghten_prefix(triple.get('p')))
            if triple.get('literal') == 'true': object = f"'{triple.get('o')}'"
            else: object = self.sparql.prepare_uri(self.sparql.lenghten_prefix(triple.get('o')))

            content += f"{subject} {predicate} {object} {graph_uri} .\n"

        return content


    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'uri': self.uri
        }

