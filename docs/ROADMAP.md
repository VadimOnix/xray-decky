# Xray Decky — Project Roadmap

**Status:** Proposal (July 2026)
**Current version:** 1.0.1

This document proposes the evolution of Xray Decky from a single-node VLESS+Reality
client into a full-featured proxy client for Steam Deck: complete xray-core protocol
coverage, multi-server subscriptions, a LAN web admin panel, and (eventually)
Hysteria2/TUIC support.

It is based on three research passes: an audit of the current codebase, the state of
the xray-core / proxy-client ecosystem (July 2026), and prior art among Decky Loader
plugins (ToMoon, DeckyClash, DeckyFileServer, tailscale-control).

---

## Where we are today

What actually works in 1.0.1:

- **VLESS + TCP + REALITY** (XTLS-Vision flow passes through). WebSocket transport is
  emitted but degenerate — `wsSettings.path`/`host` from the share link are ignored
  and hardcoded to `/` (`xray_manager.py`). Plain TLS produces no `tlsSettings` block
  at all. No gRPC / HTTPUpgrade / XHTTP / mKCP.
- **Single node only.** Subscription import takes the first node and discards the rest
  (`main.py`, "can be extended later"). The subscription parser expects a
  non-standard base64-of-JSON-array format instead of the conventional
  base64 newline-delimited link list.
- **TUN mode** via xray-core's native TUN inbound (requires ≥ v26.1.23) with
  `sockopt.interface` binding and a default route on `xray0`.
- **Embedded HTTPS server already exists** (aiohttp, self-signed cert, port 8765,
  binds 0.0.0.0) — currently only serves the QR/paste import page. This is the seed
  of the future admin panel.
- **QAM UI**: Setup / Configured layouts, connect toggle, TUN + Kill Switch toggles.
  No server list, no stats, no logs.

Known defects and tech debt (from the code audit):

| # | Issue | Where |
|---|-------|-------|
| 1 | **Kill switch never removes its iptables rules** — `_remove_rule()` is a no-op stub; deactivation resets Python state only, the kernel `OUTPUT -j DROP` rule can persist and block all traffic | `backend/src/kill_switch.py` |
| 2 | Contradictory TUN assumptions — `main.py` claims xray has no native TUN, `xray_manager.py` claims native TUN since v26.1.23; route setup is best-effort | `main.py` / `xray_manager.py` |
| 3 | No xray-core version pinning — release workflow and the runtime self-heal downloader independently fetch *latest*; bundled and re-downloaded versions can drift | `.github/workflows/release.yml`, `backend/src/xray_downloader.py` |
| 4 | ~~UUID validation requires UUIDv4 specifically; many panels emit non-v4 UUIDs~~ (fixed: any RFC-4122 UUID) | `backend/src/config_parser.py` |
| 5 | No process supervisor — a crashed xray is only noticed on the next 2s status poll; no auto-restart | `backend/src/xray_manager.py` |
| 6 | SOCKS/HTTP ports 10808/10809 hardcoded | throughout |

---

## Ecosystem context (July 2026)

Facts that shape the plan:

- **xray-core v26.3.27 added a native Hysteria 2 inbound & transport** (Salamander via
  the new "finalmask" obfuscation framework). However, it is server-side-leaning and
  immature as a *client*: open interop bugs (XTLS/Xray-core#5921, #5712), and v2rayN
  reports Hysteria2-over-xray as non-working (2dust/v2rayN#8933). **TUIC is still not
  supported by xray-core at all.**
- The mainstream way clients ship Hysteria2/TUIC remains **sing-box as a second core**
  (v2rayN bundles many cores and dispatches per protocol; Hiddify bundles both
  sing-box and xray; Throne/NekoBox/Karing are sing-box-based).
- Modern VLESS best practice: `VLESS + XTLS-Vision + REALITY` over RAW for throughput;
  **XHTTP + REALITY** (H1/H2/H3) as the new stealth transport; uTLS fingerprints with
  post-quantum X25519MLKEM768; the new native **VLESS Encryption**
  (`mlkem768x25519plus.*`, Xray-core PR #5067) for PQ forward secrecy. Mux is
  discouraged with Vision/REALITY. Enable sniffing (`destOverride`) and use
  fakedns + geosite/geoip routing in TUN mode.
- **Xray gRPC API** provides StatsService (traffic counters), HandlerService (runtime
  inbound/outbound changes), RoutingService, and Observatory (built-in latency
  probing feeding `leastPing` balancers). Stats require `policy` + `stats` blocks in
  the config.
- Decky precedent for the admin panel: **ToMoon** (Clash core, yacd dashboard on
  `:9090/ui`, opt-in `0.0.0.0` bind) and **DeckyClash** (mihomo, bundled
  metacubexd/yacd/zashboard, random per-install secret, `allow_remote_access`
  default-off, separate importer page on its own port). Their #1 documented failure
  mode: hijacking `/etc/resolv.conf` and dying without cleanup → Deck loses all
  connectivity → ship a recovery script and restore network in `_unload`.

---

## Phase 0 — Hardening (prerequisite for everything else)

*Goal: the existing feature set becomes trustworthy. No new features.*

- **Fix the kill switch.** _Done:_ rules now live in a dedicated `XRAY_KILLSWITCH`
  chain removed reliably on teardown; the removed-from-kernel `--pid-owner` match was
  replaced with `--uid-owner`; rules are applied on both IPv4 and IPv6; `deactivate()`
  reports failure (instead of a false success) if the chain is still hooked; `_unload`
  tears down unconditionally. Uses `-w` for the xtables lock. _Remaining:_ validate the
  permit set (loopback + TUN interface + xray uid) against a real Steam Deck in TUN mode,
  and add an on-device integration test; optionally migrate to an `nftables` named table.
- **Pin the xray-core version** _(done)_ in `backend/src/xray_version.json`, consumed by
  both the release workflow and `xray_downloader.py` (repo/asset/version/sha256).
  _Remaining:_ populate the `sha256` so downloads are integrity-verified; upgrade the
  pinned version deliberately, not implicitly.
- **Resolve the TUN contradiction**: verify native TUN inbound behavior against the
  pinned core, delete the stale comments/dead code paths (`create_tun_interface`
  no-ops), and make route setup failure a hard, user-visible error in TUN mode.
  _(done in code — stale comments fixed, route failure now hard-fails the connect;
  remaining: verify native TUN inbound against the pinned core on a real Deck)_
- **Process supervision**: `await process.wait()` in a background task → immediate
  crash detection, bounded auto-restart with backoff, kill-switch engagement on
  crash (not on next poll). _(done — `backend/src/supervisor.py`; crash loops give
  up after 3 unstable episodes, stable runs reset the counter)_
- **Relax UUID validation** to any RFC-4122 UUID. _(done — canonical dashed form
  of any UUID version is accepted)_
- **Network safety net**: a `recover.sh` shipped with the plugin + full cleanup in
  `_unload`/`_uninstall` (routes, iptables/nft rules, system proxy). Lesson learned
  from ToMoon. _(done — `scripts/recover.sh` ships in the plugin folder; `_uninstall`
  restores the network unconditionally)_
- **Suspend/resume + Wi-Fi roaming handling**: reconnect xray and re-apply routes
  after resume (Steam Deck suspends constantly; this is a top real-world failure
  source for proxy plugins). _(done — `handle_resume` repairs the TUN default route
  on wake; a core that died during suspend is restarted by the supervisor)_

**Exit criteria:** kill switch on/off leaves the system exactly as it was; a killed
`xray-core` recovers within seconds; version drift impossible.

## Phase 1 — Full xray protocol & transport coverage

*Goal: any mainstream xray share link imports and works.*

- **Complete the share-link parser and config generator** for VLESS: _(done)_
  - Transports: RAW/TCP, **WS (honor path/host/headers)**, **gRPC**, **HTTPUpgrade**,
    **XHTTP** (`mode`, `path`, `host`), mKCP. _(done, incl. `splithttp`/`raw`/`mkcp`
    alias normalization and IPv6 hosts)_
  - Security: proper `tlsSettings` (SNI, ALPN, `allowInsecure`, uTLS `fingerprint`),
    REALITY (already present, now with `spiderX`), **VLESS Encryption**
    (`encryption=mlkem768x25519plus…` passthrough). _(done)_
- **Add the other xray-native protocols**: **VMess** (`vmess://` base64-JSON),
  **Trojan** (`trojan://`), **Shadowsocks** (`ss://`, incl. 2022 ciphers). _(done;
  SIP003 plugin links are rejected as unsupported by xray-core)_ WireGuard outbound
  is optional stretch.
- **Sane defaults in the generated config**: sniffing
  (`destOverride: ["http","tls","quic"]`) and geoip private → direct now apply in
  all modes _(done)_. _Remaining:_ optional "bypass region" preset, **fakedns**
  for TUN mode.
- Make SOCKS/HTTP inbound ports configurable.
- Property-based tests for the parser (round-trip share-link ↔ config); unit
  coverage for all protocols/transports exists in `backend/tests/`.
- Standard base64 newline-delimited subscription payloads already parse (the
  multi-server storage/UI part remains Phase 2; today the first node is used).

**Exit criteria:** links exported from v2rayN / Throne / Hiddify / marzban-style
panels for VLESS/VMess/Trojan/SS import and connect without manual editing.

## Phase 2 — Multi-server & subscriptions

*Goal: from "one saved link" to a managed server list.*

- **Server list storage** (settings schema v2 with migration): multiple profiles,
  active-profile selection, per-profile protocol metadata. _(done —
  `backend/src/profile_store.py`; legacy single config migrates automatically,
  the `vlessConfig` mirror keeps the connection path unchanged)_
- **Standard subscription support**: base64 newline-delimited link lists (the de
  facto universal format), keep the current JSON-array format for backward compat.
  Named subscriptions, manual + scheduled refresh, "last updated" state. Clash YAML
  and sing-box JSON import are stretch goals (or offload via subconverter).
  _(mostly done — http(s) subscription URLs fetch and store all nodes (base64 or
  plain-text bodies), manual refresh preserves the active server, "last updated"
  shown in the admin panel; remaining: scheduled refresh, named subscriptions,
  Clash/sing-box import)_
- **Latency testing**: real-delay test through the proxy
  (`http://www.gstatic.com/generate_204`-style, configurable URL), concurrency
  limited; TCPing as the cheap fallback. Show results in the server list.
  _(TCPing done — concurrent, persisted, shown in the admin panel server list;
  real-delay through the proxy remaining)_
- **Traffic stats**: enable xray `stats` + `policy`, poll StatsService over the gRPC
  API (or `metrics` endpoint), display up/down counters and speed in the QAM.
  _(backend + admin panel done — StatsService enabled, polled via
  `xray api statsquery`, speed chips in the panel hero; QAM display remaining)_
- QAM UI: compact server picker (current server + status + latency), keeping the
  panel minimal per Decky UX guidance.
- Stretch: xray **Observatory + `leastPing` balancer** for automatic
  best-server selection ("URL-test group" equivalent).

**Exit criteria:** subscribe → list of N servers → latency-test all → pick/auto-pick
→ connect, entirely from the Deck.

## Phase 3 — Web admin panel

*Goal: full management UI in a browser (phone/PC on the same LAN), thin QAM.*

Rationale: the Quick Access Menu is a narrow, d-pad-driven sidebar with an on-screen
keyboard — wrong tool for config editing. Gaming Mode has no real browser. The proven
pattern (ToMoon, DeckyClash, DeckyFileServer) is: minimal QAM + LAN web UI + QR code
pointing at it.

- **Evolve the existing aiohttp import server** (HTTPS, self-signed cert — already
  built) into `admin/`:
  - **REST API** (`/api/v1/…`): _first cut done_ — status, connect/disconnect,
    TUN/kill-switch toggles + unblock, share-link import, all token-guarded and
    credential-redacting. _Remaining:_ profiles CRUD, subscriptions, latency tests.
  - **WebSocket** channel: live connection state, traffic speed, log tail.
  - **Static SPA**: _first cut done_ — no-build vanilla SPA
    (`backend/static/admin.{html,css,js}`) styled after the Steam UI design
    language (Steam dark palette, Play-style action button, SteamOS toggles,
    ≥44px touch targets, visible focus rings, `prefers-reduced-motion`):
    dashboard with live status, server summary, options, import. _Remaining:_
    server list with latency, subscription manager, speed graph, log viewer,
    diagnostics.
- **Security model** (copy DeckyClash's defaults):
  - Random per-install token, required for API access; shown in QAM as a QR
    code / pairing URL. _(done — token in `X-Admin-Token` header or `?token=`,
    constant-time compare, page strips it from the address bar)_
  - Bind `127.0.0.1` by default; **explicit "Allow LAN access" toggle** in QAM to
    bind `0.0.0.0`. _(remaining — server currently binds `0.0.0.0` like the
    import page, mitigated by the token)_
  - Keep HTTPS (already needed for phone clipboard access); rate-limit auth
    attempts; CSRF-safe (token header, not cookies). _(HTTPS + header token done;
    rate-limiting remaining)_
- QAM becomes: connect toggle, server picker, status/speed, TUN/kill-switch, and
  "Open admin panel" QR _(QR done)_. The old single-purpose import page folds
  into the panel.

**Exit criteria:** scan QR from phone → authenticated panel → manage everything
without Desktop Mode.

## Phase 4 — Hysteria2 / TUIC (multi-core architecture)

*Goal: protocols beyond xray-core, without destabilizing the xray path.*

Decision framework (as of July 2026):

| Option | Pros | Cons |
|--------|------|------|
| **A. xray-core native Hysteria2** | Zero new binaries; one lifecycle | Client-side immature (open bugs #5921/#5712; v2rayN reports non-working); TUIC never |
| **B. sing-box as second core** | Industry-standard path (v2rayN/Hiddify model); Hysteria2 **and** TUIC (+ Salamander/Gecko obfs); Clash-API for free | Second ~15–20 MB binary; second config generator + lifecycle |
| **C. standalone `hysteria` binary** | Reference implementation | Hysteria2-only; redundant vs B |

**Recommendation: prepare for B, re-evaluate A at execution time.**

- **First, refactor to a core-adapter interface** (`CoreAdapter`: generate config /
  start / stop / stats / test) with `XrayAdapter` as the only implementation. This
  is pure enabling work and is worth doing during Phase 2 regardless.
- Track xray's Hysteria2 client maturity each release; if the upstream bugs are
  closed by the time this phase starts, Option A makes Hysteria2 nearly free and
  sing-box can be deferred until someone actually needs TUIC.
- Otherwise add `SingBoxAdapter`: downloaded on demand (like the xray self-heal
  path, pinned + checksummed, not bundled in the plugin zip — keeps store package
  small), dispatched per-profile protocol (`hysteria2://`, `hy2://`, `tuic://`
  links). TUN stays with whichever core is active.

**Exit criteria:** a `hysteria2://` share link imports and connects; xray-only users
see zero change.

## Phase 5 — Polish & power features (grab-bag, prioritize by demand)

- Routing rules editor in the admin panel (direct/proxy/block by domain/geosite,
  per-app is not feasible with TUN alone — needs cgroup marking, research spike).
- Profile import via Clash YAML / sing-box JSON; export.
- Per-subscription user-info headers (traffic quota / expiry display).
- DNS hardening options (DoH upstream through the proxy, leak tests in diagnostics).
- Localization of QAM + admin panel (EN/RU first).
- Telemetry-free update checker for the plugin and cores.
- Automatic "connect on boot / on Wi-Fi X" rules.

---

## Suggested sequencing & effort

| Phase | Size (rough) | Depends on |
|-------|--------------|-----------|
| 0 Hardening | S–M | — |
| 1 Protocol coverage | M | 0 |
| 2 Multi-server & stats | M–L | 1 (parser), 0 (supervisor) |
| 3 Web admin panel | L | 2 (API surfaces the server list) |
| 4 Multi-core (Hy2/TUIC) | M (adapter) + M (sing-box) | 2 (adapter refactor) |
| 5 Polish | ongoing | 3 |

Phases 3 and 4 are independent of each other and can be swapped or parallelized;
the adapter refactor in Phase 4 is cheap insurance worth doing early.

Each phase should ship as its own spec under `specs/00X-…` following the existing
Spec-Kit workflow, with the phase's exit criteria as acceptance scenarios.

## Sources

- Xray-core releases & v26.3.27 changelog (Hysteria 2 inbound & transport, finalmask):
  https://github.com/XTLS/Xray-core/releases
- Hysteria2-over-xray client issues: XTLS/Xray-core#5921, XTLS/Xray-core#5712,
  2dust/v2rayN#8933
- VLESS Encryption (post-quantum): https://github.com/XTLS/Xray-core/pull/5067
- Xray gRPC API / stats: https://xtls.github.io/en/config/api.html,
  https://xtls.github.io/en/document/level-2/traffic_stats.html
- v2rayN supported cores: https://github.com/2dust/v2rayN/wiki/List-of-supported-cores
- Hysteria2: https://v2.hysteria.network/, https://github.com/apernet/hysteria
- sing-box Clash API: https://sing-box.sagernet.org/configuration/experimental/clash-api/
- ToMoon (Clash Decky plugin): https://github.com/YukiCoco/ToMoon
- DeckyClash (mihomo Decky plugin): https://github.com/chenx-dust/DeckyClash
- Decky plugin template & lifecycle: https://github.com/SteamDeckHomebrew/decky-plugin-template
