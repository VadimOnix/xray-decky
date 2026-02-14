# Contributing to Xray Decky Plugin

Thank you for your interest in contributing. This guide helps you set up a development environment from scratch: a PC (Mac/Linux) for editing and building, and a Steam Deck with Decky Loader for running the plugin.

## Table of contents

- [Prerequisites](#prerequisites)
- [1. Steam Deck: Install Decky Loader](#1-steam-deck-install-decky-loader)
- [2. Steam Deck: Enable SSH and set hostname](#2-steam-deck-enable-ssh-and-set-hostname)
- [3. PC: Clone repo and install dependencies](#3-pc-clone-repo-and-install-dependencies)
- [4. PC: Configure SSH to the Deck](#4-pc-configure-ssh-to-the-deck)
- [5. Steam Deck: One-time sudo setup for watch deploy](#5-steam-deck-one-time-sudo-setup-for-watch-deploy)
- [6. Deploy the plugin and run watch](#6-deploy-the-plugin-and-run-watch)
- [Optional: CEF remote debugging](#optional-cef-remote-debugging)
- [Optional: TUN mode development](#optional-tun-mode-development)
- [Code and PR guidelines](#code-and-pr-guidelines)

---

## Prerequisites

- **Steam Deck** (or SteamOS device) with internet
- **PC** (macOS or Linux) with Node.js 18+, pnpm 9, and SSH client
- Same LAN for PC and Deck (Wi‑Fi or Ethernet)

---

## 1. Steam Deck: Install Decky Loader

1. On the Deck, switch to **Desktop Mode** (Power menu → Desktop Mode).
2. Open a browser and go to [https://decky.xyz](https://decky.xyz) or the official Decky Loader install page.
3. Download the installer and run it (e.g. open the downloaded file in Dolphin).
4. Reboot if prompted. After boot, in **Gaming Mode** open the **Quick Access** menu (⋯); the Decky icon should appear.

---

## 2. Steam Deck: Enable SSH and set hostname

1. In **Desktop Mode**, open **Konsole**.
2. Set a password for the `deck` user (required for SSH and sudo):
   ```bash
   passwd
   ```
3. Enable and start SSH:
   ```bash
   sudo systemctl enable sshd
   sudo systemctl start sshd
   ```
4. (Optional) Set a stable hostname so you can use `ssh deck@steamdeck`:
   - **Settings → System → About → Device name** → set e.g. `steamdeck`
   - Or leave default; you will use the Deck’s IP in `~/.ssh/config` (see step 4).

5. Note the Deck’s IP address: **Settings → Internet** or in Konsole:
   ```bash
   ip addr
   ```
   (e.g. `192.168.1.100`)

---

## 3. PC: Clone repo and install dependencies

```bash
git clone https://github.com/SteamDeckHomebrew/xray-decky.git
cd xray-decky
pnpm install
pnpm run build
```

Optional: place the xray-core binary for local/testing (see [README](README.md#xray-core-binary-missing)):

- Download from [Xray-core releases](https://github.com/XTLS/Xray-core/releases)
- Put it in `backend/out/xray-core` and `chmod +x backend/out/xray-core`

---

## 4. PC: Configure SSH to the Deck

Create or edit `~/.ssh/config`:

```
Host steamdeck
  HostName 192.168.x.x
  User deck
  Port 22
```

Replace `192.168.x.x` with your Deck’s IP from step 2.

**Test and optionally use SSH keys (recommended for watch):**

```bash
ssh steamdeck "echo OK"
# If it asks for password, type the deck user password.

# Optional: passwordless login (run once, enter password when asked)
ssh-copy-id steamdeck
# After this, ssh and rsync won’t ask for password.
```

---

## 5. Steam Deck: One-time sudo setup for watch deploy

Watch mode deploys files via rsync and then restarts Decky. For that to work without typing a password each time, the `deck` user on the Deck must be allowed to run two commands as root without a password:

1. `chown -R deck:deck /home/deck/homebrew/plugins/xray-decky` — so the plugin directory stays owned by `deck` after Decky restarts.
2. `systemctl restart plugin_loader` — to reload the plugin after deploy.

From your **PC** (you will be prompted once for the deck user password):

```bash
scp scripts/setup-decky-restart.sh steamdeck:~/
ssh -t steamdeck "bash setup-decky-restart.sh"
```

**Verify from PC (no password should be asked):**

```bash
ssh steamdeck 'sudo -n /usr/bin/systemctl restart plugin_loader'
```

If that runs without “password is required”, watch mode will be able to restart Decky automatically after each deploy.

---

## 6. Deploy the plugin and run watch

**First-time deploy (build + copy to Deck):**

```bash
pnpm run deploy
```

This builds the frontend and syncs the plugin to `/home/deck/homebrew/plugins/xray-decky/` on the Deck. Open **Quick Access (⋯) → Decky** and you should see the Xray Decky plugin.

**Development with live UI updates:**

```bash
pnpm run watch
```

- Edit files in `src/` (and save). Rollup will rebuild and `deploy-sync.sh` will rsync to the Deck.
- If step 5 was done, Decky will restart automatically and the next time you open Quick Access you’ll see the new UI.
- If you didn’t run the sudo setup, after each deploy either close and reopen Quick Access, or on the Deck run: `sudo systemctl restart plugin_loader`.

More detail: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) (SSH, CEF debugging, manual deploy).

---

## Optional: CEF remote debugging

To debug the plugin UI in Chrome DevTools on your PC:

1. On the Deck: **Quick Access → Decky Loader → Settings** → enable **Developer → Allow Remote CEF Debugging**.
2. On the PC: open Chrome → `chrome://inspect` → **Configure** → add `DECK_IP:8081` (e.g. `192.168.1.100:8081`).
3. In the list, pick the Quick Access (or relevant) target and click **inspect**.

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#cef-remote-debugging-ui-debugging) for more.

---

## Optional: TUN mode development

If you work on TUN mode, the Deck user needs NOPASSWD for `ip tuntap add/del`. See [INSTALLATION.md](INSTALLATION.md) (TUN Mode Privilege Setup). This is separate from the deploy/restart sudo rules above.

---

## Code and PR guidelines

- The project uses **trunk-based development**; the only long-lived branch is `master`. Open pull requests against `master`.
- Follow the existing code style (TypeScript/React in `src/`, Python in `backend/`).
- For UI: use components and patterns from `@decky/ui` and `@decky/api` (see [Decky plugin template](https://github.com/SteamDeckHomebrew/decky-plugin-template)).
- Run `pnpm run build` before submitting; ensure the plugin loads and works on the Deck.
- Open an issue first for larger changes; for small fixes feel free to open a pull request with a short description.

---

## Quick reference

| Task              | Command |
|-------------------|--------|
| Build             | `pnpm run build` |
| Deploy (build + sync) | `pnpm run deploy` |
| Watch (build + sync on save, optional auto-restart) | `pnpm run watch` |
| Sync only (no build) | `./deploy-sync.sh` |
| One-time Deck sudo for watch | `scp scripts/setup-decky-restart.sh steamdeck:~/` then `ssh -t steamdeck "bash setup-decky-restart.sh"` |

For more: [README](README.md), [Development & debugging](docs/DEVELOPMENT.md), [Installation (TUN etc.)](INSTALLATION.md).
