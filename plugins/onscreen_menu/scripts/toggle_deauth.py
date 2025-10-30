#!/usr/bin/env python3
# toggle_deauth.py
# Toggle a persisted runtime flag and optionally notify local agent (safe scaffolding).
# This script is invoked by Fancygotchi via run_python.

import os
import json
import time
from datetime import datetime
import subprocess

DEAUTH_FLAG = "/var/lib/pwnagotchi/deauth_enabled"
DEAUTH_ALLOW = "/etc/pwnagotchi/allow_deauth"
DEAUTH_TOKEN = "/etc/pwnagotchi/deauth_token"
DEAUTH_LOG = "/var/log/pwnagotchi/deauth.log"
AGENT_HTTP = "http://127.0.0.1:8422/deauth"  # must match plugin setting

def _audit(entry):
    try:
        os.makedirs(os.path.dirname(DEAUTH_LOG), exist_ok=True)
        with open(DEAUTH_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def _notify_agent(action):
    try:
        if not os.path.exists(DEAUTH_TOKEN):
            return False
        token = open(DEAUTH_TOKEN).read().strip()
        payload = {"action": action, "token": token, "ts": time.time()}
        subprocess.Popen(["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
                          "-d", json.dumps(payload), AGENT_HTTP],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def main():
    # Read current persisted flag (best-effort)
    current = False
    try:
        if os.path.exists(DEAUTH_FLAG):
            v = open(DEAUTH_FLAG).read().strip()
            current = (v == "1")
    except Exception:
        current = False

    new = not current
    try:
        os.makedirs(os.path.dirname(DEAUTH_FLAG), exist_ok=True)
        with open(DEAUTH_FLAG, "w") as f:
            f.write("1" if new else "0")
    except Exception:
        pass

    entry = {"ts": datetime.utcnow().isoformat()+"Z", "action": "arm" if new else "disarm", "method": "script"}

    # If allow file present, try to notify the local agent (non-blocking)
    if os.path.exists(DEAUTH_ALLOW):
        ok = _notify_agent("arm" if new else "disarm")
        entry["agent_notify"] = ok
    else:
        entry["agent_notify"] = False

    _audit(entry)

    # Print a short message; Fancygotchi will surface stdout in logs/UI.
    print("Deauth: %s" % ("ARMED" if new else "DISARMED"))

if __name__ == "__main__":
    main()
