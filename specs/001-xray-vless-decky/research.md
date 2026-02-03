# Research: Xray Reality VLESS Decky Plugin

**Date**: 2026-01-26  
**Feature**: 001-xray-vless-decky  
**Status**: Complete

## Research Objectives

This document consolidates research findings for technical decisions required to implement the Xray Reality VLESS Decky Plugin. All "NEEDS CLARIFICATION" items from the implementation plan have been resolved.

---

## 1. xray-core Integration with Python Backend

### Decision: Use xray-core binary with subprocess management

**Rationale**:

- xray-core is written in Go and distributed as a single binary
- Python backend will spawn xray-core as a subprocess and manage its lifecycle
- Configuration passed via JSON config file or command-line arguments
- Process management via `asyncio.subprocess` for non-blocking operations

**Alternatives Considered**:

- **Go library bindings**: Rejected - Complex FFI setup, maintenance overhead, no official Python bindings
- **REST API wrapper**: Rejected - Additional complexity, xray-core doesn't expose HTTP API by default
- **Direct binary execution**: ✅ Chosen - Simple, reliable, matches existing xray clients (NekoRay, NekoBox)

**Implementation Pattern**:

```python
# Pseudo-code pattern
async def start_xray(config_path: str):
    process = await asyncio.create_subprocess_exec(
        'backend/out/xray-core',
        '-config', config_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return process
```

**References**:

- xray-core GitHub: https://github.com/XTLS/Xray-core
- xray-core documentation: https://xtls.github.io/
- NekoRay implementation patterns (reference)

---

## 2. TUN Mode Implementation on Linux/SteamOS

### Decision: Use systemd-networkd or iproute2 for TUN interface management

**Rationale**:

- TUN mode requires creating a virtual network interface (`tun0`)
- xray-core can create TUN interface when configured with `tun` outbound
- Requires elevated privileges (CAP_NET_ADMIN or root)
- SteamOS uses systemd-networkd for network management

**Alternatives Considered**:

- **xray-core built-in TUN**: ✅ Chosen - xray-core supports TUN mode natively via config
- **Manual TUN creation**: Rejected - More complex, xray-core handles it better
- **Third-party TUN manager**: Rejected - Unnecessary dependency

**Privilege Management**:

- Use sudo exemption pattern (not root flag in plugin.json)
- Add AppImage to `/etc/sudoers.d/` with NOPASSWD for specific commands
- Check privileges before enabling TUN mode
- Provide clear error messages if privileges insufficient

**Implementation Pattern**:

```python
# Check if TUN can be created
async def check_tun_privileges():
    try:
        # Attempt to create TUN interface (test)
        result = await run_command(['ip', 'tuntap', 'add', 'mode', 'tun', 'test0'])
        await run_command(['ip', 'tuntap', 'del', 'test0'])
        return True
    except PermissionError:
        return False
```

**References**:

- xray-core TUN documentation
- Linux TUN/TAP interfaces: https://www.kernel.org/doc/html/latest/networking/tuntap.html
- SteamOS network management patterns

---

## 3. Kill Switch Implementation

### Decision: Use iptables/nftables rules to block all traffic except xray-core process

**Rationale**:

- Kill switch must block ALL system traffic when proxy disconnects unexpectedly
- iptables/nftables provide kernel-level packet filtering
- Rules must be applied immediately on disconnect detection
- Rules must be removed when connection restored or kill switch disabled

**Alternatives Considered**:

- **iptables DROP rules**: ✅ Chosen - Standard Linux firewall, reliable
- **nftables**: Alternative - Modern replacement, but iptables more widely available
- **Application-level blocking**: Rejected - Can be bypassed, not system-wide
- **NetworkManager disconnect**: Rejected - Too aggressive, disconnects all networks

**Implementation Pattern**:

