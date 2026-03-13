from __future__ import annotations

import re
from urllib.parse import urlencode

from lib import state

_DOC_LINK_RE = re.compile(r"/documentation\?section=([a-z0-9-]+)")


def _current_endpoint_key() -> str | None:
    return state.get_endpoint_key()


def _current_db_key() -> str | None:
    db = state.get_data_bundle()
    return db.key if db else None


def doc_link(section: str) -> str:
    params = {"section": section}
    endpoint_key = _current_endpoint_key()
    db_key = _current_db_key()
    if endpoint_key:
        params["endpoint"] = endpoint_key
    if db_key:
        params["db"] = db_key
    return "/documentation?" + urlencode(params)


def decorate_doc_links(text: str) -> str:
    if not text:
        return text
    return _DOC_LINK_RE.sub(lambda match: doc_link(match.group(1)), text)
