from typing import Any
import streamlit.web.cli as stcli
import sys
import os

def resource_path(filename) -> Any | str:
    return os.path.join(os.path.dirname(__file__), filename)

if __name__ == "__main__":
    script_path = resource_path("src/server.py")
    config_path = resource_path(".streamlit/config.toml")

    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"

    sys.argv = ["streamlit", "run", script_path, "--client.showSidebarNavigation=false", "--server.maxUploadSize=1500"]
    sys.exit(stcli.main())