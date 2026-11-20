import sys
import unittest
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lib.data_table import (  # noqa: E402
    EntityFilter,
    RelationStep,
    export_data_table_csv,
    hide_empty_model_columns,
)


class TestDataTableExport(unittest.TestCase):
    def test_empty_model_fields_are_hidden_only_from_displayed_page(self):
        table = pd.DataFrame(
            {
                "URI": ["person1", "person2"],
                "Title": ["", None],
                "Name": ["Alice", ""],
                "Outgoing count": [0, 0],
            }
        )

        displayed = hide_empty_model_columns(table, ["Title", "Name"])

        self.assertEqual(["URI", "Name", "Outgoing count"], list(displayed.columns))
        self.assertIn("Title", table.columns)

    def test_export_fetches_all_filtered_rows_in_batches_with_full_columns(self):
        selected_class = SimpleNamespace(uri="http://example.org/Person")
        calls = []
        rows = [
            {"URI": "person1", "Title": "", "Name": "Alice"},
            {"URI": "person2", "Title": "", "Name": "Bob"},
            {"URI": "person3", "Title": "Dr", "Name": "Carol"},
        ]

        def get_data_table(cls, **kwargs):
            self.assertIs(cls, selected_class)
            calls.append(kwargs)
            start = kwargs["offset"]
            return pd.DataFrame(
                rows[start : start + kwargs["limit"]],
                columns=["URI", "Title", "Name"],
            )

        bundle = SimpleNamespace(get_data_table=get_data_table)
        filters = [
            EntityFilter(selected_class.uri, "Title", "Dr"),
            EntityFilter(
                "http://example.org/Birth",
                "Name",
                "Alice",
                (
                    RelationStep(
                        "http://example.org/subject",
                        "subject",
                        selected_class.uri,
                        "http://example.org/Birth",
                        reverse=True,
                    ),
                ),
            ),
        ]
        content = export_data_table_csv(
            bundle,
            selected_class,
            filters,
            "OR",
            batch_size=2,
        )

        self.assertEqual([0, 2], [call["offset"] for call in calls])
        self.assertTrue(
            all(
                call["filters"] == filters
                and call["filter_operator"] == "OR"
                for call in calls
            )
        )
        exported = pd.read_csv(StringIO(content), keep_default_na=False)
        self.assertEqual(["person1", "person2", "person3"], exported["URI"].tolist())
        self.assertEqual(["URI", "Title", "Name"], list(exported.columns))

    def test_empty_export_still_has_headers(self):
        selected_class = SimpleNamespace(uri="http://example.org/Person")
        bundle = SimpleNamespace(
            get_data_table=lambda *args, **kwargs: pd.DataFrame(),
            get_data_table_columns_names=lambda cls: ["Title"],
        )

        content = export_data_table_csv(bundle, selected_class, [])

        self.assertEqual(
            "URI,Title,Outgoing count,Incoming count\n", content
        )


if __name__ == "__main__":
    unittest.main()
