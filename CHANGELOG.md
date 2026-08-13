# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `pnpm-lock.yaml` regenerated in the pnpm 9 format (`lockfileVersion: 9.0`).
  It had been left at the pnpm 8 format while CI and the documented toolchain
  both moved to pnpm 9, so every `pnpm install` rewrote 5000+ lines and no
  one could tell a real dependency change from format churn. Nothing in the
  dependency graph moved: the same 555 packages resolve to the same versions
  before and after, and `pnpm install --frozen-lockfile` now succeeds.
  `site/pnpm-lock.yaml` was already on 9.0.

## [2.3.0] - 2026-08-13

### Fixed

- **Every outbound HTTPS request from the backend failed instantly** — which
  showed up as "Failed to fetch subscription URL" for any `https://`
  subscription, in the QAM setup screen and the web admin panel alike, on a
  perfectly reachable server. The Decky sandbox hands plugin backends an
  environment aimed at Decky Loader's own PyInstaller bundle, and both halves
  of it break TLS clients: `LD_LIBRARY_PATH` puts the bundle's older
  `libssl.so.3` ahead of the system one, so system `curl` dies with
  `version 'OPENSSL_3.2.0' not found` before it opens a socket; and the
  bundle's CA variables (`SSL_CERT_FILE`/`SSL_CERT_DIR`) make Python's default
  SSL context verify against material that resolves to nothing. Server-side
  TLS needs no CA store, so the plugin's own HTTPS admin panel kept working
  and hid the problem — the only visible signature was that plain HTTP
  succeeded while every HTTPS request failed in well under a second. The new
  `net_env` module pins the system trust store for in-process aiohttp and
  hands system binaries a scrubbed environment plus an explicit `--cacert`;
  the two core downloaders' local `_clean_env()` helpers, which stripped only
  the `LD_*` pair, now delegate to it, and the update checker pins the trust
  store too. Subscription import, core downloads and update checks were all
  affected by this single cause.
- **Importing or refreshing a subscription failed while TUN mode was
  connected.** TUN mode installs `default dev xray0` at metric 100, which
  outranks the physical default route (DHCP gives it 600), so every socket
  the backend itself opened was pulled into the tunnel — xray's own outbound
  escapes only because it sets `sockopt.interface`. The fetch had three
  "fallback" attempts, but two of them (the plain aiohttp GET and the curl
  GET) took that same hijacked route and the third went through the tunnel
  on purpose, so all three failed together and instantly, and the plugin
  reported the subscription URL as unreachable when it was merely
  unreachable *through itself*. Subscription fetches now detect the hijacked
  default route and add an attempt bound to the physical interface
  (`curl --interface`, i.e. SO_BINDTODEVICE), tried right after the plain
  GET and before the tunnel paths — so a tunnel that cannot carry the
  request no longer blocks an import, while a subscription host that only
  the tunnel can reach still resolves via the proxy attempt. The extra
  attempt is skipped entirely when no TUN route is present.
- **Subscription bodies arriving in more than one chunk were truncated.**
  The response was read with a single `StreamReader.read(n)` call, which
  returns whatever is buffered at that moment rather than `n` bytes, so a
  large profile list could be cut mid-link. The body is now read to EOF and
  still stops one byte past the 2 MB cap.
- Subscription fetch diagnostics now record the HTTP status the server
  answered with, instead of only "returned no usable body".

## [2.3.0-alpha.1] - 2026-08-13

### Added

