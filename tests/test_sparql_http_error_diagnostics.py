import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import requests
from requests.exceptions import HTTPError


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graphly.schema import Sparql  # noqa: E402
import schema.sparql_technologies  # noqa: F401, E402


class TestSparqlHttpErrorDiagnostics(unittest.TestCase):
    def test_logs_rdf4j_response_before_reraising_http_error(self):
        endpoint = Sparql("http://rdf4j:8080/rdf4j-server/repositories/logre", "", "")
        response = requests.Response()
        response.status_code = 400
        response.reason = "Bad Request"
        response.url = endpoint.url
        response._content = b"Malformed SPARQL Update"

        output = io.StringIO()
        with (
            patch("schema.sparql_technologies.requests.post", return_value=response),
            redirect_stdout(output),
            self.assertRaises(HTTPError),
        ):
            endpoint.run("INSERT DATA { <http://example.org/s> <http://example.org/p> 'x' . }")

        self.assertIn("status=400", output.getvalue())
        self.assertIn("Malformed SPARQL Update", output.getvalue())


if __name__ == "__main__":
    unittest.main()
