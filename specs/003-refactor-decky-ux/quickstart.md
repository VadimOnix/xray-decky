# Quickstart: Xray Decky UI Refactor (two-state layout)

**Branch**: `003-refactor-decky-ux`  
**Date**: 2026-02-03  
**Goal**: Verify the two UI layouts, reset gating, and contextual help behavior on a real Steam Deck.

## Prerequisites

- Steam Deck with Decky Loader installed
- Plugin installed (development build or packaged build)
- Optional: CEF debugging enabled for frontend inspection (Deckbrew: “Frontend Debugging”)

## Test Plan (manual)

### 1) Setup layout (no saved config)

1. Ensure no saved connection configuration exists (use Reset from step 3 if needed).
2. Open the plugin.
3. Verify the UI shows the **Setup** layout:
   - QR code visible
   - LAN import address visible
   - textarea/input showing current VLESS link value
   - explicit **Save** action
4. Enter an invalid VLESS link and tap Save → verify an actionable error is shown and no state transition occurs.
5. Enter a valid VLESS link and tap Save → verify the UI transitions to **Configured** without plugin reload.

### 2) Configured layout (config exists)

1. With a saved config, open the plugin.
2. Verify the UI shows the **Configured** layout:
   - primary Connect/Disconnect control
   - status bar reflecting current state
   - config summary card (compact, not raw config dump)
   - options block with TUN Mode + Kill Switch toggles
   - Reset configuration action

### 3) Reset gating

1. While **disconnected**, tap Reset configuration → verify config is cleared and UI returns to Setup.
2. Save config again, then connect.
3. While **connected** (or connecting), verify Reset configuration is **disabled** and cannot be executed.

### 4) Contextual help popups

1. In Setup layout, verify “About” content is not shown as large inline blocks.
2. Tap question-mark help icons → verify popup help appears and can be dismissed without losing current state or typed input.
3. In Configured layout, verify TUN/Kill Switch “About” content is similarly moved behind help.

## References

- Deckbrew: new API migration (`@decky/api` + `@decky/ui`) — `https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration`
- Deckbrew: plugin structure / getting started — `https://wiki.deckbrew.xyz/en/plugin-dev/getting-started`
