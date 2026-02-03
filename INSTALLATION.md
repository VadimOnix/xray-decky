# Installation Guide: Xray Decky Plugin

## TUN Mode Privilege Setup

TUN mode allows system-wide traffic routing through the proxy. It requires elevated privileges to create network interfaces.

### Method 1: Sudo Exemption (Recommended)

This method allows the plugin to create TUN interfaces without password prompts.

#### Step 1: Enable Developer Mode

1. Go to Settings → System
2. Enable Developer Mode

#### Step 2: Create Sudoers Configuration

1. Open Konsole (Desktop Mode) or SSH into your Steam Deck
2. Create a sudoers configuration file:
   ```bash
   sudo nano /etc/sudoers.d/decky-tun
   ```

3. Add the following lines:
   ```
   # Allow Decky Loader to manage TUN interfaces
   deck ALL=(ALL) NOPASSWD: /usr/bin/ip tuntap add mode tun *
   deck ALL=(ALL) NOPASSWD: /usr/bin/ip tuntap del mode tun *
   ```

4. Save and exit (Ctrl+X, then Y, then Enter)

5. Set correct permissions:
   ```bash
   sudo chmod 0440 /etc/sudoers.d/decky-tun
   ```

6. Verify the configuration:
   ```bash
   sudo visudo -c -f /etc/sudoers.d/decky-tun
   ```
   Should output: `/etc/sudoers.d/decky-tun: parsed OK`

#### Step 3: Verify in Plugin

1. Open the Xray Decky plugin in Decky Loader
2. The plugin will automatically check for privileges
3. If setup is correct, TUN mode toggle will be enabled

### Method 2: Linux Capabilities (Advanced)

This method uses Linux capabilities instead of sudo.

1. Find the Decky Loader binary path
2. Set CAP_NET_ADMIN capability:
   ```bash
   sudo setcap cap_net_admin+ep /path/to/decky-loader
   ```

**Note**: This method is more complex and may not work with AppImage/Flatpak distributions.

### Troubleshooting

#### "Insufficient privileges" error

1. Verify sudoers file exists and has correct permissions:
   ```bash
   ls -l /etc/sudoers.d/decky-tun
   ```
   Should show: `-r--r----- 1 root root`

2. Test sudo command manually:
   ```bash
   sudo ip tuntap add mode tun test0
   sudo ip tuntap del mode tun test0
   ```
   Should work without password prompt

3. Check sudoers syntax:
   ```bash
   sudo visudo -c
   ```

#### TUN mode still not working / traffic not routed through proxy

1. **Verify TUN interface exists** (with plugin running and TUN enabled):
   ```bash
   ip link show xray0
   # or: ip link show tun0
   ```

2. **System routing**: Xray does not auto-modify the system routing table. If traffic still uses your real IP, ensure default route points to the TUN interface. With the plugin running as root and TUN enabled:
   ```bash
   # Check current routes
   ip route
   # The default route should go via xray0 (or tun0) when TUN is active
   ```
   If the interface exists but traffic bypasses it, you may need to add routes manually (advanced; consult Xray TUN docs).

3. Check plugin logs for detailed error messages

### Security Considerations

- The sudo exemption is limited to specific ip commands only
- It does not grant full root access
- The configuration is read-only and cannot be modified by the plugin
- Always verify the sudoers file syntax before saving

### Reverting Changes

To remove the sudo exemption:

```bash
sudo rm /etc/sudoers.d/decky-tun
```

The plugin will continue to work in SOCKS proxy mode without TUN mode.