```python
# Block all traffic except xray-core
async def enable_kill_switch():
    # Allow xray-core process
    await run_command(['iptables', '-A', 'OUTPUT', '-m', 'owner', '--pid-owner', str(xray_pid), '-j', 'ACCEPT'])
    # Block everything else
    await run_command(['iptables', '-A', 'OUTPUT', '-j', 'DROP'])

async def disable_kill_switch():
    # Remove kill switch rules
    await run_command(['iptables', '-D', 'OUTPUT', '-m', 'owner', '--pid-owner', str(xray_pid), '-j', 'ACCEPT'])
    await run_command(['iptables', '-D', 'OUTPUT', '-j', 'DROP'])
```

**Edge Cases**:

- Must handle iptables rules cleanup on plugin unload
- Must preserve existing firewall rules
- Must work with SteamOS firewall configuration
- Must not conflict with Steam ports (UDP 27015-27030) when blocking

**References**:

- iptables documentation
- Linux firewall best practices
- SteamOS firewall considerations

---

## 4. VLESS URL Validation and Parsing

### Decision: Parse VLESS URLs using regex and validate against xray-core config schema

**Rationale**:

- VLESS URLs follow format: `vless://uuid@host:port?params#name`
- Must validate UUID format, host/port, and parameter keys
- Must support subscription URLs (base64-encoded JSON array)
- Must reject invalid formats before storing

**Alternatives Considered**:

- **Regex validation**: ✅ Chosen - Fast, sufficient for URL format
- **Full xray-core config validation**: ✅ Combined - Validate against xray-core after parsing
- **Third-party parser**: Rejected - Unnecessary dependency, simple format

**Implementation Pattern**:

```python
import re
import base64
import json

VLESS_URL_PATTERN = r'^vless://([a-f0-9-]+)@([^:]+):(\d+)(\?[^#]*)?(#.*)?$'

def validate_vless_url(url: str) -> bool:
    match = re.match(VLESS_URL_PATTERN, url)
    if not match:
        return False
    # Additional validation: UUID format, port range, etc.
    return True

def parse_subscription_url(url: str) -> list:
    # Handle subscription-style URLs (base64 encoded JSON)
    try:
        decoded = base64.b64decode(url)
        configs = json.loads(decoded)
        return configs
    except:
        return []
```

**References**:

- VLESS protocol specification
- xray-core config documentation
- NekoRay/NekoBox URL parsing (reference)

---

## 5. GitHub Best Practices for Testing and CI/CD

### Decision: Use GitHub Actions with matrix testing, automated releases, and test coverage

**Rationale**:

- Repository must be testable (unit tests, integration tests)
- CI/CD pipeline ensures code quality before merge
- Automated releases streamline distribution
- Test coverage tracking improves maintainability

**Alternatives Considered**:

- **GitHub Actions**: ✅ Chosen - Native GitHub integration, free for public repos
- **GitLab CI**: Rejected - Not using GitLab
- **Jenkins**: Rejected - Overkill for this project
- **Local testing only**: Rejected - Doesn't ensure quality, no automation

**CI/CD Structure**:

```yaml
# .github/workflows/ci.yml
- Lint frontend (ESLint, TypeScript)
- Test frontend (Jest/Vitest)
- Lint backend (ruff, mypy)
- Test backend (pytest)
- Build plugin (pnpm build)
- Validate plugin structure (check mandatory files)
```

**Testing Strategy**:

- **Unit tests**: Frontend components, backend functions
- **Integration tests**: Backend xray-core interaction, SettingsManager
- **Manual testing**: Required on actual Steam Deck hardware (Game Mode, Desktop Mode)
- **Test coverage**: Aim for >70% coverage on critical paths

**Release Automation**:

- Tag-based releases
- Automated zip creation
- Version bump validation
- Changelog generation

**References**:

- GitHub Actions documentation
- Decky Loader plugin testing patterns
- Open source project best practices

---

## 6. Decky Loader Specific Patterns

### Decision: Follow official Decky plugin template structure and patterns

**Rationale**:

