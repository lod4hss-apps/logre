"""
This script regroups things that need to be done when upgrading Logre version.
For example when the configuration format changes between version, the script
handles the configuration transformation.
"""

from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from lib.config_migrations import migrate_config_if_needed
from lib.config_paths import get_config_path


def main() -> None:
    load_dotenv()
    config_path = get_config_path()
    migrate_config_if_needed(config_path)


############ MAIN ############

if __name__ == "__main__":
    main()
