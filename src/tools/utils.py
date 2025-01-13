def ensure_uri(supposed_uri: str) -> str:
    """
    Make sure that the given URI has the correct format.
    Knows a list of prefixes.
    eg: "https://.../i1234" -> "<https://.../i1234>"
    eg: "geov:i1234" -> "geov:i1234"
    """

    if not supposed_uri:
        return None

    # First check if the given URI has a prefix
    prefixes = ["rdf", "rdfs", "owl", "ontome", "geov", "infocean"]
    for prefix in prefixes:
        if supposed_uri.startswith(prefix + ":"):
            return supposed_uri

    # Then check if it is a value
    if supposed_uri.startswith("'") and supposed_uri.endswith("'"):
        return supposed_uri
    
    # If there is the "a" keyword, keep it
    if supposed_uri == "a": 
        return supposed_uri

    # If it is a variable
    if supposed_uri.startswith('?'):
        return supposed_uri

    # Finally, it then should be a real URI, adds the "<" and ">" if needed
    uri = supposed_uri.strip()
    if not uri.startswith("<"):
        uri = "<" + uri
    if not uri.endswith(">"):
        uri = uri + ">"
    return uri