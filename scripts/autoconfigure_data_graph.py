#!/usr/bin/env python3
"""
Ensure the generated Logre configuration points the data graph URI to an actual
graph that contains triples. When users load external datasets (e.g. DH25-Lisbon)
into RDF4J via N-Quads, triples usually live in a named graph that differs from
the default placeholder ``base:data``. Without adjusting the config, all queries
scoped to ``GRAPH base:data`` return zero results and features like Find Entity
appear broken. This helper inspects the configured repositories and rewrites the
YAML file so ``graph_data_uri`` targets a real context (or the default graph).
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import requests
from requests.auth import HTTPBasicAuth
from yaml import safe_dump, safe_load


CONTEXTS_QUERY = """
SELECT ?g (COUNT(*) AS ?triples)
WHERE {
  GRAPH ?g { ?s ?p ?o }
}
GROUP BY ?g
ORDER BY DESC(?triples)
"""

DEFAULT_GRAPH_SAMPLE_QUERY = """
SELECT (COUNT(*) AS ?triples)
WHERE {
  ?s ?p ?o .
}
LIMIT 1
"""


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Adjust graph_data_uri entries to match existing RDF4J contexts.")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file to update.")
    return parser


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file {path} not found.")
    with path.open("r", encoding="utf-8") as handle:
        return safe_load(handle.read()) or {}


def save_config(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        safe_dump(data, handle, sort_keys=False)


def build_prefix_map(prefixes: Sequence[dict]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for prefix in prefixes or []:
        short = prefix.get("short")
        long = prefix.get("long")
        if short and long:
            mapping[short] = long
    return mapping


def expand_uri(value: Optional[str], prefix_map: Dict[str, str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    if trimmed.startswith("<") and trimmed.endswith(">"):
        trimmed = trimmed[1:-1]
    if ":" in trimmed and not trimmed.startswith("http"):
        short, rest = trimmed.split(":", 1)
        base = prefix_map.get(short)
        if base:
            return f"{base}{rest}"
    return trimmed


def shorten_uri(value: str, prefix_map: Dict[str, str]) -> str:
    cleaned = value.strip()
    for short, long in prefix_map.items():
        if cleaned.startswith(long):
            return f"{short}:{cleaned[len(long):]}"
    return cleaned


def query(endpoint_url: str, query_text: str, username: str, password: str) -> Optional[dict]:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/sparql-results+json",
    }
    auth = HTTPBasicAuth(username, password) if username else None
    try:
        response = requests.post(
            endpoint_url,
            data={"query": query_text},
            headers=headers,
            auth=auth,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"[autoconfigure] Unable to query {endpoint_url}: {exc}", file=sys.stderr)
        return None


def list_contexts(endpoint_url: str, username: str, password: str) -> List[Tuple[str, int]]:
    payload = query(endpoint_url, CONTEXTS_QUERY, username, password)
    if not payload:
        return []

    contexts: List[Tuple[str, int]] = []
    for row in payload.get("results", {}).get("bindings", []):
        context = row.get("g", {}).get("value")
        count_literal = row.get("triples", {}).get("value")
        if context and count_literal is not None:
            try:
                contexts.append((context, int(count_literal)))
            except ValueError:
                continue
    return contexts


def default_graph_has_data(endpoint_url: str, username: str, password: str) -> bool:
    payload = query(endpoint_url, DEFAULT_GRAPH_SAMPLE_QUERY, username, password)
    if not payload:
        return False
    bindings = payload.get("results", {}).get("bindings", [])
    if not bindings:
        return False
    try:
        return int(bindings[0].get("triples", {}).get("value", "0")) > 0
    except (TypeError, ValueError):
        return False


def choose_data_graph(
    contexts: List[Tuple[str, int]],
    ignored: Sequence[Optional[str]],
) -> Optional[str]:
    ignore_set = {ctx for ctx in ignored if ctx}
    for context, _ in contexts:
        if context not in ignore_set:
            return context
    return None


def ensure_data_graph(bundle: dict, prefixes: Dict[str, str]) -> bool:
    endpoint_url = bundle.get("endpoint_url")
    if not endpoint_url:
        return False

    username = bundle.get("username") or ""
    password = bundle.get("password") or ""

    contexts = list_contexts(endpoint_url, username, password)
    context_map = {ctx: count for ctx, count in contexts}

    current_data_graph = expand_uri(bundle.get("graph_data_uri"), prefixes)
    if current_data_graph and current_data_graph in context_map:
        return False  # Config already points to a populated graph.

    model_graph = expand_uri(bundle.get("graph_model_uri"), prefixes)
    metadata_graph = expand_uri(bundle.get("graph_metadata_uri"), prefixes)

    candidate = choose_data_graph(contexts, [model_graph, metadata_graph])
    if candidate:
        bundle["graph_data_uri"] = shorten_uri(candidate, prefixes)
        print(f"[autoconfigure] Data graph for '{bundle.get('name', endpoint_url)}' set to {bundle['graph_data_uri']}")
        return True

    if default_graph_has_data(endpoint_url, username, password):
        bundle["graph_data_uri"] = ""
        print(f"[autoconfigure] Data graph for '{bundle.get('name', endpoint_url)}' set to default graph")
        return True

    return False


def main() -> int:
    args = parse_args().parse_args()
    config_path = Path(args.config)

    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"[autoconfigure] {exc}", file=sys.stderr)
        return 0

    prefixes = build_prefix_map(config.get("prefixes", []))
    changed = False
    for bundle in config.get("data_bundles", []):
        if ensure_data_graph(bundle, prefixes):
            changed = True

    if changed:
        save_config(config_path, config)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
