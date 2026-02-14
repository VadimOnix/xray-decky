# Scripts

## Desktop Mode Installation (Steam Deck)

Install the Xray Decky plugin with one click from Steam Deck Desktop Mode.

### Prerequisites

- Decky Loader installed on your Steam Deck
- Desktop Mode (Power menu → Desktop Mode)

### Option 1: Download and run .desktop file

1. Download [Install-Xray-Decky.desktop](Install-Xray-Decky.desktop) to your Steam Deck (e.g. to `~/Downloads`)
2. Right-click the file → Properties → Permissions → check "Is executable"
3. Double-click the file to run the installer
4. A terminal will open and the script will download and install the plugin
5. Switch to Gaming Mode and open Quick Access (⋯) to see Xray Decky

### Option 2: Run from Konsole

1. Switch to Desktop Mode
2. Open Konsole
3. Run:
   ```bash
   curl -sSL https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/install-xray-decky.sh | bash
   ```

### What the installer does

- Verifies Decky Loader is installed
- Downloads the latest release from GitHub
- Extracts the plugin to `~/homebrew/plugins/xray-decky/`
- Restarts the plugin loader (if possible)
- The plugin appears in Quick Access menu after switching to Gaming Mode

### Troubleshooting

- **"Decky Loader plugins directory not found"**: Install Decky Loader first from [decky.xyz](https://decky.xyz)
- **"Missing required tools"**: Run `sudo pacman -S curl unzip`
- **Permission denied**: Right-click the .desktop file → Properties → Permissions → enable "Is executable"
