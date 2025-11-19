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

# Validate destination path for security
if [[ "$DEST_BASE" == *".."* ]]; then
  echo "[!] ERROR: Path traversal detected in destination: $DEST_BASE"
  exit 1
fi

if [[ ! "$DEST_BASE" =~ ^/[a-zA-Z0-9/_-]+$ ]]; then
  echo "[!] ERROR: Invalid destination path format: $DEST_BASE"
  exit 1
fi

# Confirm non-default paths
if [ $# -eq 1 ]; then
  echo "[!] WARNING: Installing to non-default location: $DEST_BASE"
  read -p "    Continue? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[*] Installation cancelled."
    exit 0
  fi
fi

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

# Generate secure deauth token with proper permissions
echo "[*] Generating deauth token..."
head -c 16 /dev/urandom | xxd -p -c 100 | sudo tee /etc/pwnagotchi/deauth_token >/dev/null
sudo chown root:root /etc/pwnagotchi/deauth_token
sudo chmod 600 /etc/pwnagotchi/deauth_token
echo "[*] Deauth token created (permissions: 600)."

# Create allow file with secure permissions
echo "allow" | sudo tee /etc/pwnagotchi/allow_deauth >/dev/null
sudo chmod 644 /etc/pwnagotchi/allow_deauth
