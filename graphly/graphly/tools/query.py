from typing import Literal
import re


def get_sparql_type(query: str) -> Literal['SELECT', 'CONSTRUCT', 'INSERT', 'DELETE', 'CLEAR', 'OTHER']:
    """
    Determine the type of a SPARQL query.

    This function analyzes a SPARQL query string and returns its main operation type.
    It correctly handles leading comments and PREFIX declarations.

    Supported query types:
        - "SELECT"
        - "CONSTRUCT"
        - "INSERT"
        - "DELETE"
        - "CLEAR"
    If the query does not match any of these, it returns "OTHER".

    Args:
        query (str): The SPARQL query string to analyze.

    Returns:
        str: The type of the SPARQL query ("SELECT", "INSERT", "DELETE", "CLEAR", or "OTHER").
    """
    # Remove leading whitespace
    q = query.lstrip()
    
    # Remove comments
    q = '\n'.join([line for line in q.split('\n') if not line.strip().startswith('#')])
    
    # Skip PREFIX declarations
    q = re.sub(r'^(?:\s*PREFIX\s+\w*:\s*<[^>]*>\s*)*', '', q, flags=re.IGNORECASE)
    
    # Get the first keyword
    first_word_match = re.match(r'^\s*(\w+)', q, flags=re.IGNORECASE)
    if first_word_match:
        kw = first_word_match.group(1).upper()
        if kw in ["SELECT", "CONSTRUCT", "INSERT", "DELETE", "CLEAR"]:
            return kw
    
    return "OTHER"