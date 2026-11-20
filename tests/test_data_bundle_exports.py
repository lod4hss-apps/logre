import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from schema.data_bundle import DataBundle  # noqa: E402


class _FakeGraph:
    def __init__(self, nquads: str, turtle: str) -> None:
        self.nquads = nquads
        self.turtle = turtle

    def dump_nquad(self):
        return self.nquads

    def dump_turtle(self):
        return self.turtle


class TestDataBundleExports(unittest.TestCase):
    def setUp(self):
        self.bundle = DataBundle.__new__(DataBundle)
        self.bundle.model = _FakeGraph("model.nq\n", "model.ttl\n")
        self.bundle.data = _FakeGraph("data.nq\n", "data.ttl\n")
        self.bundle.metadata = _FakeGraph("metadata.nq\n", "metadata.ttl\n")

    def test_dump_nq_concatenates_graphs_in_order(self):
        content = self.bundle.dump_nq()

        self.assertEqual("model.nq\ndata.nq\nmetadata.nq\n", content)

    def test_dump_ttl_exports_each_current_graph(self):
        content = self.bundle.dump_ttl()

        self.assertEqual(
            {
                "data": "data.ttl\n",
                "model": "model.ttl\n",
                "metadata": "metadata.ttl\n",
            },
            content,
        )

    def test_get_model_as_turtle_queries_model_graph(self):
        self.bundle.model.sparql_begin = "GRAPH <model> {"
        self.bundle.model.sparql_end = "}"
        queries = []

        def run(query):
            queries.append(query)
            return "model turtle"

        self.bundle.run = run

        self.assertEqual("model turtle", self.bundle.get_model_as_turtle())
        self.assertEqual(1, len(queries))
        self.assertIn("GRAPH <model> {", queries[0])
        self.assertIn("?s ?p ?o", queries[0])


if __name__ == "__main__":
    unittest.main()
