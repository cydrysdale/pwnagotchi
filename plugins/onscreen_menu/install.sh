#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="/usr/local/share/pwnagotchi/custom-plugins/onscreen_menu"
CFG="/etc/pwnagotchi/config.toml"

# Ensure target dir exists (in case user copied just the files)
sudo mkdir -p /usr/local/share/pwnagotchi/custom-plugins

# If running from a cloned repo elsewhere, copy into the canonical location
if [ ! -f "$PLUGIN_DIR/onscreen_menu.py" ]; then
  SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  sudo rm -rf "$PLUGIN_DIR"
  sudo mkdir -p "$PLUGIN_DIR"
  sudo cp -r "$SRC_DIR/"* "$PLUGIN_DIR/"
fi

# Ownership/permissions
sudo chown -R root:root "$PLUGIN_DIR"
sudo chmod -R a+rX "$PLUGIN_DIR"

# System convenience deps (safe if already installed)
sudo apt-get update
sudo apt-get install -y python3-pip fonts-dejavu rclone || true

# Python deps
sudo pip3 install -r "$PLUGIN_DIR/requirements.txt"

# Enable plugin block if missing
sudo touch "$CFG"
if ! grep -q '^\s*\[main\.plugins\.onscreen_menu\]' "$CFG"; then
  cat <<'EOF' | sudo tee -a "$CFG" >/dev/null

[main.plugins.onscreen_menu]
enabled = true
# rclone_remote = "gdrive:pwna-logs"
EOF
fi

# Restart pwnagotchi service if present
UNIT="$(systemctl list-units --type=service --all | awk '{print $1}' | grep -i pwnagotchi | head -n1 || true)"
if [ -n "$UNIT" ]; then
  sudo systemctl restart "$UNIT" || true
fi

echo "onscreen_menu installed."
