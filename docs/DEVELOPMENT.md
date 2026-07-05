# Development: Watch Mode & Debugging

Setting up the environment from scratch (Decky on Deck, SSH, one-time sudo for watch): see [CONTRIBUTING.md](../CONTRIBUTING.md). Below are details on watch, SSH, and debugging.

**Creating a release?** See [RELEASING.md](RELEASING.md).

## Watch mode (continuous UI delivery)

For UI development, rebuild the frontend on each save and sync to the Deck when ready:

```bash
pnpm run watch     # rebuilds src/ on every save
pnpm run deploy    # build + sync to the Deck over SSH (set DECK_RESTART=1 to restart Decky too)
```

**How to see changes on the Deck:** after deploy, close Quick Access (⋯) and open it again — the plugin will pick up the new bundle. If passwordless sudo for `systemctl restart plugin_loader` is set up on the Deck, `DECK_RESTART=1 pnpm run deploy` restarts Decky automatically (see the Decky restart section below).

### Manual deploy

- Full build + deploy: `pnpm run deploy` (or `./deploy.sh`)
- Build + zip + upload the zip to the Deck: `pnpm run package`
- Build + zip locally (no device): `pnpm run package:local`

All three share the same staging step (`scripts/stage-plugin.sh`), so the
file set on the device always matches the packaged one.

### Deploy configuration

Nothing is hardcoded — the deploy scripts read environment variables, with
an optional `.deckdeployrc` file in the repo root (gitignored, plain shell
assignments) for per-developer defaults:

| Variable | Default | Meaning |
|---|---|---|
| `DECK_HOST` | `steamdeck` | ssh destination (host alias or `user@ip`) |
| `DECK_PLUGINS_DIR` | `/home/deck/homebrew/plugins` | Decky plugins dir on the device |
| `DECK_RESTART` | `0` | `1` = restart `plugin_loader` after deploy (needs sudo on the device) |
| `DECK_UPLOAD_DIR` | `~/Downloads` | where `pnpm run package` uploads the zip |

Example `.deckdeployrc`:

```bash
DECK_HOST=deck@192.168.1.50
DECK_RESTART=1
```

The plugin name and version come from `package.json`; the device's `bin/`
directory (the self-healed xray-core) is preserved across deploys.

---

## SSH connection to Steam Deck

Deploy goes over SSH to `DECK_HOST` (default `steamdeck`) into
`DECK_PLUGINS_DIR/<plugin name>` (default `/home/deck/homebrew/plugins/xray-decky`).

### 1. Check connection

```bash
ssh steamdeck "echo OK"
```

If it prompts for a password — enter it once or set up keys (see below).

### 2. Host configuration (if needed)

Add to `~/.ssh/config`:

```
Host steamdeck
  HostName 192.168.x.x
  User deck
  Port 22
```

Replace with your Deck’s actual IP (on Deck: **Settings → Internet → IP Address** or in Konsole: `ip addr`).

### 3. Password authentication

The `deck` user password is set during initial SteamOS setup. For automatic deploy without typing a password, set up SSH keys.

### 4. SSH keys (recommended for watch mode)

On Mac/Linux:

```bash
# Create key (if you don't have one yet)
ssh-keygen -t ed25519 -f ~/.ssh/id_deck -N ""

# Copy key to Deck (enter deck user password once)
ssh-copy-id -i ~/.ssh/id_deck deck@steamdeck
```

In `~/.ssh/config` for host `steamdeck` add:

```
IdentityFile ~/.ssh/id_deck
```

After that, `ssh steamdeck` and `./deploy-sync.sh` should not ask for a password.

### 5. Root session

If you need access as root (e.g. to restart services), on the Deck in Konsole:

```bash
sudo passwd root
# set password (e.g. 0000)
```

Connect: `ssh root@steamdeck` (or use `Host steamdeck-root` with `User root` in config).

---

## CEF Remote Debugging (UI debugging)

To debug the plugin frontend in Chrome DevTools on your PC:

1. **On Steam Deck**  
   - Go to **Quick Access (⋯) → Decky Loader → Settings (gear icon)**.  
   - Enable **Developer** → **Allow Remote CEF Debugging**.

2. **Get Deck IP**  
   - On Deck: **Settings → Internet** or in Konsole: `ip addr` (e.g. `192.168.30.209`).

3. **On PC (Chrome/Chromium)**  
   - Open `chrome://inspect`.  
   - **Configure** in the "Discover network targets" block → add `DECK_IP:8081` (e.g. `192.168.30.209:8081`).  
   - Connect Deck and PC to the same network.

4. **Inspect**  
   - The device will appear in the list with tabs (Quick Access, SharedJSContext, etc.).  
   - Select the one you need (e.g. Quick Access for the plugin overlay) and click **inspect** — DevTools will open.

After changes in watch mode, reload the plugin on the Deck (or reopen Quick Access) and refresh the page in DevTools if needed.

---

## Restarting Decky Loader

After updating the backend (Python) or after deploying the frontend in watch mode, you may need to restart the plugin loader to see changes. Simple approach: **close Quick Access (⋯) and open it again**.

On the Deck in Konsole or over SSH (manual):

```bash
sudo systemctl restart plugin_loader
```

For watch mode to automatically restart Decky after each deploy (and restore plugin directory ownership after restart), run the setup script once on the Deck. It creates `/etc/sudoers.d/zzz-decky-restart` with two NOPASSWD rules for user `deck`:

1. **chown** — before each rsync, `chown -R deck:deck .../xray-decky` is run so the plugin directory is owned by `deck` again after plugin_loader restarts.
2. **systemctl restart plugin_loader** — after each deploy Decky restarts, and the next time you open Quick Access the new bundle is loaded.

**Run from PC (use `-t` so sudo prompts for password on the Deck):**

```bash
scp scripts/setup-decky-restart.sh steamdeck:~/
ssh -t steamdeck "bash setup-decky-restart.sh"
```

Enter the `deck` user password when prompted. After that, from the PC rsync (after chown) and Decky restart will work without a password.

**Verify:** from PC run `ssh steamdeck 'sudo -n /usr/bin/systemctl restart plugin_loader'`. If no password is asked — auto-restart in watch will work.

**If password is still asked:** on the Deck run `sudo -l -U deck`. You should see two NOPASSWD lines: for chown and for systemctl. Rules are written to `zzz-decky-restart` (the `zzz-` prefix ensures the file is read last and is not overridden by a general `(ALL) ALL` rule). Re-run the setup script and verify again from the PC.

**If after Decky restart rsync reports "Permission denied":** ensure the setup script was run and it includes the chown rule. Before each rsync, `deploy-sync.sh` runs `sudo chown -R deck:deck .../xray-decky`; without NOPASSWD for this command you will be prompted for a password or the write will fail.

In VS Code/Cursor you can use the **restart-decky** task (if it uses the same host).
