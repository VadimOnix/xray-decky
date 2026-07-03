# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Process supervisor** (roadmap Phase 0): a crashed xray-core is now
  detected the moment it exits (not on the next status poll). The kill
  switch engages immediately (fail closed) when enabled, then the process is
  auto-restarted with exponential backoff (1s/2s/4s); TUN routes are
  re-applied and the auto-engaged kill switch is lifted on success. Repeated
  crash loops give up cleanly after 3 unstable episodes instead of flapping
  (a run ≥60s resets the counter).
- **Network recovery script** (`scripts/recover.sh`, shipped in the plugin
  folder): one command restores connectivity if the plugin ever dies without
  cleaning up — removes the kill-switch chain (IPv4+IPv6), stale TUN
  routes/interface and legacy fwmark rules, stops leftover xray-core
  processes, and turns the desktop system proxy off.
- `_uninstall` hook: removing the plugin now unconditionally restores the
  network (system proxy, routes, xray-core, kill switch chain).

### Fixed

- Stopping an already-dead xray-core process no longer reports a failure
  (`ProcessLookupError` is treated as already stopped, and the temp config
  file is still cleaned up).

- **LAN web admin panel** (roadmap Phase 3, first cut): `https://<deck>:<port>/admin`
  served by the existing embedded HTTPS server. Steam-UI-styled dashboard
  (dark Steam palette, big touch/gamepad-friendly controls, SteamOS-style
  toggles, focus rings, reduced-motion support) with live status, server
  summary, connect/disconnect, TUN and kill-switch toggles, kill-switch
  unblock, and share-link import.
- Admin REST API (`/api/v1/status|connection|tun|killswitch|
  killswitch/deactivate|import`) guarded by a random per-install token
  (`X-Admin-Token` header or `?token=`); credentials (UUIDs/passwords) are
  never exposed by the API.
- QAM Options tab now shows an **Admin panel QR code** (URL with the pairing
  token embedded) via the new `get_admin_panel_url` backend method.

- Full xray protocol coverage for imports (roadmap Phase 1): in addition to
  VLESS, the plugin now imports and connects **VMess** (`vmess://` base64-JSON),
  **Trojan** (`trojan://`) and **Shadowsocks** (`ss://`, SIP002 + legacy base64 +
  2022 ciphers; SIP003 plugin links are rejected as unsupported by xray-core).
- Full transport coverage in the share-link parser and config generator:
  **WebSocket now honors `path`/`host`** (previously hardcoded to `/`), plus
  **gRPC** (`serviceName`, `authority`, `multiMode`), **HTTPUpgrade**, **XHTTP**
  (`path`, `host`, `mode`; `splithttp` alias normalized), **mKCP**
  (`headerType`, `seed`) and TCP with HTTP header obfuscation.
- Proper TLS parameters from share links: SNI, ALPN, uTLS `fingerprint`,
  `allowInsecure`; REALITY links now also honor `spx` (spiderX). VLESS
  Encryption strings (`encryption=mlkem768x25519plus…`) are passed through.
- Standard subscription payloads (base64 of newline-delimited share links) are
  now accepted alongside the legacy base64 JSON-array format.
- IPv6 server addresses in share links (`vless://uuid@[2001:db8::1]:443`).
- Sane config defaults in all modes: sniffing
  (`destOverride: ["http","tls","quic"]`) on all inbounds and
  `geoip:private → direct` bypass routing (previously TUN-only).

### Changed

- UUID validation now accepts any RFC-4122 UUID in canonical form (previously
  UUIDv4 only, which rejected links from panels that emit v1/v5/v7 UUIDs).
- Import UI texts (QAM help + web import page) now describe all supported
  share-link schemes instead of VLESS only.

- Auto-recover the xray-core binary: on startup the plugin checks for the
  xray-core binary and geo data files and re-downloads them into a persistent
  runtime directory if missing. This fixes connections breaking after a reboot
  on SteamOS, where the plugin's bundled `bin/` can be wiped by the immutable
  filesystem / atomic system updates.
- Project roadmap (`docs/ROADMAP.md`) covering full xray protocol coverage,
  multi-server subscriptions, a LAN web admin panel, and a multi-core path for
  Hysteria2/TUIC.
- Pinned xray-core version: the bundled release and the runtime self-heal
  downloader now read the same `backend/src/xray_version.json`
  (repo/asset/version/sha256), so they can no longer drift. The pin includes an
  optional `sha256` that both the release workflow and the downloader verify
  when set (and only for the pinned version, so explicit version overrides are
  not rejected). The `deploy.sh` / `package-and-deploy.sh` dev scripts ship the
  pin file too.

### Fixed

- Kill switch now actually removes its firewall rules on deactivation. Rules
  are kept in a dedicated `XRAY_KILLSWITCH` chain, so teardown is reliable,
  idempotent, and survives a plugin reload — previously the removal step was a
  no-op that could leave the system's traffic blocked. Additional fixes:
  - the rules match by `--uid-owner` instead of the `--pid-owner` match that
    modern kernels removed (the old rule could never apply on SteamOS), and no
    longer break when xray-core restarts with a new PID;
  - rules are applied on both IPv4 and IPv6, so traffic can't leak over IPv6;
  - loopback and the TUN interface are always allowed while active;
  - `deactivate()` reports failure instead of a false success if the chain is
    still hooked, and `_unload` tears down unconditionally so a live chain can't
    survive plugin removal;
  - iptables calls use `-w` to wait for the xtables lock;
  - kill-switch activation failures on an unexpected disconnect are now logged
    instead of silently failing open.
- `xray_version.json` that parses to a non-object no longer crashes the runtime
  self-heal downloader (falls back cleanly).

## [1.0.0] - 2026-02-14

### Added

- SECURITY.md for responsible vulnerability disclosure
- CODE_OF_CONDUCT.md (Contributor Covenant)
- .github/dependabot.yml for automated dependency updates
- .github/ISSUE_TEMPLATE for bug reports and feature requests
- Automated release workflow with xray-core binary bundling
- Desktop Mode install script and .desktop launcher
- ShellCheck CI workflow for scripts

### Changed

- Bump version to 1.0.0 for first stable release

## [0.3.0-alpha.1] - Initial release

### Added

- VLESS proxy connections with Reality protocol support
- Import configurations via URL (single node or subscription)
- Connection toggle and status display
- TUN mode for system-wide traffic routing
- Kill switch for blocking traffic on unexpected disconnect
- System proxy support (SOCKS/HTTP)
- QR code import from mobile devices
