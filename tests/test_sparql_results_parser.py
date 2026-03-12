import sys
import unittest
from pathlib import Path

import pandas as pd
from graphly.schema import Prefix, Prefixes


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lib.sparql_results import parse_sparql_json_response  # noqa: E402


class TestSparqlResultsParser(unittest.TestCase):
    def test_graphly_parser_is_patched(self):
        import graphly.schema.sparql as graphly_sparql
        import schema.sparql_technologies  # noqa: F401

        self.assertIs(
            graphly_sparql.parse_sparql_json_response,
            parse_sparql_json_response,
        )

    def test_keeps_columns_from_head_vars_when_unbound(self):
        response_json = {
            "head": {
                "vars": [
                    "quantite_uri",
                    "quantite_label",
                    "valeur_num",
                    "year_begin",
                ]
            },
            "results": {
                "bindings": [
                    {
                        "quantite_uri": {
                            "type": "uri",
                            "value": "http://example.org/resource/q1",
                        },
                        "quantite_label": {"type": "literal", "value": "abc"},
                    },
                    {
                        "quantite_uri": {
                            "type": "uri",
                            "value": "http://example.org/resource/q2",
                        },
                        "quantite_label": {"type": "literal", "value": "42"},
                        "valeur_num": {
                            "type": "literal",
                            "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                            "value": "42.0",
                        },
                        "year_begin": {
                            "type": "literal",
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "value": "1900",
                        },
                    },
                ]
            },
        }
        prefixes = Prefixes([Prefix("ex", "http://example.org/resource/")])

        rows = parse_sparql_json_response(response_json, prefixes)
        self.assertEqual(2, len(rows))
        self.assertEqual(
            ["quantite_uri", "quantite_label", "valeur_num", "year_begin"],
            list(rows[0].keys()),
        )
        self.assertIsNone(rows[0]["valeur_num"])
        self.assertEqual("42.0", rows[1]["valeur_num"])
        self.assertEqual(1900, rows[1]["year_begin"])
        self.assertEqual("ex:q1", rows[0]["quantite_uri"])

    def test_csv_header_contains_optional_column(self):
        response_json = {
            "head": {"vars": ["a", "valeur_num", "b"]},
            "results": {
                "bindings": [
                    {
                        "a": {"type": "literal", "value": "x"},
                        "b": {"type": "literal", "value": "y"},
                    }
                ]
            },
        }

        rows = parse_sparql_json_response(response_json, Prefixes())
        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False)

        self.assertEqual(["a", "valeur_num", "b"], list(df.columns))
        self.assertTrue(csv.startswith("a,valeur_num,b\n"))

    def test_only_first_row_is_seeded_with_missing_columns(self):
        response_json = {
            "head": {"vars": ["a", "valeur_num", "b"]},
            "results": {
                "bindings": [
                    {
                        "a": {"type": "literal", "value": "x"},
                        "b": {"type": "literal", "value": "y"},
                    },
                    {
                        "a": {"type": "literal", "value": "x2"},
                        "b": {"type": "literal", "value": "y2"},
                    },
                ]
            },
        }

        rows = parse_sparql_json_response(response_json, Prefixes())

        self.assertIn("valeur_num", rows[0])
        self.assertIsNone(rows[0]["valeur_num"])
        self.assertNotIn("valeur_num", rows[1])


if __name__ == "__main__":
    unittest.main()
