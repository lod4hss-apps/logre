import requests, pandas as pd
from .sparql import SPARQL
from .errors import HTTPError

class Fuseki(SPARQL):
    
    def __init__(self, url: str, username: str, password: str) -> None:
        super().__init__(url, username, password)
        self.name = 'Fuseki'


    def upload_nquads_chunk(self, nquad_content: str) -> None:
        """
        Function to import raw n-Quads data (as string) into the endpoint.
        As n-quads already include the graph, data can't be imported into a specified graph.
        """
        
        # Prepare query
        headers = {"Content-Type": "application/n-quads"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(self.url, data=nquad_content, headers=headers, auth=auth)
        try:
            response.raise_for_status()  # Raise error for bad responses
        except requests.exceptions.HTTPError as error:
            msg = f"HTTP code {str(error)}.\n"
            msg += error.response.text
            raise HTTPError(msg)


    def upload_turtle_chunk(self, turtle_content: str, named_graph_uri: str = None) -> None:

        # Prepare query
        if named_graph_uri: url = self.url + '?graph=' + named_graph_uri
        else: url = self.url
        headers = {"Content-Type": "application/turtle"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=turtle_content, headers=headers, auth=auth)
        try:
            response.raise_for_status()  # Raise error for bad responses
        except requests.exceptions.HTTPError as error:
            msg = f"HTTP code {str(error)}.\n"
            msg += error.response.text
            raise HTTPError(msg)