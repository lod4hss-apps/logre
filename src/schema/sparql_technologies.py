from enum import Enum
import os
import re

import requests
from graphly.schema import Sparql
import graphly.schema.sparql as graphly_sparql
from graphly.schema.prefixes import Prefixes
from graphly.sparql import Fuseki, Allegrograph, GraphDB, RDF4J
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth

from lib.sparql_results import parse_sparql_json_response


PREFIX_DECLARATION_RE = re.compile(
    r"(?im)^\s*PREFIX\s+([A-Za-z][\w.-]*)\s*:\s*<[^>]+>\s*$"
)


def _extract_declared_prefix_shorts(query_text: str) -> set[str]:
    return {match.group(1) for match in PREFIX_DECLARATION_RE.finditer(query_text)}


def _patch_graphly_parser() -> None:
    graphly_sparql.parse_sparql_json_response = parse_sparql_json_response


def _get_sparql_timeout_seconds() -> float:
    raw_value = os.getenv("LOGRE_SPARQL_TIMEOUT", "12")
    try:
        parsed = float(raw_value)
    except (TypeError, ValueError):
        return 12.0
    return parsed if parsed > 0 else 12.0


def _get_nquads_chunk_lines() -> int:
    raw_value = os.getenv("LOGRE_NQUADS_CHUNK_LINES", "10000")
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return 10000
    return parsed if parsed > 0 else 10000


def _patch_graphly_timeout() -> None:
    if getattr(graphly_sparql.Sparql, "_logre_timeout_patched", False):
        return

    def _run_with_timeout(
        self,
        text: str,
        prefixes: Prefixes = None,
        query_param: str = "query",
        url_appendix: str = "",
        parse_response: bool = True,
    ):
        prefixes = prefixes or Prefixes()

        if os.getenv("GRAPHLY_MODE") == "debug":
            graphly_sparql.log_query(self.url, text, prefixes)

        text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])

        declared_prefixes = _extract_declared_prefix_shorts(text)
        merged_prefix_lines = []
        added_shorts = set()
        for prefix in prefixes:
            short = getattr(prefix, "short", None)
            if not short or short in added_shorts or short in declared_prefixes:
                continue
            merged_prefix_lines.append(prefix.to_sparql())
            added_shorts.add(short)

        if merged_prefix_lines:
            text = "\n".join(merged_prefix_lines) + "\n" + text

        data = {query_param: text}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        }
        auth = HTTPBasicAuth(self.username, self.password) if self.username else None

        response = requests.post(
            self.url + url_appendix,
            data=data,
            headers=headers,
            auth=auth,
            timeout=_get_sparql_timeout_seconds(),
        )
        response.raise_for_status()

        if parse_response:
            try:
                return graphly_sparql.parse_sparql_json_response(
                    response.json(), prefixes
                )
            except Exception:
                return response.text

    graphly_sparql.Sparql.run = _run_with_timeout
    graphly_sparql.Sparql._logre_timeout_patched = True


def _patch_graphly_nquads_upload() -> None:
    if getattr(graphly_sparql.Sparql, "_logre_nquads_upload_patched", False):
        return

    def _upload_nquads_with_adaptive_chunking(self, nquad_content: str) -> None:
        lines = nquad_content.splitlines()
        lines_number = len(lines)

        if lines_number == 0:
            print("> Uploaded a total of 0 triples")
            return

        chunk_lines = min(_get_nquads_chunk_lines(), lines_number)
        uploaded_count = 0

        while uploaded_count < lines_number:
            next_count = min(uploaded_count + chunk_lines, lines_number)
            chunk = "\n".join(lines[uploaded_count:next_count])
            chunk_len = next_count - uploaded_count
            percent_done = round((uploaded_count / lines_number) * 100)
            print(
                f"> Uploaded {uploaded_count} triples / {lines_number} ({percent_done} %) - Uploading {chunk_len} more..."
            )

            try:
                self.upload_nquads_chunk(chunk)
                uploaded_count = next_count
            except HTTPError as err:
                status_code = getattr(
                    getattr(err, "response", None), "status_code", None
                )
                if status_code != 413:
                    raise

                if chunk_lines <= 1:
                    raise HTTPError(
                        "Upload failed with HTTP 413 even for a single N-Quads line. "
                        "Increase the endpoint/proxy request body limit or split very large lines.",
                        response=err.response,
                        request=err.request,
                    ) from err

                chunk_lines = max(1, chunk_lines // 2)
                print(
                    f"> GraphDB returned 413. Reducing N-Quads chunk size to {chunk_lines} lines and retrying..."
                )

        print(f"> Uploaded a total of {lines_number} triples")

    graphly_sparql.Sparql.upload_nquads = _upload_nquads_with_adaptive_chunking
    graphly_sparql.Sparql._logre_nquads_upload_patched = True


_patch_graphly_parser()
_patch_graphly_timeout()
_patch_graphly_nquads_upload()


class SPARQLTechnology(str, Enum):
    """
    Enum representing supported SPARQL endpoint technologies.

    Attributes:
        FUSEKI: Apache Jena Fuseki endpoint.
        ALLEGROGRAPH: AllegroGraph endpoint.
        GRAPHDB: GraphDB endpoint.
        RDF4J: Eclipse RDF4J endpoint.
    """

    FUSEKI = "Fuseki"
    ALLEGROGRAPH = "Allegrograph"
    GRAPHDB = "GraphDB"
    RDF4J = "RDF4J"


def get_sparql(
    sparql_dict: dict[str, str],
) -> Allegrograph | Fuseki | GraphDB | RDF4J | None:
    """
    Returns the right Sparql instance given a rightfull dictionnary

    Args:
        sparql_dict (dict[str, str]): the dictionnary version of a Sparql endpoint

    Returns:
        Sparql: Instance of the right Sparql endpoint
    """

    if sparql_dict["technology"] == SPARQLTechnology.ALLEGROGRAPH:
        return Allegrograph(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )
    if sparql_dict["technology"] == SPARQLTechnology.FUSEKI:
        return Fuseki(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )
    if sparql_dict["technology"] == SPARQLTechnology.GRAPHDB:
        return GraphDB(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )
    if sparql_dict["technology"] == SPARQLTechnology.RDF4J:
        return RDF4J(
            sparql_dict["url"],
            sparql_dict["username"],
            sparql_dict["password"],
            sparql_dict["name"],
        )


def get_sparql_technology(sparql_technology_name: str) -> Sparql:
    """
    Returns the corresponding SPARQL technology class based on the given technology name.

    Args:
        sparql_technology_name (str): The name of the SPARQL technology (e.g., 'FUSEKI', 'ALLEGROGRAPH', 'GRAPHDB').

    Returns:
        Sparql: The class representing the specified SPARQL technology.

    Raises:
        ValueError: If the provided technology name does not match any known SPARQL technology.
    """
    technology = SPARQLTechnology(sparql_technology_name)

    if technology == SPARQLTechnology.FUSEKI:
        return Fuseki
    elif technology == SPARQLTechnology.ALLEGROGRAPH:
        return Allegrograph
    elif technology == SPARQLTechnology.GRAPHDB:
        return GraphDB
    elif technology == SPARQLTechnology.RDF4J:
        return RDF4J
