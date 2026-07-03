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
  downloader now read the same `backend/src/xray_version.json`, so they can no
  longer drift. The pin includes an optional `sha256` that both the release
  workflow and the downloader verify when set.

### Fixed

- Kill switch now actually removes its firewall rules on deactivation. Rules
  are kept in a dedicated `XRAY_KILLSWITCH` iptables chain, so teardown is
  reliable, idempotent, and survives a plugin reload — previously the removal
  step was a no-op that could leave the system's traffic blocked. Loopback is
  always allowed while the switch is active.

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
