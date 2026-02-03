# Feature Specification: Xray Reality VLESS Decky Plugin

**Feature Branch**: `001-xray-vless-decky`  
**Created**: 2026-01-26  
**Status**: Draft  
**Input**: User description: "create steam deck deckyLoader plugin who can implement xray reality vless connection."

## Clarifications

### Session 2026-01-26

- Q: When unexpected disconnect occurs and kill switch is on, what should the system do? → A: Block all system traffic until the user reconnects or disables the kill switch (no leak to clearnet).
- Q: What counts as an "unexpected" disconnect? → A: Any drop (network error, server down, timeout, etc.) except when the user explicitly turns the connection off.
- Q: Where should connection status be shown? → A: Only in the plugin panel (user must open the plugin to see status).
- Q: Kill switch default on first use? → A: Off by default (user opts in).
- Q: When kill switch blocks traffic, how is the user informed? → A: Brief notification (e.g. toast) plus a clear message inside the plugin panel.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Import VLESS config via URL (Priority: P1)

A Steam Deck user in Game Mode or Desktop Mode opens the plugin, pastes or enters a VLESS configuration URL (single node or subscription), and the system stores and uses that configuration for proxy connectivity.

**Why this priority**: Without a config, the user cannot connect. Import is the foundation for all other flows.

**Independent Test**: Can be fully tested by entering a valid VLESS URL, confirming it is stored, and verifying the config is available for connection. Delivers value even if connect/toggle are not yet implemented.

**Acceptance Scenarios**:

1. **Given** the plugin is installed and open, **When** the user pastes a valid VLESS config URL and confirms, **Then** the system stores the config and shows success (and the config is available for connection).
2. **Given** a stored VLESS config exists, **When** the user revisits the import screen, **Then** the user can replace it with a new URL or keep the existing one.
3. **Given** the user submits an invalid or malformed VLESS URL, **When** validation runs, **Then** the system rejects it and shows a clear error message without storing.

---

### User Story 2 - Connection on/off toggle (Priority: P2)

A user with at least one stored VLESS config can turn the proxy connection on or off from the plugin UI (Game Mode or Desktop Mode) via a single toggle or equivalent control.

**Why this priority**: Toggling is the primary day-to-day interaction; TUN mode extends functionality but is optional for users who only need app-level or browser proxy.

**Independent Test**: Can be tested by enabling the toggle (connection starts), disabling it (connection stops), and confirming traffic flows or stops as expected. Delivers value with or without TUN mode.

**Acceptance Scenarios**:

1. **Given** a valid VLESS config is stored and the connection is off, **When** the user turns the connection on, **Then** the system establishes the proxy and the UI reflects "connected" (or equivalent).
2. **Given** the connection is on, **When** the user turns it off, **Then** the system tears down the proxy and the UI reflects "disconnected."
3. **Given** the connection is on, **When** the user switches between Game Mode and Desktop Mode (or suspends/resumes), **Then** the connection state remains consistent where the platform allows, or the user can quickly toggle again if not.
4. **Given** kill switch is on and the connection drops unexpectedly, **When** the user opens the plugin, **Then** they see a clear in-panel message that traffic is blocked and can reconnect or disable the kill switch; they also received a brief notification (e.g. toast) when it happened.

---

### User Story 3 - TUN mode for system-wide tunneling (Priority: P3)

A user who needs all system traffic (including games) to go through the proxy can enable TUN mode. TUN mode creates a virtual network adapter (xray0) and routes all system traffic through the VLESS proxy. It runs only with elevated (administrator) privileges. When TUN mode connects, the plugin automatically enables System Proxy (gsettings/kwriteconfig5) so that Desktop Mode applications (browsers, GTK/Qt apps) also use the proxy; no manual gsettings configuration is required.

**Why this priority**: Required for Game Mode and full-device tunneling but depends on working config and toggle. Higher setup friction (privileges, installation steps).

**Independent Test**: Can be tested by enabling TUN mode (when the plugin runs with required privileges and installation steps are done), running a game or system app, and confirming traffic is tunneled. Delivers value for users who need global routing.

