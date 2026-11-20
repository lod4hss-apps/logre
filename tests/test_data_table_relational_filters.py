import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lib.data_table import EntityFilter, find_relation_paths  # noqa: E402
from schema.data_bundle import DataBundle  # noqa: E402


def property_(uri, label, domain, range_, card_of):
    return SimpleNamespace(
        uri=uri, label=label, domain=domain, range=range_, card_of=card_of, order=1
    )


class TestRelationalDataTableFilters(unittest.TestCase):
    def setUp(self):
        self.person = SimpleNamespace(
            uri="http://example.org/Person", label="Person", class_uri="owl:Class"
        )
        self.birth = SimpleNamespace(
            uri="http://example.org/Birth", label="Birth", class_uri="owl:Class"
        )
        self.event = SimpleNamespace(
            uri="http://example.org/Event", label="Event", class_uri="owl:Class"
        )
        string = SimpleNamespace(
            uri="xsd:string", class_uri="rdfs:Datatype", label="String"
        )
        self.name = property_(
            "http://example.org/name", "Name", self.person, string, self.person
        )
        self.date = property_(
            "http://example.org/date", "Date", self.birth, string, self.birth
        )
        self.has_person = property_(
            "http://example.org/subject", "subject", self.birth, self.person, self.birth
        )
        self.second_person = property_(
            "http://example.org/witness", "witness", self.birth, self.person, self.birth
        )
        self.bundle = DataBundle.__new__(DataBundle)
        self.bundle.model = SimpleNamespace(
            properties=[self.name, self.date, self.has_person, self.second_person],
            type_property="rdf:type",
            label_property="rdfs:label",
            comment_property="rdfs:comment",
        )
        self.bundle.prefixes = SimpleNamespace(shorts=lambda: {})
        self.queries = []

        def run(query, prefixes):
            self.queries.append(query)
            if len(self.queries) == 1:
                return [{"uri": "http://example.org/person1", "col_0": "Alice", "col_1": ""}]
            return []

        self.bundle.data = SimpleNamespace(
            sparql_begin="GRAPH <http://example.org/data> {",
            sparql_end="}",
            sparql=SimpleNamespace(run=run),
        )

    def test_multiple_relation_paths_are_available_in_both_directions(self):
        paths = find_relation_paths(
            self.bundle.model.properties, self.person.uri, self.birth.uri
        )
        self.assertEqual(2, len(paths))
        self.assertTrue(all(path[0].reverse for path in paths))
        self.assertEqual(
            ["http://example.org/subject", "http://example.org/witness"],
            [path[0].property_uri for path in paths],
        )
        reverse = find_relation_paths(
            self.bundle.model.properties, self.birth.uri, self.person.uri
        )
        self.assertTrue(all(not path[0].reverse for path in reverse))

    def test_person_name_and_linked_birth_date_are_combined(self):
        path = find_relation_paths(
            self.bundle.model.properties, self.person.uri, self.birth.uri
        )[0]
        filters = [
            EntityFilter(self.person.uri, "Name (String)", "Alice"),
            EntityFilter(self.birth.uri, "Date (String)", "1900", path),
        ]
        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            table = self.bundle.get_data_table(
                self.person, filters=filters, filter_operator="AND"
            )

        query = self.queries[0]
        self.assertEqual(1, len(table))
        self.assertIn("?uri_ <http://example.org/name> ?filter_value_0", query)
        self.assertIn("?filter_node_1_0 <http://example.org/subject> ?uri_", query)
        self.assertIn("?filter_node_1_0 rdf:type <http://example.org/Birth>", query)
        self.assertIn("?filter_node_1_0 <http://example.org/date> ?filter_value_1", query)
        self.assertIn("} && EXISTS {", query)

        self.queries.clear()
        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            self.bundle.get_data_table(self.person, filters=filters, filter_operator="OR")
        self.assertIn("} || EXISTS {", self.queries[0])

    def test_indirect_path_can_be_selected_and_wrong_path_is_rejected(self):
        through_event = property_(
            "http://example.org/hasEvent",
            "has event",
            self.person,
            self.event,
            self.person,
        )
        event_birth = property_(
            "http://example.org/hasBirth", "has birth", self.event, self.birth, self.event
        )
        self.bundle.model.properties += [through_event, event_birth]
        paths = find_relation_paths(
            self.bundle.model.properties, self.person.uri, self.birth.uri
        )
        indirect = next(path for path in paths if len(path) == 2)
        criterion = EntityFilter(self.birth.uri, "Date (String)", "1900", indirect)

        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            self.bundle.get_data_table(self.person, filters=[criterion])
        self.assertIn("?uri_ <http://example.org/hasEvent> ?filter_node_0_0", self.queries[0])
        self.assertIn(
            "?filter_node_0_0 <http://example.org/hasBirth> ?filter_node_0_1",
            self.queries[0],
        )

        with self.assertRaisesRegex(ValueError, "No model relation"):
            self.bundle.get_data_table(
                self.person,
                filters=[EntityFilter(self.birth.uri, "Date (String)", "1900")],
            )

    def test_incoming_field_on_related_class_and_disconnected_class(self):
        place = SimpleNamespace(
            uri="http://example.org/Place", label="Place", class_uri="owl:Class"
        )
        self.bundle.model.properties.append(
            property_("http://example.org/placeOf", "place of", place, self.birth, self.birth)
        )
        path = find_relation_paths(
            self.bundle.model.properties, self.person.uri, self.birth.uri
        )[0]
        with patch("schema.data_bundle.prepare", side_effect=lambda uri, _: f"<{uri}>"):
            self.bundle.get_data_table(
                self.person,
                filters=[
                    EntityFilter(self.birth.uri, "place of (Birth) (incoming)", "Paris", path)
                ],
            )
        self.assertIn(
            "?filter_entity_0 <http://example.org/placeOf> ?filter_node_0_0",
            self.queries[0],
        )
        self.assertIn("?filter_entity_0 rdfs:label ?filter_value_0", self.queries[0])

        unrelated = SimpleNamespace(uri="http://example.org/Unrelated")
        self.assertEqual(
            [],
            find_relation_paths(
                self.bundle.model.properties, self.person.uri, unrelated.uri
            ),
        )


if __name__ == "__main__":
    unittest.main()
