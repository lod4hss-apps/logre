import requests
from typing import List
from graphly.schema.prefix import Prefix
from graphly.schema.prefixes import Prefixes
from graphly.schema.sparql import Sparql
from graphly.tools.uri import prepare


class Allegrograph(Sparql):
    """
    AllegroGraph-specific implementation of the Sparql wrapper.

    This class extends the generic `Sparql` wrapper to handle AllegroGraph-specific
    behavior, including query execution with an additional prefix, insertions that
    ensure triple uniqueness, and chunked uploads of RDF data in N-Quads and Turtle formats.

    Key features:
    - Automatically includes the required `franzOption_defaultDatasetBehavior` prefix in all queries.
    - Ensures uniqueness of triples by deleting them before insertion.
    - Supports chunked uploads for large datasets.
    - Raises HTTP errors on failed upload requests.

    Attributes:
        additional_prefix (Prefix): AllegroGraph-specific prefix automatically added to queries.
        technology_name (str): Set to 'Allegrograph' to indicate the SPARQL technology.
    """

    additional_prefix = Prefix('franzOption_defaultDatasetBehavior', 'franz:rdf')
    

    def __init__(self, url: str, username: str, password: str) -> None:
        """
        Initializes an AllegroGraph SPARQL wrapper instance.

        Args:
            url (str): The endpoint URL of the AllegroGraph SPARQL service.
            username (str): The username for authentication.
            password (str): The password for authentication.
        """
        super().__init__(url, username, password)
        self.technology_name = 'Allegrograph'


    def run(self, text: str, prefixes: Prefixes = None) -> None | list[dict]:
        """
        Executes a SPARQL query against the AllegroGraph endpoint, automatically 
        including an additional prefix required by AllegroGraph.

        Args:
            text (str): The raw SPARQL query string.
            prefixes (Prefixes, optional): A collection of prefixes to prepend to the query.

        Returns:
            None | list[dict]: The parsed query results for SELECT/ASK queries, or None for update operations.
        """
        if prefixes is None: prefixes = Prefixes([self.additional_prefix])  
        else: prefixes.add(self.additional_prefix)
        return super().run(text, prefixes)


    def insert(self, triples: List[tuple] | tuple, graph_uri: str | None = None) -> None:
        """
        Inserts one or more RDF triples into the AllegroGraph endpoint, ensuring uniqueness.

        This method first deletes the provided triples to prevent duplicates, then inserts them.

        Args:
            triples (List[tuple] | tuple): A single triple or a list of triples to insert.
            graph_uri (str | None, optional): The URI of the named graph where the triples should be inserted.
                If not provided, triples are inserted into the default graph.

        Returns:
            None
        """
        # Because we can not be sure user has set the option, 
        # Triples need to be deleted before inserting so that we make sure of unicity
        self.delete(triples, graph_uri)
        super().insert(triples, graph_uri) 


    def upload_nquads_chunk(self, nquad_content: str) -> None:
        """
        Uploads a chunk of RDF data in N-Quads format to the AllegroGraph endpoint.

        Args:
            nquad_content (str): A chunk of RDF data serialized in N-Quads format.

        Raises:
            requests.HTTPError: If the HTTP request to the endpoint fails.
        """
        # Prepare query
        url = self.url if not self.url.endswith('/sparql') else self.url.replace('/sparql', '')
        url = f"{url}/statements"
        headers = {"Content-Type": "application/n-quads"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=nquad_content, headers=headers, auth=auth)
        response.raise_for_status()


    def upload_turtle_chunk(self, turtle_content: str, named_graph_uri: str = None) -> None:
        """
        Uploads a chunk of RDF data in Turtle format to the AllegroGraph endpoint.

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