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
