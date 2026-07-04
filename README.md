# Xray Decky

Decky Loader plugin for Steam Deck: a full-featured xray-core proxy client
(VLESS/VMess/Trojan/Shadowsocks) with multi-server subscriptions, a Steam-styled
web admin panel, and Gaming-Mode TUN routing.

## Features

- **Broad protocol & transport coverage** — imports **VLESS** (REALITY /
  XTLS-Vision), **VMess**, **Trojan** and **Shadowsocks** (incl. 2022 ciphers)
  over RAW/TCP, WebSocket, gRPC, HTTPUpgrade, XHTTP and mKCP, with full TLS /
  REALITY / uTLS-fingerprint parameters.
- **Multi-server profiles & subscriptions** — store many servers; import a
  subscription URL (base64 or plain-text link lists) and refresh it in place.
  Manually-added servers are preserved across refreshes, and the provider's
  data quota / expiry (`Subscription-Userinfo`) is shown when available.
- **Latency testing** — TCPing all servers, with color-coded per-server results
  in both the QAM picker and the web panel.
- **Live traffic stats** — download / upload speed and session totals in the
  QAM, plus a real-time speed graph in the web panel.
- **Web Admin Panel** — Steam-styled management UI on your phone/PC (QR pairing
  from the QAM): live status + speed graph, server list, subscription info,
  import, TUN / kill-switch toggles, and a core update checker. Guarded by a
  random per-install token with failed-auth rate limiting.
- **Quick Access Menu** — connect toggle, server picker, live status/speed,
  TUN + kill-switch, and an admin-panel QR code.
- **English / Russian** — both the QAM and the web panel are localized
  (auto-detected from the Steam / browser locale).
- **Connection Toggle** — turn proxy on/off from Quick Access.
- **TUN Mode** — system-wide traffic routing, **recommended for Gaming Mode**.
- **Kill Switch** — block traffic when the proxy disconnects (optional).
- **Resilient** — a crashed xray-core is detected instantly and restarted with
  backoff; TUN routes are re-applied after sleep/resume; the pinned core
  self-heals if the immutable filesystem wipes the bundled binary.

**Network recovery:** if the Deck ever loses connectivity because the plugin
died uncleanly, run `sudo bash recover.sh` (shipped in the plugin folder,
also at [scripts/recover.sh](scripts/recover.sh)) from a Desktop Mode
terminal — it removes the kill-switch firewall chain, stale TUN routes and
the system proxy.

## Installation

**Prerequisites:** Steam Deck with [Decky Loader](https://wiki.deckbrew.xyz/) installed.

- **Plugin Store (recommended):** Decky Loader → Plugin Store → search "Xray Decky" → Install.
- **Desktop Mode (one-click):** Download [Install-Xray-Decky.desktop](https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop), set executable (Properties → Permissions), double-click to run. See [scripts/README.md](scripts/README.md).
- **Manual:** Download [latest release](https://github.com/VadimOnix/xray-decky/releases/latest) zip → Decky Loader → Settings → Developer → Install Plugin from URL → paste zip URL.

**TUN mode (recommended):** In Gaming Mode, Steam does not respect system SOCKS proxy settings — games and most system services ignore it. TUN mode creates a virtual network interface that routes **all** system traffic through the proxy, making it the only reliable way to proxy traffic in Gaming Mode. Enable TUN in the plugin settings; no extra setup is required.

Without TUN, the plugin falls back to SOCKS proxy mode, which works in Desktop Mode but may not cover games and system services in Gaming Mode.

**Usage, troubleshooting, more:** [GitHub Pages docs](https://vadimonix.github.io/xray-decky/).

## Development

### Prerequisites

- Node.js v16.14+
- pnpm v9 (mandatory)
- Python 3.x
- xray-core binary

### Setup

```bash
pnpm install
pnpm run build
# Backend: pip install -r backend/requirements.txt
# xray-core: place in backend/out/xray-core
```

### Project Structure

```
├── src/           # Frontend TypeScript/React
├── backend/       # Backend Python, xray-core
├── docs/          # GitHub Pages (index.html, styles, assets)
├── main.py        # Backend entry point
├── plugin.json
└── package.json
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and [docs/RELEASING.md](docs/RELEASING.md) for more.

## License

MIT — see LICENSE.md.

## Resources

- [Decky Loader](https://wiki.deckbrew.xyz/)
- [xray-core](https://xtls.github.io/)
- [Plugin spec](./specs/001-xray-vless-decky/spec.md)
