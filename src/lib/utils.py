import re
import unicodedata
import uuid
import time
import toml
import streamlit as st

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
    prefixes = ["xsd", "rdf", "rdfs", "owl", "sh", "crm", "sdh", "sdh-shortcut", "sdh-shacl", "ontome", "geov", "base"]
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


def generate_uuid() -> str:
    "Generate a uuid base on the current time"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(time.time())))


def load_config(file_content) -> None:
    """From a file content, parse it as configuration and set it in session"""

    config = toml.loads(file_content)

    st.session_state['configuration'] = True
    if 'all_endpoints' in config:
        st.session_state['all_endpoints'] = config['all_endpoints']
    if 'all_queries' in config:
        st.session_state['all_queries'] = config['all_queries']