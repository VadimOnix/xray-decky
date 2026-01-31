# Feature Specification: VLESS Import via QR and Paste Form

**Feature Branch**: `002-vless-import-qr`  
**Created**: 2026-01-30  
**Status**: Draft  
**Input**: User description: "Я как пользователь хочу импортировать vless ссылку через удобную форму ввода. Иметь возможность отсканировать камерой телефона QR код, который откроет мне в браузере удобную форму ввода vless ссылки, нажать Paste -> Save и перейти к дальнейшей настройке подключения в плагине."

## Clarifications

### Session 2026-01-30

- Q: Should the import page follow any specific visual design? → A: Yes — the import page MUST use a color design consistent with Steam UI (преемственный Steam UI).
- Q: In what order should plugin UI blocks appear on Steam Deck? → A: The QR code block MUST be displayed first (before any other plugin content).
- Q: Which address should the QR code URL use so the phone can reach the import page? → A: The URL MUST use the Steam Deck's local network (LAN) address, not 127.0.0.1; the backend MUST determine the device's LAN IP (e.g. default route / first non-loopback) so that devices on the same WiFi can open the import page.
- Q: How should frontend–backend communication and plugin structure be implemented after the UI-not-responding-to-backend debugging? → A: The current implementation is the correct approach: (1) Frontend uses the new Decky API: definePlugin from @decky/api with no arguments; backend calls via callable() from @decky/api, not decky-frontend-lib serverAPI. (2) Backend: plugin directory on sys.path; backend package with __init__.py (backend/, backend/src/); plugin name in plugin.json must match loader registration. (3) LAN IP for QR URL resolved by backend (e.g. socket + hostname -I + ip route fallbacks), not 127.0.0.1.

### Session 2026-01-31

- Q: How should the Paste button work when the import page is opened from another device (phone/PC) over the network? → A: The import page MUST be served over HTTPS with a self-signed certificate so that the browser secure context allows `navigator.clipboard.readText()`. The plugin MUST generate and store the certificate (e.g. in `DECKY_PLUGIN_RUNTIME_DIR`) on first run or at startup if missing; start the import server with TLS (aiohttp with `ssl.SSLContext`); return `baseUrl` with protocol `https` in `get_import_server_url()`. On first visit from a device the browser will show a certificate warning; the user accepts once per device (e.g. "Advanced" → "Proceed"); after that Paste works. On certificate generation or load failure the implementation MUST log the error and MUST NOT start the import server (optional: document or implement HTTP fallback as a degraded mode).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import VLESS via QR and Paste (Priority: P1)

When the plugin is running, the user sees a QR code. They scan it with their phone camera, which opens a self-hosted import page in the mobile browser. On that page they tap "Paste" to fill the input with the VLESS link from the clipboard, then tap "Save". The link is delivered to the plugin so the user can continue with connection setup (e.g. connect, test, configure) without typing the link on the Steam Deck.

**Why this priority**: This is the core flow; without it the feature has no value.

**Independent Test**: User can complete the full path: scan QR → open page → Paste → Save → see the link available in the plugin for further setup.

**Acceptance Scenarios**:

1. **Given** the plugin is running and showing the QR code, **When** the user scans the QR with the phone camera, **Then** the mobile browser opens a page at the URL encoded in the QR (local address: `https://{Steam Deck LAN IP}:{plugin port}/import`).
2. **Given** the user is on the import page, **When** they tap "Paste", **Then** the VLESS link from the device clipboard is inserted into the visible input field.
3. **Given** the input contains a VLESS link (from Paste or manual entry), **When** the user taps "Save", **Then** the link is submitted to the plugin and the user can proceed to further connection setup in the plugin.
4. **Given** the user has just saved a link, **When** they return to the plugin UI, **Then** the imported VLESS link is available for connection configuration (e.g. select and connect).
5. **Given** the user opens the plugin on Steam Deck, **When** the plugin UI is displayed, **Then** the block containing the QR code is the first visible block (above any other sections or controls).

---

### User Story 2 - Manual URL Entry Fallback (Priority: P2)

If the user cannot or does not want to use Paste (e.g. link came via message or notes), they can type or paste the VLESS link manually into the same import form and save it the same way.

**Why this priority**: Ensures the form is still useful when clipboard is empty or unavailable.

**Independent Test**: User opens the import page (via QR or by entering the URL), types or pastes a VLESS link into the input, taps Save, and the link is available in the plugin.

**Acceptance Scenarios**:

