#!/usr/bin/env python3
# onscreen_menu.py
# On-device menu for Pwnagotchi on Waveshare 1.3" LCD HAT (ST7789).
# Controls (per user request):
#   UP/DOWN .......... navigate
#   RIGHT or KEY1 .... Select / Confirm
#   LEFT  or KEY2 .... Back / Exit
#   KEY3 ............. Toggle menu open/close
#   Joystick press ... Unused (prevents accidental nav while pressing)
#
# Features:
#   - Status (uptime/service/IP)
#   - Restart pwnagotchi service
#   - Toggle deauth in /etc/pwnagotchi/config.toml (service auto-restarts)
#   - Reboot / Shutdown device
#   - View events (40)  [journalctl -u <pwnagotchi*> if available, fallback to generic journal/grep]
#   - Saved nets (10)   [pulls from common json/paths, fallback to journal/grep]
#   - Upload logs       [tar.gz; optional rclone upload to configured remote]
#
# Notes:
#   - Designed/tested against Jayofelony's "pwnagotchi-noai" build which ships the 'lcdhat' driver (ST7789 LCD_1inch3).
#   - Backlight is BCM 24 in that driver; we do NOT bind it here.
# Safe defaults: deauth OFF at boot, runtime toggle only, guarded notify to local agent.
# Injects menu via ui._update (Fancygotchi-compatible).
# Integrates with Fancygotchi (V0r-T3x) menu API. 

import os
import json
import time
import logging
import subprocess
import threading
from datetime import datetime

try:
    from pwnagotchi.plugins import Plugin
except Exception:
    class Plugin(object):
        pass

HERE = os.path.dirname(__file__)
SCRIPTS = os.path.join(HERE, "scripts")
TOOLS = os.path.join(HERE, "tools")

# Gate & artifact locations (device-level)
DEAUTH_FLAG = "/var/lib/pwnagotchi/deauth_enabled"
DEAUTH_ALLOW = "/etc/pwnagotchi/allow_deauth"
DEAUTH_TOKEN = "/etc/pwnagotchi/deauth_token"
DEAUTH_LOG = "/var/log/pwnagotchi/deauth.log"
AGENT_HTTP = "http://127.0.0.1:8422/deauth"   # optional local agent endpoint

# UI throttling
_UPDATE_HZ = 2.0
_UPDATE_DT = 1.0 / _UPDATE_HZ

class OnscreenMenu(Plugin):
    __author__ = "you"
    __version__ = "1.0.0"
    __name__ = "onscreen_menu"
    __license__ = "MIT"
    __description__ = "Fancygotchi-friendly on-screen menu + safe scaffolds."

    def __init__(self):
        super().__init__()
        self._ui = None
        self._last_ui_tick = 0.0
        self._lock = threading.Lock()
        self._deauth_enabled = False

    # lifecycle hooks -----------------------------------------------------
    def on_loaded(self):
        logging.info("[onscreen_menu] loaded")

    def on_unload(self, ui):
        logging.info("[onscreen_menu] unloading")

    def on_ui_setup(self, ui):
        """Called when UI is available. Inject menu and perform layout adjustments."""
        self._ui = ui
        logging.info("[onscreen_menu] ui setup")
        # Push the menu via dict_part["menu"] (supported by Fancygotchi)
        try:
            self._push_menu_tree()
        except Exception:
            logging.exception("[onscreen_menu] failed to push menu")
        # Apply small theme-safe layout changes
        try:
            self._apply_initial_layout()
        except Exception:
            logging.exception("[onscreen_menu] initial layout failed")

    def on_ui_update(self, ui):
        """Throttled update loop. Keep it lightweight to suit Zero 2 W."""
        now = time.time()
        if now - self._last_ui_tick < _UPDATE_DT:
            return
        self._last_ui_tick = now
        # nothing heavy per-frame

    # menu injection -----------------------------------------------------
    def _push_menu_tree(self):
        if not self._ui:
            return

        # Build menu tree. Use run_python/run_bash actions that reference package scripts.
        # run_python/run_bash expect a file path. We use absolute paths derived from package location.
        # Keep entries simple and fast — scripts should exit quickly.
        menu_tree = {
            "Main menu": {
                "options": {"title": "Main", "back": None},
                "u": {"title": "Utilities →", "action": "submenu", "value": "Utilities"},
            },
            "Utilities": {
                "options": {"title": "Utilities", "back": "Main menu"},
                "i1": {"title": "Status",               "action": "run_python", "file": os.path.join(SCRIPTS, "show_status.py")},
                "i2": {"title": "Restart pwnagotchi",   "action": "restart", "mode": "menu"},
                "i3": {"title": "Toggle deauth",        "action": "run_python", "file": os.path.join(SCRIPTS, "toggle_deauth.py")},
                "i4": {"title": "Reboot device",        "action": "reboot", "mode": "menu"},
                "i5": {"title": "Shutdown device",      "action": "shutdown"},
                "sep": {"title": "────────────",        "action": "submenu", "value": "Utilities"},
                "i6": {"title": "View events (40)",     "action": "run_python", "file": os.path.join(SCRIPTS, "view_events.py")},
                "i7": {"title": "Saved nets (10)",      "action": "run_python", "file": os.path.join(SCRIPTS, "list_networks.py")},
                "i8": {"title": "Upload logs",          "action": "run_bash",   "file": os.path.join(SCRIPTS, "upload_logs.sh")},
                "i9": {"title": "PiSugar: battery",     "action": "run_python", "file": os.path.join(SCRIPTS, "pisugar_status.py")},
            }
        }

        payload = {"update": True, "partial": True, "dict_part": {"menu": menu_tree}}
        # ui._update.update is how Fancygotchi accepts the menu injection
        try:
            self._ui._update.update(payload)
            logging.debug("[onscreen_menu] menu injected")
        except Exception:
            logging.exception("[onscreen_menu] ui._update failed")

    # layout tweaks -----------------------------------------------------
    def _apply_initial_layout(self):
        if not self._ui:
            return
        dict_part = {"widget": {}}
        # pin bottom strip widgets if theme supports anchors
        for w in ("pwned", "mode"):
            dict_part["widget"].setdefault(w, {}).update({"position": ["bottom", "center"]})
        # increase status font slightly
        dict_part["widget"].setdefault("status", {}).update({"font_size": "+2", "position": ["center", "center"]})
        # enlarge face if supported
        dict_part["widget"].setdefault("face", {}).update({"scale": 1.4})
        try:
            self._ui._update.update({"update": True, "partial": True, "dict_part": dict_part})
        except Exception:
            logging.exception("[onscreen_menu] apply_initial_layout update failed")

# Helper utilities exported for local scripts to reuse -------------------
def _audit(entry):
    try:
        os.makedirs(os.path.dirname(DEAUTH_LOG), exist_ok=True)
        with open(DEAUTH_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        logging.exception("_audit failed")

def _permit():
    if not os.path.exists(DEAUTH_ALLOW):
        return False, "allow-file-missing"
    if not os.path.exists(DEAUTH_TOKEN):
        return False, "token-missing"
    return True, "ok"

def _notify_agent(action):
    """Notify a local agent endpoint non-blocking. Returns True if started."""
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
        logging.exception("_notify_agent failed")
        return False
