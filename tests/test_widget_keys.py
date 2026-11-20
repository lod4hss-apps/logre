import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lib.utils import get_widget_key  # noqa: E402


class TestWidgetKeys(unittest.TestCase):
    def test_duplicate_property_occurrences_have_distinct_card_keys(self):
        first = get_widget_key(
            "entity-card", "base:entity", "card", "out", 0, 0, "info"
        )
        second = get_widget_key(
            "entity-card", "base:entity", "card", "out", 1, 0, "info"
        )

        self.assertNotEqual(first, second)

    def test_separator_characters_do_not_make_keys_ambiguous(self):
        first = get_widget_key("entity-card", "a-b", "c", 0)
        second = get_widget_key("entity-card", "a", "b-c", 0)

        self.assertNotEqual(first, second)

    def test_same_structure_keeps_the_same_key(self):
        parts = ("base:entity", "extended", "in", 2, 0, "info")

        self.assertEqual(
            get_widget_key("entity-card", *parts),
            get_widget_key("entity-card", *parts),
        )


if __name__ == "__main__":
    unittest.main()
