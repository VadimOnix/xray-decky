---
name: decky-plugin-dev
description: Decky Loader (Steam Deck) plugin platform patterns — plugin lifecycle, frontend↔backend RPC via @decky/api, the decky Python module, SettingsManager, plugin.json/package.json rules, packaging layout. Use when writing or reviewing Decky plugin code (src/index.tsx, main.py, py_modules/), adding backend methods or events, touching plugin metadata, or when Decky/Steam Deck plugin questions come up.
---

# Decky Loader plugin development

Based on the official [decky-plugin-template](https://github.com/SteamDeckHomebrew/decky-plugin-template) (commit 90d0780, 2026-04) and `decky-loader-plugin-best-practices.md` in the repo root.

## Plugin anatomy

```
plugin/
├── src/index.tsx        # frontend entry — definePlugin()
├── main.py              # backend entry — class Plugin (async methods = RPC surface)
├── py_modules/          # extra Python modules, added to sys.path by Decky
├── backend/src|out/     # compiled-binary backends; only backend/out/ ships
├── defaults/            # non-build files copied into the package (configs, static web assets)
├── assets/              # images
├── plugin.json          # Decky metadata [required]
├── package.json         # name (lowercase-hyphens), version — bump before every release [required]
└── dist/index.js        # rollup build output [shipped, required]
```

Shipped zip contains: `dist/`, `plugin.json`, `package.json`, `main.py`, `py_modules/`, `defaults/*` content, `bin/`, `LICENSE`, `README.md`. Anything else (src/, tests/) never reaches the device.

## Backend (Python)

```python
import decky

class Plugin:
    async def my_method(self, a: int, b: str) -> dict:   # callable from frontend
        return {"ok": True}

    async def _main(self):        # runs as a task for the plugin's lifetime
        self.loop = asyncio.get_event_loop()
    async def _unload(self): ...  # plugin stopped (Decky reload/shutdown)
    async def _uninstall(self): ...  # plugin removed — clean up system remnants
    async def _migration(self):   # runs before _main; decky.migrate_logs/settings/runtime
        ...
```

The `decky` module (typed in the template's `decky.pyi`):

- `decky.logger` — standard logger; logs land in `DECKY_PLUGIN_LOG_DIR`
- `await decky.emit("event_name", *args)` — push event to frontend
- Path constants (also env vars): `DECKY_PLUGIN_SETTINGS_DIR`, `DECKY_PLUGIN_RUNTIME_DIR`, `DECKY_PLUGIN_LOG_DIR`, `DECKY_PLUGIN_DIR`, `DECKY_USER_HOME`, `DECKY_HOME`. Never write outside `DECKY_HOME`; settings/runtime/log dirs survive plugin updates, `DECKY_PLUGIN_DIR` does not.

Persistence — `SettingsManager`, not raw files, not frontend `localStorage`:

```python
from settings import SettingsManager
settings = SettingsManager(name="settings", settings_directory=os.environ["DECKY_PLUGIN_SETTINGS_DIR"])
settings.read()
settings.setSetting(key, value)   # + settings.commit() to flush
```

Rules of thumb: keep `_main()` non-blocking (spawn tasks), make every RPC method fast or async-background, avoid the `"root"` flag in plugin.json unless the plugin genuinely needs it (this repo needs it for TUN/kill switch).

## Frontend (TypeScript/React)

```tsx
import { definePlugin, callable, addEventListener, removeEventListener, toaster } from "@decky/api";
import { PanelSection, PanelSectionRow, ButtonItem, staticClasses } from "@decky/ui";

const add = callable<[first: number, second: number], number>("add"); // name = Python method

export default definePlugin(() => {
  const listener = addEventListener<[msg: string]>("my_event", (msg) => toaster.toast({ title: msg, body: "" }));
  return {
    name: "My Plugin",
    titleView: <div className={staticClasses.Title}>My Plugin</div>,
    content: <Content />,
    icon: <FaShip />,
    onDismount() { removeEventListener("my_event", listener); },
  };
});
```

- `callable<[args], ret>("python_method_name")` is the only RPC mechanism; the old `ServerAPI.callPluginMethod` is legacy. In this repo all callables live in `src/services/api.ts` — add new ones there, keep TS types in sync with the Python return shape.
- UI must use `@decky/ui` components (PanelSection, ButtonItem, ToggleField, SliderField, DropdownItem, Navigation, …) for native Steam Deck look and gamepad focus handling.
- React and react-dom come from the Steam client at runtime — never add them as real dependencies; only `@types/react` (pinned) is allowed. `rollup.config.js` should stay a one-liner around `@decky/rollup`.
- Routes outside Quick Access: `routerHook.addRoute("/my-page", Component)` in `definePlugin`, remove in `onDismount`.
- On build errors after Decky updates: `pnpm update @decky/ui --latest`.

## plugin.json

```json
{
  "name": "Display Name",
  "author": "...",
  "flags": ["debug"],          // "root" only when required; "_root" disables it
  "api_version": 1,
  "publish": { "tags": ["..."], "description": "...", "image": "https://.../image.png" }  // PNG only
}
```

`"debug"` flag enables auto-reload during development. `api_version: 1` selects the modern `@decky/api` interface.

## Checklists

New backend RPC method: Python method on `Plugin` → typed `callable` in `src/services/api.ts` → unit test (pytest for logic in `py_modules/backend/src/`, keep `main.py` a thin wiring layer).

Pre-publish: version bumped in package.json; LICENSE present; binaries in `backend/out/`; store image is PNG; `pnpm run build` output verified on a real Deck; no unnecessary `root` flag.