**Acceptance Scenarios**:

1. **Given** the plugin is installed with elevated privileges and the user has a stored VLESS config, **When** the user enables TUN mode and turns the connection on, **Then** all system traffic is routed through the proxy (e.g. games in Game Mode use it) and System Proxy is automatically enabled (gsettings mode=manual, SOCKS 127.0.0.1:10808).
2. **Given** TUN mode is on, **When** the user disables TUN mode or turns the connection off, **Then** system traffic resumes normal routing. System Proxy is cleared only if it was auto-enabled by TUN; a manually enabled System Proxy (via toggle_system_proxy) is preserved.
3. **Given** the user enables TUN mode but the plugin does not have the required privileges, **When** the system checks, **Then** the user is informed that TUN mode requires elevated privileges and guided on next steps (e.g. installation / sudo configuration).

---

### User Story 4 - Installation and privileges (Priority: P2)

During installation, the user can set up the plugin so that it runs with administrator privileges when needed (e.g. for TUN). The installation process adds the plugin’s AppImage (or equivalent executable) to the relevant sudo exemption list and ensures it runs under the appropriate administration account.

**Why this priority**: TUN mode depends on it; without correct setup, TUN cannot function. Applicable to users who want TUN.

**Independent Test**: Can be tested by completing installation (including sudo exclude and run-as-admin steps), then enabling TUN and verifying it works. Delivers value by unblocking TUN.

**Acceptance Scenarios**:

1. **Given** the user is installing the plugin, **When** they follow the installation steps, **Then** the AppImage is added to the sudo exemption list and configured to run with the required administration account.
2. **Given** the plugin is installed this way, **When** the user enables TUN mode, **Then** the plugin can perform TUN-related operations without prompting for a password each time (within the defined security model).
3. **Given** SteamOS applies a system update, **When** the update completes, **Then** the plugin installation (AppImage location, sudo exclude, etc.) persists where the platform supports it; any known limitations are documented.

---

### Edge Cases

- What happens when the user enters an empty or non-VLESS URL? The system rejects it and shows an error; no config is stored or used.
- What happens when the connection fails (e.g. server down, network error)? The system surfaces a clear error, allows the user to retry or turn the connection off, and does not leave the UI stuck in "connecting."
- What happens when TUN mode is enabled but privileges are insufficient? The system detects this, does not start TUN, and informs the user how to fix it (e.g. re-run installation, check sudo configuration).
- What happens when Steam or other services use ports (e.g. UDP 27015–27030) that could conflict? The plugin avoids using those ports for its own listeners where possible; if conflict occurs, the user is informed and guided to adjust config or firewall.
- What happens when the user manually enables System Proxy, then enables TUN mode (which auto-enables proxy), then disconnects? The system clears only proxy that was auto-enabled by TUN; the user's manual preference is preserved and proxy remains enabled.
- What happens when the user switches between Game Mode and Desktop Mode while connected? Behavior follows platform constraints; the plugin aims to keep connection state where possible, and the user can toggle again if the platform resets it.
- What happens when the proxy disconnects unexpectedly and kill switch is on? “Unexpected” means any drop (network error, server down, timeout) except when the user explicitly turns the connection off. The system blocks all system traffic immediately, informs the user via a brief notification (e.g. toast) and a clear message inside the plugin panel, and keeps blocking until the user reconnects or disables the kill switch.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST allow users to import and store at least one VLESS configuration via a config URL (single-node or subscription).
- **FR-002**: The system MUST validate VLESS config URLs before storing; invalid or unsupported formats MUST be rejected with a clear error message.
- **FR-003**: Users MUST be able to turn the proxy connection on and off via a dedicated toggle (or equivalent) in the plugin UI.
- **FR-004**: The system MUST reflect connection state (e.g. connected / disconnected / error) clearly in the UI. Status is shown only inside the plugin panel (user opens the plugin to see it).
- **FR-005**: The system MUST support an optional TUN mode that routes all system traffic through the VLESS proxy when enabled. When TUN mode connects, the system MUST automatically enable System Proxy (gsettings for GNOME/GTK, kwriteconfig5 for KDE) so that Desktop Mode applications use the local SOCKS/HTTP proxy (127.0.0.1:10808/10809) without manual configuration.
- **FR-006**: TUN mode MUST run only when the plugin has elevated (administrator) privileges; the system MUST detect insufficient privileges and MUST NOT start TUN without them.
- **FR-007**: The installation process MUST support adding the plugin’s AppImage to the sudo exemption list and running it under the appropriate administration account so that TUN can function.
- **FR-008**: The system MUST persist the user’s VLESS config(s), TUN on/off preference, and kill switch on/off preference across plugin restarts and, where the platform allows, across reboots.
- **FR-009**: The system MUST operate correctly on SteamOS (including Game Mode and Desktop Mode), respecting immutable filesystem, recommended use of AppImage/Flatpak, and firewall/port considerations.
- **FR-010**: The system MUST surface actionable error messages when connection or TUN setup fails (e.g. invalid config, no privileges, network error).
- **FR-012**: For VLESS Reality protocol, the system MUST generate xray-core client config using `publicKey` (server public key), `serverName`, `shortId`, and `fingerprint`—never `privateKey`, `dest`, or `xver` (these are server-side only).
- **FR-011**: The system MUST support an optional kill switch, off by default (user opts in). When enabled and the proxy disconnects unexpectedly (any drop—network error, server down, timeout, etc.—except when the user explicitly turns the connection off), the system MUST block all system traffic until the user reconnects or disables the kill switch (no clearnet leak). When kill switch blocks traffic, the system MUST inform the user via a brief notification (e.g. toast) and a clear message inside the plugin panel.

