# Decky Loader Plugin Development Best Practices

> This document is based on analysis of official documentation, templates, and the Decky Loader developer community (January 2026)

## Table of contents

1. [Project structure](#project-structure)
2. [Plugin metadata](#plugin-metadata)
3. [Frontend development (TypeScript/React)](#frontend-development-typescriptreact)
4. [Backend development (Python)](#backend-development-python)
5. [Build and distribution](#build-and-distribution)
6. [Security and performance](#security-and-performance)
7. [Update recommendations](#update-recommendations)

---

## Project structure

### Basic plugin structure

```
pluginname/
├── assets/              # Images and other resources
├── defaults/            # Config files and templates (optional)
├── backend/             # Backend code (if used)
│   ├── src/            # Backend source code
│   └── out/            # Compiled binaries (created on build)
├── py_modules/         # Python modules (if used)
├── src/                # Frontend TypeScript code
│   └── index.tsx       # Main entry point
├── main.py             # Backend Python code (if used)
├── plugin.json         # Plugin metadata [REQUIRED]
├── package.json        # pnpm metadata [REQUIRED]
├── README.md           # Project description (recommended)
├── LICENSE(.md)        # License [REQUIRED]
└── tsconfig.json       # TypeScript configuration
```

### Quick start

1. Use the official [Decky Plugin Template](https://github.com/SteamDeckHomebrew/decky-plugin-template)
2. Click "Use this Template" on GitHub to create a new repository
3. Clone the created repository

---

## Plugin metadata

### plugin.json

Required file for every plugin. Contains:

```json
{
  "name": "Plugin name",
  "author": "Your name",
  "flags": [
    "debug", // Enables auto-reload and debugging
    "root" // Run as root (USE ONLY WHEN NECESSARY!)
  ],
  "publish": {
    "tags": ["tag1", "tag2"],
    "description": "Short plugin description",
    "image": "https://example.com/plugin-image.png" // Must be PNG!
  }
}
```

**Important notes:**

- The `"root"` flag should only be used when truly necessary
- Store image must be in PNG format
- Tags help users find your plugin

### package.json

Required file for every plugin. Contains:

```json
{
  "name": "plugin-name", // Lowercase with hyphens only
  "version": "1.0.0", // Update before every PR
  "remote_binary": {
    // Optional, for large binaries
    "name": "binary-name",
    "url": "https://direct-download-url",
    "sha256hash": "sha256-hash-here"
  }
}
```

**Important notes:**

- `name` must be lowercase with hyphens (e.g.: `donkey-farm`, not `Donkey Farm`)
- `version` must be updated before every PR with updates
- `remote_binary` is used for large binary files to avoid zip archive size issues

---

## Frontend development (TypeScript/React)

### Requirements

- **Node.js**: v16.14 or higher
- **pnpm**: version 9 (mandatory!)
- **@decky/ui**: React component library for Steam Deck UI

### Installing dependencies

```bash
# Install pnpm v9 (recommended via npm)
sudo npm i -g pnpm@9

# Install project dependencies
pnpm i

# Build project
pnpm run build
```

### Frontend code structure

Main entry point is `src/index.tsx`:

```typescript
import { definePlugin } from 'decky-frontend-lib'

export default definePlugin((serverAPI: ServerAPI) => {
  return {
    title: <div>Plugin name</div>,
    content: <Content serverAPI={serverAPI} />,
    icon: <Icon />,
  }
})
```

### Backend interaction

Use `ServerAPI` to call backend functions:

```typescript
// Call backend function
serverAPI!.callPluginMethod('my_backend_function', {
  parameter_a: 'Hello',
  parameter_b: 'World',
})
```

### UI components

Use components from `@decky/ui` to match Steam Deck design:

- Components are based on Steam Deck React UI
- Documentation is available at [decky-frontend-lib](https://github.com/SteamDeckHomebrew/decky-frontend-lib)
- Usage examples can be found in the plugin template

### Updating libraries

If build errors occur due to outdated libraries:

```bash
pnpm update @decky/ui --latest
```

### Rebuild after changes

**Important:** After every frontend code change you must rebuild:

```bash
pnpm run build
```

Or use VSCode/VSCodium tasks: `setup`, `build`, `deploy`

---

## Backend development (Python)

### Backend code structure

All plugin functions are defined in the `Plugin` class:

```python
class Plugin:
    # Backend function called from frontend
    async def my_backend_function(self, parameter_a, parameter_b):
        print(f"{parameter_a} {parameter_b}")
        return {"result": "success"}

    # Long-running code, runs for plugin lifetime
    async def _main(self):
        pass

    # Cleanup on plugin unload
    async def _unload(self):
        pass
```

### SettingsManager

Use `SettingsManager` to persist settings in JSON files:

```python
from settings import SettingsManager
import os

# Get settings directory from environment variable
settingsDir = os.environ["DECKY_PLUGIN_SETTINGS_DIR"]
settings = SettingsManager(name="settings", settings_directory=settingsDir)
settings.read()

class Plugin:
    async def settings_read(self):
        return settings.read()

    async def settings_commit(self):
        return settings.commit()

    async def settings_getSetting(self, key: str, defaults):
        return settings.getSetting(key, defaults)

    async def settings_setSetting(self, key: str, value):
        settings.setSetting(key, value)
```

**Important:** Do not use `localStorage` directly in React — use SettingsManager via the backend.

### Backend with binaries

If your plugin uses a custom backend with binaries:

1. **Source location**: `backend/src/`
2. **Output binaries**: `backend/out/` (created on build)
3. **CI automatically creates the `out` folder**, but it is recommended to create it during the build process

Example Makefile:

```makefile
hello:
    mkdir -p ./out
    gcc -o ./out/hello ./src/main.c
```

**Critical:** Binaries must be in `backend/out/`, otherwise they will not be included in the distribution.

### Using defaults/ for additional files

The `defaults/` folder is used to include files that are not part of the standard build:

- Python libraries
- Configuration files
- Other resources required by the plugin

**Note:** This is a temporary solution. A whitelist in `plugin.json` is planned for the future.

---

## Build and distribution

### Zip archive structure for distribution

```
pluginname-v1.0.0.zip
│
└── pluginname/
    ├── bin/              # Optional: binaries
    │   └── binary
    ├── dist/             # [REQUIRED]
    │   └── index.js      # [REQUIRED]
    ├── package.json      # [REQUIRED]
    ├── plugin.json       # [REQUIRED]
    ├── main.py           # [REQUIRED if Python backend is used]
    ├── README.md         # Recommended
    └── LICENSE(.md)      # [REQUIRED]
```

### License requirements

- A license is **required** for Plugin Store publication
- If the license requires including its text, it must be in the repository root
- Common practice: your license on top, original template license below

### Publishing to Plugin Store

1. Follow the instructions in [decky-plugin-database](https://github.com/SteamDeckHomebrew/decky-plugin-database)
2. Open a Pull Request adding your plugin as a submodule
3. Ensure all required files are present
4. Verify that the version in `package.json` is updated

### Install via URL

Plugins can be installed via URL to a zip file:

- URL must point to direct access to the zip file
- Install via URL works only in Desktop Mode (not in Game Mode)

---

## Security and performance

### Security

1. **Installing plugins:**

   - Install only from trusted sources
   - Use the official Plugin Store
   - Check reviews before installing

2. **Development:**

   - Avoid using the `"root"` flag unless necessary
   - Validate all user input
   - Use SettingsManager instead of direct filesystem access

3. **Distribution:**
   - Include the license in the repository
   - Use `remote_binary` for large files
   - Provide SHA256 hashes for remote binaries

### Performance

1. **Code optimization:**

   - Minimize backend function calls
   - Use async operations where possible
   - Avoid blocking operations in `_main()`

2. **Plugin size:**

   - Use `remote_binary` for files > 10MB
   - Optimize images and assets
   - Remove unused dependencies

3. **UI/UX:**
   - Use components from `@decky/ui` for native look
   - Follow Steam Deck UI design patterns
   - Test on a real device

---

## Update recommendations

### Updating Decky Loader and plugins

**Critical:**

- **Always update Decky Loader and plugins BEFORE updating Steam**
- Steam updates can break compatibility
- If using Steam beta, use Decky prerelease for testing

### Versioning

1. Update `version` in `package.json` before every PR
2. Use semantic versioning (SemVer)
3. Include a changelog in update descriptions

### Testing

1. Test on a real Steam Deck, not only in an emulator
2. Verify compatibility with the latest Decky Loader version
3. Test updates before publishing

---

## Additional resources

- [Official plugin template](https://github.com/SteamDeckHomebrew/decky-plugin-template)
- [Decky Loader Wiki documentation](https://wiki.deckbrew.xyz/en/plugin-dev/getting-started)
- [decky-frontend-lib (@decky/ui)](https://github.com/SteamDeckHomebrew/decky-frontend-lib)
- [Plugin Database](https://github.com/SteamDeckHomebrew/decky-plugin-database)
- [Decky Loader Repository](https://github.com/SteamDeckHomebrew/decky-loader)

---

## Pre-publication checklist

- [ ] All required files are present (`plugin.json`, `package.json`, `LICENSE`)
- [ ] Version in `package.json` is updated
- [ ] Plugin tested on a real Steam Deck
- [ ] Backend binaries (if any) are in `backend/out/`
- [ ] License is included in the repository
- [ ] README.md contains description and instructions
- [ ] Store image is in PNG format
- [ ] All dependencies are up to date (`pnpm update @decky/ui --latest`)
- [ ] Code follows community standards
- [ ] Plugin does not require root without necessity

---

**Last updated:** January 2026  
**Sources:** Decky Loader official documentation, plugin templates, developer community
