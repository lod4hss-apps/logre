import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lib.state import get_entity_form_field_key  # noqa: E402


class TestEntityFormKeys(unittest.TestCase):
    def test_property_occurrences_have_distinct_keys(self):
        property_ = Mock()
        property_.get_key.return_value = "crm:E21-sdh-shortcut:P10-xsd:string"

        first = get_entity_form_field_key(property_, 0)
        second = get_entity_form_field_key(property_, 1)

        self.assertEqual("crm:E21-sdh-shortcut:P10-xsd:string-0", first)
        self.assertEqual("crm:E21-sdh-shortcut:P10-xsd:string-1", second)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
