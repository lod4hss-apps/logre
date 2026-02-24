"""Shared helpers to compute statistics for dashboards and insights views."""

from __future__ import annotations

from typing import Any, Dict, List


def summarize_classes(data_bundle, limit: int = 5) -> Dict[str, Any]:
    """Return class distribution, total count and Plotly-friendly data."""
    query = f"""
        SELECT ?class (COUNT(?instance) AS ?count)
        WHERE {{
            {data_bundle.graph_data.sparql_begin}
                ?instance {data_bundle.model.type_property} ?class .
            {data_bundle.graph_data.sparql_end}
        }}
        GROUP BY ?class
        ORDER BY DESC(?count)
    """
    response = data_bundle.graph_data.run(query, data_bundle.prefixes)
    if not response:
        return {"total": 0, "rows": [], "top": []}

    rows = []
    total = 0
    for row in response:
        total += int(row["count"])
        cls = data_bundle.model.find_class(row["class"])
        label = cls.get_text() if cls else data_bundle.prefixes.shorten(row["class"])
        rows.append({"uri": row["class"], "label": label, "count": int(row["count"])})

    top = rows[:limit]
    return {"total": total, "rows": rows, "top": top}


def summarize_properties(data_bundle, limit: int = 5) -> Dict[str, Any]:
    """Return property distribution (excluding type/label/comment)."""
    query = f"""
        SELECT ?property (COUNT(*) AS ?count)
        WHERE {{
            {data_bundle.graph_data.sparql_begin}
                ?subject ?property ?object .
            {data_bundle.graph_data.sparql_end}
        }}
        GROUP BY ?property
        ORDER BY DESC(?count)
    """
    response = data_bundle.graph_data.run(query, data_bundle.prefixes)
    if not response:
        return {"total": 0, "rows": [], "top": []}

    ignored = {
        data_bundle.model.type_property,
        data_bundle.model.label_property,
        data_bundle.model.comment_property,
    }

    rows: List[Dict[str, Any]] = []
    total = 0
    for row in response:
        if row["property"] in ignored:
            continue
        props = data_bundle.model.find_properties(row["property"])
        label = props[0].label if props and props[0].label else data_bundle.prefixes.shorten(row["property"])
        count = int(row["count"])
        total += count
        rows.append({"uri": row["property"], "label": label, "count": count})

    rows.sort(key=lambda r: r["count"], reverse=True)
    top = rows[:limit]
    return {"total": total, "rows": rows, "top": top}
