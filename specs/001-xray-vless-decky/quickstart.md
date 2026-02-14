# Quick Start: Xray Reality VLESS Decky Plugin

**Date**: 2026-01-26  
**Feature**: 001-xray-vless-decky  
**Status**: Phase 1 Design

## Overview

This guide provides a quick start for developers working on the Xray Reality VLESS Decky Plugin. It covers setup, development workflow, and key concepts.

---

## Prerequisites

### Required Software

- **Node.js**: v16.14 or higher
- **pnpm**: Version 9 (mandatory, not optional)
- **Python**: 3.x (for backend development)
- **Git**: For version control
- **Steam Deck** (or SteamOS VM): For testing

### Development Tools

- **VS Code** or **VSCodium**: Recommended IDE
- **Decky Loader**: Installed on Steam Deck for testing
- **xray-core binary**: Will be downloaded/built during setup

---

## Project Setup

### 1. Clone and Initialize

```bash
# Clone repository (if applicable)
git clone <repository-url>
cd xray-decky

# Navigate to plugin directory (when created)
cd xray-decky-plugin

# Install frontend dependencies
pnpm install

# Verify pnpm version (must be 9)
pnpm --version  # Should show 9.x.x
```

### 2. Install pnpm v9 (if needed)

```bash
# Install pnpm v9 globally
sudo npm i -g pnpm@9

# Or use corepack (if available)
corepack enable
corepack prepare pnpm@9 --activate
```

### 3. Download xray-core Binary

```bash
# Create backend/out directory
mkdir -p backend/out

# Download xray-core binary for Linux (amd64)
# Replace with latest version from https://github.com/XTLS/Xray-core/releases
wget -O backend/out/xray-core https://github.com/XTLS/Xray-core/releases/download/v1.8.4/Xray-linux-64.zip
unzip backend/out/xray-core -d backend/out/
chmod +x backend/out/xray-core
```

### 4. Build Frontend

```bash
# Build frontend TypeScript/React code
pnpm run build

# Verify dist/index.js is created
ls -la dist/index.js
```

---

## Project Structure

```
xray-decky-plugin/
├── src/                    # Frontend TypeScript/React
│   ├── index.tsx          # Plugin entry point
│   ├── components/        # React components
│   ├── services/          # API services
│   └── utils/             # Utilities
├── backend/               # Backend Python
│   ├── src/               # Python source
│   └── out/               # xray-core binary
├── main.py                # Backend entry point
├── plugin.json            # Plugin metadata
├── package.json           # Package metadata
├── tsconfig.json          # TypeScript config
└── README.md              # Documentation
```

---

## Development Workflow

### Frontend Development

1. **Make changes** to TypeScript/React files in `src/`
2. **Build** after every change:
   ```bash
   pnpm run build
   ```
3. **Test** on Steam Deck (copy `dist/index.js` to plugin directory)

### Backend Development

1. **Make changes** to Python files in `backend/src/` or `main.py`
2. **Test** backend methods:
   ```bash
   # Run Python tests
   pytest backend/tests/
   ```
3. **Test** on Steam Deck (restart plugin to load changes)

### Full Development Cycle

```bash
# 1. Make code changes
# 2. Build frontend
pnpm run build

# 3. Run tests
pnpm test              # Frontend tests
pytest backend/tests/   # Backend tests

# 4. Deploy to Steam Deck (manual or via script)
# 5. Test on actual hardware
```

---

## Key Concepts

### Frontend-Backend Communication

All communication uses `ServerAPI.callPluginMethod()`:

```typescript
// Frontend example
const result = await serverAPI.callPluginMethod('import_vless_config', {
  url: 'vless://...',
})
```

### Settings Persistence

Use SettingsManager (never localStorage):

```python
# Backend example
from settings import SettingsManager
import os

settingsDir = os.environ["DECKY_PLUGIN_SETTINGS_DIR"]
settings = SettingsManager(name="settings", settings_directory=settingsDir)
settings.read()

# Get setting
value = settings.getSetting("key", "default")

# Set setting
settings.setSetting("key", "value")
settings.commit()
```

### xray-core Integration

xray-core is managed as a subprocess:

```python
# Backend example
import asyncio

async def start_xray(config_path: str):
    process = await asyncio.create_subprocess_exec(
        'backend/out/xray-core',
        '-config', config_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return process
```

---

## Testing

### Unit Tests

```bash
# Frontend tests
pnpm test

# Backend tests
pytest backend/tests/unit/
```

### Integration Tests

```bash
# Backend integration tests
pytest backend/tests/integration/
```

### Manual Testing on Steam Deck

1. **Build plugin**:

   ```bash
   pnpm run build
   ```

2. **Copy to Steam Deck** (via SSH or USB):

   ```bash
   # SSH to Steam Deck
   scp -r . deck@<steam-deck-ip>:/home/deck/homebrew/plugins/xray-decky/
   ```

3. **Restart Decky Loader** or reload plugin

4. **Test in Game Mode and Desktop Mode**

---

## Common Tasks

### Update Dependencies

```bash
# Update @decky/ui to latest
pnpm update @decky/ui --latest

# Update all dependencies
pnpm update
```

### Check Code Quality

```bash
# Frontend linting
pnpm run lint

# Backend linting (if configured)
ruff check backend/
mypy backend/
```

### Build for Distribution

```bash
# Build frontend
pnpm run build

# Create distribution zip
# (Follow Decky Loader distribution guidelines)
```

---

## Troubleshooting

### Build Errors

**Error**: `pnpm: command not found`

- **Solution**: Install pnpm v9: `sudo npm i -g pnpm@9`

**Error**: `@decky/ui not found`

- **Solution**: Run `pnpm install` and ensure pnpm v9 is used

**Error**: `dist/index.js not found`

- **Solution**: Run `pnpm run build` after code changes

### Runtime Errors

**Error**: `xray-core: command not found`

- **Solution**: Ensure `backend/out/xray-core` exists and is executable

**Error**: `TUN mode requires privileges`

- **Solution**: Complete installation steps for sudo exemption (or use plugin.json "root" flag)

**Note**: When TUN mode connects, System Proxy is automatically enabled (gsettings). No manual gsettings/SSH configuration required.

**Error**: `SettingsManager error`

- **Solution**: Check `DECKY_PLUGIN_SETTINGS_DIR` environment variable

---

## Next Steps

1. **Read the specification**: `specs/001-xray-vless-decky/spec.md`
2. **Review the data model**: `specs/001-xray-vless-decky/data-model.md`
3. **Check API contracts**: `specs/001-xray-vless-decky/contracts/frontend-backend-api.md`
4. **Follow development standards**: See `decky-loader-plugin-best-practices.md`

---

## Resources

- **Decky Plugin Template**: https://github.com/SteamDeckHomebrew/decky-plugin-template
- **Decky Loader Wiki**: https://wiki.deckbrew.xyz/en/plugin-dev/getting-started
- **decky-frontend-lib**: https://github.com/SteamDeckHomebrew/decky-frontend-lib
- **xray-core**: https://github.com/XTLS/Xray-core
- **xray-core Documentation**: https://xtls.github.io/

---

## Getting Help

- Check existing documentation in `specs/001-xray-vless-decky/`
- Review error messages and logs
- Test on actual Steam Deck hardware
- Follow Decky Loader community best practices
