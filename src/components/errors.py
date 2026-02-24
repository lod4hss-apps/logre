"""Contextual error snippets reused across pages."""

from typing import Optional

ERROR_TEXTS = {
    "configuration.load": (
        "There was an error while loading the configuration file."
    )
}

def error_text(key: str, additionals: str, fallback: Optional[str] = None) -> Optional[str]:
    """Return the textual hint associated with `key`, falling back when not existing"""
    return ERROR_TEXTS.get(key, fallback) + "More about the error:\n\n" + additionals