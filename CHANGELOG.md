# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
