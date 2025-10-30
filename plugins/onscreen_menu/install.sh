#!/usr/bin/env bash
# install.sh - install the onscreen_menu plugin package to target Pwnagotchi plugins dir.
# Usage:
#   sudo ./install.sh                  # default destination
#   sudo ./install.sh /custom/path     # custom plugins directory
set -euo pipefail

# Default destination; change if your Pwnagotchi uses another path
DEST_BASE="${1:-/etc/pwnagotchi/custom_plugins}"
PLUGIN_NAME="onscreen_menu"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[*] Installing $PLUGIN_NAME to $DEST_BASE/$PLUGIN_NAME"

# Prepare destination
sudo mkdir -p "$DEST_BASE"
sudo rm -rf "$DEST_BASE/$PLUGIN_NAME"
sudo mkdir -p "$DEST_BASE/$PLUGIN_NAME"

# Copy plugin package
sudo cp -r "$SRC_DIR"/* "$DEST_BASE/$PLUGIN_NAME/"

# Ensure __init__.py exists so plugin loader can import it as a package
if [ ! -f "$DEST_BASE/$PLUGIN_NAME/__init__.py" ]; then
  echo 'from .onscreen_menu import OnscreenMenu as Plugin' | sudo tee "$DEST_BASE/$PLUGIN_NAME/__init__.py" >/dev/null
fi

# Make bundled scripts executable (if present)
if [ -d "$DEST_BASE/$PLUGIN_NAME/scripts" ]; then
  echo "[*] Making scripts executable..."
  sudo find "$DEST_BASE/$PLUGIN_NAME/scripts" -type f -iname "*.py" -exec chmod +x {} \;
  sudo find "$DEST_BASE/$PLUGIN_NAME/scripts" -type f -iname "*.sh" -exec chmod +x {} \;
fi

# Make tools executable (agent skeleton etc.)
if [ -d "$DEST_BASE/$PLUGIN_NAME/tools" ]; then
  echo "[*] Making tool files executable..."
  sudo find "$DEST_BASE/$PLUGIN_NAME/tools" -type f -iname "*.py" -exec chmod +x {} \;
fi

if [ -f "$DEST_BASE/$PLUGIN_NAME/tools/agent_skeleton.py" ]; then
  echo "[*] Installing agent skeleton to /usr/local/bin/pwn-deauth-agent.py"
  sudo cp "$DEST_BASE/$PLUGIN_NAME/tools/agent_skeleton.py" /usr/local/bin/pwn-deauth-agent.py
  sudo chmod +x /usr/local/bin/pwn-deauth-agent.py
fi

# Create log dir & audit log file with safe permissions
echo "[*] Creating audit log (if missing) and setting permissions..."
sudo mkdir -p /var/log/pwnagotchi
sudo touch /var/log/pwnagotchi/deauth.log
sudo chown root:root /var/log/pwnagotchi/deauth.log
sudo chmod 640 /var/log/pwnagotchi/deauth.log

echo "[*] Install complete."

cat <<-EOF

Next steps:
  1) Enable the plugin in your config (example):
     [main.plugins.$PLUGIN_NAME]
     enabled = true

  2) Ensure deauth is off by default:
     [personality]
     deauth = false

  3) Restart pwnagotchi:
     sudo systemctl restart pwnagotchi

EOF
head -c 16 /dev/urandom | xxd -p -c 100 | sudo tee /etc/pwnagotchi/deauth_token >/dev/null
echo "allow" | sudo tee /etc/pwnagotchi/allow_deauth >/dev/null
echo "[*] Deauth token created."
