#!/usr/bin/env bash
# upload_logs.sh
# Archive and upload pwnagotchi logs to remote storage (rclone, scp, or local backup)

set -euo pipefail

# Configuration
LOG_DIR="/var/log/pwnagotchi"
BACKUP_DIR="/tmp/pwnagotchi-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="pwnagotchi-logs_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"

echo "=== Pwnagotchi Log Upload ==="

# Check if log directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "ERROR: Log directory not found: $LOG_DIR"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create archive
echo "[*] Creating archive: $ARCHIVE_NAME"
if tar -czf "$ARCHIVE_PATH" -C "$(dirname "$LOG_DIR")" "$(basename "$LOG_DIR")" 2>/dev/null; then
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
    echo "[+] Archive created: $ARCHIVE_SIZE"
else
    echo "[!] ERROR: Failed to create archive"
    exit 1
fi

# Try rclone first (if configured)
if command -v rclone >/dev/null 2>&1; then
    # Check for rclone remote configuration in plugin config
    # (This would be read from /etc/pwnagotchi/config.toml in production)
    RCLONE_REMOTE="${RCLONE_REMOTE:-}"

    if [ -n "$RCLONE_REMOTE" ]; then
        echo "[*] Uploading to rclone remote: $RCLONE_REMOTE"
        if rclone copy "$ARCHIVE_PATH" "$RCLONE_REMOTE" --progress 2>&1 | head -n 5; then
            echo "[+] Upload successful!"
            echo "[*] Cleaning up local archive..."
            rm -f "$ARCHIVE_PATH"
            exit 0
        else
            echo "[!] WARNING: rclone upload failed"
        fi
    else
        echo "[!] INFO: rclone available but RCLONE_REMOTE not configured"
        echo "    Set in config: [main.plugins.onscreen_menu]"
        echo "                   rclone_remote = \"remote:path\""
    fi
fi

# Fallback: SCP (if SSH_UPLOAD_TARGET is set)
SSH_UPLOAD_TARGET="${SSH_UPLOAD_TARGET:-}"
if [ -n "$SSH_UPLOAD_TARGET" ] && command -v scp >/dev/null 2>&1; then
    echo "[*] Uploading via SCP to: $SSH_UPLOAD_TARGET"
    if scp -o ConnectTimeout=10 "$ARCHIVE_PATH" "$SSH_UPLOAD_TARGET" 2>&1 | tail -n 3; then
        echo "[+] Upload successful!"
        rm -f "$ARCHIVE_PATH"
        exit 0
    else
        echo "[!] WARNING: SCP upload failed"
    fi
fi

# Final fallback: Keep local backup
echo "[*] No remote upload configured."
echo "[*] Archive saved locally:"
echo "    $ARCHIVE_PATH"
echo ""
echo "To configure upload, set one of:"
echo "  1. RCLONE_REMOTE env var or plugin config"
echo "  2. SSH_UPLOAD_TARGET env var (user@host:/path)"
echo ""
echo "Archive will remain in: $BACKUP_DIR"

# List existing backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo ""
    echo "Existing backups: $BACKUP_COUNT"
    ls -lh "$BACKUP_DIR"/*.tar.gz | tail -n 5
fi

exit 0
