from io import StringIO
from collections import defaultdict, deque
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RelationStep:
    property_uri: str
    label: str
    from_class_uri: str
    to_class_uri: str
    reverse: bool = False


@dataclass(frozen=True)
class EntityFilter:
    class_uri: str
    column_name: str
    value: str
    path: tuple[RelationStep, ...] = ()


def find_relation_paths(
    properties, source_uri: str, target_uri: str, max_hops: int = 3
) -> list[tuple[RelationStep, ...]]:
    """Find distinct, short model paths in either direction between classes."""
    adjacency = defaultdict(list)
    seen_edges = set()
    for prop in properties:
        if not prop.domain or not prop.range:
            continue
        if prop.range.class_uri == "rdfs:Datatype" or prop.range.uri.startswith("xsd:"):
            continue
        domain_uri, range_uri = prop.domain.uri, prop.range.uri
        if not domain_uri or not range_uri or not prop.uri:
            continue
        for origin, destination, reverse in (
            (domain_uri, range_uri, False),
            (range_uri, domain_uri, True),
        ):
            key = (origin, destination, prop.uri, reverse)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            adjacency[origin].append(
                RelationStep(prop.uri, prop.label or prop.uri, origin, destination, reverse)
            )

    paths = [()] if source_uri == target_uri else []
    queue = deque([(source_uri, (), frozenset({source_uri}))])
    while queue and len(paths) < 50:
        current, path, visited = queue.popleft()
        if len(path) >= max_hops:
            continue
        for step in adjacency[current]:
            next_path = (*path, step)
            if step.to_class_uri == target_uri:
                paths.append(next_path)
                if len(paths) >= 50:
                    break
            elif step.to_class_uri not in visited:
                queue.append((step.to_class_uri, next_path, visited | {step.to_class_uri}))
    return paths


def hide_empty_model_columns(
    table: pd.DataFrame, model_columns: list[str]
) -> pd.DataFrame:
    """Hide model fields without a value on the displayed page only."""
    empty_columns = [
        name
        for name in model_columns
        if table[name].fillna("").astype(str).str.strip().eq("").all()
    ]
    return table.drop(columns=empty_columns)


def export_data_table_csv(
    data_bundle,
    selected_class,
    filters: list[EntityFilter],
    filter_operator: str = "AND",
    batch_size: int = 500,
) -> str:
    """Export every matching row, keeping the full set of model columns."""
    output = StringIO()
    offset = 0
    first_batch = True

    while True:
        batch = data_bundle.get_data_table(
            selected_class,
            limit=batch_size,
            offset=offset,
            filters=filters,
            filter_operator=filter_operator,
        )
        if batch.empty:
            if first_batch:
                columns = [
                    "URI",
                    *data_bundle.get_data_table_columns_names(selected_class),
                    "Outgoing count",
                    "Incoming count",
                ]
                pd.DataFrame(columns=columns).to_csv(output, index=False)
            break

        batch.to_csv(output, index=False, header=first_batch)
        first_batch = False
        offset += len(batch)
        if len(batch) < batch_size:
            break

    return output.getvalue()
