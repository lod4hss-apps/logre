from typing import List
import time, unicodedata, re, io, zipfile


def normalize_text(text: str, to_lower_case: bool = True) -> str:
    """
    Normalize the given text: binary chars, accents, spaces, lower case.
    
    Args:
        text (string): The "dirty text" (eg "  héLlo  worlD ").

    Returns:
        string: The cleaned text (eg "hello world").

    """    
    # To avoid errors if no text is sent
    if not text: return text

    # Remove binary chars
    allowed_categories = ('L', 'N', 'P', 'S', 'Z') # Letters, Numbers, Punctuation, Symbols, Spaces
    to_return = ''.join(c for c in text if unicodedata.category(c)[0] in allowed_categories)
    
    # Normalize text to decompose accented characters (e.g., é -> e + <accent>)
    to_return = unicodedata.normalize("NFKD", to_return)

    # Remove combining marks (accents)
    to_return = "".join([c for c in text if not unicodedata.combining(c)])

    # Handle extra spaces
    to_return = re.sub(r'\s+', ' ', to_return).strip()

    # Lower case
    if to_lower_case: to_return = to_return.lower()

    return to_return


def to_snake_case(text: str) -> str:
    """
    Format the given string into snake-case.
    
    Args:
        text (string): The normal text (eg "Hello world").

    Returns:
        string: the snake case version of given text (eg "hello-world").
    """
    # Clean the incoming text
    clean_text = normalize_text(text)

    # Replace underscores by dashes
    clean_text = clean_text.replace('_', '-')

    # Replace spaces with dashs
    snake_case_text = re.sub(r"\s+", "-", clean_text)

    return snake_case_text


def from_snake_case(text: str) -> str:
    """
    From a snake cased string, get a normal string.
    Put a cap letter for each word

    Args:
        text (string): Snake text (eg "hello-world").

    Returns:
        string: Normal text (eg "Hello World").
    
    """
    return text.replace('_', ' ').title()


def build_zip_file(file_names: List[str], file_contents: List[str]) -> io.BytesIO:
    """
    Build a zip file (file content) using given file names and file contents.

    Args:
        file_names (list of strings): Names files should have, in the correct order;
        file_content (list of strings): Content of files, in the correct order.

    Returns:
        bytes: the file content that need to be written on disk.
    """
    zip_buffer = io.BytesIO()

    # Create a zip archive in the buffer
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, content in zip(file_names, file_contents):
            zip_file.writestr(name, content)

    zip_buffer.seek(0)
    return zip_buffer


def generate_id() -> str:
    """
    Generate an id base on the current time (conversion of current millisecond timestamp into b62 char).
    Uses base 62 chars (b64 without "/" and "+").
    Always prepend an "i" in front, to match recommendation

    Returns:
        string: the generated id eg "i3shkRl2e"
    """
    # The used alphabet
    BASE62_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    # The seed (current timestamp in ms)
    timestamp_ms = int(time.time() * 1000)

    # Generate the id
    result = ""
    while timestamp_ms:
        timestamp_ms, remainder = divmod(timestamp_ms, 62)
        result = BASE62_ALPHABET[remainder] + result

    # Make sure that the id generation took at least 1 ms, 
    # Doing so, we ensure that each generated ids are different
    # Having in mind that this is true only computer wide.
    if int(time.time() * 1000) - timestamp_ms < 1:
        time.sleep(0.001)

    return 'i' + result[::-1]


def generate_uri(id: str = None) -> str:
    """
    Build a local URI. In case an id is given, build the URI with the given ID.

    Args: 
        id (string): Optional, the id to have in the URI.

    Returns:
        string: Generated URI.
    """

    if id: return f"base:i{id}"
    else: return f"base:i{generate_id()}"
    

def get_max_length_text(text: str, max_length: 50) -> str:
    """
    Truncates a text string to a maximum length, appending "..." if it exceeds that length.

    Args:
        text (str): The input text to process.
        max_length (int, optional): Maximum allowed length for the text. Defaults to 50.

    Returns:
        str: The original text if its length is within the limit, otherwise a truncated
            version ending with "...".
    """
    if len(text) < max_length: return text
    else: return text[0:max_length] + '...'