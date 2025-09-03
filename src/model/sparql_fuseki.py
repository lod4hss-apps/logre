from typing import List
import requests, os
from requests.auth import HTTPBasicAuth

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
        if named_graph_uri: url = self.url + '?graph=' + self.unroll_uri(named_graph_uri)
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
        

    def run(self, query: str) -> None | list[dict]:
        """Make a HTTP POST request with all needed params to the SPARQL endpoint."""

        # Before adding the prefixes, check if it is a select, insert, delete, clear
        query_lower = query.lower()
        if "select" in query_lower: select_index = query_lower.index('select')
        else: select_index = float('inf')
        if "insert" in query_lower: insert_index = query_lower.index('insert')
        else: insert_index = float('inf')
        if "delete" in query_lower: delete_index = query_lower.index('delete')
        else: delete_index = float('inf')
        if "clear" in query_lower: clear_index = query_lower.index('clear')
        else: clear_index = float('inf')
        min_index = min(select_index, insert_index, delete_index, clear_index)
        if min_index == select_index: query_type = "select"
        elif min_index == insert_index: query_type = "insert"
        elif min_index == delete_index: query_type = "delete"
        elif min_index == clear_index: query_type = "clear"


        if os.getenv('LOGRE_MODE') == "debug":
            # Prettifying query: un-tab to the right the query in case of debug mode
            query_lines = query.split('\n')
            for line in query_lines:
                if line.strip() == '': continue
                index = len(line) - len(line.lstrip())
                break
            query = '\n'.join(list(map(lambda line: line[index:], query_lines)))

            # Add prefixes
            query = '\n'.join(list(map(lambda prefix: prefix.to_sparql(), self.prefixes))) + '\n' + query

            # DEBUG
            print('==============')
            print(query)
        else:
            # Is different because in the debug mode, we keep indentation for visual reading, here not

            # Add prefixes
            query = '\n'.join(list(map(lambda prefix: prefix.to_sparql(), self.prefixes))) + '\n' + query
            # Strip all lines
            query = '\n'.join(list(map(lambda line: line.strip(), query.split('\n'))))


        # Prepare the request
        param_name = 'query' if query_type == 'select' else 'update'
        data = {param_name: query}
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/sparql-results+json'}
        auth = HTTPBasicAuth(self.username, self.password) if self.username else None

        # Execute the request
        response = super().execute_http_request(self.url, data, headers, auth)

        # If there is a response, parse and transform into a list of dict
        if query_type == 'select': return super().parse_sparql_json_response(response.json())
        else: return []


    def insert(self, triples: List[tuple] | tuple, graph_uri: str | None = None) -> None:
        """From a list (or unique) of triples, insert them (it) in the endpoint, in the given graph."""

        # If only a single triple is given, transform it into a list
        if isinstance(triples, tuple):
            triples = [triples]

        # Since inserts can be pretty huge, here we split them
        # in "smaller insert" of maximum 1k triples.

        chunk_size = 1000
        chunked_triples = [triples[i: i + chunk_size] for i in range(0, len(triples), chunk_size)]

        # Prepare the query
        graph_sparql_open = "GRAPH " + graph_uri + " {" if graph_uri else ""
        graph_sparql_close = "}" if graph_uri else ""
        
        for small_triples in chunked_triples:
            # Transform the triples into strings, and make the query "pretty"
            triples_str = '\n                        '.join(map(lambda triple: self.prepare_triple(triple), small_triples))

            # Prepare the query
            text = """
                # SPARQL.insert()
                INSERT DATA {
                    """ + graph_sparql_open + """
                        """ + triples_str + """
                    """ + graph_sparql_close + """
                }
            """

            # Insert the triples in the endpoint
            self.run(text)
