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

Если QR показывает правильный URL (например `https://192.168.30.209:8765/import`), но в браузере на телефоне/ПК — «Не удается установить соединение» / ERR_CONNECTION_REFUSED, проверьте на **Steam Deck** (Desktop Mode → Konsole).

### 1. Сервер слушает порт

Плагин должен быть запущен (Game Mode: открыт плагин Xray Decky хотя бы раз). На Deck выполните:

```bash
# Есть ли процесс, слушающий порт 8765 (или ваш importServer.port)?
ss -tlnp | grep 8765
# или
ss -tlnp
```

Ожидаемо: строка вида `LISTEN 0 128 0.0.0.0:8765 0.0.0.0:*` (или ваш порт). Если вывода нет — сервер импорта не запущен (плагин не загружен, папка `backend/static` отсутствует при деплое или порт занят).

**Если в выводе только `127.0.0.1:8765` и `[::1]:8765`, а не `0.0.0.0:8765`** — это не наш плагин. Наш сервер привязывается к `0.0.0.0`, чтобы принимать подключения из LAN. Значит порт 8765 занят другим процессом (слушает только localhost), а наш сервер при старте не смог занять порт (Address already in use). Либо запущена старая сборка. Действия:

1. Узнать, какой процесс держит порт:
   ```bash
   lsof -i :8765
   # или (PID в последней колонке)
   ss -tlnp | grep 8765
   ```
2. Если это не наш плагин (не python/плагин Decky) — освободить порт или сменить порт плагина в настройках: в Decky Store/настройках плагина задать `importServer.port` = например **8766**, перезапустить плагин (выйти из настроек плагина и открыть снова).
3. Если процесс — наш (python), но слушает 127.0.0.1 — переустановить/задеплоить последнюю сборку, где в `main.py` используется `TCPSite(runner, "0.0.0.0", port)`.

Дополнительно: если `curl http://127.0.0.1:8765/import` возвращает **404**, а не 200 — на порту отвечает не наша страница импорта (у нас GET `/import` отдаёт HTML). Значит на 8765 точно другой сервис; наш плагин тогда не слушает 8765 — см. пункты выше (сменить порт или освободить 8765).

### 2. Доступ с самого Deck (localhost)

```bash
# Замените 8765 на ваш порт при необходимости
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/import
```

Ожидаемо: `200`. Если пусто или ошибка — сервер не отвечает даже локально.

### 3. Доступ по LAN IP с Deck

```bash
# Замените 192.168.30.209 и 8765 на ваш IP и порт
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.30.209:8765/import
```

Ожидаемо: `200`. Если localhost отвечает, а по LAN IP — нет, возможна маршрутизация/интерфейс (редко при bind 0.0.0.0).

### 4. Фаервол на Steam Deck

SteamOS (Arch-based) может использовать **iptables** или **nftables**. Входящие подключения к порту импорта по умолчанию могут блокироваться.

Проверка:

```bash
# Есть ли правила, ограничивающие входящие?
sudo iptables -L INPUT -n -v 2>/dev/null || true
sudo nft list ruleset 2>/dev/null | head -80
```

Если фаервол разрешает только часть портов (например, SSH 22, Steam), добавьте правило для порта импорта (например 8765).

**nftables** (если используется):

```bash
# Разрешить входящий TCP на порт 8765 (подставьте свой порт)
sudo nft add rule inet filter input tcp dport 8765 accept
```

**iptables**:

```bash
sudo iptables -I INPUT -p tcp --dport 8765 -j ACCEPT
```

Правило действует до перезагрузки. Для постоянного правила нужна настройка скрипта/юнита вашей системы (SteamOS может сбрасывать правила при обновлении).

После добавления правила снова откройте в браузере `https://192.168.30.209:8765/import` (при первом заходе примите предупреждение о сертификате — см. раздел «First visit: certificate warning» выше).

### Кратко

| Проверка | Команда | Ожидание |
|----------|--------|----------|
| Порт слушает | `ss -tlnp \| grep 8765` | Строка с 0.0.0.0:8765 |
| Локально | `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/import` | 200 |
| По LAN с Deck | `curl -s -o /dev/null -w "%{http_code}\n" http://192.168.30.209:8765/import` | 200 |
| Фаервол | Открыть TCP 8765 (nft/iptables) | После правила — браузер открывает страницу |
