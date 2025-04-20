from schema import EntityType
import re
import unicodedata
import time
from .prefixes import is_prefix


def ensure_uri(supposed_uri: str) -> str | None:
    """
    Make sure that the given URI has the correct format.
    Knows a list of prefixes.
    eg: "https://.../i1234" -> "<https://.../i1234>"
    eg: "geov:i1234" -> "geov:i1234"
    """

    if not supposed_uri:
        return None

    # First check if the given URI has a known prefix
    if ":" in supposed_uri:
        supposed_prefix = supposed_uri[0:supposed_uri.index(':')]
        if is_prefix(supposed_prefix):
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

    # Replace spaces with dashs and convert to lowercase
    snake_case_text = re.sub(r"\s+", "_", cleaned_text.strip()).lower()

    return snake_case_text


def generate_id(entity_type: EntityType = EntityType.RESOURCE) -> str:
    "Generate a uuid base on the current time"

    # The seed (now's timestamp in ms)
    timestamp_ms = int(time.time() * 1000)

    # The used alphabet
    BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    # Should never occur
    # if timestamp_ms == 0: 
    #     return BASE64_ALPHABET[0]
    
    # Generate the id
    result = ""
    while timestamp_ms:
        timestamp_ms, remainder = divmod(timestamp_ms, 62)
        result = BASE64_ALPHABET[remainder] + result

    # Prepend a prefix so that it is clearer what it is
    # Also it makes sure that all entities will then start with a letter
    if entity_type == EntityType.RESOURCE: prefix = 'i'
    elif entity_type == EntityType.GRAPH: prefix = 'g'
    else: prefix = 'i'

    return prefix + result[::-1]


def normalize_text(text: str):
    """Normalize the given text (remove accents, caps, ...)."""

    # Remove diacritics (accents) by filtering out non-ASCII characters
    to_return = "".join([c for c in text if not unicodedata.combining(c)])

    # Lower case
    to_return = to_return.lower()

    return to_return


