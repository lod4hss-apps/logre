from __future__ import annotations

from typing import List

from graphly.schema import Prefixes, Prefix

from lib.utils import to_snake_case
from .sparql_technologies import get_sparql_technology


class Endpoint:
    """
    Represents a SPARQL endpoint configuration (connection parameters + prefixes).

    Attributes:
        key (str): Stable identifier used in configuration files.
        name (str): Human friendly label displayed in the UI.
        technology (str): SPARQL implementation (Fuseki, GraphDB, RDF4J, ...).
        url (str): Base URL of the endpoint.
        username (str): Optional username for authentication.
        password (str): Optional password for authentication.
        prefixes (Prefixes): Prefix list attached to this endpoint.
        sparql: Instantiated SPARQL client matching the technology.
    """

    key: str
    name: str
    technology: str
    url: str
    username: str
    password: str
    prefixes: Prefixes

    def __init__(
        self,
        name: str,
        technology: str,
        url: str,
        username: str,
        password: str,
        prefixes: Prefixes | None = None,
        key: str | None = None,
    ) -> None:
        self.name = name
        self.key = key or to_snake_case(name)
        self.technology = technology
        self.url = url
        self.username = username or ''
        self.password = password or ''
        self.prefixes = prefixes or Prefixes()

        SparqlClass = get_sparql_technology(technology)
        self.sparql = SparqlClass(url, self.username, self.password)

    def to_dict(self) -> dict:
        return {
            'key': self.key,
            'name': self.name,
            'technology': self.technology,
            'url': self.url,
            'username': self.username,
            'password': self.password,
            'prefixes': [prefix.to_dict() for prefix in self.prefixes] if self.prefixes else [],
        }

    @staticmethod
    def from_dict(obj: dict) -> 'Endpoint':
        prefixes_raw: List[dict] = obj.get('prefixes', [])
        prefixes = Prefixes([Prefix(p.get('short'), p.get('long')) for p in prefixes_raw])
        return Endpoint(
            name=obj.get('name'),
            technology=obj.get('technology'),
            url=obj.get('url'),
            username=obj.get('username'),
            password=obj.get('password'),
            prefixes=prefixes,
            key=obj.get('key'),
        )
