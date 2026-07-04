# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- **Admin API auth rate limiting** (roadmap Phase 3): repeated failed token
  attempts from one client are now counted in a sliding window and, past a
  threshold, locked out for a cooldown (HTTP 429 with `Retry-After`) — a
  brute-force speed bump for the LAN-exposed panel. A valid token clears the
  client's failure history, so honest clients are never affected. The limiter
  is in-memory and per-install (cleared on plugin reload).

### Added

- **Admin server list sorts by latency** (roadmap Phase 5 polish): after a
  "Ping all", the web panel orders servers fastest-first (measured servers,
  then untested, then offline). The sort is presentational and stable, so an
  unpinged list keeps its stored order.

- **QAM localization (English / Russian)** (roadmap Phase 5): the whole in-game
  Quick Access Menu is now localized via a small `src/utils/i18n.ts` helper —
  the connection tab (status, connection toggle, server picker), the options tab
  (TUN mode, kill switch, reset, admin-panel QR), the setup flow (share-link
  import, QR import) and every help popover. The language is auto-detected once
  from the Steam client locale (`ru*` → Russian, otherwise English), so `t()` is
  a pure function with no re-render wiring and no toggle in the QAM.

- **Core badge in the admin server list**: servers that need the second core
  (hysteria2 / tuic) now show a distinct `sing-box` chip next to their
  protocol chip, so it's clear at a glance which servers depend on the
  sing-box core (whose connect path is still being wired up).

- **Subscription quota & expiry** (roadmap Phase 5): the standard
  `Subscription-Userinfo` header (upload / download / total / expire) returned
  by most subscription panels is now parsed on import and refresh, stored with
  the subscription, and shown in the admin panel's subscription line as
  used / total data and an expiry date.

- **Update checker for the plugin and cores** (roadmap Phase 5): the admin
  panel's Updates card compares the plugin's own version (package.json) and
  the pinned xray-core / sing-box versions against their latest GitHub
  releases on demand, showing an "up to date" / "vX available" badge per
  component. Telemetry-free — an anonymous request to the public releases API,
  made only when you press Check; new `check_updates` backend method and
  token-guarded `GET /api/v1/updates`. Version comparison is numeric (so
  `v1.10` &gt; `v1.9`) and pre-release tags are handled.

- **Admin panel localization (English / Russian)** (roadmap Phase 5): the
  whole web panel is now translatable, with a top-bar language switch. The
  language is auto-detected from the browser (`ru*` → Russian, otherwise
  English) and remembered across visits; switching re-renders everything
  live, including status text, toasts, the server list and the import hints.
  Built as a dependency-free `data-i18n` layer over the existing vanilla JS.

- **Live traffic speed graph in the admin panel** (roadmap Phase 3): the hero
  card now draws a real-time dual-line sparkline (download in green, upload in
  blue) of the last two minutes of traffic, scaled to the in-view peak, with
  per-direction peak labels — a dependency-free Steam-styled canvas that fills
  as the existing stats poll streams in and clears on disconnect. The import
  hints now also list the `hysteria2://` / `tuic://` schemes that already
  parse and store.

- **sing-box core substrate** (roadmap Phase 4): a config generator
  (`singbox_manager.build_singbox_config`) that turns hysteria2/tuic
  profiles into sing-box JSON (proxy outbound + SOCKS/HTTP/TUN inbounds on
  the same ports as xray + private-IP bypass route), and an on-demand
  downloader (`singbox_downloader`) that fetches the pinned sing-box release
  (`singbox_version.json`, optional sha256) into the persistent runtime
  directory — not bundled in the plugin zip, to keep the store package
  small. Process-lifecycle wiring into the connect path is the next step.

- **Hysteria2 / TUIC share links parse and import** (roadmap Phase 4, first
  cut): `hysteria2://` (`hy2://`) and `tuic://` links are recognized and
  stored as profiles tagged with the core they need (`"core": "sing-box"`);
  the classic protocols are tagged `"core": "xray"`. Subscriptions with
  mixed protocols no longer silently drop the sing-box nodes. `core_for_protocol`
  centralizes the protocol → core mapping.
