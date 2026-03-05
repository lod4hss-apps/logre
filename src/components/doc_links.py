from __future__ import annotations

import re
from urllib.parse import urlencode

import streamlit as st

from lib import state

_DOC_LINK_RE = re.compile(r"/documentation\?section=([a-z0-9-]+)")


def _first_param(value: str | list[str] | tuple[str, ...] | None) -> str | None:
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _current_param(name: str) -> str | None:
    return _first_param(st.query_params.get(name))


def _current_endpoint_key() -> str | None:
    return _current_param("endpoint") or state.get_endpoint_key()


def _current_db_key() -> str | None:
    db_param = _current_param("db")
    if db_param:
        return db_param
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
