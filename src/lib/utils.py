from typing import List
import time
import unicodedata, re, io, zipfile


def normalize_text(text: str):
    """Normalize the given text (remove accents, caps, ...)."""
    
    if not text: 
        return text

    # Remove diacritics (accents) by filtering out non-ASCII characters
    to_return = "".join([c for c in text if not unicodedata.combining(c)])

    # Lower case
    to_return = to_return.lower()

    return to_return


def to_snake_case(text: str) -> str:
    """Format the given string into snake-case"""

    # Normalize text to decompose accented characters (e.g., é -> e)
    normalized_text = unicodedata.normalize("NFKD", text)

    # Replace underscores by dashes
    no_underscores = normalized_text.replace('_', '-')

    # Remove diacritics (accents) by filtering out non-ASCII characters
    no_accents_text = "".join([c for c in no_underscores if not unicodedata.combining(c)])

    # Remove punctuation
    cleaned_text = re.sub(r"[^\w\s-]", "", no_accents_text)

    # Replace spaces with dashs and convert to lowercase
    snake_case_text = re.sub(r"\s+", "-", cleaned_text.strip()).lower()

    return snake_case_text


def from_snake_case(text: str) -> str:
    """From a snake cased string, get a normal string."""
    return text.replace('_', ' ').title()


def build_zip_file(file_names: List[str], file_contents: List[str]) -> io.BytesIO:
    """Transform the result of the endpoint extract into one single zip file."""

    zip_buffer = io.BytesIO()

    # Create a zip archive in the buffer
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, content in zip(file_names, file_contents):
            zip_file.writestr(name, content)

    zip_buffer.seek(0)
    return zip_buffer


# GERER les wait(1ms)
def generate_id() -> str:
    "Generate a uuid base on the current time"

    # The seed (now's timestamp in ms)
    timestamp_ms = int(time.time() * 1000)

    # The used alphabet
    BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    # Generate the id
    result = ""
    while timestamp_ms:
        timestamp_ms, remainder = divmod(timestamp_ms, 62)
        result = BASE64_ALPHABET[remainder] + result

    # Make sure that the id generation took at least 1 ms, 
    # Doing so, we ensure that each generated ids are different
    if int(time.time() * 1000) - timestamp_ms < 1:
        time.sleep(0.001)

    return 'i' + result[::-1]