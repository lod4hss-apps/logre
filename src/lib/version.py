from lib import state


VERSION_PATH = './VERSION'

def read_version() -> str:
    """Load version number from disk."""

    file = open(VERSION_PATH, 'r')
    version = file.read()
    file.close()

    state.set_version(version)
    