#!/usr/bin/env python3
# pisugar_status.py
# Probes PiSugar REST endpoint (127.0.0.1:8421) and prints a short status line.

import subprocess
import json
import sys

try:
    out = subprocess.check_output(["curl", "-s", "http://127.0.0.1:8421/v1/battery"], timeout=1.0)
    data = json.loads(out.decode("utf-8", "ignore"))
    pct = int(data.get("percent", -1))
    chg = data.get("charging", False)
    s = f"PiSugar: {pct}%{' ⚡' if chg else ''}"
    print(s)
except Exception:
    print("PiSugar: n/a")
    sys.exit(0)
