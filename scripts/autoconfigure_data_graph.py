#!/usr/bin/env python3
"""
Adjust graph_data_uri entries to match existing RDF4J contexts.
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from lib.autoconfigure_data_graph import autoconfigure_config


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(
        description="Adjust graph_data_uri entries to match existing RDF4J contexts."
    )
    parser.add_argument(
        "--config", required=True, help="Path to the YAML configuration file to update."
    )
    return parser


def main() -> int:
    args = parse_args().parse_args()
    config_path = Path(args.config)
    autoconfigure_config(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
