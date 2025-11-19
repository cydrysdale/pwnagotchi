#!/usr/bin/env python3
"""
utils.py - Shared utilities for onscreen_menu plugin
Provides common functions for audit logging, agent notifications, and validation.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Tuple, Optional

# Constants - centralized configuration
DEAUTH_FLAG = "/var/lib/pwnagotchi/deauth_enabled"
DEAUTH_ALLOW = "/etc/pwnagotchi/allow_deauth"
DEAUTH_TOKEN = "/etc/pwnagotchi/deauth_token"
DEAUTH_LOG = "/var/log/pwnagotchi/deauth.log"
AGENT_HTTP = "http://127.0.0.1:8422/deauth"


def audit(entry: Dict) -> bool:
    """
    Append an audit entry to the deauth log file.

    Args:
        entry: Dictionary containing audit information

    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(DEAUTH_LOG), exist_ok=True)
        with open(DEAUTH_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        logging.error(f"Audit logging failed: {e}")
        return False


def validate_url(url: str) -> bool:
    """
    Validate that a URL is safe to use.

    Args:
        url: URL string to validate

    Returns:
        True if URL appears safe, False otherwise
    """
    # Only allow localhost URLs for agent communication
    if not url.startswith(("http://127.0.0.1:", "http://localhost:")):
        logging.warning(f"Invalid URL rejected: {url}")
        return False
    return True


def notify_agent(action: str) -> Tuple[bool, Optional[str]]:
    """
    Notify a local agent endpoint about deauth state changes.
    Uses requests library for safer HTTP communication.

    Args:
        action: The action to notify about ("arm" or "disarm")

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        import requests
    except ImportError:
        logging.warning("requests library not available, falling back to curl")
        return _notify_agent_curl(action)

    try:
        # Validate token file exists and is readable
        if not os.path.exists(DEAUTH_TOKEN):
            return False, "token-missing"

        # Read token with proper error handling
        try:
            with open(DEAUTH_TOKEN, 'r') as f:
                token = f.read().strip()
        except (IOError, OSError) as e:
            return False, f"token-read-error: {e}"

        # Validate token is not empty
        if not token:
            return False, "token-empty"

        # Validate URL before use
        if not validate_url(AGENT_HTTP):
            return False, "invalid-url"

        # Prepare payload
        payload = {
            "action": action,
            "token": token,
            "ts": time.time()
        }

        # Make request with timeout
        response = requests.post(
            AGENT_HTTP,
            json=payload,
            timeout=2.0,
            headers={"Content-Type": "application/json"}
        )

        # Check response status
        if response.status_code == 200:
            return True, None
        else:
            return False, f"http-{response.status_code}"

    except requests.exceptions.Timeout:
        return False, "timeout"
    except requests.exceptions.ConnectionError:
        return False, "connection-refused"
    except Exception as e:
        logging.exception("Agent notification failed")
        return False, f"error: {str(e)}"


def _notify_agent_curl(action: str) -> Tuple[bool, Optional[str]]:
    """
    Fallback notification using curl (less secure, for compatibility).
    Only used if requests library is not available.

    Args:
        action: The action to notify about

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    import subprocess

    try:
        if not os.path.exists(DEAUTH_TOKEN):
            return False, "token-missing"

        with open(DEAUTH_TOKEN, 'r') as f:
            token = f.read().strip()

        if not token:
            return False, "token-empty"

        if not validate_url(AGENT_HTTP):
            return False, "invalid-url"

        payload = {
            "action": action,
            "token": token,
            "ts": time.time()
        }

        # Use subprocess.run with timeout for better control
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
                AGENT_HTTP,
                "--max-time", "2"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=3.0
        )

        if result.returncode == 0:
            return True, None
        else:
            return False, f"curl-exit-{result.returncode}"

    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        logging.exception("Agent notification (curl) failed")
        return False, f"error: {str(e)}"


def check_permit() -> Tuple[bool, str]:
    """
    Check if deauth operations are permitted based on gate files.

    Returns:
        Tuple of (permitted: bool, reason: str)
    """
    if not os.path.exists(DEAUTH_ALLOW):
        return False, "allow-file-missing"
    if not os.path.exists(DEAUTH_TOKEN):
        return False, "token-missing"
    return True, "ok"


def read_deauth_state() -> bool:
    """
    Read the current deauth state from the flag file.

    Returns:
        True if deauth is enabled, False otherwise
    """
    try:
        if os.path.exists(DEAUTH_FLAG):
            with open(DEAUTH_FLAG, 'r') as f:
                value = f.read().strip()
                return value == "1"
    except Exception as e:
        logging.error(f"Failed to read deauth state: {e}")
    return False


def write_deauth_state(enabled: bool) -> bool:
    """
    Write the deauth state to the flag file.

    Args:
        enabled: True to enable deauth, False to disable

    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(DEAUTH_FLAG), exist_ok=True)
        with open(DEAUTH_FLAG, 'w') as f:
            f.write("1" if enabled else "0")
        return True
    except Exception as e:
        logging.error(f"Failed to write deauth state: {e}")
        return False


def create_audit_entry(action: str, method: str = "script", **kwargs) -> Dict:
    """
    Create a standardized audit log entry.

    Args:
        action: The action being audited (e.g., "arm", "disarm")
        method: How the action was triggered (default: "script")
        **kwargs: Additional fields to include in the entry

    Returns:
        Dictionary containing the audit entry
    """
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "method": method
    }
    entry.update(kwargs)
    return entry
