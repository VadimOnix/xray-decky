# Xray Decky Plugin

Decky Loader plugin for Steam Deck that enables VLESS proxy connections with Reality protocol support.

## Features

- **Import VLESS Configurations**: Import VLESS configurations via URL (single node or subscription)
- **Connection Toggle**: Turn proxy connection on/off with a simple toggle
- **TUN Mode**: Enable system-wide traffic routing through the proxy (requires elevated privileges)
- **Kill Switch**: Optional kill switch that blocks all traffic when proxy disconnects unexpectedly

## Installation

### Prerequisites

- Steam Deck with Decky Loader installed
- For TUN mode: Elevated privileges setup (see TUN Mode Setup below)

### Install from Plugin Store

1. Open Decky Loader settings
2. Navigate to Plugin Store
3. Search for "Xray Decky"
4. Click Install

### Manual Installation

1. Download the latest release zip file
2. In Decky Loader, go to Settings → Developer → Install Plugin from URL
3. Enter the URL to the zip file

### TUN Mode Setup (Optional)

TUN mode requires elevated privileges to create network interfaces. To enable TUN mode:

1. **Enable Developer Mode** (if not already enabled):
   - Go to Settings → System → Enable Developer Mode

2. **Set up sudo exemption** for Decky Loader:
   - Open Konsole (Desktop Mode) or SSH into your Steam Deck
   - Create sudoers configuration file:
     ```bash
     sudo nano /etc/sudoers.d/decky-tun
     ```
   - Add the following line (replace `/path/to/decky-loader` with actual path):
     ```
     deck ALL=(ALL) NOPASSWD: /usr/bin/ip tuntap add mode tun *
     deck ALL=(ALL) NOPASSWD: /usr/bin/ip tuntap del mode tun *
     ```
   - Save and exit (Ctrl+X, Y, Enter)
   - Set correct permissions:
     ```bash
     sudo chmod 0440 /etc/sudoers.d/decky-tun
     ```

3. **Alternative: Use CAP_NET_ADMIN capability** (if supported):
   - This requires setting capabilities on the Decky Loader binary
   - More complex setup, see Linux capabilities documentation

4. **Verify privileges**:
   - Open the plugin in Decky Loader
   - The plugin will automatically check for privileges
   - If insufficient, you'll see an error message with setup instructions

**Note**: TUN mode is optional. The plugin works without it using SOCKS proxy mode.

## Usage

### Import VLESS Configuration

1. Open the plugin in Decky Loader
2. Enter your VLESS URL in the import field
3. Click Import
4. The configuration will be validated and stored

**VLESS URL Format**: `vless://uuid@host:port?params#name`

### Toggle Connection

1. After importing a configuration, use the connection toggle
2. The status will show: disconnected, connecting, connected, or error
3. Toggle off to disconnect

### Enable TUN Mode

1. Complete installation steps for elevated privileges (see README)
2. Enable TUN mode toggle in the plugin
3. TUN mode will route all system traffic through the proxy

### Kill Switch

1. Enable kill switch in settings (off by default)
2. If the proxy disconnects unexpectedly, all traffic will be blocked
3. Reconnect or disable kill switch to restore traffic

## Development

### Prerequisites

- Node.js v16.14+
- pnpm v9 (mandatory)
- Python 3.x
- xray-core binary

### Setup

```bash
# Install dependencies
pnpm install

# Build frontend
pnpm run build

# Download xray-core binary to backend/out/xray-core
```

### Project Structure

```
xray-decky/
├── src/                    # Frontend TypeScript/React
├── backend/               # Backend Python
│   ├── src/              # Python source
│   └── out/              # xray-core binary
├── main.py               # Backend entry point
├── plugin.json           # Plugin metadata
└── package.json          # Package metadata
```

## Configuration

### Port Conflicts

The plugin avoids using Steam ports (UDP 27015-27030) for local listeners to prevent conflicts:
- SOCKS proxy uses port 10808 (non-TUN mode)
- TUN mode uses high ports (>32768) for local listeners
- All ports are configurable via xray-core configuration

### TUN Mode Privileges

TUN mode requires elevated privileges. See installation documentation for setup steps.

## Troubleshooting

### Connection Fails

- Verify VLESS configuration is valid
- Check network connectivity
- Review error messages in the plugin UI

### TUN Mode Not Working

- Verify privileges are set up correctly
- Check installation documentation
- Ensure plugin has required permissions

### Kill Switch Active

- Reconnect the proxy to deactivate automatically
- Or manually disable kill switch in the plugin UI
- Kill switch blocks all traffic when proxy disconnects unexpectedly (if enabled)

### xray-core Binary Missing

- Download xray-core binary from [Xray-core releases](https://github.com/XTLS/Xray-core/releases)
- Place in `backend/out/xray-core`
- Make executable: `chmod +x backend/out/xray-core`

## License

MIT License - see LICENSE.md for details

## Contributing

Contributions are welcome! Please open an issue or pull request.

## Resources

- [Decky Loader Documentation](https://wiki.deckbrew.xyz/)
- [xray-core Documentation](https://xtls.github.io/)
- [Plugin Specification](./specs/001-xray-vless-decky/spec.md)
