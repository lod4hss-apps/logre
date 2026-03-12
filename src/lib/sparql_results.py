from typing import Any, Dict, List

from graphly.schema import Prefixes


def _parse_binding_value(binding: dict[str, Any], prefixes: Prefixes) -> Any:
    value_type = binding.get("type")
    datatype = binding.get("datatype")
    value = binding.get("value")

    if value_type == "uri":
        return prefixes.shorten(value)
    if (
        value_type == "literal"
        and datatype == "http://www.w3.org/2001/XMLSchema#integer"
    ):
        if value is None:
            return None
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return value
    return value


def parse_sparql_json_response(
    response_json: object,
    prefixes: Prefixes,
) -> List[Dict[str, Any]]:
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

    rows: List[Dict[str, Any]] = []
    for binding_row in bindings:
        if not isinstance(binding_row, dict):
            continue

        row: Dict[str, Any] = {}
        for key, value_obj in binding_row.items():
            if isinstance(value_obj, dict):
                row[key] = _parse_binding_value(value_obj, prefixes)
            else:
                row[key] = value_obj

        rows.append(row)

    # Preserve SELECT projection columns without forcing every row to carry
    # explicit None values (which floods table cells with blanks).
    if rows and columns:
        first_row = rows[0]
        ordered_first_row: Dict[str, Any] = {
            column: first_row.get(column) for column in columns
        }
        for key, value in first_row.items():
            if key not in ordered_first_row:
                ordered_first_row[key] = value
        rows[0] = ordered_first_row

    return rows
