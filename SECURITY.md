# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the latest release (trunk-based development on `master`).

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. Email the maintainers or create a [private security advisory](https://github.com/VadimOnix/xray-decky/security/advisories/new) on GitHub.
3. Include a clear description of the vulnerability, steps to reproduce, and potential impact.
4. Allow reasonable time for a fix before any public disclosure.

We appreciate your effort to report vulnerabilities responsibly and will acknowledge your contribution once the issue is resolved.

## LAN Admin Server Security Posture

The plugin embeds an aiohttp HTTPS server (import page + `/admin` panel +
`/api/v1/*`) on a configurable port (default 8765, `py_modules/backend/src/import_server.py`,
`py_modules/backend/src/admin_api.py`).

- **Transport:** the server only starts once a self-signed TLS certificate is
  generated (OpenSSL, 365-day validity, `py_modules/backend/src/cert_utils.py:23-72`)
  and only serves HTTPS with a minimum protocol version of TLS 1.2
  (`main.py:255-257`). There is no plaintext HTTP fallback.
- **Token auth:** every `/api/v1/*` endpoint requires a random per-install
  token (`secrets.token_urlsafe(16)`, generated on first use and stored in
  plugin settings — `admin_api.py:104-113`), presented via the
  `X-Admin-Token` header or a `?token=` query parameter and checked with a
  constant-time comparison (`secrets.compare_digest`, `admin_api.py:202-209`).
  The token is shown to the user as a QR code from the Quick Access Menu.
- **Rate limiting:** failed-auth attempts are tracked per client IP; after 15
  failures within a 60-second window the client is locked out for 60 seconds
  (`admin_api.py:28-30, 54-84`). This is an in-memory speed bump against
  brute-forcing the token over the LAN, not a persistent ban list.
- **Credential redaction:** status and profile-list responses strip stored
  server configs down to a fixed allow-list of non-secret fields
  (`config_summary`, `admin_api.py:86-101, 145-149`); the one endpoint that
  returns full, un-redacted profiles (`GET /api/v1/export`) is gated by the
  same token and only invoked explicitly from the panel
  (`admin_api.py:400-409`).
- **Bind scope:** an "Allow LAN access" preference controls whether the
  server binds `0.0.0.0` (LAN, needed for QR pairing from a phone — the
  default) or `127.0.0.1` (Deck-only), toggleable from the QAM
  (`lan_access_enabled` / `admin_bind_host`, `admin_api.py:116-142`).
- **Intentionally open endpoint:** `POST /import` accepts a share link
  without a token, by design — it is the bootstrap pairing flow for a fresh
  install (`import_server.py:34-105`). The response embeds the admin
  URL+token on any successful import while the profile store is empty
  (fresh install or after removing all profiles) (`import_server.py:93-99`).

## Why the Plugin Requests `root`

`plugin.json` sets `"flags": ["root"]` because core functionality requires
privileged system operations that Decky Loader's sandboxed plugin user
cannot perform: creating and routing a TUN network interface for system-wide
proxying (`ip tuntap`/`ip link`/`ip route`, `py_modules/backend/src/tun_manager.py`),
installing/removing the `iptables`/`ip6tables` kill-switch chain that blocks
traffic if the proxy drops (`py_modules/backend/src/kill_switch.py`), and
writing the desktop session's system proxy settings
(`py_modules/backend/src/system_proxy.py`). `defaults/recover.sh` (shipped
with the plugin) reverses all three manually if the plugin ever exits
without cleaning up.

## Runtime Binary Download Policy

`xray-core` and `sing-box` are not required to be bundled in the store
package; if missing, the plugin downloads them on first use into the
Decky-managed runtime directory. Both are version-pinned and, when a hash is
configured, sha256-verified against upstream GitHub release assets before
use — see `py_modules/backend/src/xray_version.json` (`XTLS/Xray-core`) and
`py_modules/backend/src/singbox_version.json` (`SagerNet/sing-box`). Bumping
a pinned version is a deliberate, reviewed change to those JSON files, not
something the plugin decides at runtime.
