#!/usr/bin/env python3
"""Display Pwnagotchi system status."""

import subprocess
import socket
from datetime import datetime
from typing import Optional


def get_uptime() -> str:
    """Get system uptime."""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"
    except (IOError, ValueError):
        return "unknown"


def get_ip_address() -> str:
    """Get primary IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (OSError, socket.error):
        return "no network"


def get_service_status(service: str = "pwnagotchi") -> str:
    """Get systemd service status."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def get_hostname() -> str:
    """Get system hostname."""
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def main() -> None:
    """Display system status."""
    now = datetime.now().strftime("%H:%M:%S")
    uptime = get_uptime()
    ip = get_ip_address()
    service = get_service_status()
    hostname = get_hostname()

    print(f"Host: {hostname}")
    print(f"Time: {now}")
    print(f"Uptime: {uptime}")
    print(f"IP: {ip}")
    print(f"Service: {service}")


if __name__ == "__main__":
    main()
