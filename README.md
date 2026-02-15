# Xray Decky

Decky Loader plugin for Steam Deck that enables VLESS proxy connections with Reality protocol support.

## Features

- **Import VLESS Configurations** — via URL (single node or subscription)
- **Connection Toggle** — turn proxy on/off from Quick Access
- **TUN Mode** — system-wide traffic routing, **recommended for Gaming Mode**
- **Kill Switch** — block traffic when proxy disconnects (optional)

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
