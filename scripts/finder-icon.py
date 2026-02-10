from pathlib import Path
import plistlib

app_path = Path("dist/logre-launcher.app")
plist_path = app_path / "Contents" / "Info.plist"

icon_name = "icon.ico"  # no .icns extension

with plist_path.open("rb") as f:
    plist = plistlib.load(f)

plist["CFBundleIconFile"] = icon_name

with plist_path.open("wb") as f:
    plistlib.dump(plist, f)