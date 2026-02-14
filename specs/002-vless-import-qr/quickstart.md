# Quickstart: VLESS Import via QR and Paste Form

**Feature**: 002-vless-import-qr  
**Date**: 2026-01-30

## Goal

Implement the flow: plugin shows QR first → user scans → opens import page in browser → Paste → Save → link appears in plugin UI. Backend runs an **HTTPS** server (TLS, self-signed cert) for the import page so Paste works from any device; each Save overwrites the stored VLESS config.

## Prerequisites

- Repo on branch `002-vless-import-qr`
- Spec read: `specs/002-vless-import-qr/spec.md`
- Plan and contracts: `plan.md`, `contracts/import-http-api.md`, `data-model.md`, `research.md`

## Implementation order

1. **Backend: Import HTTPS server**

   - **TLS certificate**: On first run or at startup, if cert/key missing under `DECKY_PLUGIN_RUNTIME_DIR`, generate self-signed cert via **OpenSSL subprocess only** (system `/usr/bin/openssl` on Linux; subprocess env without `LD_LIBRARY_PATH`/`LD_PRELOAD` so Decky sandbox libs are not used). Save `cert.pem`, `key.pem`. Create runtime dir if missing. On generation/load failure: log error, do not start import server. No `cryptography` dependency.
   - **SSL context**: `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)`, load cert and key, set minimum TLS 1.2.
   - Add `backend/src/import_server.py`: aiohttp app with GET `/import`, GET `/import/static/*`, POST `/import`. Start server in `main.py` `Plugin._main()` with `web.TCPSite(runner, "0.0.0.0", port, ssl_context=ssl_context)`; stop in `_unload()`.
   - Add `backend/static/import.html` and `backend/static/import.css` (Steam-like dark theme). Form: input, Paste button, Save button; POST to `/import`.
   - Add backend method `get_import_server_url()`: return `{ baseUrl: "https://{localIP}:{port}", path: "/import" }` (protocol **https**, local IP from system, port from settings).
   - Backend Python deps: **aiohttp only** in `backend/requirements.txt`; cert generation uses system OpenSSL (no cryptography).

2. **Backend: Settings**

   - Ensure `importServer.port` (default 8765) is read when starting the server; optional: add to existing settings read path.

3. **Frontend: QR block first**

   - Add component `src/components/QRImportBlock.tsx`: call `get_import_server_url()`, render QR code (use a small QR lib, e.g. `qrcode.react` or lightweight alternative) with `baseUrl + path`, show URL text. Place it first in `src/index.tsx` (above ConfigImport).

4. **Frontend: Link input**

   - ConfigImport already loads `get_vless_config()` on mount and shows `config.sourceUrl` in the input. Ensure it stays that way; no change required unless you add refetch on focus. Multiple imports overwrite config; UI shows latest after mount.

5. **Dependencies**
   - Backend: `aiohttp` only (plugin runtime may not install backend/requirements.txt; cert via system OpenSSL, no extra Python deps).
   - Frontend: add QR library (e.g. `qrcode.react` + `qrcode` or similar) for QR generation.

## Key files

| File                               | Purpose                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------ |
| `backend/src/cert_utils.py`        | Self-signed cert generation via OpenSSL subprocess (system /usr/bin/openssl, clean env)   |
| `backend/src/import_server.py`     | aiohttp app, routes, POST handler (reuse validate_vless_url, build_vless_config, settings) |
| `backend/static/import.html`       | Import page markup and form                                                                |
| `backend/static/import.css`        | Steam-consistent dark theme                                                                |
| `main.py`                          | Start/stop HTTPS import server in \_main/\_unload; cert gen/load; register get_import_server_url (https baseUrl) |
| `src/components/QRImportBlock.tsx` | QR code + URL, first in layout                                                             |
| `src/index.tsx`                    | Render QRImportBlock first, then ConfigImport, etc.                                        |

## First visit: certificate warning

When opening the import page from a phone or PC for the **first time**, the browser will show a certificate warning (self-signed). The user MUST accept once per device:

- **Chrome/Edge**: "Advanced" → "Proceed to {host} (unsafe)".
- **Safari**: "Show Details" → "visit this website" → "Visit Website".
- **Firefox**: "Advanced" → "Accept the Risk and Continue".

After acceptance, the page is in a secure context and the **Paste** button works (clipboard is readable). Document this in quickstart and optionally show a short hint in the plugin UI or on the import page.