- Official template provides proven structure
- Community expects standard patterns
- Compatibility with Decky Loader build system
- Easier maintenance and updates

**Key Patterns**:

1. **Frontend-Backend Communication**: Use `ServerAPI.callPluginMethod()`
2. **Settings Persistence**: Use `SettingsManager` (never localStorage)
3. **Error Handling**: Surface errors via UI, log to console
4. **State Management**: React state for UI, SettingsManager for persistence
5. **Build Process**: `pnpm run build` after every frontend change

**UI Components**:

- Use `@decky/ui` components for native Steam Deck look
- Follow Steam Deck UI design patterns
- Test in both Game Mode and Desktop Mode

**References**:

- Official Decky Plugin Template: https://github.com/SteamDeckHomebrew/decky-plugin-template
- decky-frontend-lib documentation
- Decky Loader Wiki

---

## 7. SteamOS Constraints and Considerations

### Decision: Respect immutable filesystem, use AppImage/Flatpak patterns, avoid system partition writes

**Rationale**:

- SteamOS has read-only system partition
- Changes to system partition are wiped on updates
- Must use user-writable locations for data
- AppImage/Flatpak are recommended distribution methods

**Storage Locations**:

- Settings: `DECKY_PLUGIN_SETTINGS_DIR` (provided by Decky Loader)
- Binary: `backend/out/` (included in plugin package)
- Logs: User-writable location (e.g., `~/.local/share/`)

**Port Conflicts**:

- Avoid using Steam ports (UDP 27015-27030)
- Use high ports (>32768) for local listeners
- Document port usage in README

**References**:

- SteamOS documentation
- Decky Loader platform constraints
- Arch Linux immutable filesystem patterns

---

## 8. VLESS Reality Client Configuration

### Decision: Use correct xray-core client-side Reality settings

**Rationale**:

- Reality protocol has different config for server vs client
- Client MUST use: `publicKey` (server's public key), `serverName`, `shortId`, `fingerprint`
- Client MUST NOT use: `privateKey`, `dest`, `xver` (server-only settings)
- Using wrong settings causes "Connection reset by peer"

**References**: Xray-core Reality documentation, nekoray implementation

---

## 9. System Proxy with TUN Mode

### Decision: Auto-enable System Proxy when TUN mode connects

**Rationale**:

- TUN mode routes layer-3 traffic; System Proxy (gsettings) routes application-level traffic
- NekoRay enables both together for Desktop Mode compatibility
- gsettings (GNOME/GTK) and kwriteconfig5 (KDE) configure SOCKS/HTTP proxy
- No manual SSH/gsettings step required—plugin applies on connect, clears on disconnect

**Implementation**: `system_proxy.py` module, called from `toggle_connection` when TUN mode connects

**References**: NekoRay QvProxyConfigurator (gsettings, kwriteconfig5)

---

## Summary of Technical Decisions

| Area                  | Decision                                                    | Status      |
| --------------------- | ----------------------------------------------------------- | ----------- |
| xray-core integration | Subprocess management                                       | ✅ Resolved |
| TUN mode              | xray-core built-in TUN with privilege checks                | ✅ Resolved |
| Kill switch           | iptables rules for traffic blocking                         | ✅ Resolved |
| VLESS URL validation  | Regex + xray-core config validation                         | ✅ Resolved |
| Testing strategy      | GitHub Actions CI/CD with unit/integration tests            | ✅ Resolved |
| Decky patterns        | Official template structure                                 | ✅ Resolved |
| SteamOS constraints   | User-writable storage, AppImage distribution                | ✅ Resolved |
| Reality client config | publicKey, serverName, shortId (never privateKey/dest/xver) | ✅ Resolved |
| System Proxy with TUN | Auto-enable gsettings/kwriteconfig5 on TUN connect          | ✅ Resolved |

**All "NEEDS CLARIFICATION" items resolved. Ready for Phase 1 design.**
