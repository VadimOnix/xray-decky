#!/usr/bin/env bash
# Install Xray Decky plugin from GitHub releases
# Run from Steam Deck Desktop Mode (double-click .desktop or run in Konsole)

set -euo pipefail

readonly PLUGIN_NAME="xray-decky"
readonly PLUGINS_DIR="${HOME}/homebrew/plugins"
readonly REPO_API="https://api.github.com/repos/VadimOnix/xray-decky/releases/latest"
readonly EXIT_DECKY_MISSING=2
readonly EXIT_DEPS_MISSING=3
readonly EXIT_DOWNLOAD_FAILED=4

err() {
  echo "Error: $*" >&2
}

check_decky() {
  if [[ ! -d "${PLUGINS_DIR}" ]]; then
    err "Decky Loader plugins directory not found: ${PLUGINS_DIR}"
    err "Please install Decky Loader first: https://decky.xyz"
    exit "${EXIT_DECKY_MISSING}"
  fi
}

check_deps() {
  local missing=()
  command -v curl &>/dev/null || missing+=(curl)
  command -v unzip &>/dev/null || missing+=(unzip)
  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required tools: ${missing[*]}"
    err "Install with: sudo pacman -S curl unzip"
    exit "${EXIT_DEPS_MISSING}"
  fi
}

get_latest_zip_url() {
  # Avoid pipefail exit when grep finds no match (e.g. API error/rate limit)
  curl -sSL "${REPO_API}" | grep -E '"browser_download_url".*xray-decky.*\.zip"' | head -1 | sed -n 's/.*"browser_download_url": *"\([^"]*\)".*/\1/p' || true
}

main() {
  echo "Xray Decky Plugin Installer"
  echo "==========================="

  check_deps
  check_decky

  local zip_url
  zip_url=$(get_latest_zip_url)
  if [[ -z "${zip_url:-}" ]]; then
    err "Could not find release download URL"
    exit "${EXIT_DOWNLOAD_FAILED}"
  fi

  echo "Downloading latest release..."
  local tmpdir
  tmpdir=$(mktemp -d)
  trap '[[ -n "${tmpdir:-}" && -d "${tmpdir}" ]] && rm -rf "${tmpdir}"' EXIT

  if ! curl -sSLo "${tmpdir}/plugin.zip" "${zip_url}"; then
    err "Download failed"
    exit "${EXIT_DOWNLOAD_FAILED}"
  fi

  echo "Extracting to ${PLUGINS_DIR}/${PLUGIN_NAME}..."
  # Unzip to tmpdir (user-writable), then install to plugins dir with sudo (often root-owned on Deck)
  unzip -o -q "${tmpdir}/plugin.zip" -d "${tmpdir}"
  sudo rm -rf "${PLUGINS_DIR:?}/${PLUGIN_NAME:?}"
  sudo cp -r "${tmpdir}/${PLUGIN_NAME}" "${PLUGINS_DIR}/"
  # So Decky (running as current user) can read the plugin
  sudo chown -R "$(whoami):" "${PLUGINS_DIR}/${PLUGIN_NAME}" 2>/dev/null || true

  if [[ -f "${PLUGINS_DIR}/${PLUGIN_NAME}/bin/xray-core" ]]; then
    sudo chmod +x "${PLUGINS_DIR}/${PLUGIN_NAME}/bin/xray-core"
  fi

  echo "Restarting plugin loader..."
  if command -v systemctl &>/dev/null; then
    sudo -n systemctl restart plugin_loader 2>/dev/null || echo "  (Restart skipped; you may need to restart Decky Loader manually)"
  fi

  echo ""
  echo "Installation complete!"
  echo "Switch to Gaming Mode and open Quick Access (⋯) to see Xray Decky."
}

main "$@"
