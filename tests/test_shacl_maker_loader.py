import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from urllib.error import URLError


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lib.shacl_maker import load_shacl_maker_js  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload.encode("utf-8")


class TestShaclMakerLoader(unittest.TestCase):
    def test_reads_existing_file_without_downloading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            shacl_path = Path(temp_dir) / "shacl-maker.js"
            shacl_path.write_text("const loaded = true;\n", encoding="utf-8")

            with (
                patch("lib.shacl_maker.SHACL_MAKER_PATH", shacl_path),
                patch("lib.shacl_maker.urlopen") as mock_urlopen,
            ):
                js_code, error = load_shacl_maker_js()

            self.assertEqual("const loaded = true;", js_code)
            self.assertIsNone(error)
            mock_urlopen.assert_not_called()

    def test_downloads_and_trims_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            shacl_path = Path(temp_dir) / "nested" / "shacl-maker.js"
            remote_source = "line1\nline2\n// To not include\nline3\n"

            with (
                patch("lib.shacl_maker.SHACL_MAKER_PATH", shacl_path),
                patch(
                    "lib.shacl_maker.urlopen",
                    return_value=_FakeResponse(remote_source),
                ),
            ):
                js_code, error = load_shacl_maker_js()

            self.assertEqual("line1\nline2", js_code)
            self.assertIsNone(error)
            self.assertEqual("line1\nline2\n", shacl_path.read_text(encoding="utf-8"))

    def test_returns_error_when_download_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            shacl_path = Path(temp_dir) / "shacl-maker.js"

            with (
                patch("lib.shacl_maker.SHACL_MAKER_PATH", shacl_path),
                patch(
                    "lib.shacl_maker.urlopen",
                    side_effect=URLError("network down"),
                ),
            ):
                js_code, error = load_shacl_maker_js()

            self.assertIsNone(js_code)
            self.assertIn("network down", error)


if __name__ == "__main__":
    unittest.main()