- **Your own SOCKS5 proxy as a server** (`socks://` / `socks5://`). Nothing
  in the plugin ever required a paid subscription — single share links have
  always worked — but every supported scheme was an encrypted VPN protocol,
  so a plain SOCKS5 proxy (a phone's hotspot proxy, an SSH tunnel, a box on
  the LAN) had no way in. Links parse with or without credentials, in the
  plain `user:pass@` form and the v2rayN `base64(user:pass)@` form, and
  export back out with the rest of the profile list. Note that SOCKS5 is not
  an encrypted transport: the profile is pinned to tcp/none regardless of
  what a stored profile claims, so a mislabelled entry cannot make the
  plugin attempt a TLS handshake the proxy will not answer — and the
  credentials travel in the clear, which the import help text now says.
  Closes [#69](https://github.com/VadimOnix/xray-decky/issues/69).

### Fixed

- **CI's backend lint job was broken by an upstream release.** The workflow
  installed ruff unpinned, so it picked up ruff 0.16.0 (released
  2026-07-23) — which widened its implicit default rule set and turned a
  green `ruff check` into ~550 findings on an unchanged tree. The rule set
  is now declared explicitly in `pyproject.toml` and the tool versions are
  pinned in `requirements-dev.txt`, which CI installs from. Widening the
  rule set is now a deliberate edit rather than something an upstream
  release can do on its own.
- **Placeholder substitution in both translation layers.** `t()` used
  `String.replace` with a string pattern, which rewrites only the first
  occurrence of a placeholder and expands `$&` / `$'` / `` $` `` in the
  substituted value. Interpolated values include server names, which come
  from whatever a subscription URL returns, so a name containing those
  sequences rendered corrupted text. Both the QAM (`src/utils/i18n.ts`) and
  the web panel (`defaults/static/admin.js`) now substitute verbatim.
- The admin panel's failed-auth rate limiter tracked one entry per source
  address with no upper bound, and only ever dropped an entry when that
  same client came back. It now caps the table and evicts the least
  informative entries first, never a live lockout.

### Changed

- **`pnpm test` runs a real test suite** instead of printing "No frontend
  tests configured" — CI had a green "Test Frontend" check that asserted
  nothing. 51 vitest tests now cover the QAM's pure logic and, more
  importantly, the web admin panel: `defaults/static/` ships unbundled, so
  nothing in the toolchain previously parsed or executed those 1300 lines.
  The suite boots the real `admin.html` + `admin.js` in jsdom to exercise
  the QR pairing flow, and pins the source-level contracts a compiler would
  otherwise enforce — element-id resolution, `data-i18n` key coverage,
  EN/RU dictionary parity, and the panel's no-`innerHTML` rule.
- `tsc` now typechecks the test suite too (`tsconfig.test.json`), kept
  separate from the build's tsconfig so tests can never reach the bundle.
- Documented the test and lint workflow in CONTRIBUTING.md — it was not
  written down anywhere before.
- Cleared the remaining ESLint warnings: hoisted `ConfiguredLayout`'s tab-id
  list out of the render body (its `useCallback`s closed over a fresh array
  each render) and removed four stale `eslint-disable` directives.

## [2.2.0] - 2026-07-22

### Changed

- **Repository layout is now buildable by the official Decky CLI** —
  groundwork for Plugin Store distribution. Backend Python moved to
  `py_modules/`, web assets ship as `static/` (from `defaults/static/`),
  `LICENSE.md` became `LICENSE`. No user-facing behavior changes; the
  self-made release zips ship the same on-device layout as the store build.
- Store metadata: real author, updated multi-protocol description and a
  store card image in `plugin.json`; `debug` flag removed.
- Runtime binary downloads are now sha256-verified: both the pinned
  xray-core and sing-box assets carry verified checksums.
- The release workflow stages through `scripts/stage-plugin.sh` (single
  source of truth) and a new CI job reproduces the exact plugin-store
  build (Decky CLI) on every PR.

## [2.1.1] - 2026-07-22

### Fixed

- **TUN mode no longer kills all connectivity** (v2 regression). xray
  routing rules are first-match, and since the traffic-stats release the
  TUN catch-all rule was inserted *before* the private-IP bypass, so LAN
  traffic — including DNS queries to the home router — was sent into the
  tunnel and died, which looked like "internet stops working the moment
  the connection is enabled" (the tunnel itself was healthy). The TUN
  rule now sits behind the `geoip:private` bypass again, restoring the
  original v1 rule order, and a test pins the ordering so it can't
  silently regress a second time.

## [2.1.0] - 2026-07-22

### Added

- **Hysteria2 / TUIC servers now connect** via the sing-box core. Previously
  such profiles imported fine but connecting failed with "requires the
  sing-box core, which is not available yet". The connect path now dispatches
  by the profile's core: xray-based protocols (VLESS/VMess/Trojan/
  Shadowsocks) keep running on xray-core, while hysteria2/tuic profiles
  start sing-box with the same localhost SOCKS/HTTP ports (10808/10809) and
  TUN interface, so system proxy, TUN routing, the kill switch and crash
  auto-restart all work identically whichever core is active.
- The sing-box binary is downloaded automatically into the persistent
  runtime directory the first time a hysteria2/tuic profile connects —
  xray-only users never download a second core.

### Known limitations

- Traffic statistics (speed/total in the QAM) come from xray's StatsService
  and show as unavailable while a sing-box connection is active.

## [2.0.1] - 2026-07-21

### Fixed

- **Subscription fetch now survives DPI filtering and an active tunnel**:
  importing or refreshing a subscription URL tries three paths in order —
  a plain aiohttp GET, the same GET through xray's local HTTP proxy
  (encrypted past DPI when the tunnel is up), and finally the system curl
  binary, whose TLS fingerprint passes DPI middleboxes that silently
  stall Python's ClientHello (observed on a real Deck: `curl` got the
  subscription in 0.4s while Python's TLS handshake timed out). Each
  failed attempt is logged by name (never the URL), and the import error
  now says what was tried and hints that a subscription server may be
  unreachable *through its own tunnel* while the VPN is connected.

### Added

- **The web import page opens the admin panel after the first import**:
  when `/import` saves the very first configuration on a fresh install,
  the browser is redirected to `/admin` with the pairing token — the same
  trust as the QR code shown in the QAM. Later imports never expose the
  token through the open `/import` endpoint.

### Changed

- The `/import` page hint and placeholder now mention subscription URLs
  (`https://…`) explicitly.

## [2.0.0] - 2026-07-21

First stable release of the v2 line — everything shipped in
[2.0.0-alpha.1] below (multi-protocol imports, subscriptions with
refresh, the LAN admin panel, multi-server profiles, TUN/kill-switch
hardening, sing-box substrate, localization) is now considered ready
for daily use, plus:

### Changed

- **Import texts now advertise subscription URLs**: the QAM share-link
  field description and the invalid-link error messages (QAM + backend)
  now say a subscription URL (`https://…`) can be pasted directly,
  matching what the importer has accepted since 2.0.0-alpha.1 — an
  `http(s)://` link is fetched and all its servers are stored. Verified
  end-to-end against a live subscription (base64 body with mixed
  vless/hysteria2 nodes).

## [2.0.0-alpha.1] - 2026-07-05

> **⚠️ Work in progress.** This alpha is being tested by the author on real
> hardware and is not ready for daily use — please don't install it yet.
> Grab it only if you want to help test and develop the project.

### Added

- **Release automation on master** (`.github/workflows/auto-release.yml`):
  merging a `package.json` version bump to `master` now tags that commit
  (`v<version>`) and dispatches the Release workflow automatically — the
  version bump is the single deliberate release act. Versions with a `-`
  (e.g. `2.0.0-alpha.1`) are published as pre-releases. Manually pushed
  `v*` tags keep working.
- **New CI checks**: a *Package Plugin (dry run)* job builds the real zip
  through the shared staging script on every PR and asserts the required
  files are inside (a broken release file set now fails CI, not the
  release); plugin/package metadata and the xray-core / sing-box pin files
  are validated (valid JSON, semver version, repo/asset/version fields);
  ShellCheck now also covers the root `deploy.sh` / `package-and-deploy.sh`;
  superseded CI runs on the same PR are cancelled.

### Changed

- **Deploy tooling has no hardcoded values anymore**: `deploy.sh`,
  `package-and-deploy.sh` and the new `scripts/package-local.sh` read the
  Deck host / plugins dir / upload dir from environment variables (or an
  optional gitignored `.deckdeployrc`), and take the plugin name, version
  and zip filename from `package.json`. All three now share one staging
  step (`scripts/stage-plugin.sh`), so the deployed file set can't drift
  from the packaged one; a deploy also preserves the device's `bin/`
  directory (the self-healed xray-core) instead of deleting it. The stale
  `deploy:simple` / `package:local` inline npm scripts (hardcoded host and
  an old zip name) were replaced.

### Security

- **Admin API auth rate limiting** (roadmap Phase 3): repeated failed token
  attempts from one client are now counted in a sliding window and, past a
  threshold, locked out for a cooldown (HTTP 429 with `Retry-After`) — a
  brute-force speed bump for the LAN-exposed panel. A valid token clears the
  client's failure history, so honest clients are never affected. The limiter
  is in-memory and per-install (cleared on plugin reload).

- **"Allow LAN access" toggle** (roadmap Phase 3): the QAM options tab can now
  restrict the embedded HTTPS server (admin panel + QR import page) to this
  Deck only. Toggling rebinds the live server immediately — `0.0.0.0` when
  allowed, `127.0.0.1` when restricted — and the QAM QR/URL switches to match
  (the QR is hidden in Deck-only mode since a phone can't reach it). The
  default remains LAN-on so the QR pairing flow keeps working for existing
  installs; new backend helpers `lan_access_enabled`/`admin_bind_host`, a
  `set_lan_access` RPC, and the server start refactored into a re-invokable
  `_start_import_server`.

### Added

- **Scheduled subscription auto-refresh** (roadmap Phase 2): a subscription can
  now carry an optional refresh interval (Off / 6h / 12h / daily / 2 days),
  set from a selector in the admin panel's subscription bar. A slow background
  tick re-fetches the subscription URL once the interval has elapsed since the
  last update. **Off by default** — zero change for anyone who doesn't opt in.
  The auto-refresh reuses the existing refresh flow, so it preserves the active
  server and manually-added servers, and it never touches or reconnects the live
  xray process. New pure `refresh_scheduler.is_refresh_due`, `ProfileStore`
  `set_refresh_interval`, `set_subscription_refresh_interval` RPC + token-guarded
  `POST /api/v1/subscription/interval`.

- **Profile export** (roadmap Phase 5): the admin panel gains an **Export
  servers** card that reveals a standard share link for every saved server
  (`vless`/`vmess`/`trojan`/`ss`/`hysteria2`/`tuic`) plus a base64 subscription
  blob, with copy-to-clipboard. Export is the exact inverse of the share-link
  parser (round-trip tested), so a server survives a parse → export → parse
  cycle unchanged. Because a share link *is* the credential, export is
  deliberately un-redacted but produced only on an explicit, token-guarded
  request (revealed behind a button, never in the passive list view). New
  backend `export_profiles` RPC + token-guarded `GET /api/v1/export`
  (`backend/src/exporter.py`).

- **sing-box JSON config import** (roadmap Phase 5 / Phase 2 stretch): pasting a
  full sing-box config — or a bare `outbounds` array — now imports every server
  outbound (`vless`, `vmess`, `trojan`, `shadowsocks`, `hysteria2`, `tuic`).
  Structural outbounds (`direct`, `block`, `selector`, `urltest`, …) are skipped.
  Each server is converted back into a standard share link and run through the
  existing share-link parser, so transports (WS/gRPC/HTTPUpgrade), TLS/REALITY and
  uTLS fingerprints are handled by one code path with no drift. Backend-only,
  no new runtime dependency (`backend/src/singbox_import.py`).

- **Named subscriptions** (roadmap Phase 2): the stored subscription now carries
  a user-facing label — it defaults to the subscription's URL host and can be
  renamed from the admin panel (a **Rename** button next to Refresh). The name
  shows in the subscription bar and survives a refresh; a new backend
  `rename_subscription` method and token-guarded `POST /api/v1/subscription/rename`.

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
