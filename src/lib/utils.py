import re
import unicodedata
import time


def ensure_uri(supposed_uri: str) -> str | None:
    """
    Make sure that the given URI has the correct format.
    Knows a list of prefixes.
    eg: "https://.../i1234" -> "<https://.../i1234>"
    eg: "geov:i1234" -> "geov:i1234"
    """

    if not supposed_uri:
        return None

    # First check if the given URI has a prefix
    prefixes = ["xsd", "rdf", "rdfs", "owl", "sh", "crm", "sdh", "sdh-shortcut", "sdh-shacl", "ontome", "geov", "base", "_"]
    for prefix in prefixes:
        if supposed_uri.startswith(prefix + ":"):
            return supposed_uri

    # Then check if it is a value
    if (supposed_uri.startswith("'") and supposed_uri.endswith("'")) or (supposed_uri.startswith('"') and supposed_uri.endswith('"')):
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


def readable_number(number: float) -> str:
    """Convert the given number into a more readable string"""

    for x in ["", "k", "M", "B"]:
        if number < 1000.0:
            return str(round(number, 1)) + x
        number /= 1000.0
    raise Exception("This Exception should never happen")


def to_snake_case(text: str) -> str:
    """Format the given string into snake-case"""

    # Normalize text to decompose accented characters (e.g., é -> e)
    normalized_text = unicodedata.normalize("NFKD", text)

    # Remove diacritics (accents) by filtering out non-ASCII characters
    no_accents_text = "".join([c for c in normalized_text if not unicodedata.combining(c)])

    # Remove punctuation
    cleaned_text = re.sub(r"[^\w\s]", "", no_accents_text)

    # Replace spaces with underscores and convert to lowercase
    snake_case_text = re.sub(r"\s+", "_", cleaned_text.strip()).lower()

    return snake_case_text


def generate_id() -> str:
    "Generate a uuid base on the current time"

    timestamp_ms = int(time.time() * 1000)
    BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    if timestamp_ms == 0: 
        return BASE64_ALPHABET[0]
    
    result = ""
    while timestamp_ms:
        timestamp_ms, remainder = divmod(timestamp_ms, 62)
        result = BASE64_ALPHABET[remainder] + result

    return result[::-1]

