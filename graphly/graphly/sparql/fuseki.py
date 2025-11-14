import requests
from graphly.schema.prefixes import Prefixes
from graphly.schema.sparql import Sparql
from graphly.tools.query import get_sparql_type
from graphly.tools.uri import prepare


class Fuseki(Sparql):
    """
    Fuseki-specific implementation of the Sparql wrapper.

    This class extends the generic `Sparql` wrapper to handle Fuseki-specific
    behavior, including query execution, data dumping, and chunked uploads
    for both N-Quads and Turtle formats.

    Key features:
    - Automatically distinguishes between query and update operations.
    - Dumps the full dataset from all graphs in N-Quads-like format.
    - Supports chunked uploads of RDF data, handling named graphs when provided.
    - Raises HTTP errors on failed upload requests.

    Attributes:
        technology_name (str): Set to 'Fuseki' to indicate the SPARQL technology.
    """
    
    
    def __init__(self, url: str, username: str, password: str) -> None:
        """
        Initializes a Fuseki SPARQL wrapper instance.

        Args:
            url (str): The endpoint URL of the Fuseki SPARQL service.
            username (str): The username for authentication.
            password (str): The password for authentication.
        """
        super().__init__(url, username, password)
        self.technology_name = 'Fuseki'


    def run(self, text: str, prefixes: Prefixes = None) -> None | list[dict]:   
        """
        Executes a SPARQL query against the Fuseki endpoint, handling both query and update operations.

        Args:
            text (str): The raw SPARQL query string.
            prefixes (Prefixes, optional): A collection of prefixes to prepend to the query.

        Returns:
            None | list[dict]: The parsed query results for SELECT/ASK queries, or None for update operations.
        """     
        # Analyze query type
        query_type = get_sparql_type(text)

        # If query is an update one
        if query_type in ['INSERT', 'DELETE', 'CLEAR', 'OTHER']:
            param_name = 'update'
            parse_response = False

        # Otherwise it is a query one
        else:
            param_name = 'query'
            parse_response = True
        
        # Call and return parent function
        return super().run(text, prefixes, param_name, '', parse_response=parse_response)


    def dump(self) -> str:
        """
        Dumps the entire dataset (in n-quad format) from the Fuseki endpoint by iterating through all graphs.

        This method retrieves triples from both the default graph and all named graphs,
        fetching results in batches to handle large datasets. The data is returned as a
        single N-Quads-like string.

        Returns:
            str: The full dataset serialized line by line, with each line representing a triple
            and its associated graph (if any).
        """
        # Prepare the extraction: list all graph (+ default one)
        graphs = self.run("""
                # graphly.sparql.fuseki.dump
                SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o . } }
            """)
        graphs = [''] + [g['g'] for g in graphs]

        # Number of triples extracted at once
        step = 5000

        results = []
        for graph in graphs:
            
            # Prepare the extraction for a dedicated graph
            graph_uri = prepare(graph)
            offset = 0
            graph_result = []
            # Change query according to graph (if it is default one, graph clause need not to be here)
            if graph_uri: query = f"""
                # graphly.sparql.fuseki.dump
                SELECT ?s ?p ?o WHERE {{ GRAPH {graph_uri} {{ ?s ?p ?o .}}}}
            """
            else: query = f"""
                # graphly.sparql.fuseki.dump
                SELECT ?s ?p ?o WHERE {{ ?s ?p ?o .}}
            """

            # Extract triples as long as they are coming
            while True:
                query_ = query + f"    OFFSET {offset}" # Append the offset
                local_result = self.run(query_) # Run the query

                # If there are results, add them, and prepare next request, otherwise, everything is extracted
                if len(local_result) > 0: 
                    graph_result += local_result
                    offset += step
                else:
                    break
            
            # Build the n-quads lines
            results += [f"{prepare(t['s'])} {prepare(t['p'])} {prepare(t['o'])} {graph_uri or ''} .".replace('  ', ' ') for t in graph_result]

        # And make a single string
        return "\n".join(results)


    def upload_nquads_chunk(self, nquad_content: str) -> None:
        """
        Uploads a chunk of RDF data in N-Quads format to the Fuseki endpoint.

        Args:
            nquad_content (str): A chunk of RDF data serialized in N-Quads format.

        Raises:
            requests.HTTPError: If the HTTP request to the endpoint fails.
        """
        # Prepare query
        headers = {"Content-Type": "application/n-quads"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(self.url, data=nquad_content, headers=headers, auth=auth)
        response.raise_for_status()  # Raise error for bad responses
            

    def upload_turtle_chunk(self, turtle_content: str, named_graph_uri: str = None) -> None:
        """
        Uploads a chunk of RDF data in Turtle format to the Fuseki endpoint.

        Args:
            turtle_content (str): A chunk of RDF data serialized in Turtle format.
            named_graph_uri (str, optional): The URI of the named graph where the data 
                should be uploaded. If not provided, data is uploaded to the default graph.

        Raises:
            requests.HTTPError: If the HTTP request to the endpoint fails.
        """
        # Prepare query
        if named_graph_uri: 
            url = f"{self.url}/data?graph={named_graph_uri}"
        else: url = f"{self.url}/data"
        headers = {"Content-Type": "text/turtle"}
        auth = (self.username, self.password)

        # Make the request
        response = requests.post(url, data=turtle_content, headers=headers, auth=auth)
        response.raise_for_status()  # Raise error for bad responses