from typing import List, Any


def prepare(uri_or_value: Any, prefixes_names: List[str] = []) -> str | None:
    """
    Prepare a URI, variable, or literal value for use in a SPARQL query.

    Args:
        uri_or_value (str | int | float): The value to prepare, which can be a full URI, prefixed name, variable, or literal.
        prefixes_names (List[str], optional): A list of allowed prefix names. If the value has a recognized prefix, it is returned as-is. Defaults to [].

    Returns:
        str | None: The SPARQL-ready representation of the input:
            - Full URIs are wrapped in angle brackets.
            - Recognized prefixed names are returned unchanged.
            - Variables (starting with '?') and numbers are returned as-is.
            - Literals are wrapped in single quotes.
            - None if the input is falsy.
    """
    # If None is given, make the call transparent
    if not uri_or_value: return None
    # Check if it is the "a" keyword: if yes, nothing to do 
    if uri_or_value == "a": return uri_or_value
    # If it is a numerical value: nothing to do
    if isinstance(uri_or_value, (int, float, complex)): return str(uri_or_value)
    # If at this point it is not a string, transform it into string
    if not isinstance(uri_or_value, str): uri_or_value = str(uri_or_value)
    # Check if it is a variable: if yes, nothing to do
    if uri_or_value.startswith('?'): return uri_or_value

    # Make it work it is a real URI
    # "://" are not added to also cover httpS in a single call
    # This is here to make sure "http" is not taken as a prefix
    if uri_or_value.startswith('http'):
        return f"<{uri_or_value}>"
    
    # Look for prefixes: if it has one, nothing to do
    prefix = uri_or_value[0:uri_or_value.find(':')]
    if prefix in prefixes_names:
        return uri_or_value
    
    # Finally, if it comes at this point, uri_or_value should be a value, then add quotes:
    return f"'{uri_or_value}'"