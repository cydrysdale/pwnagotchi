#!/usr/bin/env python3
# list_networks.py
# Display captured networks and handshakes from pwnagotchi

import os
import json
import glob
from datetime import datetime


def find_handshake_files():
    """
    Find handshake files in common pwnagotchi locations.

    Returns:
        List of tuples: (filename, modified_time)
    """
    handshake_dirs = [
        "/root/handshakes",
        "/home/pi/handshakes",
        "/var/lib/pwnagotchi/handshakes"
    ]

    handshakes = []

    for dir_path in handshake_dirs:
        if os.path.exists(dir_path):
            # Look for .pcap files
            pcap_files = glob.glob(os.path.join(dir_path, "*.pcap"))
            for pcap in pcap_files:
                try:
                    mtime = os.path.getmtime(pcap)
                    filename = os.path.basename(pcap)
                    # Extract SSID from filename (usually format: SSID_MAC.pcap)
                    ssid = filename.replace('.pcap', '').split('_')[0]
                    handshakes.append((ssid, mtime, pcap))
                except Exception:
                    continue

    # Sort by most recent first
    handshakes.sort(key=lambda x: x[1], reverse=True)
    return handshakes


def find_networks_from_json():
    """
    Find networks from pwnagotchi's memory/session data.

    Returns:
        List of network dictionaries
    """
    json_paths = [
        "/var/lib/pwnagotchi/pwnagotchi.json",
        "/root/.pwnagotchi-data",
        "/home/pi/.pwnagotchi-data"
    ]

    for json_path in json_paths:
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)

                # Try to extract network info (structure varies by version)
                if 'aps' in data:
                    return list(data['aps'].keys())
                elif 'networks' in data:
                    return list(data['networks'].keys())

            except Exception:
                continue

    return []


def display_networks(limit=10):
    """
    Display captured networks with proper formatting for small screen.

    Args:
        limit: Maximum number of networks to display
    """
    print(f"=== Captured Networks (last {limit}) ===")

    # Try to get handshake files first
    handshakes = find_handshake_files()

    if handshakes:
        print(f"\nHandshakes: {len(handshakes)} total\n")
        for i, (ssid, mtime, filepath) in enumerate(handshakes[:limit]):
            # Format timestamp
            dt = datetime.fromtimestamp(mtime)
            time_str = dt.strftime("%m/%d %H:%M")

            # Truncate SSID if too long
            if len(ssid) > 25:
                ssid = ssid[:22] + "..."

            print(f"{i+1:2d}. {ssid:<25s} {time_str}")

    # Also try JSON data
    networks_json = find_networks_from_json()
    if networks_json and not handshakes:
        print(f"\nFrom session data: {len(networks_json)} total\n")
        for i, ssid in enumerate(networks_json[:limit]):
            if len(ssid) > 30:
                ssid = ssid[:27] + "..."
            print(f"{i+1:2d}. {ssid}")

    # If nothing found
    if not handshakes and not networks_json:
        print("\nNo networks found.")
        print("\nSearched locations:")
        print("  - /root/handshakes/")
        print("  - /home/pi/handshakes/")
        print("  - /var/lib/pwnagotchi/")


if __name__ == "__main__":
    display_networks(limit=10)
