# Third-Party Notices

Xray Decky does not bundle or redistribute any modified proxy-core source
code. At runtime it downloads official, unmodified release binaries of the
following third-party projects (see `py_modules/backend/src/xray_downloader.py`,
`py_modules/backend/src/singbox_downloader.py`, `py_modules/backend/src/xray_version.json`
and `py_modules/backend/src/singbox_version.json` for the exact pinned
versions and download sources) and runs them as separate subprocesses:

## Xray-core

- Project: [XTLS/Xray-core](https://github.com/XTLS/Xray-core)
- License: [Mozilla Public License 2.0](https://github.com/XTLS/Xray-core/blob/main/LICENSE) (MPL-2.0)
- Distribution: downloaded on demand from the project's official GitHub
  Releases; not modified or included in this repository's source tree.

## sing-box

- Project: [SagerNet/sing-box](https://github.com/SagerNet/sing-box)
- License: [GNU General Public License v3.0](https://github.com/SagerNet/sing-box/blob/main/LICENSE) (GPL-3.0-or-later)
- Distribution: downloaded on demand from the project's official GitHub
  Releases; not modified or included in this repository's source tree.

Xray Decky itself is licensed under the MIT License — see `LICENSE`.
