import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from schema.data_bundle import DataBundle  # noqa: E402


class TestDataTableDuplicateColumns(unittest.TestCase):
    def setUp(self):
        self.bundle = DataBundle.__new__(DataBundle)
        self.cls = SimpleNamespace(uri="http://example.org/Person")
        datatype = SimpleNamespace(
            uri="xsd:string", label="String", class_uri="rdfs:Datatype"
        )
        self.properties = [
            SimpleNamespace(
                uri=f"http://example.org/{uri}",
                label="Alternative Label",
                domain=self.cls,
                range=datatype,
                card_of=self.cls,
                order=index,
            )
            for index, uri in enumerate(("preferred", "alternate"), start=1)
        ]
        self.bundle.model = SimpleNamespace(
            properties=self.properties,
            type_property="rdf:type",
            label_property="rdfs:label",
            comment_property="rdfs:comment",
        )
        self.bundle.prefixes = SimpleNamespace(shorts=lambda: {})
        self.queries = []

        def run(query, prefixes):
            self.queries.append(query)
            if len(self.queries) == 1:
                return [{"uri": "http://example.org/person1", "col_0": "A", "col_1": "B"}]
            return []

        self.bundle.data = SimpleNamespace(
            sparql_begin="GRAPH <http://example.org/data> {",
            sparql_end="}",
            sparql=SimpleNamespace(run=run),
        )

    def test_duplicate_labels_are_unique_and_select_the_right_property(self):
        names = self.bundle.get_data_table_columns_names(self.cls)
        self.assertEqual(
            ["Alternative Label (String)", "Alternative Label (String) [2]"], names
        )

        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            table = self.bundle.get_data_table(
                self.cls, limit=10, sort_col=names[1], sort_way="ASC",
                filter_col=names[1], filter_value="B",
            )

        self.assertEqual(
            ["URI", *names, "Outgoing count", "Incoming count"],
            list(table.columns),
        )
        self.assertEqual("A", table.iloc[0][names[0]])
        self.assertEqual("B", table.iloc[0][names[1]])
        self.assertIn("?uri_ <http://example.org/alternate> ?sort_on", self.queries[0])
        self.assertIn("?uri_ <http://example.org/alternate> ?filter_value_0", self.queries[0])
        self.assertIn("ORDER BY ASC(?sort_on) ?uri_", self.queries[0])

    def test_unsorted_pages_use_distinct_uris_in_stable_order(self):
        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            self.bundle.get_data_table(self.cls, limit=10)

        self.assertIn("SELECT DISTINCT ?uri_", self.queries[0])
        self.assertIn("ORDER BY ?uri_", self.queries[0])

    def test_multiple_filters_combine_independent_exists_conditions(self):
        names = self.bundle.get_data_table_columns_names(self.cls)
        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            self.bundle.get_data_table(
                self.cls,
                filters=[(names[0], "A"), (names[1], 'B"C'), (names[0], "   ")],
                filter_operator="OR",
            )

        query = self.queries[0]
        self.assertIn("SELECT DISTINCT ?uri_", query)
        self.assertIn("?uri_ <http://example.org/preferred> ?filter_value_0", query)
        self.assertIn("?uri_ <http://example.org/alternate> ?filter_value_1", query)
        self.assertIn("LCASE(\"b\\\"c\")", query)
        self.assertIn("} || EXISTS {", query)
        self.assertNotIn("?filter_value_2", query)

    def test_and_filters_can_repeat_the_same_property(self):
        name = self.bundle.get_data_table_columns_names(self.cls)[0]
        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            self.bundle.get_data_table(
                self.cls, filters=[(name, "Alice"), (name, "Bob")]
            )

        query = self.queries[0]
        self.assertIn("} && EXISTS {", query)
        self.assertIn("?filter_value_0", query)
        self.assertIn("?filter_value_1", query)

    def test_existing_suffix_and_reserved_columns_do_not_collide(self):
        self.properties[0].label = "Title"
        self.properties[0].range = None
        self.properties[1].label = "Title"
        self.properties[1].range = None
        self.properties.append(
            SimpleNamespace(
                label="Title [2]",
                range=None,
                domain=self.cls,
                card_of=self.cls,
                order=3,
            )
        )
        names = self.bundle.get_data_table_columns_names(self.cls)
        self.assertEqual(["Title", "Title [3]", "Title [2]"], names)


if __name__ == "__main__":
    unittest.main()
