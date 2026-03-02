from __future__ import annotations

import os
import sys
from pathlib import Path


def get_config_home() -> Path:
    env_path = os.getenv("LOGRE_CONFIG_HOME")
    if env_path:
        return Path(env_path)

    if sys.platform == "win32":
        base = os.getenv("APPDATA")
        if not base:
            base = str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "Logre"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Logre"

    xdg_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home) / "logre"
    return Path.home() / ".config" / "logre"


def get_config_path() -> Path:
    override = os.getenv("LOGRE_CONFIG_PATH")
    if override:
        return Path(override)
    return get_config_home() / "logre-config.yaml"


def get_default_config_path(base_dir: str) -> Path | None:
    override = os.getenv("LOGRE_DEFAULT_CONFIG_PATH")
    if override:
        return Path(override)
    fallback = Path(base_dir) / "docker" / "logre-config.yml"
    if fallback.exists():
        return fallback
    return None


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
