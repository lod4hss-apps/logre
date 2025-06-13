import requests, re, os
from requests.auth import HTTPBasicAuth

from .sparql import SPARQL
from .errors import HTTPError

class GraphDB(SPARQL):
    
    def __init__(self, url: str, username: str, password: str) -> None:
        super().__init__(url, username, password)
        self.name = 'GraphDB'


    def run(self, query: str) -> None | list[dict]:
        if self.is_update(query): self.update(query)
        else: return super().run(query)


    def is_update(self, query: str) -> bool:
        """Check if the given query is an update or not."""

        # Remove comments
        lines = re.sub(r'#.*', '', query).splitlines()

        # Remove empty lines and strip whitespace
        lines = [line.strip().lower() for line in lines if line.strip()]

        # Skip PREFIX and BASE declarations
        for line in lines:
            if line.startswith(('prefix', 'base')):
                continue
            # Found the first non-declaration line
            return line.startswith(('insert', 'delete', 'load', 'clear', 'create', 'drop', 'copy', 'move', 'add', 'modify'))
        
        return False  # fallback if no operation found


    def update(self, query: str) -> None:
        
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
            # Add prefixes
            query = '\n'.join(list(map(lambda prefix: prefix.to_sparql(), self.prefixes))) + '\n' + query
            # Strip all lines
            query = '\n'.join(list(map(lambda line: line.strip(), query.split('\n'))))


        # Prepare the request
        url = self.url + '/statements'
        headers = { 'Content-Type': 'application/x-www-form-urlencoded'}
        auth = HTTPBasicAuth(self.username, self.password)
        data = {'update': query}

        # Execute the request
        response = requests.post(url, data=data, headers=headers, auth=auth)
        try:
            response.raise_for_status()  # Raise error for bad responses
        except requests.exceptions.HTTPError as error:
            msg = f"HTTP code {str(error)}.\n"
            msg += error.response.text
            raise HTTPError(msg)
        

    def upload_nquads_chunk(self, nquad_content: str) -> None:
        """
        Function to import raw n-Quads data (as string) into the endpoint.
        As n-quads already include the graph, data can't be imported into a specified graph.
        """
        
        # Prepare query
        url = f"{self.url}/statements"
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


    def upload_turtle_chunk(self, turtle_content: str, named_graph_uri: str = None) -> None:

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