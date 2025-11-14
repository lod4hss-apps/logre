from typing import List, Dict
import os, requests
from requests.auth import HTTPBasicAuth
from graphly.schema.prefixes import Prefixes
from graphly.tools.triple import prepare_triple
from graphly.tools.uri import prepare


class Sparql: 
    """
    A Python wrapper for interacting with a SPARQL endpoint, providing methods 
    to query, insert, delete, dump, and upload RDF data in various formats.

    This class supports:

    - Executing SPARQL queries with optional prefixes.
    - Inserting and deleting triples, including large batch operations.
    - Dumping the full dataset in N-Quads format.
    - Uploading RDF data in N-Quads or Turtle formats in chunks.
    - Abstract methods for technology-specific chunk uploads, to be implemented by subclasses.

    Attributes:
        technology_name (str): The name of the SPARQL technology or implementation.
        endpoint_url (str): The URL of the SPARQL endpoint.
        username (str): Username for endpoint authentication.
        password (str): Password for endpoint authentication.
    """

    technology_name: str
    endpoint_url: str
    username: str
    password: str


    def __init__(self, url: str, username: str, password: str) -> None:
        """
        Initializes a SPARQL wrapper instance with connection credentials.

        Parameters:
            url (str): The endpoint URL of the SPARQL service.
            username (str): The username for authentication.
            password (str): The password for authentication.
        """
        self.url = url
        self.username = username
        self.password = password


    def run(self, text: str, prefixes: Prefixes = None, query_param: str = 'query', url_appendix: str = '', parse_response: bool = True) -> List[Dict] | None:
        """
        Executes a SPARQL query against the configured endpoint.

        Parameters:
            text (str): The raw SPARQL query string (without prefixes).
            prefixes (Prefixes, optional): A container of prefixes to prepend to the query. Defaults to an empty Prefixes instance.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing query results.
        """
        prefixes = prefixes or Prefixes()
        
        # Print the query in case of debug mode activated
        if os.getenv('GRAPHLY_MODE') == "debug": 
            log_query(text, prefixes)

        # Build the full query to send to sparql server
        text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()]) # Strip all lines and remove empty ones
        text = '\n'.join([p.to_sparql() for p in prefixes]) + '\n' + text # Add prefixes

        # Prepare the request
        data = {query_param: text}
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/sparql-results+json'}
        auth = HTTPBasicAuth(self.username, self.password) if self.username else None

        # Execute request
        response = requests.post(self.url + url_appendix, data=data, headers=headers, auth=auth)
        response.raise_for_status()  # Raise error for bad responses

        # If there is a response, and it is expected, parse and transform into a list of dict
        if parse_response:
            try:
                return parse_sparql_json_response(response.json(), prefixes)
            except:
                return response.text
    

    def insert(self, triples: List[tuple] | tuple, graph_uri: str = None, prefixes: Prefixes = None) -> None:
        """
        Inserts one or more RDF triples into the SPARQL endpoint, optionally within a named graph.

        Args:
            triples (List[tuple] | tuple): A single triple or a list of triples to insert.
            graph_uri (str, optional): The URI of the named graph where the triples should be inserted.
                If not provided, triples are inserted into the default graph.
            prefixes (Prefixes, optional): A collection of prefixes to include in the SPARQL query.

        Returns:
            None
        """

        # If only a single triple is given, transform it into a list
        if isinstance(triples, tuple):
            triples = [triples]

        # Since inserts can be pretty huge, here we split them
        # in smaller insert of maximum 5k triples.

        chunk_size = 5000
        chunked_triples = [triples[i: i + chunk_size] for i in range(0, len(triples), chunk_size)]

        # Prepare the query - Graph part
        graph_sparql_open = "GRAPH " + prepare(graph_uri, prefixes.shorts() if prefixes else None) + " {" if graph_uri else ""
        graph_sparql_close = "}" if graph_uri else ""
        
        for small_triples in chunked_triples:
            # Transform the triples into strings, and make the query "pretty"
            triples_str = '\n                        '.join([prepare_triple(triple, prefixes.shorts() if prefixes else None) for triple in small_triples])

            # Prepare the query
            text = """
                # graphly.schema.sparql.insert
                INSERT DATA {
                    """ + graph_sparql_open + """
                        """ + triples_str + """
                    """ + graph_sparql_close + """
                }
            """

            # Insert the triples in the endpoint
            self.run(text, prefixes)


    def delete(self, triples: List[tuple] | tuple, graph_uri: str = None, prefixes: Prefixes = None) -> None:
        """
        Deletes one or more RDF triples from the SPARQL endpoint, optionally within a named graph.

        Args:
            triples (List[tuple] | tuple): A single triple or a list of triples to delete.
            graph_uri (str, optional): The URI of the named graph from which the triples should be deleted.
                If not provided, triples are deleted from the default graph.
            prefixes (Prefixes, optional): A collection of prefixes to include in the SPARQL query.

        Returns:
            None
        """

        # If only a single triple is given, transform is into a list
        if isinstance(triples, tuple):
            triples = [triples]

        # Transform the triples into strings
        triples_str = '\n                    '.join([prepare_triple(triple, prefixes.shorts() if prefixes else None) for triple in triples])

        # Prepare query
        graph_sparql_open = "GRAPH " + prepare(graph_uri, prefixes.shorts() if prefixes else None) + " {" if graph_uri else ""
        graph_sparql_close = "}" if graph_uri else ""
        text = """
            # graphly.schema.sparql.delete
            DELETE WHERE {
                """ + graph_sparql_open + """
                    """ + triples_str + """
                """ + graph_sparql_close + """
            }
        """

        # Execute
        self.run(text, prefixes)

    
    def dump(self) -> str:
        """
        Dumps the entire RDF dataset from the SPARQL endpoint in N-Quads format.

        Returns:
            str: The full dataset serialized as N-Quads.
            
        Raises:
            requests.HTTPError: If the HTTP request to the endpoint fails.
        """
        # Prepare the request
        url = self.url + '/statements'
        headers = {"Accept": "application/n-quads"}
        auth = HTTPBasicAuth(self.username, self.password) if self.username else None

        # Make the request
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()  # Raise error for bad responses

        # Return n-quads as string
        return response.text
    

    def upload_nquads(self, nquad_content: str) -> None:
        """
        Uploads RDF data in N-Quads format to the SPARQL endpoint in chunks.

        Args:
            nquad_content (str): The RDF dataset serialized in N-Quads format.

        Returns:
            None
        """
        line_number = 10000
        lines = nquad_content.splitlines()
        chunks = ['\n'.join(lines[i:i + line_number]) for i in range(0, len(lines), line_number)]

        for i, chunk in enumerate(chunks):
            print(f"> Uploading {line_number} triples ({line_number * i} / {len(lines)})")
            self.upload_nquads_chunk(chunk)
    

    def upload_turtle(self, turtle_content: str, named_graph_uri: str) -> None:
        """
        Uploads RDF data in Turtle format to a specified named graph on the SPARQL endpoint in chunks.

        Args:
            turtle_content (str): The RDF dataset serialized in Turtle format.
            named_graph_uri (str): The URI of the named graph where the data should be uploaded.

        Returns:
            None
        """

        line_number = 10000
        lines = turtle_content.splitlines()

        # Extract prefixes
        prefixes = []
        triples = []
        for line in lines:
            if line.strip().startswith('@prefix'):
                prefixes.append(line)
            else:
                triples.append(line)
        
        prefixes = '\n'.join(prefixes) + "\n"
        chunks = ['\n'.join(triples[i:i + line_number]) for i in range(0, len(triples), line_number)]

        for i, chunk in enumerate(chunks):
            print(f"> Uploading ({line_number * i} / {len(triples)})")
            self.upload_turtle_chunk(prefixes + chunk, named_graph_uri)


    def upload_nquads_chunk(self, nquad_content: str) -> None:
        """
        Abstract method to upload a chunk of RDF data in N-Quads format.

        This method is intended to be implemented by subclasses specific to a technology.
        Calling it on the base class will raise an exception.

        Args:
            nquad_content (str): A chunk of RDF data in N-Quads format.

        Raises:
            Exception: Always, indicating that this method must be implemented in a subclass.
        """
        raise Exception(f'Method <upload_nquads> not implemented in {self.technology_name}')


    def upload_turtle_chunk(self, turtle_content: str, named_graph_uri: str) -> None:
        """
        Abstract method to upload a chunk of RDF data in Turtle format to a named graph.

        This method is intended to be implemented by subclasses specific to a technology.
        Calling it on the base class will raise an exception.

        Args:
            turtle_content (str): A chunk of RDF data in Turtle format.
            named_graph_uri (str): The URI of the named graph where the data should be uploaded.

        Raises:
            Exception: Always, indicating that this method must be implemented in a subclass.
        """
        raise Exception(f'Method <upload_turtle> not implemented in {self.technology_name}')
    


