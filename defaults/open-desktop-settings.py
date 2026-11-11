#!/usr/bin/env python3
"""Open Xray Decky's authenticated loopback panel in the default browser."""

import argparse
import json
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode


def desktop_directory(home):
    try:
        path = Path(subprocess.check_output(["xdg-user-dir", "DESKTOP"], text=True).strip())
    except (FileNotFoundError, subprocess.CalledProcessError):
        return home / "Desktop"
    return path if path.is_absolute() and path != home else None


def write_shortcut(path, entry, mode, remove):
    if path.is_symlink():
        return
    if path.exists():
        if not path.is_file():
            return
        existing = path.read_text(encoding="utf-8")
        if "X-Xray-Decky-Managed=true" not in existing.splitlines():
            return
        if remove:
            path.unlink()
            return
        if existing == entry:
            path.chmod(mode)
            return
    elif remove:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
        file.write(entry)
    temporary = Path(file.name)
    try:
        temporary.chmod(mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def update_shortcut(remove=False):
    home = Path.home()
    filename = "xray-decky.desktop"
    applications = home / ".local/share/applications"
    desktop = desktop_directory(home)
    launcher = str(Path(__file__).resolve())
    exec_argument = launcher.replace("\\", "\\\\").replace('"', '\\"')
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Xray Decky\n"
        "Comment=Open Xray Decky settings\n"
        f'Exec=/usr/bin/python3 "{exec_argument}"\n'
        "Icon=network-vpn\n"
        "Categories=Network;\n"
        "Terminal=false\n"
        "X-Xray-Decky-Managed=true\n"
    )
    write_shortcut(applications / filename, entry, 0o644, remove)
    if desktop is not None:
        write_shortcut(desktop / filename, entry, 0o755, remove)


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