- Connecting to a sing-box profile now fails with a clear "requires the
  sing-box core, not available yet" message instead of feeding an
  unsupported config to xray-core. The bundled sing-box core (download +
  `SingBoxAdapter`) is the next Phase 4 step.

- **QAM server picker** (roadmap Phase 2): the Quick Access Menu now shows a
  compact server dropdown (with per-server latency) when more than one
  profile is stored, so you can switch servers without opening the web
  panel — a live connection reconnects through the new server. Secondary/
  options button on the picker pings all servers.
- **Live speed in the QAM**: the connection status card shows ▼ download /
  ▲ upload speed and session-total traffic while connected, polled from the
  StatsService.

- **Traffic statistics** (roadmap Phase 2): the generated config now enables
  the xray StatsService (localhost-only API inbound); totals are read with
  `xray api statsquery` and per-second speeds derived between samples
  (counter resets clamp to zero). New `get_traffic_stats` backend method and
  token-guarded `GET /api/v1/stats`.
- The admin panel hero card shows live ▼/▲ speed chips and session-total
  traffic while connected, in the established Steam style.

- **Subscription URLs** (roadmap Phase 2): importing an `http(s)://` link now
  fetches the subscription and stores all its servers — both the de facto
  standard body (base64 of newline-delimited share links) and plain-text
  link lists are accepted. The subscription (URL, server count, last
  updated) is remembered.
- **Subscription refresh**: `refresh_subscription` backend method and
  `POST /api/v1/subscription/refresh` re-fetch the stored URL and replace
  the server list; the active server survives the refresh when still
  present (matched by protocol/address/port). The admin panel shows a
  subscription bar ("N servers · updated …") with a Refresh button.
- Shared import flow (`backend/src/importer.py`) used by the plugin RPC,
  the web import page and the admin API, so behavior can't drift between
  entry points.

- **Multi-server profiles** (roadmap Phase 2, first cut): settings schema v2
  stores a list of server profiles with an active selection; an existing
  single config is migrated automatically and the legacy `vlessConfig` key
  is kept in sync so older flows keep working. Importing a subscription now
  stores **all** its nodes (previously only the first); importing a single
  link appends to the list.
- **Latency testing**: TCPing all profiles concurrently (bounded), results
  persisted per profile (`test_profiles_latency` / `POST /api/v1/profiles/ping`).
- **Server list in the web admin panel**: pick the active server (a live
  connection reconnects through it automatically), per-row latency badges
  (color-coded, `offline` for unreachable), protocol chips, remove buttons,
  and a "Ping all" action — in the same Steam UI style.
- New backend methods: `get_profiles`, `set_active_profile` (reconnects when
  connected), `remove_profile` (refuses to remove the active profile of a
  live connection), `test_profiles_latency`; admin REST endpoints
  `GET /api/v1/profiles`, `POST /api/v1/profiles/activate|remove|ping`
  (token-guarded, credentials redacted).

- **Suspend/resume handling** (roadmap Phase 0): when the Deck wakes from
  sleep, the frontend notifies the backend (`handle_resume` via
  `SteamClient.System.RegisterForOnResumeFromSuspend`), which re-adds the
  TUN default route if it vanished during suspend or Wi-Fi roaming while
  xray-core kept running. A core that died during suspend is already
  restarted by the process supervisor.

### Changed

- TUN route setup failure on connect is now a hard, user-visible error
  (xray-core is stopped and the connection reports the failure) instead of
  silently degrading to SOCKS-only, which left Gaming Mode traffic
  unproxied while the UI claimed otherwise.
- Resolved the stale "xray-core has no native TUN" comments: the pinned
  core (≥ v26.1.23) creates the TUN interface natively from its config.

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

- **Subscription import/refresh no longer wipes manually-added servers.**
  Previously importing (or refreshing) a subscription replaced the *entire*
  profile list, so a server you added by hand was silently dropped. It now
  replaces only the subscription-sourced profiles and keeps your manual ones;
  the active selection is preserved when it survives. New
  `ProfileStore.replace_subscription_profiles` / `clear_subscription`.

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