def log_query(query: str, prefixes: Prefixes) -> None:
    """
    Logs a SPARQL query with proper formatting and prefixes.

    Args:
        query (str): The raw SPARQL query string.
        prefixes (Prefixes): A collection of prefixes to prepend to the query.

    Returns:
        None
    """

    # Split in a list of lines (and remove empty ones)
    all_lines = [line for line in query.split("\n") if line.strip()]

    # Get the first left index (remove prepending left spaces)
    for line in all_lines:
        if line.strip() == '': continue # Ignore first empty lines
        index = len(line) - len(line.lstrip())
        break
    
    # Rebuild the query (un-tab)
    query = [line for line in query.split("\n") if line.strip()]
    query = '\n'.join(list(map(lambda line: line[index:], all_lines)))

    # Add prefixes
    query = '\n'.join(list(map(lambda prefix: prefix.to_sparql(), prefixes))) + '\n' + query

    # DEBUG
    print('==============')
    print(query)

        
def parse_sparql_json_response(response_json: object, prefixes: Prefixes) -> List[Dict]:
    """
    Parses a SPARQL JSON response into a list of dictionaries with simplified values.

    Args:
        response_json (object): The JSON response returned by a SPARQL endpoint.
        prefixes (Prefixes): A prefix handler used to shorten URIs.

    Returns:
        List[Dict]: A list of rows where each row is a dictionary mapping column names 
        to their parsed values. URIs are shortened using the provided prefixes, 
        and integer literals are converted to Python integers.
    """
    if 'results' in response_json and 'bindings' in response_json['results']:
        rows = []
        for row in response_json['results']['bindings']:
            obj: dict = {}
            for key in row.keys(): # For Each columns
                type = row[key].get('type')
                datatype = row[key].get('datatype')
                value = row[key].get('value')
                if type == 'uri': 
                    value = prefixes.shorten(value)
                elif type == 'literal' and datatype == 'http://www.w3.org/2001/XMLSchema#integer':
                    value = int(value)
                obj[key] = value
            rows.append(obj)

        return rows
    return []