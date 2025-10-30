#!/usr/bin/env bash
# install.sh - install the onscreen_menu plugin package to target Pwnagotchi plugins dir.
set -euo pipefail

# Default destination; change if your build uses another path
DEST_BASE="${1:-/usr/local/src/pwnagotchi/pwnagotchi/plugins}"
PLUGIN_NAME="onscreen_menu"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[*] Installing $PLUGIN_NAME to $DEST_BASE/$PLUGIN_NAME"
sudo mkdir -p "$DEST_BASE"
sudo rm -rf "$DEST_BASE/$PLUGIN_NAME"
sudo mkdir -p "$DEST_BASE/$PLUGIN_NAME"
sudo cp -r "$SRC_DIR"/* "$DEST_BASE/$PLUGIN_NAME/"

# Ensure package export exists
if [ ! -f "$DEST_BASE/$PLUGIN_NAME/__init__.py" ]; then
  echo 'from .onscreen_menu import OnscreenMenu as Plugin' | sudo tee "$DEST_BASE/$PLUGIN_NAME/__init__.py" >/dev/null
fi

# Make scripts executable
if [ -d "$DEST_BASE/$PLUGIN_NAME/scripts" ]; then
  sudo chmod +x "$DEST_BASE/$PLUGIN_NAME/scripts/"*.py 2>/dev/null || true
  sudo chmod +x "$DEST_BASE/$PLUGIN_NAME/scripts/"*.sh 2>/dev/null || true
fi

# Create log dir & file
sudo mkdir -p /var/log/pwnagotchi
sudo touch /var/log/pwnagotchi/deauth.log
sudo chmod 640 /var/log/pwnagotchi/deauth.log

echo "[*] Installed. Enable plugin in config.toml:"
echo "    [main.plugins.onscreen_menu]"
echo "    enabled = true"
echo
echo "Set personality.deauth = false to keep deauth off at boot (recommended)."
echo "Restart pwnagotchi: sudo systemctl restart pwnagotchi"
