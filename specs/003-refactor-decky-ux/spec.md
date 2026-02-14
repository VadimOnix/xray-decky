# Feature Specification: Xray Decky Plugin UI Refactor (Decky/SteamOS UX)

**Feature Branch**: `003-refactor-decky-ux`  
**Created**: 2026-02-03  
**Status**: Ready for publication  
**Input**: User description: "требуется отрефакторить интерфейс плагина xray-decky в соответствии с лучшими практиками UX плагинов decky loader"

**Delivered in branch** (same release): UI refactor per this spec; additionally shipped in this branch: System Proxy (GNOME/KDE gsettings/kwriteconfig5), TUN system route setup/removal (xray0, sockopt.interface), xray Reality client config and SOCKS/HTTP inbounds (ports 10808/10809), import page assets (favicons, webmanifest), and backend error codes for reset gating (NOT_CONNECTED, CONNECTION_ACTIVE).

## User Scenarios & Testing _(mandatory)_

### User Story 1 - First-time setup layout (Priority: P1)

A Steam Deck user opens the plugin and does not yet have a saved connection configuration. The plugin shows a dedicated setup screen that helps them import/paste a VLESS link and explicitly save it, using a compact layout that matches SteamOS/Decky UI patterns.

**Why this priority**: This is the entry point. Without a clear first-run setup flow, users cannot reach a usable connection state.

**Independent Test**: Can be tested end-to-end by ensuring the plugin shows the setup layout when no configuration exists, the user can input a VLESS link (via QR-assisted flow or manual paste/typing), save it, and transition to the configured state.

**Acceptance Scenarios**:

1. **Given** the plugin is opened and no connection configuration exists, **When** the UI is rendered, **Then** the plugin shows the “Setup” layout (state 1) and does not show the “Connected/Configured” layout (state 2).
2. **Given** the user is on the “Setup” layout, **When** they look for onboarding elements, **Then** the UI contains (a) a QR code, (b) a local-network configuration page address, (c) a single input/textarea that displays the VLESS link value, and (d) a dedicated manual “Save” action.
3. **Given** the user enters or pastes a VLESS link into the input/textarea, **When** they tap “Save”, **Then** the system validates and stores the configuration and transitions the UI to the “Configured” layout (state 2).
4. **Given** the user enters an invalid or unsupported VLESS link, **When** they tap “Save”, **Then** the system does not store it, stays in the “Setup” layout, and shows a clear, actionable error message.
5. **Given** the user is on the “Setup” layout, **When** they need more explanations, **Then** non-critical “About” information is accessible via help popups (question-mark icon), not as long inline text blocks.

---

### User Story 2 - Daily connect + status + options (Priority: P2)

A user with an existing configuration opens the plugin and sees a focused control surface: a primary connect action, current connection status, a compact summary of the active configuration, advanced toggles (TUN Mode and Kill Switch), and a reset action that returns them to the setup screen.

**Why this priority**: This is the main day-to-day usage. The UI should minimize scrolling and surface the primary action and status first.

**Independent Test**: Can be tested by storing a configuration, confirming the configured layout appears, verifying connect/disconnect changes the visible status, verifying toggles are available, and verifying reset returns the user to setup.

**Acceptance Scenarios**:

1. **Given** a saved configuration exists, **When** the plugin is opened, **Then** the UI shows the “Configured” layout (state 2) and does not show the “Setup” layout (state 1).
2. **Given** the user is on the “Configured” layout and currently disconnected, **When** they tap the primary “Connect” action, **Then** the system starts connecting and the status bar reflects the connection progress and final state (connected or error).
3. **Given** the user is connected, **When** the connection state changes (connecting → connected, connected → disconnected, error), **Then** the status bar updates within the plugin panel without requiring a reload.
4. **Given** the user is on the “Configured” layout, **When** they review the configuration, **Then** they see a compact configuration information card (human-readable summary) without exposing excessive raw config text by default.
5. **Given** the user is on the “Configured” layout, **When** they adjust advanced options, **Then** they can toggle TUN Mode and Kill Switch from a dedicated options block and immediately see the updated setting state.
6. **Given** the user is connected, **When** they look at “Reset configuration”, **Then** the reset action is disabled and clearly indicates it cannot be used while the proxy connection is active.
7. **Given** the user is disconnected, **When** they tap “Reset configuration”, **Then** the system clears the saved configuration and returns the user to the “Setup” layout (state 1).

---

### User Story 3 - Contextual help instead of “About” blocks (Priority: P3)

The user can access longer explanations (previously shown in “About” blocks) via small contextual help popups, so the main screens stay compact and focused.

**Why this priority**: Quick Access Menu plugins have limited space; long text reduces usability and increases scrolling.

