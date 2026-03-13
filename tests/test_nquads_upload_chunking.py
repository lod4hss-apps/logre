import os
import sys
import unittest
from pathlib import Path

import requests
from requests.exceptions import HTTPError


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import graphly.schema.sparql as graphly_sparql  # noqa: E402
import schema.sparql_technologies  # noqa: F401, E402


class _FakeUploader:
    def __init__(self, max_lines: int) -> None:
        self.max_lines = max_lines
        self.chunk_sizes: list[int] = []

    def upload_nquads_chunk(self, nquad_content: str) -> None:
        chunk_size = len(nquad_content.splitlines())
        self.chunk_sizes.append(chunk_size)

        if chunk_size > self.max_lines:
            response = requests.Response()
            response.status_code = 413
            response.reason = "Request Entity Too Large"
            raise HTTPError(
                "413 Client Error: Request Entity Too Large",
                response=response,
            )


class TestNQuadsAdaptiveUpload(unittest.TestCase):
    def test_reduces_chunk_size_on_http_413(self):
        previous = os.environ.get("LOGRE_NQUADS_CHUNK_LINES")
        os.environ["LOGRE_NQUADS_CHUNK_LINES"] = "8"
        try:
            uploader = _FakeUploader(max_lines=3)
            content = "\n".join([f"<s{i}> <p> <o> <g> ." for i in range(10)])

            graphly_sparql.Sparql.upload_nquads(uploader, content)

            self.assertEqual([8, 4, 2], uploader.chunk_sizes[:3])
            self.assertTrue(any(size <= 3 for size in uploader.chunk_sizes[3:]))
        finally:
            if previous is None:
                os.environ.pop("LOGRE_NQUADS_CHUNK_LINES", None)
            else:
                os.environ["LOGRE_NQUADS_CHUNK_LINES"] = previous

    def test_raises_clear_error_when_even_one_line_fails(self):
        previous = os.environ.get("LOGRE_NQUADS_CHUNK_LINES")
        os.environ["LOGRE_NQUADS_CHUNK_LINES"] = "4"
        try:
            uploader = _FakeUploader(max_lines=0)
            content = "<s> <p> <o> <g> ."

            with self.assertRaisesRegex(HTTPError, "single N-Quads line"):
                graphly_sparql.Sparql.upload_nquads(uploader, content)
        finally:
            if previous is None:
                os.environ.pop("LOGRE_NQUADS_CHUNK_LINES", None)
            else:
                os.environ["LOGRE_NQUADS_CHUNK_LINES"] = previous


if __name__ == "__main__":
    unittest.main()
