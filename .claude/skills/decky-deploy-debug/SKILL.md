---
name: decky-deploy-debug
description: Deploying and debugging this plugin on a real Steam Deck — pnpm deploy/watch/package scripts, .deckdeployrc config, restarting Decky Loader, CEF remote debugging, reading plugin logs, running the test suites. Use when the task involves getting changes onto a Deck, verifying behavior on device, diagnosing why a deployed change doesn't show up, or choosing which tests to run.
---

# Deploy & debug on Steam Deck

Full setup from scratch (Decky install, SSH, sudoers): `CONTRIBUTING.md`. Reference details: `docs/DEVELOPMENT.md`.

## Deploy commands

```bash
pnpm run deploy         # build + rsync over SSH into the Deck's plugins dir
pnpm run package        # build + zip + upload zip to the Deck (~/Downloads)
pnpm run package:local  # build + zip locally — use when no device is reachable
pnpm run watch          # rebuild on save; pair with deploy when ready
```

All three share `scripts/stage-plugin.sh` — the deployed file set always equals the packaged one. The device's `bin/` dir (self-healed xray-core) is preserved across deploys.

Config via env or gitignored `.deckdeployrc` (plain shell assignments in repo root):

| Var | Default | Meaning |
|---|---|---|
| `DECK_HOST` | `steamdeck` | ssh destination (`user@ip` or ssh-config alias) |
| `DECK_PLUGINS_DIR` | `/home/deck/homebrew/plugins` | Decky plugins dir |
| `DECK_RESTART` | `0` | `1` = restart `plugin_loader` after deploy (needs NOPASSWD sudo) |
| `DECK_UPLOAD_DIR` | `~/Downloads` | where `package` uploads the zip |

## Seeing changes on the Deck

- Frontend-only change: after deploy, close and reopen Quick Access (⋯) — plugin picks up the new bundle.
- Backend (Python) change: restart Decky — `DECK_RESTART=1 pnpm run deploy`, or on the Deck `sudo systemctl restart plugin_loader`.
- Passwordless restart + chown rules: run `scripts/setup-decky-restart.sh` once on the Deck (`scp` it over, `ssh -t steamdeck "bash setup-decky-restart.sh"`). Verify with `ssh steamdeck 'sudo -n /usr/bin/systemctl restart plugin_loader'`.
- rsync "Permission denied" after a Decky restart means the chown NOPASSWD rule is missing — re-run the setup script.

## Debugging

Frontend (CEF remote debugging):
1. On Deck: Quick Access → Decky → Settings → Developer → **Allow Remote CEF Debugging**.
2. PC Chrome: `chrome://inspect` → add network target `DECK_IP:8081`.
3. Inspect the **Quick Access** target for the plugin overlay (SharedJSContext for Steam client globals).

Backend: `decky.logger` output → `/home/deck/homebrew/logs/<plugin>/` on the device (`DECKY_PLUGIN_LOG_DIR`). Decky Loader's own log: `journalctl -u plugin_loader` over SSH.

Import page / web admin panel run over HTTPS with a self-signed cert — browser warnings on first open are expected.

## Tests & linters (run before claiming done)

```bash
pytest tests/                                   # backend; single: pytest tests/test_foo.py -k name
ruff check py_modules/ tests/ main.py conftest.py
pnpm test                                       # vitest: src/ pure logic + defaults/static admin panel (jsdom)
pnpm run lint && pnpm run lint:ts               # eslint+prettier, tsc
```

pytest needs no device — `conftest.py` puts `py_modules/` on `sys.path`. TUN mode, kill switch and system proxy can only be truly verified on a real Deck (see `steamos network restrictions.md` for SteamOS network constraints).