1. **Given** the user is on the import page, **When** they enter a VLESS link in the input (by typing or pasting), **Then** they can tap "Save" and the link is submitted to the plugin.
2. **Given** the user has entered an invalid or non-VLESS string, **When** they tap "Save", **Then** the system indicates an error and does not treat the value as a valid import (user can correct and try again).

---

### User Story 3 - Reliable Access to Import Page (Priority: P3)

The user can reach the import page consistently: either by scanning the QR shown by the plugin, or by manually opening the same URL in a browser when they know the Steam Deck’s local IP and the plugin port.

**Why this priority**: Supports different usage habits and recovery when QR is not at hand.

**Independent Test**: With plugin running, user opens `https://{Steam Deck LAN IP}:{plugin port}/import` in a browser (phone or other device on same network) and sees the same import form; Paste and Save behave as in Story 1.

**Acceptance Scenarios**:

1. **Given** the plugin is running and the device is on the same local network as the Steam Deck, **When** the user navigates to the import URL, **Then** the import page loads and shows the form (Paste, input, Save).
2. **Given** the QR code is displayed in the plugin, **When** the user scans it, **Then** the URL encoded in the QR points to the same import page (same path and port).

---

### Edge Cases

- What happens when the clipboard does not contain a valid VLESS link and the user taps "Paste"? The pasted content is shown in the input; validation applies on "Save".
- What happens when the user taps "Save" with an empty or invalid link? The system shows a clear error and does not overwrite or clear existing plugin configuration; the user can correct the input and try again.
- What happens when the Steam Deck or plugin is unreachable (wrong network, plugin stopped)? The import page does not load or Save fails with a clear indication; the user can retry when the device and plugin are available.
- What happens when multiple devices open the import page and save different links? The last successfully saved link is the one used by the plugin for further setup; behavior is predictable and documented.
- What happens on first visit to the import page from a new device? The browser shows a certificate warning (self-signed). The user MUST accept once per device (e.g. "Advanced" → "Proceed to site"); after acceptance the page is in a secure context and the Paste button works. This flow MUST be documented (e.g. in quickstart or in-plugin hint).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When the plugin is running, the user MUST be shown a QR code that encodes the URL of the self-hosted import page (local address: `https://{steam deck LAN ip}:{plugin port}/import`). The backend MUST resolve the Steam Deck's LAN IP (not 127.0.0.1) so that phones and other devices on the same network can open the URL. On Steam Deck, the block containing this QR code MUST be displayed first in the plugin UI (before any other section or control).
- **FR-002**: The system MUST serve the import page over **HTTPS** at the path `/import` on the same port used by the plugin, reachable from devices on the same local network. The server MUST use TLS with a self-signed certificate so that the page is in a browser secure context and `navigator.clipboard.readText()` (Paste) works from any device.
- **FR-003**: The import page MUST provide a visible input field for the VLESS link and a "Paste" control that, when activated, inserts the current device clipboard content into that input.
- **FR-004**: The import page MUST provide a "Save" control that, when activated, submits the current input value to the plugin as the VLESS link for import.
- **FR-005**: After a successful Save, the plugin MUST store or expose the submitted VLESS link so the user can proceed to further connection setup (e.g. select connection, connect, test) without re-entering the link.
- **FR-006**: The system MUST validate the submitted value as a VLESS link on Save; if invalid, the system MUST reject the save, show a clear error, and allow the user to correct and retry.
- **FR-007**: The import page MUST be usable on mobile browsers (e.g. after opening via QR scan): form, Paste, and Save MUST work without requiring desktop-only interactions.
- **FR-008**: The import page MUST be accessible only over the local network (same host/port as the plugin); no requirement for public or internet-accessible import URL.
- **FR-009**: The import page MUST use a color design consistent with Steam UI (преемственный Steam UI): palette, contrast, and overall look and feel must align with Steam / Steam Deck visual identity so the page feels part of the same experience.

### Design Reference (for implementation)

Steam does not publish a single public UI kit. To align the import page with Steam UI, use:

