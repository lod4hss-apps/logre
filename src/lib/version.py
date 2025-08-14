# Local imports
from lib import state

# Path on disk of the file where version number is saved
VERSION_PATH = './VERSION'


def read_version() -> None:
    """Load version number from disk."""

    with open(VERSION_PATH, 'r', encoding='utf-8') as file:
        state.set_version(file.read())