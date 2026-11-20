import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class TestDataTableFilterUI(unittest.TestCase):
    def test_first_filter_class_controls_table_after_adding_and_removing_rows(self):
        person = SimpleNamespace(
            uri="http://example.org/Person",
            class_uri="owl:Class",
            get_text=lambda: "Person",
        )
        birth = SimpleNamespace(
            uri="http://example.org/Birth",
            class_uri="owl:Class",
            get_text=lambda: "Birth",
        )
        requested = []
        bundle = SimpleNamespace(
            key="example",
            model=SimpleNamespace(classes=[person, birth], properties=[]),
            get_data_table_columns_names=lambda cls: [],
            get_data_table=lambda cls, **kwargs: requested.append(cls.uri) or pd.DataFrame(),
        )

        with (
            patch("components.init.init"),
            patch("components.menu.menu"),
            patch("lib.state.get_data_bundle", return_value=bundle),
            patch("lib.state.get_endpoint_key", return_value="example-endpoint"),
            patch("lib.state.data_table_get_page", return_value=1),
            patch("lib.state.data_table_set_page"),
        ):
            app = AppTest.from_file(str(SRC_DIR / "pages" / "data-table.py"))
            app.run()
            self.assertFalse(app.exception)
            self.assertNotIn("Get entity table of class:", [widget.label for widget in app.selectbox])
            self.assertEqual([], requested)

            app.selectbox[1].set_value("http://example.org/Person").run()
            self.assertFalse(app.exception)
            self.assertEqual(person.uri, requested[-1])

            next(button for button in app.button if button.label == "+ Add filter").click().run()
            self.assertFalse(app.exception)
            app.selectbox[3].set_value("http://example.org/Birth").run()
            self.assertFalse(app.exception)
            self.assertEqual(person.uri, requested[-1])

            next(button for button in app.button if button.label == "Remove").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(
                birth.uri,
                requested[-1],
                f"ids={app.session_state['data_table_filter_ids']} "
                f"classes={[widget.value for widget in app.selectbox]}",
            )

            next(button for button in app.button if button.label == "Remove").click().run()
            self.assertFalse(app.exception)
            self.assertEqual([], app.session_state["data_table_filter_ids"])
            self.assertEqual(birth.uri, requested[-1])

            next(button for button in app.button if button.label == "+ Add filter").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(birth.uri, requested[-1])
            app.selectbox[1].set_value(person.uri).run()
            self.assertEqual(person.uri, requested[-1])


if __name__ == "__main__":
    unittest.main()
