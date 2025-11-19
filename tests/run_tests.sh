#!/usr/bin/env bash
# run_tests.sh - Test runner for onscreen_menu plugin
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Onscreen Menu Plugin Test Suite ==="
echo ""

# Check if pytest is available
if command -v pytest >/dev/null 2>&1; then
    echo "[*] Running tests with pytest..."
    python3 -m pytest tests/ -v --tb=short
else
    echo "[*] pytest not found, using unittest..."
    python3 -m unittest discover tests/ -v
fi

echo ""
echo "[+] Tests complete!"
