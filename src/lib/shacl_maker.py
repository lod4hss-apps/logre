from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


SHACL_MAKER_SOURCE_URL = "https://raw.githubusercontent.com/gaetanmuck/shacl-maker/refs/heads/main/src/index.js"
SHACL_MAKER_TRUNCATION_MARKER = "// To not include"
SHACL_MAKER_PATH = Path(__file__).resolve().parent / "shacl-maker.js"


def _trim_source(source: str) -> str:
    lines: list[str] = []
    for line in source.splitlines():
        if SHACL_MAKER_TRUNCATION_MARKER in line:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def load_shacl_maker_js(timeout_seconds: float = 8.0) -> tuple[str | None, str | None]:
    if SHACL_MAKER_PATH.is_file():
        js_code = SHACL_MAKER_PATH.read_text(encoding="utf-8").strip()
        if js_code:
            return js_code, None

    try:
        with urlopen(SHACL_MAKER_SOURCE_URL, timeout=timeout_seconds) as response:
            source = response.read().decode("utf-8")
    except (URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
        return None, str(exc)

    js_code = _trim_source(source)
    if not js_code:
        return None, "downloaded source is empty"

    try:
        SHACL_MAKER_PATH.parent.mkdir(parents=True, exist_ok=True)
        SHACL_MAKER_PATH.write_text(js_code + "\n", encoding="utf-8")
    except OSError as exc:
        return None, str(exc)

    return js_code, None
