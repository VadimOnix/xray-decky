#!/usr/bin/env python3
"""Open Xray Decky's authenticated loopback panel in the default browser."""

import argparse
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlencode


def update_shortcut(remove=False):
    directory = Path.home() / ".local/share/applications"
    desktop_file = directory / "xray-decky.desktop"
    launcher = str(Path(__file__).resolve())
    exec_argument = launcher.replace("\\", "\\\\").replace('"', '\\"')
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Xray Decky\n"
        "Comment=Open Xray Decky settings\n"
        f'Exec=/usr/bin/python3 "{exec_argument}"\n'
        "Icon=network-vpn\n"
        "Categories=Network;Settings;\n"
        "Terminal=false\n"
        "X-Xray-Decky-Managed=true\n"
    )
    if desktop_file.exists():
        existing = desktop_file.read_text(encoding="utf-8")
        if "X-Xray-Decky-Managed=true\n" not in existing:
            return
        if remove:
            desktop_file.unlink()
            return
        if existing == entry:
            return
    elif remove:
        return
    directory.mkdir(parents=True, exist_ok=True)
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as file:
        file.write(entry)
    os.chmod(file.name, 0o644)
    os.replace(file.name, desktop_file)


def main():
    settings_file = Path.home() / "homebrew/settings/xray-decky/settings.json"
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        port = int(settings["importServer"]["desktopPort"])
        token = settings["adminPanel"]["token"]
        if not 1024 <= port <= 65535 or not isinstance(token, str) or not token:
            raise ValueError("Invalid desktop panel settings")
    except (OSError, ValueError, TypeError, KeyError):
        subprocess.run(
            ["kdialog", "--error", "Xray Decky settings are unavailable. Check that Decky Loader is running."],
            check=False,
        )
        return 1

    fragment = urlencode({"token": token})
    return subprocess.call(["xdg-open", f"http://127.0.0.1:{port}/admin#{fragment}"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if args.install or args.uninstall:
        update_shortcut(remove=args.uninstall)
    else:
        raise SystemExit(main())
