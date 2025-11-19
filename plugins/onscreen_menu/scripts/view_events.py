#!/usr/bin/env python3
# view_events.py
# Display recent system events from journalctl (pwnagotchi service logs)

import subprocess
import sys


def get_pwnagotchi_events(lines=40):
    """
    Retrieve recent pwnagotchi service events from journalctl.

    Args:
        lines: Number of log lines to retrieve (default: 40)

    Returns:
        String containing formatted log output
    """
    try:
        # Try to find pwnagotchi service logs
        services = ["pwnagotchi", "pwnagotchi-noai"]

        for service in services:
            try:
                result = subprocess.run(
                    ["journalctl", "-u", service, "-n", str(lines), "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )

                if result.returncode == 0 and result.stdout.strip():
                    # Format output for small screen
                    lines_list = result.stdout.strip().split('\n')
                    # Show service name and line count
                    print(f"=== {service} (last {len(lines_list)} lines) ===")

                    # Show recent entries (truncate if needed for small display)
                    for line in lines_list[-lines:]:
                        # Truncate long lines for display
                        if len(line) > 80:
                            print(line[:77] + "...")
                        else:
                            print(line)
                    return

            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue

        # Fallback: try generic journal
        print("=== System Events (fallback) ===")
        try:
            result = subprocess.run(
                ["journalctl", "-n", str(lines), "--no-pager", "-p", "err"],
                capture_output=True,
                text=True,
                timeout=5.0
            )

            if result.returncode == 0 and result.stdout.strip():
                lines_list = result.stdout.strip().split('\n')
                for line in lines_list[-lines:]:
                    if len(line) > 80:
                        print(line[:77] + "...")
                    else:
                        print(line)
            else:
                print("No recent errors found.")

        except Exception as e:
            print(f"Error accessing system logs: {type(e).__name__}")

    except Exception as e:
        print(f"ERROR: Failed to retrieve events: {e}")
        sys.exit(1)


if __name__ == "__main__":
    get_pwnagotchi_events(lines=40)