- **Steamworks branding**: [Steamworks Documentation – Branding](https://partner.steamgames.com/doc/marketing/branding) — asset rules and store/library visuals.
- **Valve VGUI**: [VGUI Documentation](https://developer.valvesoftware.com/wiki/VGUI_Documentation) — interface patterns for Valve UIs.
- **Steam Deck theming**: [DeckThemes / CSS Loader](https://docs.deckthemes.com/CSSLoader/) — Steam Deck UI is styled with CSS (CEF); community themes show typical dark palette, gradients, and structure.
- **Steam dark aesthetic**: Steam’s client and Deck use a dark, layered design with subtle gradients and functional navigation; the import page should match this style (e.g. dark background, Steam-typical accent colors, readable contrast).

### Key Entities

- **VLESS link**: A single string (URL) that describes a VLESS proxy connection; produced by the user (e.g. from another device or app) and consumed by the plugin for connection setup. Key attribute: it must be recognizable and valid for the plugin to use.
- **Import session**: One use of the import page: open page → optionally Paste → enter or edit link → Save. The result is one link delivered to the plugin; repeated Saves overwrite or update the imported link for the plugin.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from “plugin open” to “VLESS link available in plugin” in under 30 seconds when using scan → Paste → Save on a phone.
- **SC-002**: Paste and Save work on the import page in common mobile browsers (e.g. Safari iOS, Chrome Android) without errors under normal network conditions.
- **SC-003**: When the user taps Save with an invalid or empty link, they see a clear error message and can correct the input and save again without leaving the page.
- **SC-004**: After a successful Save, the user can immediately use the imported link in the plugin for the next step (e.g. connect or configure) without re-typing or re-importing.
- **SC-005**: The QR code displayed by the plugin reliably opens the correct import page URL when scanned by standard phone camera or QR apps.
- **SC-006**: The import page presents a color palette and visual style consistent with Steam / Steam Deck UI (e.g. dark theme, Steam-typical contrast and accents) so users perceive it as part of the same experience.

## Constraints & implementation (validated during debugging)

The following approach was validated when the UI did not respond to the backend; it is the correct implementation baseline.

- **Frontend–backend communication**: Use the **new Decky API** (api_version: 1). Entry point: `definePlugin` from `@decky/api` with **no arguments** (no serverAPI). Backend calls: `callable<[args], ReturnType>("method_name")` from `@decky/api` at module scope; call the returned function when needed. Do **not** rely on `decky-frontend-lib` `serverAPI` or `callPluginMethod` passed into `definePlugin`, as the loader may not provide it and the UI will not receive backend responses.
- **Backend Python structure**: The plugin root must be on `sys.path` before importing `backend.*` (e.g. in `main.py`, insert `PLUGIN_DIR` into `sys.path`). The `backend` package MUST have `backend/__init__.py` and `backend/src/__init__.py` so that `from backend.src.<module> import ...` works when the plugin is loaded from the Decky plugins directory. Deployment/packaging MUST include these `__init__.py` files.
- **Plugin identity**: The `name` in `plugin.json` MUST match the name used by the Decky Loader for plugin registration (e.g. "Xray Decky"); frontend callables are bound to this plugin name.
- **QR URL host**: The URL returned by `get_import_server_url` MUST use the host's **LAN IP** (not 127.0.0.1). The backend MUST resolve it (e.g. outgoing socket to 8.8.8.8, then fallbacks such as `hostname -I` or `ip -4 route get 8.8.8.8`) so that the QR code is openable from other devices on the same network.
- **HTTPS for import page**: The import server MUST listen with TLS (aiohttp with `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` and cert/key). The certificate MUST be generated on first run or at startup if missing (e.g. via `cryptography` or `openssl` subprocess) and stored under `DECKY_PLUGIN_RUNTIME_DIR` (or equivalent plugin runtime path). `get_import_server_url()` MUST return `baseUrl` with protocol **https** (e.g. `https://{lan_ip}:{port}`). On certificate generation or load failure the implementation MUST log the error and MUST NOT start the import server (optional: HTTP fallback as degraded mode). Dependencies for certificate generation (e.g. `cryptography` in `backend/requirements.txt`) MUST be declared.

## Assumptions

- The plugin already has a notion of “connection” or “config” and a way to use a VLESS link for further setup; this feature only adds the import path (QR + form), not the full connection logic.
- “Steam Deck LAN ip” is the IP of the Steam Deck on the local network; the backend MUST determine it (e.g. default route or first non-loopback) for building the QR URL so the import page is reachable from other devices on the same WiFi; it must not be 127.0.0.1.
- The import page is served by the same process or stack that serves the plugin’s backend (e.g. same port); no separate web server is assumed.
- Clipboard read permission (for Paste) is granted by the user in the mobile browser when prompted, or is already allowed; the spec does not define browser permission flows. Serving the import page over HTTPS (self-signed cert) ensures a secure context so `navigator.clipboard.readText()` is available; browsers show a one-time certificate warning per device, which is documented and accepted by the user.
- Validation of “VLESS link” follows the same rules the plugin already uses for accepting VLESS configs; the spec does not define the exact format beyond “recognizable and valid for the plugin.”
