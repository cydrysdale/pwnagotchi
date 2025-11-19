#!/usr/bin/env python3
# pisugar_status.py
# Probes PiSugar REST endpoint (127.0.0.1:8421) and prints a short status line.

import json
import sys

try:
    import requests
    USE_REQUESTS = True
except ImportError:
    # Fallback to curl if requests is not available
    import subprocess
    USE_REQUESTS = False


def get_battery_status_requests():
    """Get battery status using requests library (preferred)."""
    try:
        response = requests.get("http://127.0.0.1:8421/v1/battery", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            pct = int(data.get("percent", -1))
            chg = data.get("charging", False)
            return f"PiSugar: {pct}%{' ⚡' if chg else ''}"
    except requests.exceptions.ConnectionError:
        return "PiSugar: not connected"
    except requests.exceptions.Timeout:
        return "PiSugar: timeout"
    except Exception as e:
        return f"PiSugar: error ({type(e).__name__})"
    return "PiSugar: n/a"


def get_battery_status_curl():
    """Fallback: Get battery status using curl."""
    try:
        out = subprocess.check_output(
            ["curl", "-s", "http://127.0.0.1:8421/v1/battery", "--max-time", "2"],
            timeout=3.0,
            stderr=subprocess.DEVNULL
        )
        data = json.loads(out.decode("utf-8", "ignore"))
        pct = int(data.get("percent", -1))
        chg = data.get("charging", False)
        return f"PiSugar: {pct}%{' ⚡' if chg else ''}"
    except Exception:
        return "PiSugar: n/a"


if __name__ == "__main__":
    if USE_REQUESTS:
        status = get_battery_status_requests()
    else:
        status = get_battery_status_curl()
    print(status)
