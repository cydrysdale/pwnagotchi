#!/usr/bin/env python3
# toggle_deauth.py
# Toggle a persisted runtime flag and optionally notify local agent (safe scaffolding).
# This script is invoked by Fancygotchi via run_python.

import os
import sys

# Add plugin directory to path for imports
HERE = os.path.dirname(__file__)
PLUGIN_DIR = os.path.dirname(HERE)
sys.path.insert(0, PLUGIN_DIR)

try:
    from utils import (
        read_deauth_state,
        write_deauth_state,
        notify_agent,
        audit,
        create_audit_entry,
        check_permit,
        DEAUTH_ALLOW
    )
except ImportError:
    print("ERROR: Failed to import utils module")
    sys.exit(1)


def main():
    """Toggle deauth state with proper error handling and audit logging."""
    # Read current state
    current_state = read_deauth_state()
    new_state = not current_state

    # Write new state
    if not write_deauth_state(new_state):
        print("ERROR: Failed to write deauth state")
        return

    # Create audit entry
    action = "arm" if new_state else "disarm"
    entry = create_audit_entry(action, method="script")

    # Try to notify agent if allowed
    agent_notified = False
    agent_error = None
    if os.path.exists(DEAUTH_ALLOW):
        agent_notified, agent_error = notify_agent(action)
        entry["agent_notify"] = agent_notified
        if agent_error:
            entry["agent_error"] = agent_error
    else:
        entry["agent_notify"] = False
        entry["agent_error"] = "allow-file-missing"

    # Log the action
    if not audit(entry):
        print("WARNING: Audit logging failed")

    # Print status message for UI
    status = "ARMED" if new_state else "DISARMED"
    print(f"Deauth: {status}")

    if agent_error and agent_error != "allow-file-missing":
        print(f"(Agent notify: {agent_error})")


if __name__ == "__main__":
    main()