**Independent Test**: Can be tested by verifying that previously inline “About” content is hidden by default and appears only when a help icon is activated.

**Acceptance Scenarios**:

1. **Given** the user is on either layout (setup or configured), **When** they view the screen, **Then** “About” text blocks do not occupy persistent space in the main flow.
2. **Given** the user taps a help (question-mark) icon, **When** the popup opens, **Then** it shows the corresponding “About” information and can be dismissed without losing entered data or current state.

---

### Edge Cases

- What happens when the configuration exists but is incomplete/corrupted? The system treats it as “not configured” and presents the “Setup” layout with an explanation and a path to re-save.
- What happens when connecting fails (network error, server error)? The status bar shows an error state and a clear recovery hint (retry, check config, etc.) without breaking layout.
- What happens when the UI cannot render the QR code? The system shows a fallback message and still provides the local-network configuration page address and manual input/save.
- What happens when the local-network configuration page address cannot be determined? The system shows a fallback explanation and still allows manual entry and save.
- What happens when the user attempts to reset while connected? The reset action remains disabled and no reset occurs.
- What happens when settings toggles cannot be applied while connected (platform constraint)? The UI communicates the constraint clearly (e.g., “will apply on next connect”) without losing the user’s choice.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST present exactly two distinct UI layouts based on whether a saved connection configuration exists: (1) “Setup” and (2) “Configured”.
- **FR-002**: In the “Setup” layout, the system MUST display: (a) a QR code, (b) a local-network configuration page address, (c) a single input/textarea that displays the VLESS link value, and (d) a manual “Save” action.
- **FR-003**: The “Save” action MUST validate the entered VLESS link and MUST store the configuration only when valid; invalid input MUST show an actionable error and MUST NOT overwrite a previously valid saved configuration.
- **FR-004**: After a successful save, the system MUST transition from “Setup” to “Configured” without requiring plugin reload.
- **FR-005**: In the “Configured” layout, the system MUST display: (a) a primary “Connect” action, (b) a connection status bar, (c) a configuration information card, (d) an options block with toggles for TUN Mode and Kill Switch, and (e) a “Reset configuration” action.
- **FR-006**: The status bar MUST reflect at least these states: disconnected, connecting, connected, error; it MUST update when the underlying connection state changes while the plugin panel is open.
- **FR-007**: “Reset configuration” MUST clear the saved configuration and MUST force the UI back to the “Setup” layout.
- **FR-008**: “Reset configuration” MUST be disabled while an active proxy connection exists.
- **FR-009**: Non-critical “About” information MUST be moved into contextual help popups accessible via a help icon; it MUST NOT be shown as large persistent blocks in the main layout.
- **FR-009a**: Help popups MUST be dismissible and MUST NOT clear or reset in-progress user input (e.g., text entered in the Setup input/textarea).
- **FR-010**: The UI styling MUST match SteamOS/Decky visual patterns by using native/standard Decky UI elements where available; when a matching UI element is not available (e.g., QR code), existing custom styling MAY be retained.

### Key Entities _(include if feature involves data)_

- **Connection configuration**: A saved configuration that allows establishing a proxy connection; includes a VLESS link value and any derived connection details needed by the system.
- **Connection state**: Current runtime state of the proxy connection (disconnected/connecting/connected/error) that drives the status bar and availability of actions.
- **Option preferences**: User choices for TUN Mode and Kill Switch that affect how the connection behaves.

## Assumptions & Dependencies

- The system can reliably determine whether a saved connection configuration exists (used to select “Setup” vs “Configured” layout).
- The system can observe current connection state while the plugin panel is open (used to drive the status bar and to disable reset while connected).
- The QR code and local-network configuration page address shown in the “Setup” layout refer to an existing or planned local import/onboarding flow; this specification does not define how that page is implemented, only that it is presented consistently in the UI.
- This feature is scoped to **UI/UX refactor and layout/state presentation**; it does not introduce new proxy protocols or change the underlying connection technology beyond what is required to support the UX requirements above.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: With no existing configuration, users can complete setup (enter/paste link → save → reach configured layout) in under 60 seconds in at least 90% of first-run attempts.
- **SC-002**: With an existing configuration, users can reach “Connected” from opening the plugin with no more than 2 primary interactions (open plugin → connect), excluding any external network delays.
- **SC-003**: The configured layout fits without requiring excessive scrolling: key controls (Connect, status bar, reset) are visible within one screen height on Steam Deck in typical UI scale settings.
- **SC-004**: The system prevents accidental destructive actions: 100% of attempts to reset while connected are blocked (reset remains disabled).
- **SC-005**: Users can access “About” information when needed without permanent clutter: help content is discoverable via a help icon and does not displace primary controls.