## Testing

- On Steam Deck (or same LAN): open plugin → see QR first → scan with phone → **accept certificate once** → import page loads → Paste (clipboard) → Save → return to plugin → link input shows the saved link. Optionally verify full flow completes in under 30 seconds (SC-001).
- Save again with another link → link input updates to the new one.
- Invalid link on Save → 400 and error message on page; no overwrite of previous config.

## Contracts

- HTTP API: `specs/002-vless-import-qr/contracts/import-http-api.md`
- Plugin methods: existing `get_vless_config`, `import_vless_config`; new `get_import_server_url`.

---

## Troubleshooting: ERR_CONNECTION_REFUSED

If the QR shows the correct URL (e.g. `https://192.168.30.209:8765/import`) but the browser on phone/PC shows "Unable to connect" / ERR_CONNECTION_REFUSED, check on **Steam Deck** (Desktop Mode → Konsole).

### 1. Server is listening on the port

The plugin must be running (Game Mode: open the Xray Decky plugin at least once). On the Deck run:

```bash
# Is any process listening on port 8765 (or your importServer.port)?
ss -tlnp | grep 8765
# or
ss -tlnp
```

Expected: a line like `LISTEN 0 128 0.0.0.0:8765 0.0.0.0:*` (or your port). If there is no output — the import server is not running (plugin not loaded, `backend/static` missing on deploy, or port in use).

**If the output only shows `127.0.0.1:8765` and `[::1]:8765`, not `0.0.0.0:8765`** — that is not our plugin. Our server binds to `0.0.0.0` to accept connections from the LAN. So port 8765 is taken by another process (listening only on localhost), and our server failed to bind at startup (Address already in use). Or an old build is running. Steps:

1. Find which process holds the port:
   ```bash
   lsof -i :8765
   # or (PID in the last column)
   ss -tlnp | grep 8765
   ```
2. If it is not our plugin (not python/Decky plugin) — free the port or change the plugin port in settings: in Decky Store/plugin settings set `importServer.port` = e.g. **8766**, restart the plugin (leave plugin settings and open again).
3. If the process is ours (python) but listens on 127.0.0.1 — reinstall/redeploy the latest build where `main.py` uses `TCPSite(runner, "0.0.0.0", port)`.

Also: if `curl http://127.0.0.1:8765/import` returns **404** instead of 200 — the responder on that port is not our import page (our GET `/import` serves HTML). So 8765 is definitely another service; our plugin is not listening on 8765 — see steps above (change port or free 8765).

### 2. Access from the Deck itself (localhost)

```bash
# Replace 8765 with your port if needed
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/import
```

Expected: `200`. If empty or error — server does not respond even locally.

### 3. Access via LAN IP from Deck

```bash
# Replace 192.168.30.209 and 8765 with your IP and port
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.30.209:8765/import
```

Expected: `200`. If localhost works but LAN IP does not, routing/interface may be the cause (rare when binding to 0.0.0.0).

### 4. Firewall on Steam Deck

SteamOS (Arch-based) may use **iptables** or **nftables**. Incoming connections to the import port may be blocked by default.

Check:

```bash
# Are there rules restricting incoming traffic?
sudo iptables -L INPUT -n -v 2>/dev/null || true
sudo nft list ruleset 2>/dev/null | head -80
```

If the firewall only allows certain ports (e.g. SSH 22, Steam), add a rule for the import port (e.g. 8765).

**nftables** (if used):

```bash
# Allow incoming TCP on port 8765 (use your port)
sudo nft add rule inet filter input tcp dport 8765 accept
```

**iptables**:

```bash
sudo iptables -I INPUT -p tcp --dport 8765 -j ACCEPT
```

The rule lasts until reboot. For a persistent rule you need a script/unit for your system (SteamOS may reset rules on update).

After adding the rule, open `https://192.168.30.209:8765/import` in the browser again (on first visit accept the certificate warning — see "First visit: certificate warning" above).

### Summary

| Check | Command | Expected |
|-------|---------|----------|
| Port listening | `ss -tlnp \| grep 8765` | Line with 0.0.0.0:8765 |
| Local | `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/import` | 200 |
| LAN from Deck | `curl -s -o /dev/null -w "%{http_code}\n" http://192.168.30.209:8765/import` | 200 |
| Firewall | Open TCP 8765 (nft/iptables) | After rule — browser opens the page |
