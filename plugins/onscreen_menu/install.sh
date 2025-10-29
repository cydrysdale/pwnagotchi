#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="/etc/pwnagotchi/custom-plugins/onscreen_menu"
CFG="/etc/pwnagotchi/config.toml"

sudo mkdir -p /etc/pwnagotchi/custom-plugins

# If running from a cloned repo elsewhere, copy into /etc path
if [ ! -f "$PLUGIN_DIR/onscreen_menu.py" ]; then
  SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  sudo rm -rf "$PLUGIN_DIR"
  sudo mkdir -p "$PLUGIN_DIR"
  sudo cp -r "$SRC_DIR/"* "$PLUGIN_DIR/"
fi

sudo chown -R root:root "$PLUGIN_DIR"
sudo chmod -R a+rX "$PLUGIN_DIR"

# Deps
sudo apt-get update
sudo apt-get install -y python3-pip fonts-dejavu rclone || true
sudo pip3 install -r "$PLUGIN_DIR/requirements.txt"

# Enable plugin in config if missing
sudo touch "$CFG"
if ! grep -q '^\s*\[main\.plugins\.onscreen_menu\]' "$CFG"; then
  cat <<'EOF' | sudo tee -a "$CFG" >/dev/null

[main.plugins.onscreen_menu]
enabled = true
# rclone_remote = "gdrive:pwna-logs"
EOF
fi

# Restart service if detected
UNIT="$(systemctl list-units --type=service --all | awk '{print $1}' | grep -i pwnagotchi | head -n1 || true)"
if [ -n "$UNIT" ]; then
  sudo systemctl restart "$UNIT" || true
fi

echo "onscreen_menu installed to $PLUGIN_DIR"