### Key Entities

- **VLESS config**: The user’s proxy configuration obtained via URL. Key attributes: source URL, stored config content, validation status. Used for establishing and tearing down the connection.
- **Connection state**: Whether the proxy is on or off, and optionally status such as connecting, connected, error. Drives UI and behavior of the toggle.
- **TUN mode preference**: User’s choice to enable or disable system-wide tunneling. Stored and applied when the connection is turned on, subject to privilege checks. When TUN connects, System Proxy is auto-enabled.
- **System Proxy state**: Managed automatically or manually. When TUN mode connects, System Proxy is auto-enabled (gsettings/kwriteconfig5) unless the user had already enabled it manually. On disconnect, only auto-enabled proxy is cleared (`autoEnabled` flag); manual preference is preserved. Optional API `toggle_system_proxy` / `get_system_proxy_status` for manual control.
- **Kill switch preference**: User’s choice to enable or disable the kill switch; off by default. When on and an unexpected disconnect occurs (any drop except user-initiated toggle-off), all system traffic is blocked until reconnect or disable.

## Assumptions

- The plugin is built as a Decky Loader plugin and follows the standard Decky plugin structure (e.g. based on the official Decky plugin template).
- Users obtain VLESS config URLs from their own providers; the plugin does not supply or recommend providers.
- SteamOS versions of interest include current stable and recent betas (e.g. 3.6.x, 3.7.x). Specific version mentions (e.g. 3.19, 3.20) align with the platform’s versioning where applicable.
- Steam ToS regarding VPN/proxy use (e.g. store region, pricing) apply; the plugin does not encourage violations. Latency and WebRTC leak considerations are user responsibilities.
- NekoRay/NekoBox and similar clients are used as reference for VLESS, REALITY, and TUN behavior; the plugin implements equivalent user-facing capabilities, not those codebases directly.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can import a VLESS config via URL and see it stored and validated within 10 seconds (or within one minute if network fetch is required for subscription URLs).
- **SC-002**: Users can turn the connection on or off with a single action, and see the state update within 5 seconds.
- **SC-003**: Users who complete the documented installation steps can enable TUN mode and have all system traffic (including games in Game Mode) routed through the proxy without per-use privilege prompts.
- **SC-004**: When config validation or connection fails, users receive a clear, actionable message in the UI in all supported flows (import, toggle, TUN).
- **SC-005**: The plugin runs reliably in both Game Mode and Desktop Mode on Steam Deck, with connection state and TUN preference surviving plugin restarts where the platform permits.
