from typing import Dict, List

from graphly.schema import Prefixes


def _parse_binding_value(binding: dict, prefixes: Prefixes):
    value_type = binding.get("type")
    datatype = binding.get("datatype")
    value = binding.get("value")

    if value_type == "uri":
        return prefixes.shorten(value)
    if (
        value_type == "literal"
        and datatype == "http://www.w3.org/2001/XMLSchema#integer"
    ):
        return int(value)
    return value


def parse_sparql_json_response(response_json: object, prefixes: Prefixes) -> List[Dict]:
    """
    Parse SPARQL JSON results while preserving SELECT projection columns.

    Unlike the upstream parser, this implementation initializes each row with
    all variables declared in ``head.vars`` so optional/unbound variables remain
    present as ``None`` values.
    """
    if not isinstance(response_json, dict):
        return []

    results = response_json.get("results")
    if not isinstance(results, dict):
        return []

    bindings = results.get("bindings")
    if not isinstance(bindings, list):
        return []

    head = response_json.get("head")
    columns = []
    if isinstance(head, dict):
        vars_ = head.get("vars")
        if isinstance(vars_, list):
            columns = [str(column) for column in vars_]

    rows: List[Dict] = []
    for binding_row in bindings:
        if not isinstance(binding_row, dict):
            continue

        row = {column: None for column in columns}
        for key, value_obj in binding_row.items():
            if isinstance(value_obj, dict):
                row[key] = _parse_binding_value(value_obj, prefixes)
            else:
                row[key] = value_obj

        rows.append(row)

    return rows
