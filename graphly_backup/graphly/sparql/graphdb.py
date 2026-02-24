import requests
from graphly.schema.prefixes import Prefixes
from graphly.schema.sparql import Sparql
from graphly.tools.query import get_sparql_type
from graphly.tools.uri import prepare


class GraphDB(Sparql):
    """
    GraphDB-specific implementation of the Sparql wrapper.

    This class extends the generic `Sparql` wrapper to handle GraphDB-specific
    behavior, including query execution, data uploads, and chunked handling
    for both N-Quads and Turtle formats.

    Key features:
    - Automatically distinguishes between query and update operations.
    - Supports chunked uploads of RDF data, handling named graphs when provided.
    - Raises HTTP errors on failed upload requests.

    Attributes:
        name (str): Set to 'GraphDB' to indicate the SPARQL technology.
    """
    

    def __init__(self, url: str, username: str, password: str) -> None:
        """
        Initializes a GraphDB SPARQL wrapper instance.

        Args:
            url (str): The endpoint URL of the GraphDB SPARQL service.
            username (str): The username for authentication.
            password (str): The password for authentication.
        """
        super().__init__(url, username, password)
        self.technology_name = 'GraphDB'


    def run(self, text: str, prefixes: Prefixes = None) -> None | list[dict]:
        """
        Executes a SPARQL query against the GraphDB endpoint, handling both query and update operations.

        Args:
            text (str): The raw SPARQL query string.
            prefixes (Prefixes, optional): A collection of prefixes to prepend to the query.

        Returns:
            None | list[dict]: The parsed query results for SELECT/ASK queries, or None for update operations.
        """
        query_type = get_sparql_type(text)
        if query_type in ['INSERT', 'DELETE', 'CLEAR', 'OTHER']:
            param_name = 'update'
            url_appendix = '/statements'
            parse_response = False
        else:
            param_name = 'query'
            url_appendix = ''
            parse_response = True
        return super().run(text, prefixes, param_name, url_appendix, parse_response)
        

    def upload_nquads_chunk(self, nquad_content: str) -> None:
        """
        Uploads a chunk of RDF data in N-Quads format to the GraphDB endpoint.

        Args:
            nquad_content (str): A chunk of RDF data serialized in N-Quads format.

        Raises:
            requests.HTTPError: If the HTTP request to the endpoint fails.
        """
        # Prepare query
        url = f"{self.url}/statements"
        headers = {"Content-Type": "application/n-quads"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=nquad_content, headers=headers, auth=auth)
        response.raise_for_status()  # Raise error for bad responses


    def upload_turtle_chunk(self, turtle_content: str, named_graph_uri: str = None) -> None:
        """
        Uploads a chunk of RDF data in Turtle format to the GraphDB endpoint.

        Args:
            turtle_content (str): A chunk of RDF data serialized in Turtle format.
            named_graph_uri (str, optional): The URI of the named graph where the data 
                should be uploaded. If not provided, data is uploaded to the default graph.

        Raises:
            requests.HTTPError: If the HTTP request to the endpoint fails.
        """
        # Prepare query
        url = self.url if not self.url.endswith('/sparql') else self.url.replace('/sparql', '')
        url = f"{url}/statements"
        if named_graph_uri: url += "?context=" + prepare(named_graph_uri).replace(':', '%3A').replace('/', '%2F')
        headers = {"Content-Type": "text/turtle"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=turtle_content, headers=headers, auth=auth)
        response.raise_for_status()  # Raise error for bad responses