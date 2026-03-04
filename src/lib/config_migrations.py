from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from yaml import safe_dump, safe_load

from lib.config_paths import get_config_home


logger = logging.getLogger(__name__)


def migrate_config_if_needed(config_path: Path) -> bool:
    if not config_path.exists():
        return False

    try:
        raw = config_path.read_text(encoding="utf-8")
        old_config = safe_load(raw) or {}
    except Exception:
        logger.exception("Failed to read configuration for migration")
        return False

    if not isinstance(old_config, dict):
        return False

    if "version" in old_config:
        return False

    new_config = {
        "prefixes": [],
        "endpoints": [],
        "data_bundles": [],
        "default_data_bundle": None,
        "sparql_queries": [],
    }

    for endpoint in old_config.get("endpoints", []) or []:
        if not isinstance(endpoint, dict):
            continue

        new_config["endpoints"].append(
            {
                "name": endpoint.get("name"),
                "technology": endpoint.get("technology"),
                "url": endpoint.get("url"),
                "username": endpoint.get("username"),
                "password": endpoint.get("password"),
            }
        )

        for data_bundle in endpoint.get("data_bundles", []) or []:
            if not isinstance(data_bundle, dict):
                continue
            new_config["data_bundles"].append(
                {
                    "name": data_bundle.get("name"),
                    "base_uri": endpoint.get("base_uri"),
                    "endpoint_name": endpoint.get("name"),
                    "model_framework": data_bundle.get("ontology_framework"),
                    "prop_type_uri": data_bundle.get("type_property"),
                    "prop_label_uri": data_bundle.get("label_property"),
                    "prop_comment_uri": data_bundle.get("comment_property"),
                    "graph_data_uri": data_bundle.get("graph_data_uri"),
                    "graph_model_uri": data_bundle.get("graph_ontology_uri"),
                    "graph_metadata_uri": data_bundle.get("graph_metadata_uri"),
                }
            )

        for prefix in endpoint.get("prefixes", []) or []:
            if not isinstance(prefix, dict):
                continue
            short = prefix.get("short")
            if not short:
                continue
            have = {p.get("short") for p in new_config["prefixes"]}
            if short not in have:
                new_config["prefixes"].append(
                    {"short": short, "long": prefix.get("long")}
                )

    for query in old_config.get("queries", []) or []:
        if not isinstance(query, dict):
            continue
        new_config["sparql_queries"].append([query.get("name"), query.get("text")])

    new_config["version"] = "2.1"

    backup_dir_override = os.getenv("LOGRE_CONFIG_BACKUP_DIR")
    if backup_dir_override:
        backup_dir = Path(backup_dir_override)
    else:
        base_dir = Path(__file__).resolve().parent.parent.parent
        try:
            is_repo_path = config_path.resolve().is_relative_to(base_dir)
        except Exception:
            is_repo_path = str(config_path.resolve()).startswith(str(base_dir))
        backup_dir = (
            get_config_home() / "backups" if is_repo_path else config_path.parent
        )
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = (
        backup_dir
        / f"{config_path.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    try:
        backup_path.write_text(raw, encoding="utf-8")
    except Exception:
        logger.exception("Failed to write configuration backup")

    try:
        config_path.write_text(safe_dump(new_config, sort_keys=False), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write migrated configuration")
        return False

    logger.info("Configuration migrated to version 2.1")
    return True
