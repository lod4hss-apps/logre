import requests
from typing import List, Dict

from .sparql import SPARQL
from .errors import HTTPError
from .prefix import Prefix

class Allegrograph(SPARQL):
    
    
    def __init__(self, url: str, username: str, password: str) -> None:
        super().__init__(url, username, password)
        self.name = 'Allegrograph'
        if 'franzOption_defaultDatasetBehavior' not in list(map(lambda p: p.short, self.prefixes)):
            self.prefixes.append(Prefix('franzOption_defaultDatasetBehavior', 'franz:rdf'))

    def get_prefixes(self) -> List[Prefix]:
        return [prefix for prefix in self.prefixes if prefix.short not in ['base', 'franzOption_defaultDatasetBehavior']]

    def insert(self, triples: List[tuple] | tuple, graph_uri: str | None = None) -> None:
        # Because we can not be sure user has set the option, 
        # Triples need to be deleted before inserting so that we make sure of unicity
        self.delete(triples, graph_uri)
        super().insert(triples, graph_uri) 


    def upload_nquads(self, nquad_content: str) -> None:
        """
        Function to import raw n-Quads data (as string) into the endpoint.
        As n-quads already include the graph, data can't be imported into a specified graph.
        """
        
        # Prepare query
        url = self.url if not self.url.endswith('/sparql') else self.url.replace('/sparql', '')
        url = f"{url}/statements"
        headers = {"Content-Type": "application/n-quads"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=nquad_content, headers=headers, auth=auth)
        try:
            response.raise_for_status()  # Raise error for bad responses
        except requests.exceptions.HTTPError as error:
            msg = f"HTTP code {str(error)}.\n"
            msg += error.response.text
            raise HTTPError(msg)


    def upload_turtle(self, turtle_content: str, named_graph_uri: str = None) -> None:

        # Prepare query
        url = self.url if not self.url.endswith('/sparql') else self.url.replace('/sparql', '')
        url = f"{url}/statements"
        if named_graph_uri: url += "?context=%3C" + self.unroll_uri(named_graph_uri).replace(':', '%3A').replace('/', '%2F') + '%3E'
        headers = {"Content-Type": "text/turtle"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=turtle_content, headers=headers, auth=auth)
        try:
            response.raise_for_status()  # Raise error for bad responses
        except requests.exceptions.HTTPError as error:
            msg = f"HTTP code {str(error)}.\n"
            msg += error.response.text
            raise HTTPError(msg)